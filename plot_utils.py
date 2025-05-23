import numpy as np
import pandas as pd
import os,sys,glob
import nibabel as nib
from nibabel import Nifti1Image
from scipy import stats
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker
from nilearn import plotting
import matplotlib.pyplot as plt
from nilearn import datasets
import scprep, tphate 
import statsmodels.api as sm
import seaborn as sns
from nilearn.glm import threshold_stats_img, fdr_threshold
from nilearn.image import threshold_img, math_img
import matplotlib
from obspy.imaging.cm import viridis_white
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
from matplotlib.colors import ListedColormap, LinearSegmentedColormap,TwoSlopeNorm, Normalize
import matplotlib as mpl
from matplotlib import ticker

def vec2vol(values, mask_nii):
    mask_coords = np.where(mask_nii.get_fdata() == 1)
    X = np.zeros_like(mask_nii.get_fdata())
    X[mask_coords] = values
    vol = nib.Nifti1Image(X, affine=mask_nii.affine)
    vol.header.set_zooms(mask_nii.header.get_zooms())
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


def plot_color_bar(cmap, tick_labels, threshold, out_fn=False):
    """
    Generate a color bar with a specified colormap, tick labels, and a threshold below which the color bar is gray.

    Parameters:
    - cmap_name (str): Name of the colormap (e.g., 'viridis', 'plasma', 'coolwarm').
    - tick_labels (list): List of labels for the tick marks on the color bar.
    - threshold (float): Threshold value below which the color bar is gray.
    """
    # Get the colormap
    if type(cmap)==str:
        cmap = plt.get_cmap(cmap)
    
    # Create a custom colormap that is gray below the threshold
    colors = []
    for value in np.linspace(0, 1, 256):
        if value < threshold:
            colors.append((0.5, 0.5, 0.5, 1.0))  # Gray color for values below threshold
        else:
            colors.append(cmap(value))  # Use the specified colormap for values above threshold
    
    custom_cmap = LinearSegmentedColormap.from_list('custom_cmap', colors, N=256)
    
    # Create a normalized color map
    norm = Normalize(vmin=min(tick_labels), vmax=max(tick_labels))
    
    # Create a figure and axis for the color bar
    fig, ax = plt.subplots(figsize=(6, 1))
    fig.subplots_adjust(bottom=0.5)
    
    # Create the color bar
    cb = plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=custom_cmap),
                      cax=ax, orientation='horizontal')
    
    # Set the tick labels
    cb.set_ticks(tick_labels)
    cb.set_ticklabels([str(label) for label in tick_labels])
    
    
    if out_fn:
        plt.savefig(out_fn, bbox_inches='tight', transparent=True)

def merge_cmaps(first_cmap, second_cmap, merged_cmap_name, mirror1=False):
    '''
    this function assumes you're passing two objects of matplotlib.colors.LinearSegmentedColormap

    '''
    colors1 = first_cmap(np.linspace(0, 1, 128))
    if mirror1: colors1=colors1[::-1]
    colors2 = second_cmap(np.linspace(0, 1, 128))
    colors_combined = np.vstack((colors1,colors2))
    cmap_combined = ListedColormap(colors_combined, name=merged_cmap_name)
    return cmap_combined

def get_merged_VWRDPU_cmap():
    return merge_cmaps(viridis_white, plt.cm.RdPu, "ViridisWhiteRdPu")

def mirror_cmap(cmap):
    return merge_cmaps(cmap, cmap, 'mirrored_cmap',mirror1=True)

def plot_array_to_atlas(X, sample_vol, atlas_name='Schaefer'):
    if atlas_name == 'Schaefer':
        atlas = datasets.fetch_atlas_schaefer_2018(resolution_mm=2, yeo_networks=17)
        atlas.labels = np.insert(atlas.labels, 0, 'Background')
    else:
        print(f'{atlas_name} not implemented')
    masker = NiftiLabelsMasker(atlas.maps, labels=atlas.labels, standardize=False)
    masker.fit(sample_vol)
    nifti_data = masker.inverse_transform(X)
    return nifti_data

def plot_vol_to_surf(result_vol, cmap_type='default', output_file=None, threshold=None, vmax=None, title=None, cmap='magma'):
    assert cmap_type in ['divergent','mirror','default']

    if cmap_type == 'divergent':
        cmap = get_merged_VWRDPU_cmap()
    elif cmap_type == 'mirror':
        cmap = mirror_cmap(plt.get_cmap(cmap))
    else:
        cmap = plt.get_cmap(cmap)

    plotting.plot_img_on_surf(result_vol, 
                              views=['lateral','medial'], 
                              cmap=cmap, 
                              inflate=True, 
                              bg_on_data=False, 
                              alpha=0.8,
                              output_file=output_file,
                              darkness=0.8, 
                              vmax=vmax,
                              title=title,
                              threshold=threshold
                             )














