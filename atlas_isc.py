import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import os, sys, glob
import nilearn 
import nibabel as nib
from config import *
import ide_helpers as ide
from scipy import stats
from nilearn import plotting
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker
from nilearn.image import math_img

def load_atlas(atlas_name='Schaefer'):
    if atlas_name == 'Schaefer':
        ATLAS = nilearn.datasets.fetch_atlas_schaefer_2018(resolution_mm=2, yeo_networks=17)
        ATLAS.labels = np.insert(ATLAS.labels, 0, 'Background')
        atlas_image = nib.load(ATLAS.maps)
        atlas_df = pd.DataFrame(ATLAS)
    else:
        print(f'{atlas_name} not implemented')
    return atlas_image, atlas_df

def run_subject_ide(test_subject, train_subjects, task, atlas_name='Schaefer'): 
    atlas_image, atlas_df = load_atlas(atlas_name)
    nii = utils.get_subject_data(test_subject, task, trim=True)
    if type(nii) == list:
        nii = nii[0]
    if VERBOSE: print(f"Original shape: {nii.shape}")
    # apply whole-brain mask, then invert
    wb_mask = utils.get_intersect_mask()
    masker_wb = NiftiMasker(mask_img=wb_mask, standardize=True)
    masked_nii = masker_wb.fit_transform(nii)
    test_nii = masker_wb.inverse_transform(masked_nii)
    if VERBOSE: print(f"New shape: {test_nii.shape}")

    train_niis = []
    for i, train_sub in enumerate(train_subjects):
        nii = utils.get_subject_data(test_subject, task, trim=True)
        masker_wb = NiftiMasker(mask_img=wb_mask, standardize=True)
        masked_nii = masker_wb.fit_transform(nii)
        nii = masker_wb.inverse_transform(masked_nii)
        train_niis.append(nii)

    results_volume = None
    results_df = pd.DataFrame(columns=['region_name','score'])
    for roi_id in atlas_df.index[1:]:
        roi_mask_img = math_img(f"img == {roi_id}", img=atlas_image)
        masker = NiftiMasker(roi_mask_img, standardize=True)
        test_roi_data = masker.fit_transform(test_nii)
        n_voxels = test_roi_data.shape[1]
        test_roi_data=np.nan_to_num(test_roi_data.ravel())
        train_roi_data = [np.nan_to_num(masker.fit_transform(n).ravel()) for n in train_niis]
        train_roi_data = np.nanmean(np.array(train_roi_data),axis=0)
        r = np.corrcoef(test_roi_data, train_roi_data)[0,1]
        expanded = np.repeat(r, n_voxels).reshape(1,-1).astype("double")
        tokens = atlas_df.iloc[roi_id]['labels']
        roi_str = tokens.decode("UTF-8")
        temp =  masker.inverse_transform(expanded)
        if results_volume == None:
                results_volume = temp
        else:
            v = results_volume
            results_volume = math_img(f'img1 + img2', img1 = v, img2=temp)
        results_df.loc[len(results_df)] = {'region_name':roi_str, 'score':r}

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
    parser.add_argument('-o', '--overwrite', type=int, default=1)
    parser.add_argument('-p', '--plot', type=int, default=1)
    p = parser.parse_args()

    # import the right utils file
    if p.dataset.lower() == 'narratives': import narratives_utils as utils
    elif p.dataset.lower() == 'rest_movie': import RM_utils as utils
    elif p.dataset.lower() == 'camcan': import camcan_utils as utils
    elif p.dataset.lower() == 'infant_rest_movie': import RM_infant_utils as utils
    elif p.dataset.lower() == 'cneuromod': import CNM_utils as utils
    else: print(f'{p.dataset} not valid');  sys.exit(1)
    if p.verbose: print(f'loaded {p.dataset}_utils')
     # load target subject
    ALL_SUBJECTS = utils.get_intersecting_subjects(subject_filter=p.subject_filter)
    # make sure the desired subject exists
    if len(ALL_SUBJECTS) < p.subject_idx:
        print(f'test subject idx {p.subject_idx} not in list of len {len(ALL_SUBJECTS)}')
        sys.exit(2)
    test_subject = ALL_SUBJECTS[p.subject_idx]
    train_subjects = np.setdiff1d(ALL_SUBJECTS,test_subject)


    results_outdir = os.path.join(utils.get_scratch_dir(), 'ISC', 'LOSO_parcel', 'results')
    plot_outdir = results_outdir.replace('results', 'plots')
    os.makedirs(results_outdir,exist_ok=True)
    os.makedirs(plot_outdir,exist_ok=True)
    results_df, results_volume = run_subject_ide(test_subject, train_subjects, p.task, atlas_name=p.atlas)

    outfn_base = f'{results_outdir}/{test_subject}_{p.task}_{p.atlas}'

    results_df.to_csv(outfn_base+'_all_ISC_results.csv')
    cmap=utils.get_brain_cmap()
    nib.save(results_volume,f'{outfn_base}_ISC.nii.gz')
    if VERBOSE: print(f'saved {outfn_base}_ISC.nii.gz')
    if p.plot:
       title = f'{p.dataset} {p.task} {test_subject} ISC'
       f = outfn_base.replace(results_outdir, plot_outdir)+f'statmap.png'
       plotting.plot_stat_map(volume, output_file=f, colorbar=True, threshold=0.001, cmap=cmap, title=title)
       print(f'plotted at {f}')










