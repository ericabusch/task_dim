import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import os, sys, glob
import nilearn 
import nibabel as nib
from hbn_config import *
from hbn_utils import *
from nilearn import datasets
import stats_helper
from scipy import stats
from nilearn import plotting
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker
from nibabel.nifti1 import Nifti1Image
from nilearn.image import math_img, concat_imgs
import plot_utils

def load_sample_nii():
	dirname = get_scratch_dir()
	dirname = f'{dirname}/IDE/LOSO_parcel/results'
	fn=glob.glob(f'{dirname}/*.nii.gz')[0]
	return nib.load(fn)

def load_fit_atlas_masker():
    atlas=load_atlas()
    masker = NiftiLabelsMasker(atlas.maps, labels=atlas.labels, standardize=False)
    sample_nii = load_sample_nii()
    masked_data = masker.fit_transform(sample_nii)
    return masker

def load_parcel_data(subject, task, metric):
	ide_fn = sorted(glob.glob(f'{get_scratch_dir()}/IDE/LOSO_parcel/results/{subject}*{task}*all_IDE_results.csv'))[0]
	df = pd.read_csv(ide_fn, index_col=0)
	vals = df[df['ide_method']==metric]['id_estimate'].values
	return vals

def check_has_tasks(subject, task0, task1):
	try:
		t0_fn = sorted(glob.glob(f'{get_scratch_dir()}/IDE/LOSO_parcel/results/{subject}*{task0}*all_IDE_results.csv'))[0]
		t1_fn = sorted(glob.glob(f'{get_scratch_dir()}/IDE/LOSO_parcel/results/{subject}*{task1}*all_IDE_results.csv'))[0]
		return True
	except:
		print(f'{subject} does not have {task0},{task1}')
		return False

def run_difference_atlas(subjects_confirmed, task_pair, method, outfilename, plot, alpha=0.05):
	results_vecs = []
	for sub in subjects_confirmed:
		try:
			v0 = load_parcel_data(sub, task_pair.split('_')[0], method)
			v1 = load_parcel_data(sub, task_pair.split('_')[1], method)
		except:
			print(f'could not load {sub},{task_pair},{method}')
			return
		diff = v0 - v1
		results_vecs.append(diff)
	
	if len(results_vecs) == 0:
		return 1
	arr = np.array(results_vecs)
	np.save(outfilename+'_all_subjects.npy', arr)
	print(f'saved {outfilename}_all_subjects')
	masker=load_fit_atlas_masker()
	# run t test
	t, p = stats.ttest_1samp(arr, popmean=0, axis=0)
	mu = np.mean(arr, axis=0)
	adj_p = stats_helper.false_discovery_control(p)
	pval_mask = np.zeros_like(p)
	pval_mask[adj_p<=alpha]=1
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




if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument('-d','--dataset',type=str, default='hbn')
	parser.add_argument('-s','--subject_filter', type=str, default='0')
	parser.add_argument('-a', '--atlas',type=str, default='Schaefer')
	parser.add_argument('-v','--verbose', type=int, default=1)
	parser.add_argument('-o', '--overwrite', type=int, default=1)
	parser.add_argument('-p', '--plot', type=int, default=1)
	p = parser.parse_args()

	# import the right utils file
	if p.dataset.lower() == 'hbn': import infant_restmovie_utils as utils
	else: print(f'{p.dataset} not valid');  sys.exit(1)
	if p.verbose: print(f'loaded {p.dataset}_utils')

	# compare pairs of tasks
	TASKS=['rest','movieTP']
	METHODS_TO_RUN = ['TPHATE_DiffOp_IDE','TPHATE_optt','TPHATE_IDE_GAP','PCA']#, 'MiND_ML', 'lPCA','PCA']

	subjects = determine_intersecting_subjects()
	subjects_confirmed = []
	for s in subjects:
		if check_has_tasks(s, TASKS[0], TASKS[1]):
			subjects_confirmed.append(s)

	if p.verbose: print(f'found {len(subjects_confirmed)} subs')
	os.makedirs(f'{get_results_dir()}/task_difference_maps',exist_ok=True)
	task_pair='rest_movieTP'
	for METHOD in METHODS_TO_RUN:
		for g in get_groups():
			subjects = determine_intersecting_subjects(subject_filter=g)
			subjects_confirmed = []
			for s in subjects:
				if check_has_tasks(s, TASKS[0], TASKS[1]):
					subjects_confirmed.append(s)
			print(f'found {len(subjects_confirmed)} subs for {g}')
			outfn = f'{get_results_dir()}/task_difference_maps/{g}_{task_pair}_{METHOD}_difference'
			error_code = run_difference_atlas(subjects_confirmed, task_pair, METHOD, outfn, plot=True, alpha=0.05)
			if p.verbose and error_code == 0: print(f'successfully ran {outfn} {g}')
			elif p.verbose: print(f'failed {outfn}')












	    		