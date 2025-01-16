import numpy as np
import pandas as pd
import os,sys,glob
import nibabel as nib
from nibabel import Nifti1Image
from scipy import stats
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker
from nilearn import plotting
import matplotlib.pyplot as plt
import scprep, tphate 
import statsmodels.api as sm
import seaborn as sns
from nilearn.glm import threshold_stats_img, fdr_threshold
from nilearn.image import threshold_img, math_img
import matplotlib
from obspy.imaging.cm import viridis_white
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
from matplotlib.colors import ListedColormap, LinearSegmentedColormap,TwoSlopeNorm
import matplotlib as mpl
from matplotlib import ticker

def vec2vol(values, mask_nii):
    mask_coords = np.where(mask_nii.get_fdata() == 1)
    X = np.zeros_like(mask_nii.get_fdata())
    X[mask_coords] = values
    vol = nib.Nifti1Image(X, affine=mask.affine)
    vol.header.set_zooms(mask.header.get_zooms())
    return vol

def threshold_mask(tcc_img, avg_img):
    # binarize the thresholded image to then apply to the average image
    mask = math_img("img > 0", img=tcc_img)
    thresholded_masked = math_img('img1 * img2', img1=avg_img, img2=mask)
    return thresholded_masked

def mask_pval(original, pvalues, threshold=0.05):
    pval_masked = math_img(f'np.where(img <= {threshold}, 1, 0)', img=pvalues)
    masked_data = math_img(f'img1 * img2', img1=original, img2=pval_masked)
    return masked_data


def plot_colorbar(vmax, values, direction='horizontal', cmap='RdBu_r', nbins=5, out_fn=None):
    
    fig = plt.figure()
    
    divnorm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    psm = plt.pcolormesh([-values, values], norm=divnorm, cmap=cmap)
    plt.clf()
    
    # xloc, yloc, size x, size y
    if direction == 'horizontal':
        cbar_ax = fig.add_axes([0.5, 0, 0.6, 0.05])
    elif direction == 'vertical':
        cbar_ax = fig.add_axes([0.5, 0, 0.05, 0.6])
    
    fig.colorbar(psm, cax=cbar_ax, orientation=direction, ticks=ticker.MaxNLocator(nbins=nbins))
    
    if out_fn:
        plt.savefig(out_fn, bbox_inches='tight', transparent=True)

def merge_cmaps(first_cmap, second_cmap, merged_cmap_name):
    '''
    this function assumes you're passing two objects of matplotlib.colors.LinearSegmentedColormap

    '''
    colors1 = first_cmap(np.linspace(0, 1, 128))
    colors2 = second_cmap(np.linspace(0, 1, 128))
    colors_combined = np.vstack((colors1,colors2))
    cmap_combined = ListedColormap(colors_combined, name=merged_cmap_name)
    return cmap_combined

def get_merged_VWRDPU_cmap():
    return merge_cmaps(viridis_white, plt.cm.RdPu, "ViridisWhiteRdPu")


















