import json, glob
from os.path import join, exists
import os
import nibabel as nib
from config import *
import pandas as pd
import seaborn as sns
import matplotlib
from nilearn.image import index_img


def determine_intersecting_subjects(basedir=None, task_list=[]):
    if len(task_list) == 0:
        task_list = list(RM_INFANT_DATA_DIRS.keys())
    
    subjects_by_task = []
    for t in task_list:
        d = RM_INFANT_DATA_DIRS[t]
        filenames = sorted(glob.glob(f'{d}/{RM_INFANT_STRING_MATCH}'))
        subjects = [f.split('/')[-1].split('_')[0] for f in filenames]
        subjects_by_task.append(subjects)
    intersection = set.intersection(*map(set, [subjects_by_task[i] for i in range(len(RM_INFANT_DATA_DIRS.keys()))]))

    return sorted(list(intersection))

def get_intersecting_subjects(subject_filter=0):
    return RM_INFANTS

def get_tasks():
    return list(RM_INFANT_DATA_DIRS.keys())

def get_results_dir():
    d = RM_INFANT_RESULTS_DIR
    if not exists(d): os.makedirs(d)
    return d

def get_task_filenames(subject_list, task):
    '''
    this is useful for the script that makes intersect masks
    '''

    data_dir = RM_INFANT_DATA_DIRS[task.upper()]
    filenames = []
    for s in subject_list:
        f = glob.glob(RM_INFANT_DATA_DIRS[task.upper()]+f'/{s}*{RM_INFANT_STRING_MATCH}')
        if len(f) == 0:
            print(RM_INFANT_DATA_DIRS[task.upper()]+f'/{s}*{RM_INFANT_STRING_MATCH}')
            continue
        filenames += f
    return filenames
    
def get_subject_data(sub_id, task, trim=True):
    fn = glob.glob(RM_INFANT_DATA_DIRS[task.upper()]+f'/{sub_id}*{RM_INFANT_STRING_MATCH}')[0]
    nii = nib.load(fn)
    if trim:
        nii = index_img(nii, np.arange(RM_TIMEPOINTS[task.upper()]))
    return nii

def get_basedir():
    return BASE_DIR_RM

def get_intersect_mask(subject_filter=0):
    fn = RM_INFANT_INTERSECT_MASK
    return nib.load(fn)

def get_brain_cmap(mpl_colorname='inferno'):
    n = 40
    color_list = sns.color_palette(mpl_colorname,n)[0:n]
    indices = np.concatenate((np.arange(n-1, -1, -1), np.arange(0, n,1)))
    brain_cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", [color_list[i] for i in indices])
    return brain_cmap

