# resample from high resolution to 3mm MNI space, to match rest-movie dataset
import numpy as np
import os,sys,glob,argparse
import nibabel as nib
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker
from joblib import Parallel, delayed
from nilearn.datasets import load_mni152_template
from nilearn.image import resample_to_img


def run_resampling(subject_id, task):
    try:
        nii_fns, _, new_fns, mask_fns = utils.get_subject_data_fmriprep_output(subject_id, task)
    except:
        print(f'no files found for {subject_id},{task}')
        return
    if len(nii_fns) < 1:
        print(f'no files found for {subject_id},{task}')
        return

    # Check if already present:
    if os.path.exists(new_fns[0]):
        print(f'already ran {subject_id},{task}; returning')
        return new_fns[0]

    for i in range(len(nii_fns)):
        infilename=nii_fns[i]
        maskfilename=mask_fns[i]
        outfilename=new_fns[i]
        try:
            # apply wb mask
            orig = nib.load(infilename)
            mask = nib.load(maskfilename)
        except:
            print(f'{maskfilename} may not exist; returning')
            return infilename

        masker_wb = NiftiMasker(mask_img=mask, standardize=True)
        masked_normed = masker_wb.fit_transform(orig)
        masked_orig = masker_wb.inverse_transform(masked_normed)
        # resample to lower dim
        resampled = resample_to_img(orig, TEMPLATE, interpolation="nearest", force_resample=True)
        nib.save(resampled, outfilename)
        if config.VERBOSE: print(f'saved to {outfilename}, shape {resampled.shape}')
    return mask_fns[0]

def write_filelist(out_filename, list_of_files):
    with open(out_filename, 'w') as f:
        for fn in list_of_files:
            f.write(fn+'\n')
    if config.VERBOSE: print(f'wrote to {out_filename}')

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dataset',type=str)
    parser.add_argument('-v','--verbose', type=int, default=1)
    parser.add_argument('-r', '--resolution', type=int, default=3)
    p = parser.parse_args()

    # import the right utils file
    if p.dataset.lower() == 'narratives': import narratives_utils as utils; import narratives_config as config
    elif p.dataset.lower() == 'camcan': import camcan_utils as utils; import camcan_config as config
    elif p.dataset.lower() == 'cneuromod': import cneurmod_utils as utils; import cneuromod_config as config
    elif p.dataset.lower() == 'hbn': import hbn_utils as utils; import hbn_config as config
    else: print(f'{p.dataset} not valid'); sys.exit(1)
    if p.verbose: print(f'loaded {p.dataset}_utils')

    TEMPLATE = load_mni152_template(p.resolution)
    subject_list = utils.get_intersecting_subjects()

    new_filenames = []
    joblist = []
    for task in utils.get_tasks():
        for sub_id in subject_list:
            #f=run_resampling(sub_id, task)
            joblist.append(delayed(run_resampling)(sub_id, task))
    
    with Parallel(n_jobs=config.NJOBS) as parallel:
        filenames = parallel(joblist)

    success, fails = [], []
    for f in filenames:
        if f == None:
            continue
        if 'mask' in f:
            success.append(f)
        else:
            fails.append(f)
    print(f'failed on {len(fails)}/{len(filenames)}')

    # write out files to intersect mask
    out_filename = f'{utils.get_out_dir()}/files_for_3mm_intersect_mask.txt'
    write_filelist(out_filename, success)

    # write out files to investigate further
    out_filename = f'{utils.get_out_dir()}/failed_loading.txt'
    write_filelist(out_filename, fails)
    

