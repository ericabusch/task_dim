import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import os, sys, glob
import nilearn 
import nibabel as nib
from infant_restmovie_config import *
from infant_restmovie_utils import *
from nilearn import datasets
import stats_helpers
from scipy import stats
from nilearn import plotting
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker
from nibabel.nifti1 import Nifti1Image
from nilearn.image import math_img, concat_imgs

def get_overlap_masker(task0, task1, return_masker=False):
    mask0 = nib.load(INFANT_INTERSECT_MASKS[task0])
    mask1 = nib.load(INFANT_INTERSECT_MASKS[task1])
    sum_mask = math_img('np.where(np.add(X0,X1)==2,1,0)',X0=mask0, X1=mask1)
    if return_masker:
        return NiftiMasker(mask_img=sum_mask).fit(sum_mask)
    coords = np.where(sum_mask.get_fdata()==1)
    return coords


def run_difference_indep_samples_searchlight(task_pair, method, outfilename, plot,alpha=0.05):
	task0=task_pair.split('_')[0]
	task1=task_pair.split('_')[1]
	nii0 = nib.load(f'{utils.get_results_dir()}/{task0}_{method}_all_subjects_results.nii.gz')
	nii1 = nib.load(f'{utils.get_results_dir()}/{task1}_{method}_all_subjects_results.nii.gz')
	overlap_masker = get_overlap_masker(task0, task1, return_masker=True)
	arr0 = overlap_masker.transform(nii0)
	arr1 = overlap_masker.transform(nii1)
	print(f'after masking, arr0={arr0.shape}, arr1={arr1.shape}')
	
	if task0 == 'sleep': X0 = arr0 ; X1 = arr1
	else: X0 = arr1; X1=arr0
	# run indep samples
	t, p = stats.ttest_ind(X0,X1,axis=0)
	print(f'pvalues: {np.sum(p!=p)}/{len(p)}')
	# adjust p values
	adj_p = stats_helpers.false_discovery_control(p)
	# plot difference in means
	mu = np.mean(X0, axis=0) - np.mean(X1, axis=0)
	# mask differences
	pval_mask = np.zeros_like(p)
	pval_mask[adj_p <= alpha]=1
	masked_mu = mu * pval_mask
	masked_mu[masked_mu==0]=np.nan
	masked_mu_vol = overlap_masker.inverse_transform(masked_mu)
	adj_p_vol = overlap_masker.inverse_transform(adj_p)
	nib.save(masked_mu_vol, outfilename+'_avg_thresholded.nii.gz')
	nib.save(adj_p_vol, outfilename+'_adj_pvals_indep_samp_ttest.nii.gz')
	nib.save(overlap_masker.inverse_transform(mu), outfilename+'_avg_unthresholded.nii.gz')
	if plot:
		title = f'{task_pair} {method} avg diff thresholded'
		outfn = outfilename+'_avg_thresholded.png'

		plotting.plot_img_on_surf(masked_mu_vol, 
		views=['lateral','medial'], 
		inflate=True, 
		bg_on_data=False, 
		alpha=0.8,
		output_file=outfn,
		darkness=0.8, 
		threshold=0.1, title=f'{title}'
		)
	return 0



if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument('-d','--dataset',type=str, default='infant_restmovie')
	parser.add_argument('-s','--subject_filter', type=str, default='0')
	parser.add_argument('-a', '--atlas',type=str, default='Schaefer')
	parser.add_argument('-v','--verbose', type=int, default=1)
	parser.add_argument('-o', '--overwrite', type=int, default=1)
	parser.add_argument('-p', '--plot', type=int, default=1)
	p = parser.parse_args()

	# import the right utils file
	if p.dataset.lower() == 'infant_restmovie': import infant_restmovie_utils as utils
	else: print(f'{p.dataset} not valid');  sys.exit(1)
	if p.verbose: print(f'loaded {p.dataset}_utils')

	# compare pairs of tasks
	METHODS_TO_RUN = ['TPHATE_DiffOp_IDE']#, 'MiND_ML', 'lPCA','PCA']

	
	for task_pair, overlapping_subs in RM_INFANT_OVERLAPPING_SUBJECTS.items():
		print(f'{task_pair}: {overlapping_subs}')
		for METHOD in METHODS_TO_RUN:
			# only going to run indep sample
			outfn = f'{utils.get_results_dir()}/task_difference_maps/{task_pair}_{METHOD}_SL_difference_maps'
			error_code = run_difference_indep_samples_searchlight(task_pair, METHOD, outfn, plot=True, alpha=0.05)
			if p.verbose and error_code == 0: print(f'successfully ran {outfn}')
			elif p.verbose: print(f'failed {outfn}')

			# outfn = f'{utils.get_results_dir()}/task_difference_maps_v2/{task_pair}_{METHOD}_SL_difference_maps'
			# overlap_masker = get_overlap_masker(task_pair.split('_')[0], task_pair.split('_')[1], return_masker=True)
			# error_code = run_difference_indep_samples(overlap_masker, overlapping_subs, task_pair, METHOD, outfn, p.plot)
			# if p.verbose and error_code == 0: print(f'successfully ran {outfn}')
			# elif p.verbose: print(f'failed {outfn}')
			
			# # now run atlas version
			# outfn = f'{utils.get_results_dir()}/task_difference_maps_v2/{task_pair}_{METHOD}_Schaefer_difference_maps'
			# error_code = run_difference_atlas_map_with_stats(overlapping_subs, task_pair, METHOD, outfn, p.plot)
			# if p.verbose and error_code == 0: print(f'successfully ran {outfn}')
			# elif p.verbose: print(f'failed {outfn}')

			# run a version with all the data, across diff groups
			# outfn = f'{utils.get_results_dir()}/task_difference_maps/{task_pair}_{METHOD}_Schaefer_difference_maps_unpaired'
			# error_code = run_difference_indep_samples(task_pair, METHOD, outfn, p.plot)
			# if p.verbose and error_code == 0: print(f'successfully ran {outfn}')
			# elif p.verbose: print(f'failed {outfn}')











	    		