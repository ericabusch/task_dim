import numpy as np
import pandas as pd
import os, sys, glob
import nibabel as nib
from config import *
from nibabel import Nifti1Image
from scipy import stats
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker
import matplotlib.pyplot as plt
import scprep, tphate, phate
from nilearn import plotting
import shutil, argparse
import seaborn as sns
from camcan_utils import get_brain_cmap
import skdim
import statsmodels.api as sm
import ide_helpers as ide
import task_comparison as tc

def isc_loso(all_subjects_data):
    n_subjects, n_timepoints, n_voxels = all_subjects_data.shape
    correlations = np.zeros(n_subjects)
    for test_idx in range(n_subjects):
        train_idx = np.setdiff1d(np.arange(n_subjects),test_idx)
        train_data = np.mean(all_subjects_data[train_idx],axis=0).ravel()
        test_data = all_subjects_data[test_idx].ravel()
        correlations[test_idx] = np.corrcoef(train_data, test_data)[0,1]
    return correlations


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dataset',type=str)
    parser.add_argument('-v','--verbose', type=int, default=1)
    parser.add_argument('-o', '--overwrite', type=int, default=1)
    parser.add_argument('-p', '--plot', type=int, default=0)
    p = parser.parse_args()


    # import the right utils file
    if p.dataset.lower() == 'narratives': import narratives_utils as utils
    elif p.dataset.lower() == 'rest_movie': import RM_utils as utils
    elif p.dataset.lower() == 'camcan': import camcan_utils as utils
    else: print(f'{p.dataset} not valid');  sys.exit(1)
    if p.verbose: print(f'loaded {p.dataset}_utils')
    
    BRAIN_MASK = utils.get_intersect_mask()
    TASKS = [t.lower() for t in utils.get_tasks() if t.lower() != 'rest' ] # make sure only getting aud or vis
    RESULTS_DIR = utils.get_results_dir()
    ALL_SUBJECTS = utils.get_intersecting_subjects()
    
    if p.verbose: print(f'running {TASKS}')
    
    if p.dataset == 'narratives':
        mask_sel = nib.load('./masks/Narratives_isc_mask.nii.gz')
        mask_opp = nib.load('./masks/RestMovie_isc_mask.nii.gz')
        print('Sel=./masks/Narratives_isc_mask.nii.gz')
    else:
        mask_sel = nib.load('./masks/RestMovie_isc_mask.nii.gz')
        mask_opp = nib.load('./masks/Narratives_isc_mask.nii.gz')
        
    masker_sel = NiftiMasker(mask_sel, target_affine=BRAIN_MASK.affine, target_shape=BRAIN_MASK.shape[:3], standardize=True)
    masker_opp = NiftiMasker(mask_opp, target_affine=BRAIN_MASK.affine, target_shape=BRAIN_MASK.shape[:3], standardize=True)
        
    
    results_df = pd.DataFrame(columns = ['subject','task','metric','mask_used','score'])
    FUNCTION_DICT = {'PCA': ide.compute_PCA_dim, 'PHATE_optt':ide.compute_phate_t, 'TPHATE_optt':ide.compute_tphate_t, 'FisherS':ide.compute_FisherS}.items()

    
    for task in TASKS:
        if p.verbose: print(f'starting {task}')
        task_data_sel, task_data_opp = [], []
        scores_sel, scores_opp, metrics_sel, metrics_opp = [], [], [],[]
        for subject in ALL_SUBJECTS:
            nii = utils.get_subject_data(subject, task)
            X_sel = masker_sel.fit_transform(nii)
            X_opp = masker_opp.fit_transform(nii)
            task_data_sel.append(X_sel)
            task_data_opp.append(X_opp)
            
            for met, func in FUNCTION_DICT:
                RESULTS_sel = func(X_sel)
                RESULTS_opp = func(X_opp)
                results_df.loc[len(results_df)] = {'subject':subject, 'task':task, 'metric':met, 'mask_used':'selective', 'score':RESULTS_sel}
                results_df.loc[len(results_df)] = {'subject':subject, 'task':task, 'metric':met, 'mask_used':'opposite', 'score':RESULTS_opp}
                
        isc_sel = isc_loso(np.array(task_data_sel))
        isc_opp = isc_loso(np.array(task_data_opp))
        if p.verbose: print(f'ISC selective region: {np.round(np.mean(isc_sel),3)},{np.round(np.std(isc_sel),3)}')
        if p.verbose: print(f'ISC opp region: {np.round(np.mean(isc_opp),3)},{np.round(np.std(isc_opp),3)}')
        temp1 = pd.DataFrame({'subject':ALL_SUBJECTS, 'task':np.repeat(task, len(ALL_SUBJECTS)), 'metric':"ISC", 'mask_used':'selective', 'score':isc_sel})
        temp2 = pd.DataFrame({'subject':ALL_SUBJECTS, 'task':np.repeat(task, len(ALL_SUBJECTS)), 'metric':"ISC", 'mask_used':'opposite', 'score':isc_opp})
        results_df = pd.concat([results_df,temp1,temp2])
        

    results_df.to_csv(f'{RESULTS_DIR}/{p.dataset}_ISC_mask_dimensionality_results_v2.csv')
                
