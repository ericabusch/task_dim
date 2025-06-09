#!/usr/bin/env python3
# LARGELY BASED OFF SAM NASTASE'S CODE: https://github.com/snastase/narratives/tree/master/code
import argparse
from os import makedirs, remove, chdir
import json, sys
from subprocess import run
from os.path import basename, exists, join, splitext
import pandas as pd
sys.path.append('../')

from natsort import natsorted


# Function for extracting group of (variable number) confounds
def extract_group(confounds_df, groups):
    
    # Expect list, so change if string
    if type(groups) == str:
        groups = [groups]
    
    # Filter for all columns with label
    confounds_group = []
    for group in groups:
        group_cols = [col for col in confounds_df.columns
                      if group in col]
        confounds_group.append(confounds_df[group_cols])
    confounds_group = pd.concat(confounds_group, axis=1)
    
    return confounds_group

# Function for loading in confounds files
def load_confounds(confounds_fn):

    # Load the confounds TSV files
    confounds_df = pd.read_csv(confounds_fn, sep='\t')

    # Load the JSON sidecar metadata
    with open(splitext(confounds_fn)[0] + '.json') as f:
        confounds_meta = json.load(f)

    return confounds_df, confounds_meta

# Function for extracting aCompCor components
def extract_compcor(confounds_df, confounds_meta,
                    n_comps=5, method='tCompCor',
                    tissue=None):

    # Check that we sensible number of components
    assert n_comps > 0

    # Check that method is specified correctly
    assert method in ['aCompCor', 'tCompCor']

    # Check that tissue is specified for aCompCor
    if method == 'aCompCor' and tissue not in ['combined', 'CSF', 'WM']:
        raise AssertionError("Must specify a tissue type "
                             "(combined, CSF, or WM) for aCompCor")

    # Ignore tissue if specified for tCompCor
    if method == 'tCompCor' and tissue:
        print("Warning: tCompCor is not restricted to a tissue "
              f"mask - ignoring tissue specification ({tissue})")
        tissue = None

    # Get CompCor metadata for relevant method
    compcor_meta = {c: confounds_meta[c] for c in confounds_meta
                    if confounds_meta[c]['Method'] == method
                    and confounds_meta[c]['Retained']}

    # If aCompCor, filter metadata for tissue mask
    if method == 'aCompCor':
        compcor_meta = {c: compcor_meta[c] for c in compcor_meta
                        if compcor_meta[c]['Mask'] == tissue}

    # Make sure metadata components are sorted properly
    comp_sorted = natsorted(compcor_meta)
    for i, comp in enumerate(comp_sorted):
        if comp != comp_sorted[-1]:
            comp_next = comp_sorted[i + 1]
            assert (compcor_meta[comp]['SingularValue'] >
                    compcor_meta[comp_next]['SingularValue'])

    # Either get top n components
    if n_comps >= 1.0:
        n_comps = int(n_comps)
        if len(comp_sorted) >= n_comps:
            comp_selector = comp_sorted[:n_comps]
        else:
            comp_selector = comp_sorted
            print(f"Warning: Only {len(comp_sorted)} {method} "
                  f"components available ({n_comps} requested)")

    # Or components necessary to capture n proportion of variance
    else:
        comp_selector = []
        for comp in comp_sorted:
            comp_selector.append(comp)
            if (compcor_meta[comp]['CumulativeVarianceExplained']
                > n_comps):
                break

    # Check we didn't end up with degenerate 0 components
    assert len(comp_selector) > 0

    # Grab the actual component time series
    confounds_compcor = confounds_df[comp_selector]

    return confounds_compcor

