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
import stats_helper
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
	for sub in overlapping_subjects:
		try:
			v0 = utils.get_metric_SL_nii_subject(sub, task_pair.split('_')[0], method, file_idx=0)
			v1 = utils.get_metric_SL_nii_subject(sub, task_pair.split('_')[1], method, file_idx=0)
			masked_v0=overlap_masker.fit_transform(v0)
			masked_v1=overlap_masker.fit_transform(v1)
		except:
			if VERBOSE: print(f'could not load {sub} {task_pair}')
			continue
		
		if task_pair[0] == 'rest':
			diff = masked_v0 - masked_v1
		else:
			diff = masked_v1 - masked_v0
		vol_res = overlap_masker.inverse_transform(diff)
		results_maps.append(vol_res)
		results_vecs.append(diff)

	if len(results_maps)==0:
		if VERBOSE: print(f'did not run {method},{task_pair}')
		return -1

	# run t test
	results_vecs = np.squeeze(np.array(results_vecs))
	t, p = stats.ttest_1samp(results_vecs, popmean=0, axis=0)
	print(results_vecs.shape, p.shape)
	alpha=0.05
	mu = np.mean(results_vecs, axis=0)
	adj_p = stats_helper.false_discovery_control(p)
	pval_mask = np.zeros_like(p)
	pval_mask[adj_p<=alpha]=1
	masked_mu = mu * pval_mask
	masked_mu[masked_mu==0]=np.nan

	# project back out to nifti space
	masked_mean_img = overlap_masker.inverse_transform(masked_mu)
	nib.save(masked_mean_img, outfilename+'_avg_thresholded.nii.gz')
	mean_img = overlap_masker.inverse_transform(mu)
	nib.save(mean_img, outfilename+'_avg_unthresholded.nii.gz')
	pvals = overlap_masker.inverse_transform(p)
	nib.save(pvals, outfilename+'_pvals_1samp_ttest.nii.gz')
	tvals = overlap_masker.inverse_transform(t)
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
	adj_p = stats_helper.false_discovery_control(p)
	pval_mask = np.zeros_like(p)
	pval_mask[adj_p<=alpha]=1
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

	# compare pairs of tasks
	METHODS_TO_RUN = ['TPHATE_DiffOp_IDE','PCA']#, 'MiND_ML', 'lPCA','PCA']

	subjects = utils.get_intersecting_subjects(subject_filter=0)
	print(subjects)
	task_pairs = ['aeronaut_rest','mickey_rest','aeronaut_mickey']
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












	    		