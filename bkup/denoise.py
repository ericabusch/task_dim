## THIS SCRIPT RUNS THE DENOISING PROCESS FOR THE DATA IN THE FORREST DATASET
import numpy as np
import pandas as pd
import os, sys, glob
import nibabel as nib
import nilearn
import nilearn.signal
import utils
from nibabel.nifti1 import Nifti1Image
from config import SESSIONS2TASK, PREPROC_DATA_DIR, RAW_DIR, RUNS
from nibabel.processing import fwhm2sigma
from scipy.ndimage import gaussian_filter1d
from scipy.stats import zscore


subject = int(sys.argv[1])
smoothed=True

TR = 1.5 # 1.5 second tr
high_pass_filter = 1/100
regressors = ['trans_x', 'rot_x', 'trans_y', 'rot_y', 'trans_z', 'rot_z', 'csf', 'global_signal', 'white_matter']

# takes a surface gii, a comfounds timeseries for this run, and a file to save to
# can optionally filter the data (HP filter), run linear detrending,
# and mask a timeseries. Timing mask is expected to be [from_start, from_end]
def denoise_surface(surface_image, confounds_df, outfn, high_pass_filter=None, detrend=True, timing_mask=None, smooth_sigma=0):
    surface_image=surface_image.agg_data()
    timepoints = np.arange(surface_image.shape[-1])
    confounds = confounds_df[regressors]
    
    if timing_mask != None:
        tp_prev=len(timepoints)
        timepoints = timepoints[timing_mask[0]:-1*timing_mask[1]]
        print(f"Trimmed timepoints from {tp_prev} to {len(timepoints)}")
        surface_image=surface_image[:,timepoints]
        confounds=confounds.loc[timepoints].reset_index().drop(columns=['index'])
    
    confounds=confounds.values
    if smooth_sigma != 0:
        surface_image = gaussian_filter1d(surface_image, smooth_sigma)
        
    n_timepoints_inc = len(timepoints)
    clean = nilearn.signal.clean(surface_image.T, 
                                detrend=detrend,
                                confounds=confounds,
                                t_r=TR,
                                standardize=False,
                                high_pass=high_pass_filter)
    clean = clean.T if clean.shape[0] != n_timepoints_inc else clean # reshape to be [n_samples,n_features]
    np.save(outfn, clean)
    print(f'cleaned data of shape {clean.shape}, saving to {outfn}')
    return clean

OUTDIR = PREPROC_DATA_DIR
os.makedirs(OUTDIR, exist_ok=True)
vol_fwhm=6
sigma=fwhm2sigma(vol_fwhm)


cleaned_data = []
for ses, task in SESSIONS2TASK.items():
    dss_lh, dss_rh = [], []
    for run in np.arange(1, RUNS[task]+1):
        confound_file = utils.get_confounds(subject, ses, run)
        confounds = pd.read_csv(confound_file, sep='\t')[regressors] # only take these regressors
        for side, SIDE in zip(['lh','rh'], ['L','R']):
            img_name = utils.get_subject_raw_files(subject, hemi=side, ses=ses, run=run)
            img = nib.load(img_name)
            outfn = f'{OUTDIR}/sub-{subject:02d}_ses-{ses}_task-{task}_run-{run}_fsaverage5_cleaned_{side}.npy'
            print(f"cleaning subject {subject} task {task} ses {ses} {SIDE} data, confounds of shape {confounds.shape}")
            cleaned = denoise_surface(img, confounds, outfn, high_pass_filter=high_pass_filter, detrend=True, smooth_sigma=sigma)
            cleaned_normed = zscore(cleaned, axis=0)
            dss_lh.append(cleaned_normed) if SIDE == 'L' else dss_rh.append(cleaned_normed)
    for side, dss in zip(['lh','rh'],[dss_lh, dss_rh]):
        outfn = f'{OUTDIR}/sub-{subject:02d}_ses-{ses}_task-{task}_all_runs_{side}.npy'
        dss = np.concatenate(dss, axis=0)
        np.save(outfn, dss)
        print(f'saved {outfn}')
                