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
import shutil
import seaborn as sns
from camcan_utils import get_brain_cmap
import skdim
import statsmodels.api as sm
import ide_helpers as ide
import task_comparison as tc

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
    TASKS = [t.lower()  for t in utils.get_tasks() if t.lower() != 'rest'] # make sure only getting aud or vis
    RESULTS_DIR = utils.get_results_dir()
    ALL_SUBJECTS = utils.get_intersecting_subjects()
    
    if p.verbose: print(f'running {TASKS}')
    
    if p.dataset == 'narratives':
        mask_sel = nib.load('./masks/Narratives_isc_mask.nii.gz')
        mask_opp = nib.load('./masks/RestMovie_isc_mask.nii.gz')
    else:
        mask_sel = nib.load('./masks/RestMovie_isc_mask.nii.gz')
        mask_opp = nib.load('./masks/Narratives_isc_mask.nii.gz')
        
    masker_sel = NiftiMasker(mask_sel, target_affine=BRAIN_MASK.affine, target_shape=BRAIN_MASK.shape[:3], standardize=True)
    masker_opp = NiftiMasker(mask_opp, target_affine=BRAIN_MASK.affine, target_shape=BRAIN_MASK.shape[:3], standardize=True)
    
    IDE_FUNC = ide.METHODS[p.metric]
    
    if p.metric is in ['TPHATE_SE_delta', 'PHATE_SE_delta']: cols = ['optimal_t','DSE_t0', 'DSE_optt','delta_DSE']
    else: cols = ['ide']
    
    results_df = pd.DataFrame(columns = ['subject','task','metric','mask_used','IDE', 'DSE_t0', 'DSE_optt', 'delta_DSE'])
    
    for subject in ALL_SUBJECTS:
        if p.verbose: print(f'running {subject}')
        for task in TASKS:
            nii = utils.get_subject_data(subject, task)
            X_sel = masker_sel.fit_transform(nii)
            X_opp = masker_opp.fit_transform(nii)
            for met, func in {'PCA': compute_PCA_dim, 'PHATE_SE_delta':compute_phate_SE_delta, 'TPHATE_SE_delta':compute_tphate_SE_delta}.items():
                RESULTS_sel = func(X_sel)
                RESULTS_opp = func(X_opp)
                if met == 'PCA':
                    results_df.loc[len(results_df)] = {'subject':subject, 'task':task, 'metric':met, 'mask_used':'selective', 'IDE':RESULTS_sel}
                    results_df.loc[len(results_df)] = {'subject':subject, 'task':task, 'metric':met, 'mask_used':'opposite', 'IDE':RESULTS_opp}
                else:
                    results_df.loc[len(results_df)] = {'subject':subject, 'task':task, 'metric':met, 'mask_used':'selective', 'IDE':RESULTS_sel[0],
                                                       'DSE_t0':RESULTS_sel[1], 'DSE_t0':RESULTS_sel[2], 'DSE_t0':RESULTS_sel[3]}
                    results_df.loc[len(results_df)] = {'subject':subject, 'task':task, 'metric':met, 'mask_used':'opposite', 'IDE':RESULTS_opp[0], 
                                                      'DSE_t0':RESULTS_opp[1], 'DSE_t0':RESULTS_opp[2], 'DSE_t0':RESULTS_opp[3]}
    results_df.to_csv(f'{RESULTS_DIR}/{p.dataset}_ISC_mask_dimensionality_results.csv')
                
