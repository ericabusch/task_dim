import json, glob
from os.path import join, exists
import os
import nibabel as nib
from config import *
import pandas as pd
import seaborn as sns
import matplotlib


def get_brain_cmap(mpl_colorname='inferno'):
    n = 40
    color_list = sns.color_palette(mpl_colorname,n)[0:n]
    indices = np.concatenate((np.arange(n-1, -1, -1), np.arange(0, n,1)))
    brain_cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", [color_list[i] for i in indices])
    return brain_cmap

def check_has_preproc(subject_list, task_list=[]):
    good_subjects = []
    if len(task_list) == 0: task_list = CAMCAN_TASKS
        
    for S in subject_list:
        s = S.replace("sub-", '')
        dirname = f'{BASE_DIR_CAMCAN}/{CAMCAN_PREPROC_MIDSTR}/{s}/'
        sub_total = 0
        for task in task_list:
            fn = glob.glob(join(dirname, CAMCAN_DIR_CODE[task], f'*fMR*_{s}*.nii'))
            if len(fn) != 0: sub_total += 1
        if sub_total == len(task_list): good_subjects.append(S)
    return good_subjects

def find_intersecting_subjects(camcan_dir=None, task_list=[], filter_by_age=0):
    '''    
    Find subjects intersecting across camcan tasks.

    Inputs:
        - camcan_dir: base directory of the camcan dataset
        - task_list: list of tasks to find intersecting subjects across.

    Outputs:
        - intersection: a sorted list of subject names across tasks.
    '''
    if not camcan_dir:
        camcan_dir = join(BASE_DIR_CAMCAN, CAMCAN_RAW_MIDSTR)
    if len(task_list) == 0:
        task_list = CAMCAN_TASKS
    
    # load in participant files and filter by age
    dfs = [pd.read_csv(CAMCAN_PARTICIPANT_FILES[t], sep='\t') for t in task_list]
    if filter_by_age > 0: 
        dfs = [d[d['age'] < filter_by_age] for d in dfs]
    
    # now find who overlaps
    subjects_by_task = [d.participant_id.unique() for d in dfs]
    common = set.intersection(*map(set,subjects_by_task))
    common = check_has_preproc(common, task_list = task_list)
    taskstr='_'.join(task_list)
    
    with open(f'{ROOT}/task_dim/CamCAN/subject_lists/subject_list_group_{taskstr}_under_{filter_by_age}.txt','w') as f:
        for s in common:
            f.write(f'{s}\n')
    return sorted(common)

def get_tasks():
    return CAMCAN_TASKS

def get_results_dir():
    d = f'{ROOT}/task_dim/CamCAN/results/'
    os.makedirs(d, exist_ok=True)
    return d

def get_intersecting_subjects(subject_filter=0):
    tasks = get_tasks()
    taskstr='_'.join(tasks)
    fn = f'{ROOT}/task_dim/CamCAN/subject_lists/subject_list_group_{taskstr}_under_{subject_filter}.txt'
    if not exists(fn):
        sublist = find_intersecting_subjects(filter_by_age=subject_filter)
    else:
        with open(fn, 'r') as f:
            sublist = f.readlines()
        sublist = [s.strip() for s in sublist]
    return sublist

def get_task_filenames(subject_list, task):
    data_dir = CAMCAN_DATA_DIRS[task]
    camcan_taskcode = f'epi_{task.lower()}'
    filenames = []
    for s in subject_list:
        filenames += sorted(glob.glob(f'{data_dir}/{s}/{camcan_taskcode}/*.nii.gz'))
    return filenames

def get_basedir():
    return BASE_DIR_CAMCAN

def get_intersect_mask(subject_filter=0):
    fn = f'{ROOT}/task_dim/masks/MOVIE_REST_SMT_intersect_mask_u{subject_filter}.nii.gz'
    return nib.load(fn)

def get_subject_data(subject, task):
    fn = f'{CAMCAN_ORGANIZED_DIRS[task.upper()]}/{subject}_{task.upper()}.nii'
    nii = nib.load(fn)
    return nii

