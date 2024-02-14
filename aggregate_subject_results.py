# loads in result files for all subjects
# creates a numpy file with vectorized results for all subjects
# and an average brain volume

import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import os, sys, glob
import nilearn 
import nibabel as nib
import config
from scipy import stats
from nilearn import plotting
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker

def load_mask_data_file(mask_coords, subject, task, metric, filter_by_age=0, slrad=5):
    nii = utils.get_metric_nii_subject(subject, task, metric, filter_by_age=filter_by_age, slrad=slrad)
    if nii == None:
        z = np.zeros(len(mask_coords[0]))
        z[:] = np.nan
        return z
    x = nii.get_fdata()
    vec = x[mask_coords[0][:], mask_coords[1][:], mask_coords[2][:]]
    return vec

def vec2vol(values, mask_nii):
    mask_coords = np.where(mask_nii.get_fdata() == 1)
    X = np.zeros_like(mask_nii.get_fdata())
    X[mask_coords] = values
    vol = nib.Nifti1Image(X, affine=mask_nii.affine)
    vol.header.set_zooms(mask_nii.header.get_zooms())
    return vol

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dataset',type=str)
    parser.add_argument('-t','--task', type=str)
    parser.add_argument('-m', '--metric', type=str)
    parser.add_argument('-r','--sl_rad', type=int, default=5)
    parser.add_argument('-v','--verbose', type=int, default=1)
    parser.add_argument('-o', '--overwrite', type=int, default=1)
    parser.add_argument('-p', '--plot', type=int, default=1)
    parser.add_argument('-s','--subject_filter',type=int, default=0)
    p = parser.parse_args()
    
    
    if p.dataset.lower() == 'narratives': import narratives_utils as utils
    elif p.dataset.lower() == 'rest_movie': import RM_utils as utils
    elif p.dataset.lower() == 'camcan': import camcan_utils as utils
    else: print(f'{p.dataset} not valid');  sys.exit(1)
    
    brain_mask = utils.get_intersect_mask(subject_filter=p.subject_filter)
    mask_coords = np.where(brain_mask.get_fdata() == 1)
    all_subjects = utils.get_intersecting_subjects(subject_filter=p.subject_filter)

    if p.verbose: print(f'Loading {p.dataset} {p.task} {p.metric}')
    
    subject_vectors = []
    for s in all_subjects:
        subject_vectors.append(load_mask_data_file(mask_coords, s, p.task, p.metric, p.subject_filter, p.sl_rad))
    subject_vectors=np.array(subject_vectors)
    if p.verbose: print(f'Loaded {len(subject_vectors)} files; final shape: {subject_vectors.shape}')
    
    outdir = f'{utils.get_results_dir()}/all_subject_arrays'
    os.makedirs(outdir, exist_ok=True)
    outfn = f'{outdir}/{p.task.lower()}_{p.metric}_all_subject_results.npy'
    np.save(outfn, subject_vectors)
    if p.verbose: print(f'saved to {outfn}')
    
    # average
    avg = np.nanmean(subject_vectors, axis=0)
    avg_nii = vec2vol(avg, brain_mask)
    outdir = f'{utils.get_results_dir()}/result_volumes'
    os.makedirs(outdir, exist_ok=True)
    outfn = f'{outdir}/{p.task.lower()}_{p.metric}_average_result.nii.gz'
    nib.save(avg_nii, outfn)
    if p.verbose: print(f'saved res of shape {avg_nii.shape} to {outfn}')
    
    if p.plot: 
        if p.verbose: print(f"plotting")
        title = f'{p.dataset} {p.task} {p.metric} avg'
        outfn = outfn.replace('.nii.gz','.png')
        cmap = utils.get_brain_cmap()
        plotting.plot_img_on_surf(avg_nii, 
                                  views=['lateral','medial'], 
                                  inflate=True, 
                                  bg_on_data=False, 
                                          alpha=0.8,
                                  output_file=outfn,
                                  cmap=cmap,
                                  darkness=0.8, 
                                  threshold=0, title=f'{title}'
                                 )
    
    