def create_afni_confounds(confounds_filename):
    model =  {'confounds':
              ['trans_x', 'trans_y', 'trans_z',
               'rot_x', 'rot_y', 'rot_z', 'cosine'],
              'aCompCor': [{'n_comps': 5, 'tissue': 'CSF'},
                           {'n_comps': 5, 'tissue': 'WM'}]}

    confounds_df, confounds_meta = load_confounds(confounds_filename)
    
    # Pop out confound groups of variable number
    groups = set(model['confounds']).intersection(
                    ['cosine', 'motion_outlier'])

    # Grab the requested confounds
    confounds = confounds_df[[c for c in model['confounds']
                              if c not in groups]]
    
    # Grab confound groups if present
    if groups:
        confounds_group = extract_group(confounds_df,
                                        groups)
        confounds = pd.concat([confounds, confounds_group],
                              axis=1)

    # Get aCompCor / tCompCor confounds if requested
    compcors = set(model).intersection(
                    ['aCompCor', 'tCompCor'])
    if compcors:
        for compcor in compcors:
            if type(model[compcor]) == dict:
                model[compcor] = [model[compcor]]

            for compcor_kws in model[compcor]:
                confounds_compcor = extract_compcor(
                    confounds_df,
                    confounds_meta,
                    method=compcor,
                    **compcor_kws)

                confounds = pd.concat([confounds,
                                       confounds_compcor],
                                      axis=1)
    
    return confounds
    



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dataset',type=str)
    parser.add_argument('-t','--task', type=str)
    parser.add_argument('-s', '--subject_id', type=str)
    parser.add_argument('-r','--rerun',default=0,type=int)
    p = parser.parse_args()
    width = 6
    
    # import the right utils/config file
    if p.dataset.lower() == 'narratives': import narratives_utils as utils; import narratives_config as config
    elif p.dataset.lower() == 'adult_restmovie': import adult_restmovie_utils as utils; import adult_restmovie_config as config
    elif p.dataset.lower() == 'camcan': import camcan_utils as utils; import camcan_config as config
    elif p.dataset.lower() == 'infant_restmovie': import infant_restmovie_utils as utils; import infant_restmovie_config as config; p.subject_filter=p.task
    elif p.dataset.lower() == 'cneuromod': import cneuromod_utils as utils; import cneuromod_config as config
    elif p.dataset.lower() == 'partlycloudy': import partlycloudy_utils as utils; import partlycloudy_config as config
    elif p.dataset.lower() == 'hbn': import hbn_utils as utils; import hbn_config as config
    else: print(f'{p.dataset} not valid'); sys.exit(1)

    # Create output AFNI directory if it doesn't exist
    base_dir = utils.get_basedir()
    session = utils.get_subject_site(p.subject_id)
    deriv_dir = join(base_dir, 'derivatives')
    fmriprep_dir = join(utils.get_fmriprep_input_dir(), p.subject_id, 'ses-'+session, 'func')
    
    # Assign an AFNI pipeline output directory (either -smooth or -nosmooth)
    afni_pipe = 'afni-smooth'
    afni_dir = join(deriv_dir, afni_pipe, p.subject_id, 'func')
    makedirs(afni_dir, exist_ok=True)
    chdir(afni_dir)
    # Volumetric smoothing for MNI space
    bold_fn, conf_fn, mask_fn = utils.get_subject_fmriprep_output_files(p.subject_id, p.task)
    out_fn = join(afni_dir, f'{p.subject_id}_task-{p.task}_space-MNI152Lin_desc-sm{width}.nii.gz')
    clean_fn = out_fn.replace(f'desc-sm{width}','desc-clean')
    if exists(clean_fn) and p.rerun == 0:
        print(f'already ran {clean_fn}')
        sys.exit()

    if not exists(out_fn) or p.rerun == 1:
        run(f"3dBlurToFWHM -mask {mask_fn} -FWHM {width} "
                    f"-input {bold_fn} -prefix {out_fn} "
                    f"-blurmaster {bold_fn} -detrend -bmall", shell=True)
        print(f"finished spatial smoothing")
    else:
        print(f'spatial smoothing already performed: ({out_fn}); continuing')
    
    
    # Create AFNI style confound models 
    afni_confound_model = create_afni_confounds(conf_fn)
    ort_fn = join(afni_dir, basename(conf_fn).replace('desc-confounds',
                    f'desc-model').replace('_timeseries.tsv', '.1D'))
    print(f'will save model to {ort_fn}')
    
    afni_confound_model.to_csv(ort_fn, sep='\t', header=False,
                     index=False)
    fn2 = ort_fn.replace('.1D','.csv')
    afni_confound_model.to_csv(fn2, sep=',', index=False)
    print(f"Assembled confound models for {p.subject_id} {p.task} at {fn2}")

    # Run afni confound regression 
    assert exists(ort_fn)
    # Get output clean BOLD filename
    clean_fn = out_fn.replace(f'desc-sm{width}','desc-clean')  
    
    # Get the volumetric mask resampled for this task if necessary
    
    # Perform confound regression via AFNI's 3dTproject    
    run(f"3dTproject -input {out_fn} -ort {ort_fn} -overwrite "
            f"-prefix {clean_fn} -mask {mask_fn} -polort 2", shell=True)

    print(f"Finished model confound regression(s) for {p.subject_id} {p.task}:"
          f"\n  {basename(clean_fn)}")