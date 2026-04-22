import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import os, sys, glob
import nilearn 
import nibabel as nib
from nilearn import datasets
from scipy import stats
import stats_helpers as sh
from nilearn import plotting
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker
from nibabel.nifti1 import Nifti1Image
from nilearn.image import math_img, concat_imgs

def load_atlas(atlas_name='Schaefer'):
    if atlas_name == 'Schaefer':
        ATLAS = datasets.fetch_atlas_schaefer_2018(resolution_mm=2, yeo_networks=17)
        ATLAS.labels = np.insert(ATLAS.labels, 0, 'Background')
    else:
        print(f'{atlas_name} not implemented')
    return ATLAS

def load_mask_parcel_data_file(subject, task, metric, file_idx=0, filter_by_age=0):
    atlas=load_atlas()
    masker = NiftiLabelsMasker(atlas.maps, labels=atlas.labels, standardize=False)
    nii = utils.get_metric_atlas_nii_subject(subject, task, metric, file_idx=file_idx, filter_by_age=filter_by_age)   
    masked_data = masker.fit_transform(nii)
    return np.squeeze(masked_data), masker

def run_difference_sl_map(overlap_masker, overlapping_subjects, task_pair, method, outfilename, plot):
	results_maps = []
	results_vecs = []
	[t0,t1] = task_pair.split('_')
	v0 = nib.load(f'{utils.get_results_dir()}/{t0}_{method}_all_subjects_results.nii.gz')
	v1 = nib.load(f'{utils.get_results_dir()}/{t1}_{method}_all_subjects_results.nii.gz')
	masked_v0 = overlap_masker.fit_transform(v0)
	masked_v1 = overlap_masker.fit_transform(v1)
	
	if task_pair[0] == 'rest':
		A = masked_v0
		B = masked_v1
	else:
		B = masked_v0
		A = masked_v1
	print(task_pair, A.shape, B.shape, np.mean(A), np.mean(B))
	mean_diff, pvals, sig_mask = sh.paired_difference_ttest(A, B, alpha=0.05, alternative='two-sided')
	print(f'Number significant: {np.sum(sig_mask)}')
	masked_mu = mean_diff * sig_mask
	
	masked_mu[masked_mu==0]=np.nan
	print(f'number of voxels not signif: {np.sum(masked_mu!=masked_mu)}')
	# project back out to nifti space
	masked_mean_img = overlap_masker.inverse_transform(masked_mu)
	nib.save(masked_mean_img, outfilename+'_avg_thresholded.nii.gz')
	mean_img = overlap_masker.inverse_transform(mean_diff)
	nib.save(mean_img, outfilename+'_avg_unthresholded.nii.gz')
	# pvals = overlap_masker.inverse_transform(p)
	# nib.save(pvals, outfilename+'_pvals_1samp_ttest.nii.gz')
	# tvals = overlap_masker.inverse_transform(t)
	# nib.save(tvals, outfilename+'_tstats.nii.gz')
	if plot:
		title = f'{task_pair} {method} avg diff thresholded'
		outfn = outfilename+'_avg_thresholded.png'
		plotting.plot_img_on_surf(masked_mean_img, 
		views=['lateral','medial'], 
		inflate=True, 
		bg_on_data=False, 
		alpha=0.8,
		output_file=outfn,
		darkness=0.8, 
		threshold=0.1, title=f'{title}'
		)

		title = f'{task_pair} {method} avg diff unthresholded'
		outfn = outfilename+'_avg_unthresholded.png'
		plotting.plot_img_on_surf(mean_img, 
		views=['lateral','medial'], 
		inflate=True, 
		bg_on_data=False, 
		alpha=0.8,
		output_file=outfn,
		darkness=0.8, 
		threshold=0.1, title=f'{title}'
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
			
		if task_pair[0] == 'rest': diff = v0 - v1
		else: diff = v1 - v0
		results_vecs.append(diff)
	if len(results_vecs) == 0:
		return 1
	arr = np.array(results_vecs)
	np.save(outfilename+'_all_subjects.npy', arr)

	# run t test


	t, p = stats.ttest_1samp(arr, popmean=0, axis=0)
	print(p.shape, arr.shape)
	alpha=0.05
	mu = np.mean(arr, axis=0)
	adj_p = stats_helpers.false_discovery_control(p)
	pval_mask = np.zeros_like(p)
	pval_mask[:]=np.nan
	pval_mask[adj_p<alpha]=1
	masked_mu = mu * pval_mask
	masked_mu[masked_mu==0]=np.nan
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




if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument('-d','--dataset',type=str, default='adult_restmovie')
	parser.add_argument('-s','--subject_filter', type=str, default='0')
	parser.add_argument('-a', '--atlas',type=str, default='Schaefer')
	parser.add_argument('-v','--verbose', type=int, default=1)
	parser.add_argument('-o', '--overwrite', type=int, default=1)
	parser.add_argument('-p', '--plot', type=int, default=1)
	p = parser.parse_args()

	# import the right utils file
	if p.dataset.lower() == 'adult_restmovie': import adult_restmovie_utils as utils; import adult_restmovie_config as config
	else: print(f'{p.dataset} not valid');  sys.exit(1)
	if p.verbose: print(f'loaded {p.dataset}_utils')
	VERBOSE=p.verbose
	# compare pairs of tasks
	METHODS_TO_RUN = ['TPHATE_DiffOp_IDE']#, 'MiND_ML', 'lPCA','PCA']

	subjects = utils.get_intersecting_subjects(subject_filter=0)
	print(subjects)
	task_pairs = ['aeronaut_rest','mickey_rest']
	for task_pair in task_pairs:
		for METHOD in METHODS_TO_RUN:
			outfn = f'{utils.get_results_dir()}/task_difference_maps/{task_pair}_{METHOD}_SL_difference_maps'
			overlap_mask = utils.get_intersect_mask()
			overlap_masker = NiftiMasker(mask_img=overlap_mask)
			error_code = run_difference_sl_map(overlap_masker, subjects, task_pair, METHOD, outfn, p.plot)
			if p.verbose and error_code == 0: print(f'successfully ran {outfn}')
			elif p.verbose: print(f'failed {outfn}')
			
			# now run atlas version
			# outfn = f'{utils.get_results_dir()}/task_difference_maps_v2/{task_pair}_{METHOD}_Schaefer_difference_maps'
			# error_code = run_difference_atlas_map_with_stats(subjects, task_pair, METHOD, outfn, p.plot)
			# if p.verbose and error_code == 0: print(f'successfully ran {outfn}')
			# elif p.verbose: print(f'failed {outfn}')
