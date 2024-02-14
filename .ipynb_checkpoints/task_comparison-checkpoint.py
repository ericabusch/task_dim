# loads in two tasks for the same participant and then computes p-values across all the participants in the dataset
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
import tphate
import warnings
warnings.filterwarnings("ignore")
from scipy.stats import ttest_1samp
from nilearn.image import threshold_img, math_img
from nilearn.glm import threshold_stats_img
from ide_helpers import METHOD_NAMES


def load_mask_data_file(mask_coords, subject, task, metric, filter_by_age=0, slrad=5):
    nii = utils.get_metric_nii_subject(subject, task, metric, filter_by_age=filter_by_age, slrad=slrad)
    x = nii.get_fdata()
    vec = x[mask_coords[0][:], mask_coords[1][:], mask_coords[2][:]]
    return vec
    

def run_subtraction(subject, brain_mask, task1, task2, metric, filter_by_age=0, slrad=5):
    mask_coords = np.where(brain_mask.get_fdata() == 1)
    task1_vec = load_mask_data_file(mask_coords, subject, task1, metric, filter_by_age=filter_by_age, slrad=slrad)
    task2_vec = load_mask_data_file(mask_coords, subject, task2, metric, filter_by_age=filter_by_age, slrad=slrad)
    difference = task1_vec - task2_vec
    return difference

def ttest_vol(difference_vecs, mask):
    '''
    returns 4 volumes: 
    1. tstat map
    2. pvalue map
    3. mean map
    4. median map
    '''
    coords = np.where(mask.get_fdata() == 1)
    t, p = ttest_1samp(difference_vecs, popmean=0, axis=0)
    mu = np.mean(difference_vecs, axis=0)
    med = np.median(difference_vecs, axis=0)
    # project back out to niftis
    
    result_volumes = []
    for x in [t,p,mu, med]:
        out_vol = np.zeros_like(mask.get_fdata())
        
        out_vol[coords] = x
        res_vol = nib.Nifti1Image(out_vol, mask.affine)
        res_vol.header.set_zooms(mask.header.get_zooms())
        result_volumes.append(res_vol)
        
    return result_volumes

def vec2vol(values, mask_nii):
    mask_coords = np.where(mask_nii.get_fdata() == 1)
    X = np.zeros_like(mask_nii.get_fdata())
    X[mask_coords] = values
    vol = nib.Nifti1Image(X, affine=mask_nii.affine)
    vol.header.set_zooms(mask_nii.header.get_zooms())
    return vol
    

def threshold_visualize_results(result_volume, stat_volume, mask_volume, threshold_criteria, cluster_criteria, plotname, title, verbose=True):
    
    thresholded_image=threshold_img(
        stat_volume,
        threshold=threshold_criteria,
        cluster_threshold=cluster_criteria,
        two_sided=True
    ) # these are now thresholded t-stats -- so anywhere that is red is signif, now apply as mas
    # putting nans where not significant so it doesn't display
    thresholding_mask = math_img(f'np.where(img > 0, 1, 0)', img=thresholded_image)
    masked_result = math_img(f'img * img2', img=result_volume, img2=thresholding_mask)
    plotting.plot_img_on_surf(masked_result, threshold=0, inflate=True, output_file=plotname) # if it's significant, even if tiny, show differencs
    nib.save(masked_result, plotname.replace('.png','.nii.gz'))
    if verbose: print(f'saved to {plotname}')
    
    # now use the GLM thresholded one
    thresholded_map, threshold = threshold_stats_img(
                        stat_volume,  alpha=0.05, height_control="fdr", cluster_threshold=cluster_criteria, )
    
    plotting.plot_img_on_surf(
    thresholded_map,
    threshold=threshold,
    title=f"Thresholded & clustered {title}, fpr <.001", inflate=True, output_file=plotname.replace('thresholded_cluster_corrected','stats_img_threshold')
)
    
    mask_for_thresholding = math_img(f'np.where(img > {threshold}, 1, 0)', img=stat_volume)
    masked_mu =  math_img(f'img * img2', img=result_volume, img2=mask_for_thresholding)
    
    plotting.plot_img_on_surf(
    masked_mu,
    title=f"Mean {title} thresholded", inflate=True, 
        output_file=plotname.replace('thresholded_cluster_corrected', 'mean_img_threshold')
)
    
    
    
