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
from scipy.stats import spearmanr

# run correlation between age (in childhood) and IDE masks
def run_ide_correlation(vectors, age_values, alpha=0.05):
	'''
	sl_vectors = [n_subjects, n_voxels]
	age_values = [n_subjects,1]
	'''
	scores = np.empty((vectors.shape[1], 3))
	for i in range(vectors.shape[1]):
		if vectors[0, i] == 0:
			continue
		r0=spearmanr(vectors[:,i], age_values)
		scores[i,0]=r0[0]
		scores[i,1]=r0[1]
		scores[i,2]=int(r0[1]<=alpha)
	return scores

def run_infant_rest_movie_analyses():
	dirname = f'{utils.get_results_dir()}/all_subject_arrays'
	for task in utils.get_tasks():
		outfilename = f'{utils.get_results_dir()}/{task}_IDE_age_correlation_'
		subjects = utils.get_intersecting_subjects(task)
		print(task, subjects)
		ages = [utils.get_subject_age(s, task) for s in subjects]
		sl_array = np.load(f'{dirname}/{task}_TPHATE_DiffOp_IDE_all_subject_results.npy')
		atlas_array = np.load(f'{dirname}/{task}_TPHATE_DiffOp_IDE_all_subject_results_atlas.npy')
		assert sl_array.shape[0] == atlas_array.shape[0] == len(ages)
		atlas_corr_results = run_ide_correlation(atlas_array,ages)
		sl_corr_results = run_ide_correlation(sl_array,ages)
		np.save(outfilename+'_searchlights.npy', sl_corr_results)
		np.save(outfilename+'_atlas.npy', atlas_corr_results)

def run_partly_cloudy_analyses():
	# load in subjects 
	groups = ['3yo','4yo','5yo','7yo','8-12yo']
	atlas_data = []
	sl_data = []
	ages = []
	for group in groups:
		subjects = utils.get_intersecting_subjects(subject_filter=group)
		a1=f'{utils.get_results_dir()}/all_subject_arrays/subject_filter_{group}_TPHATE_DiffOp_IDE_atlas1_all_subject_results_no_repeats.npy'
		a2=f'{utils.get_results_dir()}/all_subject_arrays/subject_filter_{group}_TPHATE_DiffOp_IDE_atlas0_all_subject_results_no_repeats.npy'
		arr = np.load(a1)
		sl_arr = np.load(a2)
		ag = [utils.get_subject_age(s) for s in subjects]
		sl_data.append(sl_arr)
		ages.append(ag)
		atlas_data.append(arr)
	atlas_data = np.concatenate(atlas_data)
	sl_data = np.concatenate(sl_data)
	ages=np.concatenate(ages)
	scores_atlas = run_ide_correlation(atlas_data, ages)
	scores_sl = run_ide_correlation(sl_data, ages)
	print(atlas_data.shape, sl_data.shape, ages.shape)
	np.save(f'{utils.get_results_dir()}/IDE_age_correlation_atlas.npy',scores_atlas)
	np.save(f'{utils.get_results_dir()}/IDE_age_correlation_searchlights.npy',scores_sl)

def load_parcel_data(subject, task, metric):
	ide_fn = sorted(glob.glob(f'{utils.get_scratch_dir()}/IDE/LOSO_parcel/results/{subject}*{task}*all_IDE_results.csv'))[0]
	df = pd.read_csv(ide_fn, index_col=0)
	vals = df[df['ide_method']==metric]['id_estimate'].values
	return vals

def check_has_tasks(subject, task0, task1):
	try:
		t0_fn = sorted(glob.glob(f'{utils.get_scratch_dir()}/IDE/LOSO_parcel/results/{subject}*{task0}*all_IDE_results.csv'))[0]
		t1_fn = sorted(glob.glob(f'{utils.get_scratch_dir()}/IDE/LOSO_parcel/results/{subject}*{task1}*all_IDE_results.csv'))[0]
		return True
	except:
		print(f'{subject} does not have {task0},{task1}')

def run_hbn_analyses():
	# load in subjects 
	atlas_data = []
	ages = []
	subjects = utils.get_intersecting_subjects()
	TASKS=['rest','movieTP']
	subjects_confirmed = [s for s in subjects if check_has_tasks(s, TASKS[0], TASKS[1])]
	ages = np.array([utils.get_subject_age(s) for s in subjects_confirmed]).reshape(-1,1)
	task_data = {}
	for t in TASKS:
		task_data[t]=[]
		for s in subjects_confirmed:
			v = load_parcel_data(s, t, "TPHATE_DiffOp_IDE")
			task_data[t].append(v)
		task_data[t]=np.array(task_data[t])
	corr_age = {t: run_ide_correlation(task_data[t], ages) for t in TASKS}
	diffs = task_data['rest']-task_data['movieTP']
	corr_age['rest_movieTP']= run_ide_correlation(diffs, ages)
	for K,V in corr_age.items():
		np.save(f'{utils.get_results_dir()}/{K}_IDE_age_correlation_atlas.npy',V)



if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('-d','--dataset',type=str)
	parser.add_argument('-v','--verbose', type=int, default=1)
	parser.add_argument('-o', '--overwrite', type=int, default=1)
	parser.add_argument('-p', '--plot', type=int, default=1)
	p = parser.parse_args()

	# import the right utils/config file
	if p.dataset.lower() == 'infant_restmovie': 
		import infant_restmovie_utils as utils; 
		import infant_restmovie_config as config
		run_infant_rest_movie_analyses()
	elif p.dataset.lower() == 'partlycloudy': 
		import partlycloudy_utils as utils; 
		import partlycloudy_config as config
		run_partly_cloudy_analyses()
	elif p.dataset.lower() == 'hbn': 
		import hbn_utils as utils; 
		import hbn_config as config
		run_hbn_analyses()
	else: print(f'{p.dataset} not valid')  ; sys.exit(1)






