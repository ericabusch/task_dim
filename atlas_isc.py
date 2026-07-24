import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import os, sys, glob
import nilearn 
import nibabel as nib
import ide_helpers as ide
from scipy import stats
from nilearn import plotting
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker
from task_dim.stats_helpers import timeseries_correlation_permutation
from nilearn.image import math_img, index_img

def load_atlas(atlas_name='Schaefer'):
    if atlas_name == 'Schaefer':
        ATLAS = nilearn.datasets.fetch_atlas_schaefer_2018(resolution_mm=2, yeo_networks=17)
        ATLAS.labels = np.insert(ATLAS.labels, 0, 'Background')
        atlas_image = nib.load(ATLAS.maps)
        atlas_df = pd.DataFrame(ATLAS)
    else:
        print(f'{atlas_name} not implemented')
    return atlas_image, atlas_df

def remove_missing(X, return_mask=True):
    threshold = X.shape[0] // 20 # 5% are 0
    n_missing = np.sum(X==0, axis=0)
    mask = n_missing <= threshold
    if return_mask: return mask
    filtered_X = X[:,mask]
    return filtered_X

def run_subject_isc(test_subject, train_subjects, task, atlas_name='Schaefer', wb_mask=None): 
    atlas_image, atlas_df = load_atlas(atlas_name)
    nii = utils.get_subject_data(test_subject, task)
    if type(nii) == list:
        nii = nii[0]
    if VERBOSE: print(f"Original test shape: {nii.shape}")
    # apply whole-brain mask, then invert
    if not wb_mask:
        wb_mask = utils.get_intersect_mask()
    masker_wb = NiftiMasker(mask_img=wb_mask, standardize=True)
    masked_nii = masker_wb.fit_transform(nii)
    n_timepoints, n_voxels = masked_nii.shape
    test_nii = masker_wb.inverse_transform(masked_nii)
    if VERBOSE: print(f"New test shape: {test_nii.shape}")

    arr = np.empty((n_timepoints, n_voxels))
    for i, train_sub in enumerate(train_subjects):
        nii = utils.get_subject_data(train_sub, task)
        masked_nii = masker_wb.fit_transform(nii)
        masked_nii=np.nan_to_num(masked_nii)
        arr=np.add(arr,masked_nii)
        print(f'added train sub {i}/{len(train_subjects)}')
    arr=arr/len(train_subjects)
    train_nii = masker_wb.inverse_transform(arr)
    if VERBOSE: print(f"train shape: {train_nii.shape} from {arr.shape}")
    results_volume = None
    results_df = pd.DataFrame(columns=['region_name','score','p', 'z'])
    for roi_id in atlas_df.index[1:]:
        roi_mask_img = math_img(f"img == {roi_id}", img=atlas_image)
        masker = NiftiMasker(roi_mask_img, standardize=True)
        test_roi_data = np.nan_to_num(masker.fit_transform(test_nii))
        n_voxels = test_roi_data.shape[1]
        train_roi_data = masker.fit_transform(train_nii)
        # filter missing values
        missing_masks = np.array([remove_missing(X) for X in [train_roi_data, test_roi_data]]) # where everyone's missing
        mask = np.sum(missing_masks, axis=0) # sum across participants; will yield n_subj where all have the value
        mask = mask == len(missing_masks)
        if config.VERBOSE: print(f'including {np.sum(mask)} / {n_voxels}) for roi={roi_id}')
        # now filter every volume with the mask
        train_roi_data = np.squeeze(train_roi_data[:,mask]) 
        test_roi_data = np.squeeze(test_roi_data[:,mask])
        if RUN_STATS:
            # Rolls the timeseries of the test data by a random amount and computes the correlation with the training data, repeated n_permute times to generate a null distribution. 
            # The p-value is computed based on this null distribution.
            # this is expensive and not always done, so only run if requested
            metric = ISC_METRIC# bcvar[0] if len(bcvar) > 0 else 'pearson'
            these_stats = timeseries_correlation_permutation(test_roi_data, train_roi_data, method='time_shift', n_permute=1000, metric=metric, tail='two-tailed', n_jobs=-1, return_perms=False)
            r = these_stats['correlation']
            p = these_stats['p']
            z = these_stats['zstat'] # [stats['correlation'], stats['p'], stats['zstat']]
        else:
            r = stats.pearsonr(test_roi_data.ravel(), train_roi_data.ravel())[0]
            p = np.nan
            z = np.nan
            
        expanded = np.repeat(r, n_voxels).reshape(1,-1).astype("double")
        tokens = atlas_df.iloc[roi_id]['labels']
        roi_str = tokens.decode("UTF-8")
        temp =  masker.inverse_transform(expanded)
        if results_volume == None:
            results_volume = temp
        else:
            v = results_volume
            results_volume = math_img(f'img1 + img2', img1 = v, img2=temp)
        results_df.loc[len(results_df)] = {'region_name':roi_str, 'score':r, 'p':p, 'z':z}

    results_df['task']=np.repeat(task, len(results_df))
    results_df['subject']=np.repeat(test_subject, len(results_df))
    
    return results_df, results_volume


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dataset',type=str)
    parser.add_argument('-t','--task', type=str)
    parser.add_argument('-i', '--subject_idx', type=int)
    parser.add_argument('-s','--subject_filter', type=str, default='0')
    parser.add_argument('-a', '--atlas',type=str,default='Schaefer')
    parser.add_argument('-v','--verbose', type=int, default=1)
    parser.add_argument('-r','--run_stats', type=int, default=1)
    parser.add_argument('-o', '--overwrite', type=int, default=1)
    parser.add_argument('-p', '--plot', type=int, default=1)
    p = parser.parse_args()
    RUN_STATS=bool(p.run_stats) 

    # import the right utils/config file
    if p.dataset.lower() == 'narratives': import narratives_utils as utils; import narratives_config as config
    elif p.dataset.lower() == 'adult_restmovie': import adult_restmovie_utils as utils; import adult_restmovie_config as config
    elif p.dataset.lower() == 'infant_restmovie': import infant_restmovie_utils as utils; import infant_restmovie_config as config; p.subject_filter=p.task
    elif p.dataset.lower() == 'partlycloudy': import partlycloudy_utils as utils; import partlycloudy_config as config
    elif p.dataset.lower() == 'hbn': import hbn_utils as utils; import hbn_config as config
    else: print(f'{p.dataset} not valid'); sys.exit(1)
    if p.verbose: print(f'loaded {p.dataset}_utils')
    VERBOSE=config.VERBOSE
    ISC_METRIC='pearson'
    # load target subject
    ALL_SUBJECTS = utils.get_intersecting_subjects(subject_filter=p.subject_filter)
    
    # make sure the desired subject exists
    if len(ALL_SUBJECTS) < p.subject_idx:
        print(f'test subject idx {p.subject_idx} not in list of len {len(ALL_SUBJECTS)}')
        sys.exit(2)
    test_subject = ALL_SUBJECTS[p.subject_idx]
    train_subjects = np.setdiff1d(ALL_SUBJECTS,test_subject) # JUST FOR TESTING
    print(test_subject, train_subjects)
    if p.verbose: print(f'running subject {test_subject} of {len(train_subjects)} training subs')
    if p.dataset.lower() == 'hbn':
        wb_mask=utils.get_intersect_mask(p.subject_filter, p.task) # intersect mask for the HBN dataset is specific to the subject filter and task
        print(f'loaded WB Mask of shape {wb_mask.shape}')
    else:
        wb_mask=None
    results_outdir = os.path.join(utils.get_scratch_dir(), 'ISC', 'LOSO_parcel', 'results')
    plot_outdir = results_outdir.replace('results', 'plots')
    os.makedirs(results_outdir,exist_ok=True)
    os.makedirs(plot_outdir,exist_ok=True)
    results_df, results_volume = run_subject_isc(test_subject, train_subjects, p.task, atlas_name=p.atlas, wb_mask=wb_mask)

    outfn_base = f'{results_outdir}/{test_subject}_{p.task}_{p.atlas}'
    if p.subject_filter != '0': 
        outfn_base=f'{results_outdir}/results_all/{test_subject}_{p.task}_{p.atlas}_filter_{p.subject_filter}'

    results_df.to_csv(outfn_base+'_all_ISC_results.csv')
    nib.save(results_volume, f'{outfn_base}_ISC.nii.gz')
    if VERBOSE: print(f'saved {outfn_base}_ISC.nii.gz')
    if p.plot:
        cmap=utils.get_brain_cmap()
        title = f'{p.dataset} {p.task} {test_subject} ISC'
        f = outfn_base.replace(results_outdir, plot_outdir)+f'statmap.png'
        plotting.plot_stat_map(results_volume, output_file=f, colorbar=True, threshold=0.001, cmap=cmap, title=title)
        print(f'plotted at {f}')










