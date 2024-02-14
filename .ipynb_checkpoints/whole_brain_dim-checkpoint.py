import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import os, sys, glob
import nilearn 
import nibabel as nib
from config import *
import itertools
from nilearn import datasets
from scipy import stats
from nilearn import plotting
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker
import warnings
warnings.filterwarnings("ignore")
from scipy.stats import ttest_1samp
from nilearn.image import threshold_img, math_img
from nilearn.glm import threshold_stats_img
from ide_helpers import METHODS



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dataset',type=str)
    parser.add_argument('-r','--sl_rad', type=int, default=5)
    parser.add_argument('-v','--verbose', type=int, default=1)
    parser.add_argument('-o', '--overwrite', type=int, default=1)
    parser.add_argument('-p', '--plot', type=int, default=1)
    parser.add_argument('-s','--subject_filter',type=int, default=0)
    p = parser.parse_args()
    
    # import the right utils file
    if p.dataset.lower() == 'narratives': import narratives_utils as utils
    elif p.dataset.lower() == 'rest_movie': import RM_utils as utils
    elif p.dataset.lower() == 'camcan': import camcan_utils as utils
    else: print(f'{p.dataset} not valid');  sys.exit(1)
    if p.verbose: print(f'loaded {p.dataset}_utils')
    
    # THIS WAS CHANGED
    
     # load target subject
    ALL_SUBJECTS = utils.get_intersecting_subjects(subject_filter=p.subject_filter)
    # make sure the desired subject exists

#     this_subject = ALL_SUBJECTS[p.subject_idx]
#     brain_mask = utils.get_intersect_mask(subject_filter=p.subject_filter)
#     nii = utils.get_subject_data(this_subject, p.task)
#     masker_wb = NiftiMasker(mask_img=brain_mask, standardize=True)
#     masked_normed = masker_wb.fit_transform(nii)
#     masked_nii = masker_wb.inverse_transform(masked_normed)
#     coords = np.where(brain_mask.get_fdata() == 1)
#     x, y, z = coords[0], coords[1], coords[2]
#     masked_data = masked_nii.get_fdata()[x,y,z]
#     if masked_data.shape[1] != len(x):
#         masked_data = masked_data.T
#     if p.verbose: print(f'masked data of shape {masked_data.shape}')
    brain_mask = utils.get_intersect_mask(subject_filter=p.subject_filter)
    masker_wb = NiftiMasker(mask_img=brain_mask, standardize=True)
    coords = np.where(brain_mask.get_fdata() == 1)
    x, y, z = coords[0], coords[1], coords[2]
    
    df = pd.DataFrame(columns=['metric','subject','task','ide'])    
    METRICS = ['PCA','lPCA','PHATE_optt','TPHATE_optt','TPHATE_SE','PHATE_SE','FisherS']
    for this_subject in ALL_SUBJECTS:
        for task in utils.get_tasks():
            nii = utils.get_subject_data(this_subject, task)
            
            masked_normed = masker_wb.fit_transform(nii)
            masked_nii = masker_wb.inverse_transform(masked_normed)
            
            masked_data = masked_nii.get_fdata()[x,y,z]
            if masked_data.shape[1] != len(x):
                masked_data = masked_data.T
            if p.verbose: print(f'masked data of shape {masked_data.shape}')
            for metric in METRICS:
                func = METHODS[metric]
                ide = func(masked_data)
                df.loc[len(df)] = {'metric':metric, 'task':task, 'subject':this_subject, 'ide':ide}
                print(f'{metric}={ide}')
        
    outfn = f'{utils.get_results_dir()}/whole_brain_ide.csv'
    df.to_csv(outfn)