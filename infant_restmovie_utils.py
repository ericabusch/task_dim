import json, glob
from os.path import join, exists
import os,sys
import nibabel as nib
from infant_restmovie_config import *
import pandas as pd
import seaborn as sns
import matplotlib
from nilearn.image import index_img
import numpy as np


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

def create_task_intersect_mask(task0, task1):
    '''
    Creates a mask that is the intersection of task0 and task1
    '''
    mask0=get_intersect_mask(task0)
    mask1=get_intersect_mask(task1)
    sum_mask = math_img('np.where(np.add(X0,X1)==2,1,0)', X0=mask0, X1=mask1)
    mask_img = nib.Nifti1Image(sum_mask.get_fdata(), mask0.affine)
    mask_img.header = mask0.header.copy()
    return mask_img

def load_ide_isc_atlas_df():
    df = pd.read_csv(f'{get_results_dir()}/parcelwise_results_ISC_IDE.csv',index_col=0)
    return df

def get_subject_age(subject_id, task='sleep'):
    par_df = pd.read_csv(f'{INFANT_PARTICIPANT_DATA[task]}')

    if 'milgram' not in INFANT_PARTICIPANT_DATA[task]:
        age = par_df[(par_df['task']==task) & (par_df['subject_id']==subject_id)]['age']        
        if len(age)==1: 
            age=age.item()
        else:
            try: 
                age=age.values[0]
            except:
                print(f'{subject_id},{task} DNE')
                return np.nan
        return age
       
    age = par_df[par_df['ppt']==subject_id]['age']
    if len(age)==1: 
        age=age.item()
    else:
        try: 
            age=age.values[0]
        except:
            print(f'{subject_id},{task} DNE')
            return np.nan
    return age

def get_intersecting_subjects(subject_filter=0):
    if subject_filter == 0: # just get all subjects
        unique_values = list(set(value for values in INFANT_SUBJECTS_TASKS.values() for value in values))
        # Convert the set to a sorted list (optional)
        return sorted(unique_values)
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
    d = f'{SCRATCH_DIR}/infant_restmovie/'
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
    # if task == 'sleep': trim = True
    if trim: nii = index_img(nii, np.arange(RM_INFANT_TIMEPOINTS[task.lower()]))
    return nii

def get_basedir():
    return BASE_DIR_RM

def get_intersect_mask(subject_filter='sleep'):
    if subject_filter.lower() == 'sleep':
        fn = SLEEP_INFANT_INTERSECT_MASK
    elif subject_filter.lower() == 'mickey':
        fn = MICKEY_INFANT_INTERSECT_MASK
    elif subject_filter.lower()=='aeronaut':
        fn = AERONAUT_INFANT_INTERSECT_MASK
    else:
        return get_overlap_masker(subject_filter.split('_')[0], subject_filter.split('_')[1], return_masker=True)
    return nib.load(fn)

def get_overlap_masker(task0, task1, return_masker=False):
    mask0 = nib.load(INFANT_INTERSECT_MASKS[task0])
    mask1 = nib.load(INFANT_INTERSECT_MASKS[task1])
    sum_mask = math_img('np.where(np.add(X0,X1)==2,1,0)',X0=mask0, X1=mask1)
    if return_masker:
        return NiftiMasker(mask_img=sum_mask)
    coords = np.where(sum_mask.get_fdata()==1)
    return coords

def has_repeat_files(subject, task):
    if task in RM_INFANT_MULTIPLE_FILES.keys() and subject in RM_INFANT_MULTIPLE_FILES[task].keys():
        return RM_INFANT_MULTIPLE_FILES[task][subject]
    return 0

def get_brain_cmap(mpl_colorname='inferno'):
    n = 40
    color_list = sns.color_palette(mpl_colorname,n)[0:n]
    indices = np.concatenate((np.arange(n-1, -1, -1), np.arange(0, n,1)))
    brain_cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", [color_list[i] for i in indices])
    return brain_cmap

def get_metric_SL_nii_subject(subject, task, metric, file_idx=0, filter_by_age=0, slrad=5):
    dirname = get_scratch_dir()
    task = task.lower()
    if metric == 'ISC':
        dirname = f'{dirname}/ISC/LOSO/results'
        filestr = f''
    else:# metric in METHOD_NAMES:
        dirname = f'{dirname}/IDE/LOSO/results'
        filestr = f'file_idx_{file_idx}'
    try:
        f = sorted(glob.glob(f'{dirname}/{subject}*{task}*{filestr}*{metric}_whole_brain_SL_rad{slrad}.nii.gz'))[0]
    except:
        print(f'Does not exist: {subject}*{task}*{filestr}*{metric}_whole_brain_SL_rad{slrad}.nii.gz')
        return None
    return nib.load(f)


def get_metric_atlas_nii_subject(subject, task, metric, file_idx=0, filter_by_age=0):
    dirname = get_scratch_dir()
    task = task.lower()
    if metric == 'ISC':
        dirname = f'{dirname}/ISC/LOSO_parcel/results'
        filestr = ''
    else:# metric in METHOD_NAMES:
        dirname = f'{dirname}/IDE/LOSO_parcel/results'
        filestr = f'file_idx_{file_idx}'
    f = sorted(glob.glob(f'{dirname}/{subject}*{task}*{filestr}*{metric}.nii.gz'))[0]
    return nib.load(f)






