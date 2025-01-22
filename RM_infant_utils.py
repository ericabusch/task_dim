import json, glob
from os.path import join, exists
import os,sys
import nibabel as nib
from config import *
import pandas as pd
import seaborn as sns
import matplotlib
from nilearn.image import index_img


def determine_intersecting_subjects(basedir=None, task_list=[]):
    if len(task_list) == 0:
        task_list = list(RM_INFANT_DATA_DIRS.keys())
    subjects_by_task = {}
    for t in task_list:
        d = RM_INFANT_DATA_DIRS[t]
        filenames = sorted(glob.glob(f'{d}/s*{RM_INFANT_STRING_MATCH[t]}*'))
        subjects = []
        for f in filenames:
            f1 = f.split('/')[-1]
            s = f1.split('_')[:2]
            subjects.append("_".join(s))
        subjects_by_task[t] = list(set(subjects))
    intersection = intersecting_items(subjects_by_task)
    return sorted(intersection)

def get_intersecting_subjects(subject_filter=0):
	return INFANT_SUBJECTS_TASKS[subject_filter.lower()]

def get_tasks():
    return list(RM_INFANT_DATA_DIRS.keys())

def get_results_dir():
    d = RM_INFANT_RESULTS_DIR
    if not exists(d): os.makedirs(d)
    return d

def get_out_dir():
    d = RM_INFANT_OUTDIR
    if not exists(d): os.makedirs(d, exist_ok=True)
    return d

def get_scratch_dir():
    d = f'{SCRATCH_DIR}/infant_rest_movie/'
    if not exists(d): 
        os.makedirs(d, exist_ok=True)
        os.makedirs(d+'IDE/LOSO/results', exist_ok=True)
        os.makedirs(d+'IDE/LOSO/plots', exist_ok=True)
        os.makedirs(d+'ISC/LOSO/results', exist_ok=True)
        os.makedirs(d+'ISC/LOSO/plots', exist_ok=True)
        os.makedirs(d+'IDE/LOSO_parcel/results', exist_ok=True)
        os.makedirs(d+'IDE/LOSO_parcel/plots', exist_ok=True)
        os.makedirs(d+'ISC/LOSO_parcel/results', exist_ok=True)
        os.makedirs(d+'ISC/LOSO_parcel/plots', exist_ok=True)
    return d

def get_task_filenames(subject_list, task):
    '''
    this is useful for the script that makes intersect masks
    '''

    data_dir = RM_INFANT_DATA_DIRS[task.lower()]
    filenames = []
    for s in subject_list:
        f = sorted(glob.glob(RM_INFANT_DATA_DIRS[task.lower()]+f'/{s}*{RM_INFANT_STRING_MATCH[task]}*'))
        if len(f) == 0:
            print(RM_INFANT_DATA_DIRS[task.lower()]+f'/{s}*{RM_INFANT_STRING_MATCH[task]}*')
            continue
        filenames += f
    return filenames
    
def get_subject_data(sub_id, task, trim=False, file_idx=0):
    '''
    returns a list of niftis
    '''
    fn = sorted(glob.glob(RM_INFANT_DATA_DIRS[task.lower()]+f'/{sub_id}*{RM_INFANT_STRING_MATCH[task]}*'))
    try:
        fn=fn[file_idx]
    except:
        print(f'tried to find idx={file_idx} for {sub_id},{task}, but fns of len:{len(fn)}')
        sys.exit(1)
    nii =  nib.load(fn)
    if task == 'sleep':
        trim = False
    if trim:
        nii = index_img(nii, np.arange(RM_INFANT_TIMEPOINTS[task.lower()]))
    return nii

def get_basedir():
    return BASE_DIR_RM

def get_intersect_mask(subject_filter='sleep'):
	if subject_filter.lower() == 'sleep':
		fn = SLEEP_INFANT_INTERSECT_MASK
	elif subject_filter.lower() == 'mickey':
		fn = MICKEY_INFANT_INTERSECT_MASK
	else:
		fn = AERONAUT_INFANT_INTERSECT_MASK
	return nib.load(fn)

def get_brain_cmap(mpl_colorname='inferno'):
    n = 40
    color_list = sns.color_palette(mpl_colorname,n)[0:n]
    indices = np.concatenate((np.arange(n-1, -1, -1), np.arange(0, n,1)))
    brain_cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", [color_list[i] for i in indices])
    return brain_cmap

def get_metric_nii_subject(subject, task, metric, filter_by_age=0, slrad=5):
    dirname = get_scratch_dir()
    task = task.lower()
    if metric == 'ISC':
        dirname = f'{dirname}/ISC/LOSO/results'
        filter_string = f'_filter_{filter_by_age}'
    else:# metric in METHOD_NAMES:
        dirname = f'{dirname}/IDE/LOSO/results'
        filter_string=''
    try:
        #task = task.lower().capitalize()
        fn = glob.glob(f'{dirname}/{subject}{filter_string}_{task}*{metric}_whole_brain_SL_rad5.nii.gz')[0]
    except:
        #task = task.lower()
        print(f'{dirname}/{subject}{filter_string}_{task}*{metric}_whole_brain_SL_rad5.nii.gz')
        fn = glob.glob(f'{dirname}/{subject}{filter_string}_{task}*{metric}_whole_brain_SL_rad5.nii.gz')[0]
    return nib.load(fn)