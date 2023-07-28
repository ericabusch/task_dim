# functions specific to this project
import numpy as np
import glob
from config import *
from scipy.stats import zscore
import nibabel as nib
import seaborn as sns
import matplotlib

def get_brain_cmap(mpl_colorname='inferno'):
    n = 40
    color_list = sns.color_palette(mpl_colorname,n)[0:n]
    indices = np.concatenate((np.arange(n-1, -1, -1), np.arange(0, n,1)))
    brain_cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", [color_list[i] for i in indices])
    return brain_cmap

def get_subject_data(sub_id, task, trim=False):
    dirname = RM_DATA_DIRS[task]
    print(dirname)
    fn = sorted(glob.glob(f"{dirname}/rest_movie_{sub_id:02d}_functional*_Only.nii.gz"))[0]
    print(fn)
    nii=nib.load(fn)
    # trim timepoints
    if trim:
        n_TRs = RM_TIMEPOINTS[task]
        data = nii.get_fdata()
        data = data[...,:n_TRs]
        dimensions = nii.header.get_zooms() 
        nii = nib.Nifti1Image(data, nii.affine)
        nii.header.set_zooms(dimensions)
    return nii

def get_mask(task):
    dirname = './masks/'
    task = task.lower().capitalize()
    fn = sorted(glob.glob(f"{dirname}/Adult_{task}*"))[0]
    return nib.load(fn)

def get_alltask_mask():
    dirname = './masks/'
    fn = f'{dirname}/Mickey_Aeronaut_Rest_intersect.nii.gz'
    return nib.load(fn)

def get_result_vol(sub_id, task, dirname, sl_rad, restype):
    fn = f'RestMovie/results/{dirname}/sub-{sub_id:02d}_{task}_{restype}_whole_brain_SL_rad{sl_rad}.nii.gz'
    return nib.load(fn)