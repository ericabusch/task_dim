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


def determine_intersecting_subjects(basedir=None, task_list=[]):

    return CNM_SUBJECTS

def get_intersecting_subjects(subject_filter=0):
    return CNM_SUBJECTS

def get_tasks():
    return CNM_TASKS

def get_results_dir():
    d = CNM_RESULTS_DIR
    if not exists(d): os.makedirs(d, exist_ok=True)
    return d

def get_out_dir():
    d = CNM_OUTDIR
    if not exists(d): os.makedirs(d, exist_ok=True)
    return d

def get_scratch_dir():
    d = f'{SCRATCH_DIR}/cneuromod/'
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
    data_dir = CNM_DATA_DIRS[task.lower()]
    filenames = []
    for s in subject_list:
        f = sorted(glob.glob(f'{data_dir}/{s}*'))
        if len(f) == 0:
            print(f'{data_dir}/{s}*')
            continue
        filenames += f
    return filenames
    
def get_subject_data(sub_id, task, trim=False,file_idx=0):
    fn = sorted(glob.glob(f'{CNM_DATA_DIRS[task]}/{sub_id}*'))
    try:
        fn=fn[file_idx]
    except:
        print(f'tried to find idx={file_idx} for {sub_id},{task}, but fns of len:{len(fn)}')
        sys.exit(1)

    nii = nib.load(fn) 
    return nii


def get_tr():
    return CNM_TR

def get_subject_data_fmriprep_output(sub_id, task):
    task_type = CNM_TASK_TO_TASK_TYPE[task]
    nii_fns, conf_fns, new_fns, mask_fns = [], [], [], []
    for ses in CNM_SESSIONS:
        fns = glob.glob(f'{CNM_DATALAD_DIR}/{task_type}/{sub_id}/{ses}/func/*{task}*_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz')
        masks  = glob.glob(f'{CNM_DATALAD_DIR}/{task_type}/{sub_id}/{ses}/func/*{task}*_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz')
        nii_fns += fns
        mask_fns += masks
        for f in fns:
            base = f.split('/')[-1]
            new_base = base.replace('.nii.gz','3mm_masked.nii.gz')
            base_dir = get_basedir()
            os.makedirs(f'{base_dir}/{task}_3mm_cleaned/', exist_ok=True)
            new_fns.append(f'{base_dir}/{task}_3mm_cleaned/{new_base}')
        fns = glob.glob(f'{CNM_DATALAD_DIR}/{task_type}/{sub_id}/{ses}/func/*{task}*confound*.tsv')
        conf_fns += fns

    return nii_fns, conf_fns, new_fns, mask_fns
    

def get_basedir():
    return BASE_DIR_CNEUROMOD

def get_intersect_mask(subject_filter=0, resample=False):
    fn = CNM_INTERSECT_MASK
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
    dirname = get_scratch_dir()
    if metric == 'ISC':
        dirname = f'{dirname}/ISC/LOSO/results'
        filter_string = f'_filter_{filter_by_age}'
    else:# metric in METHOD_NAMES:
        dirname = f'{dirname}/IDE/LOSO/results'
        filter_string=''
    try:
        task = task.lower().capitalize()
        fn = glob.glob(f'{dirname}/{subject}{filter_string}_{task}*{metric}_whole_brain_SL_rad5.nii.gz')[0]
    except:
        task = task.lower()
        fn = glob.glob(f'{dirname}/{subject}{filter_string}_{task}*{metric}_whole_brain_SL_rad5.nii.gz')[0]
    return nib.load(fn)