import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import os, sys, glob
import tphate
import nilearn 
import nibabel as nib
import ide_helpers as ide
from scipy import stats
from nilearn import plotting
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker
from nilearn.image import math_img
from sklearn.model_selection import ParameterGrid

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

def test_kernel_parameters(X, threshold=0.9, knn=5, include_eig1=0, return_t=0, handle_negatives=0):
    # how to handle negatives 
    # 0 - do nothing
    # 1 - take absolute value of everything
    # 2 - exclude all negatives
    if return_t==1:
        tph_op = tphate.TPHATE(verbose=0, knn=knn)
        _=tph_op.fit_transform(X)
        return tph_op.optimal_t
    
    tph_op = tphate.TPHATE(verbose=0, knn=knn).fit(X)
    D = tph_op.diff_op
    
    eigenvalues, _ = np.linalg.eig(D)
    if include_eig1 == 0:
        eigenvalues=eigenvalues[1:]
    
    if handle_negatives == 1:
        eigenvalues = np.abs(eigenvalues)
    elif handle_negatives == 2:
        eigenvalues = eigenvalues[eigenvalues>=0]
    else:
        eigenvalues=eigenvalues
    # sort
    sorted_eigenvalues = np.real(np.sort(eigenvalues)[::-1])
    explained_variance_ratio = sorted_eigenvalues / np.sum(sorted_eigenvalues)
    cumulative_variance = np.cumsum(explained_variance_ratio)
    n = np.where(cumulative_variance>threshold)[0][0]+1
    return n

def make_names_from_grid(sub_id, task, parameter_grid):
    names = []
    tot = len(list(parameter_grid))
    for i in range(tot):
        p = list(parameter_grid)[i]
        joined = '_'.join(f"{k}_{v}" for k, v in p.items())
        final_str = f'{sub_id}_{task}_{joined}'
        names.append(final_str)
    return names

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
    
    columns = list(PARAMETER_GRID.param_grid[0].keys()) + ['region_name','ID']
    results_df = pd.DataFrame(columns=columns)
    results_volumes = {M:None for M in PARAMETER_STRINGS}
    for roi_id in atlas_df.index[1:]:
        roi_mask_img = math_img(f"img == {roi_id}", img=atlas_image)
        masker = NiftiMasker(roi_mask_img, standardize=True)
        roi_data = np.nan_to_num(masker.fit_transform(nii))
        tokens = atlas_df.iloc[roi_id]['labels']
        roi_str = tokens.decode("UTF-8")
        if np.linalg.norm(roi_data) == 0: 
            R = np.empty(len(list(PARAMETER_GRID)))
            R[:] = np.nan
            if VERBOSE: print(f'no unique input values')
        else:
            roi_data = remove_missing(roi_data)

            R = []
            for j,p in enumerate(PARAMETER_GRID_LIST):  
                n = test_kernel_parameters(roi_data, p['threshold'], p['knn'], 
                                            p['include_eig1'],p['return_t'],
                                           p['handle_negatives'])
                R.append(n)
                #print(PARAMETER_STRINGS[j], n)

        for j,p in enumerate(PARAMETER_GRID_LIST):
            n = R[j]
            this_name = PARAMETER_STRINGS[j]
            expanded = np.repeat(n, roi_data.shape[1]).reshape(1,-1).astype("double")
            temp =  masker.inverse_transform(expanded)
            if results_volumes[this_name] == None:
                results_volumes[this_name] = temp
            else:
                v = results_volumes[this_name]
                results_volumes[this_name] = math_img(f'img1 + img2', img1 = v, img2=temp)
            results_df.loc[len(results_df)] = {'threshold':p['threshold'], 'knn':p["knn"],
                                               'return_t':p['return_t'], 'include_eig1':p['include_eig1'], 
                                               "handle_negatives": p['handle_negatives'], 'region_name':roi_str, 'ID':n}
            
        print(f'done {roi_id}')
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

    # import the right utils/config file
    if p.dataset.lower() == 'narratives': import narratives_utils as utils; import narratives_config as config
    elif p.dataset.lower() == 'adult_restmovie': import adult_restmovie_utils as utils; import adult_restmovie_config as config
    elif p.dataset.lower() == 'camcan': import camcan_utils as utils; import camcan_config as config
    elif p.dataset.lower() == 'infant_restmovie': import infant_restmovie_utils as utils; import infant_restmovie_config as config; p.subject_filter=p.task
    elif p.dataset.lower() == 'cneuromod': import cneuromod_utils as utils; import cneuromod_config as config
    elif p.dataset.lower() == 'partlycloudy': import partlycloudy_utils as utils; import partlycloudy_config as config
    elif p.dataset.lower() == 'hbn': import hbn_utils as utils; import hbn_config as config
    else: print(f'{p.dataset} not valid'); sys.exit(1)
    
    if p.verbose: print(f'loaded {p.dataset}_utils')
    VERBOSE=config.VERBOSE
    
    PARAMETER_GRID = ParameterGrid({'threshold': [0.85], 'knn': [5, 20], 'return_t':[0, 1],
                 'include_eig1':[0, 1], 'handle_negatives': [0,1,2]})
    PARAMETER_GRID_LIST = list(PARAMETER_GRID)
    print(f'Num parameters to test: {len(PARAMETER_GRID_LIST)}')

     # load target subject
    ALL_SUBJECTS = utils.get_intersecting_subjects(subject_filter=p.subject_filter)
    
    # make sure the desired subject exists
    if len(ALL_SUBJECTS) < p.subject_idx:
        print(f'test subject idx {p.subject_idx} not in list of len {len(ALL_SUBJECTS)}')
        sys.exit(2)
    this_subject = ALL_SUBJECTS[p.subject_idx]
    results_outdir = os.path.join(utils.get_scratch_dir(), 'IDE_params', 'LOSO_parcel', 'results')
    plot_outdir = results_outdir.replace('results', 'plots')
    os.makedirs(results_outdir,exist_ok=True)
    os.makedirs(plot_outdir,exist_ok=True)

    PARAMETER_STRINGS = make_names_from_grid(this_subject, p.task, PARAMETER_GRID_LIST)
    

    outfn_base = os.path.join(results_outdir, f'{this_subject}_{p.task}_{p.atlas}')

    if p.verbose: print(f'Will save to {outfn_base}')
    results_df, results_volumes = run_subject_ide(this_subject, p.task, p.file_idx, atlas_name=p.atlas)
    results_df.to_csv(outfn_base+'_parameters_ide_results.csv')
    cmap=utils.get_brain_cmap()
    for method, volume in results_volumes.items():
        nib.save(volume,f'{method}.nii.gz')
        if VERBOSE: print(f'saved {method}.nii.gz')
        if p.plot:
            title = f'{p.dataset} {p.task} {this_subject} {method}'
            f = outfn_base.replace(results_outdir, plot_outdir)+f'{method}_statmap.png'
            plotting.plot_stat_map(volume, output_file=f, colorbar=True, threshold=0, cmap=cmap, title=title)
            print(f'plotted at {f}')

