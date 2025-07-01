import json, glob
from os.path import join, exists
import os
import nibabel as nib
import numpy as np
from narratives_config import *
import pandas as pd
import seaborn as sns
import matplotlib
from ide_helpers import METHOD_NAMES


def get_brain_cmap(mpl_colorname='inferno'):
    '''
    creates a reversible colormap good for surface plots
    '''
    
    n = 40
    color_list = sns.color_palette(mpl_colorname,n)[0:n]
    indices = np.concatenate((np.arange(n-1, -1, -1), np.arange(0, n,1)))
    brain_cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", [color_list[i] for i in indices])
    return brain_cmap

def determine_intersecting_subjects(narratives_dir=None, task_list=[]):
    '''
    from TLB
    
    Find subjects intersecting across narratives tasks.

    Inputs:
        - narratives_dir: base directory of the Narratives dataset
        - task_list: list of tasks to find intersecting subjects across.

    Outputs:
        - intersection: a sorted list of subject names across tasks.
    '''
    if not narratives_dir:
        narratives_dir = NARRATIVES_DATALAD_DIR
    if len(task_list) == 0:
        task_list = list(NARRATIVES_TIMEPOINTS.keys())
    #load the information of which subjects did which tasks
    with open(join(narratives_dir, 'code', 'task_meta.json')) as f:
        task_meta = json.load(f)

    #find each task we're curious about in the meta file
    task_info = list(map(task_meta.get, task_list))

    # take the intersection of subjects between 
    intersection = set.intersection(*map(set, map(dict.keys, task_info)))

    return sorted(list(intersection))

def get_intersecting_subjects(subject_filter=0):
    # temporarily remove these
    exclude = ['sub-309','sub-306','sub-303','sub-305','sub-298']
    n = NARRATIVES_SUBJECTS
    n = [N for N in n if N not in exclude]
    return n

def get_tasks():
    return list(NARRATIVES_DATA_DIRS.keys())

def get_out_dir():
    d = NARRATIVES_OUTDIR
    if not exists(d): os.makedirs(d)
    return d

def get_scratch_dir():
    d = f'{SCRATCH_DIR}/narratives/'
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

def get_results_dir():
    d = NARRATIVES_RESULTS_DIR
    if not exists(d): os.makedirs(d)
    return d

def get_task_filenames(subject_list, task):
    data_dir = NARRATIVES_DATA_DIRS[task.lower()]
    filenames = []
    for s in subject_list:
        f = sorted(glob.glob(NARRATIVES_DATA_DIRS[task.lower()]+f'/{s}*.nii.gz'))[0]
        filenames.append(f)
    return filenames
    
def has_repeat_files(subject, task):
    return 0

def get_subject_data(sub_id, task,trim=False,file_idx=0):
    if 'sub' not in sub_id:
        sub_id = f'sub-{sub_id}'
    fn = glob.glob(NARRATIVES_DATA_DIRS[task.lower()]+f'/{sub_id}*.nii.gz')[file_idx]
    print(NARRATIVES_DATA_DIRS[task.lower()])
    print(fn)
    nii = nib.load(fn)
    return nii

def get_basedir():
    return BASE_DIR_NARRATIVES

def get_intersect_mask(subject_filter=0):
    fn = NARRATIVES_INTERSECT_MASK
    return nib.load(fn)

def get_metric_SL_nii_subject(subject, task, metric, file_idx=0, filter_by_age=0, slrad=5):
    dirname = get_scratch_dir()
    task = task.lower()
    if metric == 'ISC':
        dirname = f'{dirname}/ISC/LOSO/results'
        filestr = ''
    else: 
        dirname = f'{dirname}/IDE/LOSO/results'
        filestr = f''
    f = sorted(glob.glob(f'{dirname}/{subject}_{task}*{filestr}*{metric}_whole_brain_SL_rad{slrad}.nii.gz'))[0]
    return nib.load(f)

def get_metric_atlas_nii_subject(subject, task, metric, file_idx=0, filter_by_age=0):
    dirname = get_scratch_dir()
    task = task.lower()
    if metric == 'ISC':
        dirname = f'{dirname}/ISC/LOSO_parcel/results'
        filestr = ''
    else:# metric in METHOD_NAMES:
        dirname = f'{dirname}/IDE/LOSO_parcel/results'
        filestr = f''
    f = sorted(glob.glob(f'{dirname}/{subject}_{task}*{filestr}*{metric}.nii.gz'))[0]
    return nib.load(f)

def get_tasks():
    return list(NARRATIVES_DATA_DIRS.keys())

def get_metric_atlas_df_subject(subject, task, metric, file_idx=0, filter_by_age=0, slrad=5):
    dirname = get_scratch_dir()
    task = task.lower()
    if metric == 'ISC':
        dirname = f'{dirname}/ISC/LOSO_parcel/results'
        f = sorted(glob.glob(f'{dirname}/{subject}_{task.lower()}*_all_ISC_results.csv'))[0]
    else:# metric in METHOD_NAMES:
        dirname = f'{dirname}/IDE/LOSO_parcel/results'
        f = sorted(glob.glob(f'{dirname}/{subject}_{task.lower()}*_all_IDE_results.csv'))[0]
    return pd.read_csv(f,index_col=0)