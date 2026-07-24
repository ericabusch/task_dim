import numpy as np
import pandas as pd
import os, sys, glob,argparse
import nibabel as nib
import nilearn
from scipy.stats import zscore
from nibabel.nifti1 import Nifti1Image
from nibabel.processing import fwhm2sigma
from scipy.ndimage import gaussian_filter1d
from nibabel.processing import smooth_image
from nilearn.datasets import load_mni152_template

# things to regress: 
regressors = ['trans_x', 'rot_x', 'trans_y', 'rot_y', 'trans_z','rot_z','csf','global_signal','white_matter']

# takes a volume image, a comfounds timeseries for this run, and a file to save to
# can optionally filter the data (HP filter), run linear detrending,
# and mask a timeseries. Timing mask is expected to be [from_start, from_end]
def denoise_volume(volume_image, mask_image, confounds_df, outfn, high_pass_filter=None, resolution=0, detrend=True, timing_mask=None, smooth_fwhm=0):
    timepoints = np.arange(volume_image.shape[-1])
    confounds = confounds_df[regressors]
    
    if timing_mask != None:
        tp_prev=len(timepoints)
        timepoints = timepoints[timing_mask[0]:-1*timing_mask[1]]
        print(f"Trimmed timepoints from {tp_prev} to {len(timepoints)}")
        vol_img_tpts = volume_image.get_fdata()[:,:,:,timepoints]
        volume_image = Nifti1Image(dataobj=vol_img_tpts, header = volume_image.header, affine=volume_image.affine)
        del vol_img_tpts
        confounds=confounds.loc[timepoints].reset_index().drop(columns=['index'])
    
    if smooth_fwhm != 0: volume_image= smooth_image(volume_image, smooth_fwhm, mode='nearest')
        
    confounds=confounds.values
    print(f"cleaning data of shape {volume_image.shape}, confounds of shape {confounds.shape}")
    clean = nilearn.image.clean_img(imgs=volume_image, 
                                        detrend=detrend,
                                        confounds=confounds, 
                                        t_r=TR,
                                        standardize=False,
                                        high_pass=high_pass_filter,
                                        mask_img=mask_image)
    if resolution != 0:
        template = load_mni152_template(resolution=resolution)
        clean = nilearn.image.resample_to_img(clean, template, force_resample=True, interpolation="nearest")

    nib.save(clean, outfn)
    print(f'saved cleaned data to {outfn}, shape={clean.shape}', outfn)
    return clean

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dataset',type=str)
    parser.add_argument('-t','--task', type=str)
    parser.add_argument('-s', '--subject_id', type=str)
    parser.add_argument('-v','--verbose', type=int, default=1)
    parser.add_argument('-o', '--overwrite', type=int, default=0)
    p = parser.parse_args()

    # import the right utils file
    if p.dataset.lower() == 'narratives': import narratives_utils as utils; import narratives_config as config
    elif p.dataset.lower() == 'rest_movie': import adult_restmovie_utils as utils; import adult_restmovie_config as config
    elif p.dataset.lower() == 'infant_rest_movie': import infant_restmovie_utils as utils; import infant_restmovie_config as config
    else: print(f'{p.dataset} not valid');  sys.exit(1)

    vol_fns, conf_fns, out_fns, wb_mask_fns = utils.get_subject_data_fmriprep_output(p.subject_id, p.task)
    print(f'running {p.subject_id}, {p.task}')
    TR = utils.get_tr()
    resolution=3
    high_pass_filter = 1/100
    smooth_fwhm=5
    print(vol_fns)
    print(conf_fns)
    print(out_fns)
    for nii_file, confound_file, out_file, brain_mask in zip(vol_fns, conf_fns, out_fns, wb_mask_fns):
        print(confound_file)
        confound_df = pd.read_csv(confound_file, sep='\t')[regressors]
        vol_img = nib.load(nii_file)
        mask_img = nib.load(brain_mask)
        print(f'Input shape: {vol_img.shape}, mask:{mask_img.shape}, will save to {out_file}')
        _=denoise_volume(vol_img, mask_img, confound_df, out_file, high_pass_filter=high_pass_filter, resolution=resolution, detrend=True, timing_mask=None, smooth_fwhm=smooth_fwhm)









