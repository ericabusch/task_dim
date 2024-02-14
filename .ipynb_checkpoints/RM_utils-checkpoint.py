import json, glob
from os.path import join, exists
import os
import nibabel as nib
from config import *
import pandas as pd
import seaborn as sns
import matplotlib
from nilearn.image import index_img
from ide_helpers import METHOD_NAMES


def determine_intersecting_subjects(rest_movie_basedir=None, task_list=[]):
    
    if not rest_movie_basedir:
        rest_movie_basedir = BASE_DIR_RM
    if len(task_list) == 0:
        task_list = list(RM_DATA_DIRS.keys())
    
    subjects_by_task = []
    for t in task_list:
        d = RM_DATA_DIRS[t]
        filenames = sorted(glob.glob(f'{d}/{RM_STRING_MATCH}'))
        subjects = [f.split('/')[-1].split('_functional')[0] for f in filenames]
        subjects_by_task.append(subjects)
    intersection = set.intersection(*map(set, [subjects_by_task[k] for k in RM_DATA_DIRS.keys()]))

    return sorted(list(intersection))

def get_intersecting_subjects(subject_filter=0):
    return RM_SUBJECTS

def get_tasks():
    return list(RM_DATA_DIRS.keys())

def get_results_dir():
    d = RM_RESULTS_DIR
    if not exists(d): os.makedirs(d)
    return d

def get_task_filenames(subject_list, task):
    '''
    this is useful for the script that makes intersect masks
    '''

    data_dir = RM_DATA_DIRS[task.upper()]
    filenames = []
    for s in subject_list:
        f = glob.glob(RM_DATA_DIRS[task.upper()]+f'/{s}*{RM_STRING_MATCH}')
        if len(f) == 0:
            print(RM_DATA_DIRS[task.upper()]+f'/{s}*{RM_STRING_MATCH}')
            continue
        filenames += f
    return filenames
    
def get_subject_data(sub_id, task, trim=True):
    if 'rest_movie' not in sub_id:
        sub_id = f'rest_movie_{sub_id:02d}'
    fn = glob.glob(RM_DATA_DIRS[task.upper()]+f'/{sub_id}*{RM_STRING_MATCH}')[0]
    nii = nib.load(fn)
    if trim:
        nii = index_img(nii, np.arange(RM_TIMEPOINTS[task.upper()]))
    return nii

def get_basedir():
    return BASE_DIR_RM

def get_intersect_mask(subject_filter=0):
    fn = RM_INTERSECT_MASK
    return nib.load(fn)




def get_brain_cmap(mpl_colorname='inferno'):
    if type(mpl_colorname)== str:
        n = 40
        color_list = sns.color_palette(mpl_colorname,n)[0:n]
        indices = np.concatenate((np.arange(n-1, -1, -1), np.arange(0, n,1)))
        brain_cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", [color_list[i] for i in indices])
    else:
        first = mpl_colorname
        second = mpl_colorname
        colors1 = first(np.linspace(0., 1, 128))
        colors2 = second(np.linspace(0, 1, 128))[::-1]
        colors_combined = np.vstack((colors2, colors1))
        brain_cmap = matplotlib.colors.ListedColormap(colors_combined)
    return brain_cmap

def get_metric_nii_subject(subject, task, metric, filter_by_age=0, slrad=5):
    # if metric == 'optt' or metric == 'autocorr':
    #     dirname = f'{RM_RESULTS_DIR}/TPHATE_optt/LOSO'
    #     filter_string=''
    if metric == 'ISC':
        dirname = f'{RM_RESULTS_DIR}/ISC/LOSO'
        filter_string = f'_filter_{filter_by_age}'
    else:# metric in METHOD_NAMES:
        dirname = f'{RM_RESULTS_DIR}/IDE/LOSO'
        filter_string=''
    # else:
    #     print(f'{metric} not found')
    #     return
    try:
        task = task.lower().capitalize()
        fn = glob.glob(f'{dirname}/{subject}{filter_string}_{task}*{metric}_whole_brain_SL_rad5.nii.gz')[0]
    except:
        task = task.lower()
        fn = glob.glob(f'{dirname}/{subject}{filter_string}_{task}*{metric}_whole_brain_SL_rad5.nii.gz')[0]
    return nib.load(fn)