def visualize_unthresholded(result_volume, plotname, threshold, title):
    plotting.plot_img_on_surf(result_volume, threshold=threshold, inflate=True, cmap='bwr', title=title)
    plt.savefig(plotname)
    plt.close()
    
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dataset',type=str)
    parser.add_argument('-m','--metric',type=str)
    parser.add_argument('-r','--sl_rad', type=int, default=5)
    parser.add_argument('-s','--subject_filter', type=int, default=0)
    parser.add_argument('-v','--verbose', type=int, default=1)
    parser.add_argument('-o', '--overwrite', type=int, default=0)
    parser.add_argument('-p', '--plot', type=int, default=1)
    p = parser.parse_args()
    
    if p.dataset.lower() == 'narratives': import narratives_utils as utils
    elif p.dataset.lower() == 'rest_movie': import RM_utils as utils
    elif p.dataset.lower() == 'camcan': import camcan_utils as utils
    else: print(f'{p.dataset} not valid');  sys.exit(1)
    if p.verbose: print(f'loaded {p.dataset}_utils; running differences for {p.metric}')
    
    ALL_SUBJECTS = utils.get_intersecting_subjects(subject_filter=p.subject_filter)
    BRAIN_MASK = utils.get_intersect_mask(subject_filter=p.subject_filter)
    ALL_TASKS = utils.get_tasks()
    RESULT_DIR = utils.get_results_dir()
    
    mask_coords = np.where(BRAIN_MASK.get_fdata() == 1)
    TSTAT_THRESHOLD = stats.t.ppf(0.05, len(ALL_SUBJECTS)-1)
    CLUSTER_THRESHOLD=10
    
    # get pairs of tasks
    task_combos = itertools.combinations(ALL_TASKS,2)
    
    for task1,task2 in task_combos:
        outfn = f'{RESULT_DIR}/all_subject_arrays/{task1}_{task2}_{p.metric}_difference_per_subject.npy'
        difference_volumes = []
        for sub in ALL_SUBJECTS:
            d = run_subtraction(sub, BRAIN_MASK, task1, task2, p.metric, p.subject_filter, p.sl_rad)
            difference_volumes.append(d)
        
        if p.verbose: print(f'ran {task1} - {task2}; {len(difference_volumes)} res')

        difference_volumes = np.array(difference_volumes)
        # save them out
        np.save(outfn, difference_volumes)
        avg = np.mean(difference_volumes, axis=0)
        avg_vol = vec2vol(avg, BRAIN_MASK)
        outfn = f'{RESULT_DIR}/result_volumes/{task1}_{task2}_{p.metric}_mean_difference.nii.gz'
        
        # save difference volume
        nib.save(avg_vol, outfn)
        
        if p.plot: visualize_unthresholded(avg_vol, outfn.replace('.nii.gz','.png'), 0, f'{p.metric} {task1} - {task2}')
        
        # run stats
        results = ttest_vol(difference_volumes, BRAIN_MASK)
        for r, q in zip(results, ['tstat', 'pvalue', 'mean_difference', 'median_difference']):
            nib.save(r, f'{RESULT_DIR}/result_volumes/{task1}_{task2}_{p.metric}_{q}.nii.gz')
        t, pv, mu, med = results
        plotname =  f'{RESULT_DIR}/result_volumes/{task1}_{task2}_{p.metric}_thresholded_cluster_corrected.png'
        threshold_visualize_results(mu, t, BRAIN_MASK, TSTAT_THRESHOLD, CLUSTER_THRESHOLD, plotname, title=f'{p.metric} {task1} - {task2}')
        
#         # now visualize
#         t, pv, mu, med = results
#         fn1=f'{RESULT_DIR}/{task1}_{task2}_mean_{p.metric}_thresholded_SL_rad{p.sl_rad}.png'
#         fn1=fn1.replace('results','plots')
#         threshold_visualize_results(mu, t, BRAIN_MASK, TSTAT_THRESHOLD, CLUSTER_THRESHOLD, fn1, verbose=p.verbose)
#         visualize_unthresholded(mu, fn1.replace('thresholded', 'unthresholded'))
#         if p.verbose: print(f'finished {fn1}')
        # fn2=f'{RESULT_DIR}/{task1}_{task2}_mean_{p.metric}_thresholded_SL_rad{p.sl_rad}.png'
        # fn2=fn1.replace('results','plots')
        # threshold_visualize_results(mu, t, mask_volume, TSTAT_THRESHOLD, CLUSTER_THRESHOLD, fn1, verbose=p.verbose)
        
        
        
        
            
    
