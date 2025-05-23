import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import os, sys, glob
import nilearn 
import nibabel as nib
from config import *
from nilearn import datasets
from scipy import stats
from nilearn import plotting
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker
from nibabel.nifti1 import Nifti1Image
from nilearn.image import math_img, concat_imgs
import stats_helper
import plot_utils

def get_overlap_masker(task0, task1, return_masker=False):
    mask0 = nib.load(INFANT_INTERSECT_MASKS[task0])
    mask1 = nib.load(INFANT_INTERSECT_MASKS[task1])
    sum_mask = math_img('np.where(np.add(X0,X1)==2,1,0)',X0=mask0, X1=mask1)
    if return_masker:
        return NiftiMasker(mask_img=sum_mask)
    coords = np.where(sum_mask.get_fdata()==1)
    return coords

def load_mask_parcel_data_file(subject, task, metric, file_idx=0, filter_by_age=0):
    atlas=load_atlas()
    masker = NiftiLabelsMasker(atlas.maps, labels=atlas.labels, standardize=False)
    nii = utils.get_metric_atlas_nii_subject(subject, task, metric, file_idx=file_idx, filter_by_age=filter_by_age)   
    masked_data = masker.fit_transform(nii)
    return np.squeeze(masked_data), masker

def run_difference_sl_map(overlap_masker, overlapping_subjects, task_pair, method, outfilename, plot):
	results_maps = []
	for sub in overlapping_subjects:
		try:
			v0 = utils.get_metric_SL_nii_subject(sub, task_pair.split('_')[0], method, file_idx=0)
			v1 = utils.get_metric_SL_nii_subject(sub, task_pair.split('_')[1], method, file_idx=0)
			masked_v0=overlap_masker.fit_transform(v0)
			masked_v1=overlap_masker.fit_transform(v1)
		except:
			if VERBOSE: print(f'could not load {sub} {task_pair}')
			continue
		
		if task_pair[0] == 'restingstate':
			diff = masked_v0 - masked_v1
		else:
			diff = masked_v1 - masked_v0
		vol_res = overlap_masker.inverse_transform(diff)

		if plot:
			title = f'{sub} {task_pair} {method}'
			outfn = outfilename.replace(task_pair,f'{sub}_{task_pair}')
			plotting.plot_img_on_surf(vol_res, 
			views=['lateral','medial'], 
			inflate=True, 
			bg_on_data=False, 
			      alpha=0.8,
			output_file=outfn,
			darkness=0.8, 
			threshold=0.5, title=f'{title}'
			)


		results_maps.append(vol_res)

	if len(results_maps)==0:
		if VERBOSE: print(f'did not run {method},{task_pair}')
		return -1

	cc_img = concat_imgs(results_maps)
	nib.save(cc_img, outfilename+'_all_subjects.nii.gz')
	mean_img = math_img('np.mean(X,axis=-1)', X=cc_img)
	nib.save(mean_img, outfilename+'_average.nii.gz')
	if plot:
		title = f'{task_pair} {method} avg'
		outfn = outfilename.replace('.nii.gz',f'_average.png')
		plotting.plot_img_on_surf(mean_img, 
		views=['lateral','medial'], 
		inflate=True, 
		bg_on_data=False, 
		      alpha=0.8,
		output_file=outfn,
		darkness=0.8, 
		threshold=0.5, title=f'{title}'
		)
	return 0

def run_difference_atlas_map_with_stats(overlapping_subjects, task_pair, method, outfilename, plot):
	results_vecs = []
	for sub in overlapping_subjects:
		try:
			v0, masker = load_mask_parcel_data_file(sub, task_pair.split('_')[0], method, file_idx=0)
			v1, masker = load_mask_parcel_data_file(sub, task_pair.split('_')[1], method, file_idx=0)
		except:
			print(f'could not load {sub},{task_pair},{method}')
			
		if task_pair[0] == 'restingstate': diff = v0 - v1
		else: diff = v1 - v0
		results_vecs.append(diff)
	if len(results_vecs) == 0:
		return 1
	arr = np.array(results_vecs)
	np.save(outfilename+'_all_subjects.npy', arr)

	# run t test
	t, p = stats.ttest_1samp(arr, popmean=0, axis=0)
	alpha=0.05
	mu = np.mean(arr, axis=0)
	pval_mask = np.zeros_like(p)
	pval_mask[p<=alpha]=1
	masked_mu = mu * pval_mask
	# project back out to nifti space
	masked_mean_img = masker.inverse_transform(masked_mu)
	nib.save(masked_mean_img, outfilename+'_avg_thresholded.nii.gz')
	mean_img = masker.inverse_transform(mu)
	nib.save(mean_img, outfilename+'_avg_unthresholded.nii.gz')
	pvals = masker.inverse_transform(p)
	nib.save(pvals, outfilename+'_pvals_1samp_ttest.nii.gz')
	tvals = masker.inverse_transform(t)
	nib.save(tvals, outfilename+'_tstats.nii.gz')
	if plot:
		title = f'{task_pair} {method} avg diff thresholded'
		outfn = outfilename+'_avg_thresholded.png'
		plotting.plot_img_on_surf(masked_mean_img, 
		views=['lateral','medial'], 
		inflate=True, 
		bg_on_data=False, 
		alpha=0.8,
		output_file=outfilename,
		darkness=0.8, 
		threshold=0.1, title=f'{title}'
		)
	return 0


