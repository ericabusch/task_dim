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

def remove_missing(X):
    threshold = X.shape[0] // 20 # 5% are 0
    n_missing = np.sum(X==0, axis=0)
    mask = n_missing <= threshold
    filtered_X = X[:,mask]
    return filtered_X

def run_subject_ide(sub_id, task, file_idx=0, atlas_name='Schaefer'): 
    atlas_image, atlas_df = load_atlas(atlas_name)
    nii = utils.get_subject_data(sub_id, task, trim=True, file_idx=file_idx)
    print(f"Original shape: {nii.shape}")
    # apply whole-brain mask, then invert
    wb_mask = utils.get_intersect_mask()
    masker_wb = NiftiMasker(mask_img=wb_mask, standardize=True)
    masked_nii = masker_wb.fit_transform(nii)
    nii = masker_wb.inverse_transform(masked_nii)
    print(f"New shape: {nii.shape}")

    results_volumes = {M: None for M in METHODS_OUTPUT_LABELS}
    results_df = pd.DataFrame(columns=['ide_method','region_name','id_estimate'])
    for roi_id in atlas_df.index[1:]:
        roi_mask_img = math_img(f"img == {roi_id}", img=atlas_image)
        masker = NiftiMasker(roi_mask_img, standardize=True)
        roi_data = np.nan_to_num(masker.fit_transform(nii))
        tokens = atlas_df.iloc[roi_id]['labels']
        roi_str = tokens.decode("UTF-8")
        if VERBOSE: print(f'before masking, roi_data={np.shape(roi_data)}')
        if np.linalg.norm(roi_data) == 0: 
            R = np.empty(len(METHODS_TO_RUN))
            R[:] = np.nan
            if VERBOSE: print(f'no unique input values')
        else:
            roi_data = remove_missing(roi_data)
            if VERBOSE: print(f'after masking, {roi_str} ={np.shape(roi_data)}')
            R = []
            for meth_name in METHODS_TO_RUN:
                func = ide.METHODS[meth_name]
                try:
                    res = func(roi_data, THRESHOLD, KNN)
                except:
                    res = np.nan 
                if type(res) == tuple:
                    for r in res:
                        R.append(r)
                else:
                    R.append(res)
            assert len(R) == len(METHODS_OUTPUT_LABELS)
        for result, method_name in zip(R, METHODS_OUTPUT_LABELS):
            expanded = np.repeat(result, roi_data.shape[1]).reshape(1,-1).astype("double")
            temp =  masker.inverse_transform(expanded)
            if results_volumes[method_name] == None:
                results_volumes[method_name] = temp
            else:
                v = results_volumes[method_name]
                results_volumes[method_name] = math_img(f'img1 + img2', img1 = v, img2=temp)
            results_df.loc[len(results_df)] = {'ide_method':method_name, 'region_name':roi_str, 'id_estimate':result}
    results_df['task']=np.repeat(task, len(results_df))
    results_df['subject']=np.repeat(sub_id, len(results_df))
    
    return results_df, results_volumes


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dataset',type=str)
    parser.add_argument('-t','--task', type=str)
    parser.add_argument('-i', '--subject_idx', type=int)
    parser.add_argument('-f', '--file_idx', type=int, default=0)
    parser.add_argument('-s','--subject_filter', type=str, default='0')
    parser.add_argument('-a', '--atlas',type=str,default='Schaefer')
    parser.add_argument('-v','--verbose', type=int, default=1)
    parser.add_argument('-o', '--overwrite', type=int, default=1)
    parser.add_argument('-p', '--plot', type=int, default=1)
    p = parser.parse_args()

    METHODS_TO_RUN = ['TPHATE_DiffOp_IDE', 'MiND_ML', 'lPCA','PCA','FisherS']
    METHODS_OUTPUT_LABELS = METHODS_TO_RUN  
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
    this_subject = ALL_SUBJECTS[p.subject_idx]
    results_outdir = os.path.join(utils.get_scratch_dir(), 'IDE', 'LOSO_parcel', 'results')
    plot_outdir = results_outdir.replace('results', 'plots')
    os.makedirs(results_outdir,exist_ok=True)
    os.makedirs(plot_outdir,exist_ok=True)

    outfn_base = f'{results_outdir}/{this_subject}_{p.task}_{p.atlas}_file_idx_{p.file_idx}'
    if p.verbose: print(f'Will save to {outfn_base}')
    results_df, results_volumes = run_subject_ide(this_subject, p.task, atlas_name=p.atlas)
    results_df.to_csv(outfn_base+'_all_IDE_results.csv')
    cmap=utils.get_brain_cmap()
    for method, volume in results_volumes.items():
        nib.save(volume,f'{outfn_base}_{method}.nii.gz')
        if VERBOSE: print(f'saved {outfn_base}_{method}.nii.gz')
        if p.plot:
           title = f'{p.dataset} {p.task} {this_subject} {method}'
           f = outfn_base.replace(results_outdir, plot_outdir)+f'{method}_statmap.png'
           plotting.plot_stat_map(volume, output_file=f, colorbar=True, threshold=0, cmap=cmap, title=title)
           print(f'plotted at {f}')