def run_difference_indep_samples(task_pair, method, outfilename, plot,alpha=0.05):
	task0=task_pair.split('_')[0]
	task1=task_pair.split('_')[1]
	arr0=np.load(f'{utils.get_results_dir()}/all_subject_arrays_v2/{task0}_{method}_all_subject_results_atlas.npy')
	arr1=np.load(f'{utils.get_results_dir()}/all_subject_arrays_v2/{task1}_{method}_all_subject_results_atlas.npy')
	sample_vol = utils.get_intersect_mask()
	print(task_pair, arr0.shape, arr1.shape)
	if task0 == 'restingstate': 
		X0 = arr0
		X1 = arr1
	else:
		X0=arr1
		X1=arr0
	# run indep samples
	t,p=stats.ttest_ind(X0,X1,axis=0)
	p[p!=p]=1
	# adjust p values
	adj_p = stats_helper.false_discovery_control(p)
	# plot difference in means
	mu = np.mean(X0,axis=0)-np.mean(X1,axis=0)
	# mask differences
	pval_mask = np.zeros_like(p)
	pval_mask[adj_p<=alpha]=1
	masked_mu = mu * pval_mask
	masked_mu_nii = plot_utils.plot_array_to_atlas(masked_mu,sample_vol)
	adj_p_vals = plot_utils.plot_array_to_atlas(adj_p,sample_vol)

	nib.save(masked_mu_nii, outfilename+'_avg_thresholded.nii.gz')

	nib.save(adj_p_vals, outfilename+'_adj_pvals_indep_samp_ttest.nii.gz')
	if plot:
		title = f'{task_pair} {method} avg diff thresholded'
		outfn = outfilename+'_avg_thresholded.png'
		plotting.plot_img_on_surf(masked_mu_nii, 
		views=['lateral','medial'], 
		inflate=True, 
		bg_on_data=False, 
		alpha=0.8,
		output_file=outfilename,
		darkness=0.8, 
		threshold=0.1, title=f'{title}'
		)
	return 0



if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument('-d','--dataset',type=str, default='cneuromod')
	parser.add_argument('-s','--subject_filter', type=str, default='0')
	parser.add_argument('-a', '--atlas',type=str, default='Schaefer')
	parser.add_argument('-v','--verbose', type=int, default=1)
	parser.add_argument('-o', '--overwrite', type=int, default=1)
	parser.add_argument('-p', '--plot', type=int, default=1)
	p = parser.parse_args()

	# import the right utils file
	if p.dataset.lower() == 'cneuromod': import CNM_utils as utils
	else: print(f'{p.dataset} not valid');  sys.exit(1)
	if p.verbose: print(f'loaded {p.dataset}_utils')

	# compare pairs of tasks
	METHODS_TO_RUN = ['TPHATE_DiffOp_IDE', 'MiND_ML', 'lPCA','PCA']

	task_pairs = ['motor_restingstate','emotion_restingstate','relational_restingstate','gambling_restingstate',
	'language_restingstate','restingstate_wm','restingstate_s01e04a','restingstate_s01e04b','restingstate_social']
	overlapping_subs=utils.get_intersecting_subjects()
	for task_pair  in task_pairs:
		for METHOD in METHODS_TO_RUN:
			# outfn = f'{utils.get_results_dir()}/task_difference_maps_v2/{task_pair}_{METHOD}_SL_difference_maps'
			# overlap_mask = utils.get_intersect_mask()
			# overlap_masker = NiftiMasker(mask_img=overlap_mask)
			# error_code = run_difference_sl_map(overlap_masker, overlapping_subs, task_pair, METHOD, outfn, p.plot)
			# if p.verbose and error_code == 0: print(f'successfully ran {outfn}')
			# elif p.verbose: print(f'failed {outfn}')
			
			# # now run atlas version
			# outfn = f'{utils.get_results_dir()}/task_difference_maps_v2/{task_pair}_{METHOD}_Schaefer_difference_maps'
			# error_code = run_difference_atlas_map_with_stats(overlapping_subs, task_pair, METHOD, outfn, p.plot)
			# if p.verbose and error_code == 0: print(f'successfully ran {outfn}')
			# elif p.verbose: print(f'failed {outfn}')

			outfn = f'{utils.get_results_dir()}/task_difference_maps_v2/{task_pair}_{METHOD}_Schaefer_difference_maps_unpaired'
			error_code = run_difference_indep_samples(task_pair, METHOD, outfn, p.plot)
			if p.verbose and error_code == 0: print(f'successfully ran {outfn}')
			elif p.verbose: print(f'failed {outfn}')
		












	    		