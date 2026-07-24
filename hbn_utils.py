# healthy brain network dataset
import json, glob
from os.path import join, exists
import os
import nibabel as nib
import numpy as np
from hbn_config import *
from nilearn import datasets
import pandas as pd
import seaborn as sns
import matplotlib
from nilearn.image import index_img
# from ide_helpers import METHOD_NAMES

def determine_intersecting_subjects(subject_filter='all'):
    par_df = pd.read_csv(f'{BASIC_PARTICIPANT_DF}')
    par_df = par_df[(par_df['include_both_tasks']==1)]
    if subject_filter=='all' or subject_filter == '0': 
        return sorted(par_df['subject_id'].values)
    participants = sorted(par_df[par_df['AgeGroup1']==subject_filter]['subject_id'].values)
    return participants

def get_groups():
    par_df = pd.read_csv(f'{BASIC_PARTICIPANT_DF}')
    groups = sorted([g for g in par_df['AgeGroup1'].unique()])
    return groups

def load_atlas(atlas_name='Schaefer'):
    if atlas_name == 'Schaefer':
        ATLAS = datasets.fetch_atlas_schaefer_2018(resolution_mm=2, yeo_networks=17)
        ATLAS.labels = np.insert(ATLAS.labels, 0, 'Background')
    else:
        print(f'{atlas_name} not implemented')
    return ATLAS

def load_ide_isc_atlas_df():
    df = pd.read_csv(f'{get_results_dir()}/parcelwise_results_ISC_IDE.csv',index_col=0)
    return df

def load_participant_df():
    df = pd.read_csv(f'{BASIC_PARTICIPANT_DF}',index_col=0)
    return df

def get_subject_age(subject_id):
    par_df = pd.read_csv(f'{BASIC_PARTICIPANT_DF}')
    age = par_df[par_df['subject_id']==subject_id]['age'].item()
    return age

def get_subject_sex(subject_id):
    par_df = pd.read_csv(f'{BASIC_PARTICIPANT_DF}')
    age = par_df[par_df['subject_id']==subject_id]['sex'].item()
    return age

def get_subject_site(subject_id):
    par_df = pd.read_csv(f'{BASIC_PARTICIPANT_DF}')
    age = par_df[par_df['subject_id']==subject_id]['session'].item()
    return age

def get_subject_group(subject_id):
    par_df = pd.read_csv(f'{BASIC_PARTICIPANT_DF}')
    age_group = par_df[par_df['subject_id']==subject_id]['AgeGroup1'].item()
    return age_group

def get_subject_motion(subject_id, task='movieTP'):
    if task == 'movieTP':
        motion_col = 'movie_FD'
    elif task == 'rest':
        motion_col = 'rest_FD'
    else:
        print(f'Task {task} not recognized for motion retrieval'); return None
    par_df = pd.read_csv(f'{BASIC_PARTICIPANT_DF}')
    motion = par_df[par_df['subject_id']==subject_id][motion_col].item()
    return motion

def get_intersecting_subjects(subject_filter='all'):
    return determine_intersecting_subjects(subject_filter)

def get_tasks():
    return HBN_TASKS

def get_results_dir():
    d = HBN_RESULTS_DIR
    if not exists(d): os.makedirs(d, exist_ok=True)
    return d

def get_out_dir():
    d = HBN_OUTDIR
    if not exists(d): os.makedirs(d, exist_ok=True)
    return d

def get_scratch_dir():
    d = f'{SCRATCH_DIR}/HBN/'
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

def get_fmriprep_input_dir():
    return MY_PREPROC_HBN

def get_fmriprep_subjects(debug=0):
    with open(f'{HBN_OUTDIR}/fmriprep_participants.txt','r') as f:
        subjects = f.readlines()
    subjects =  [s.strip() for s in subjects]
    if debug:
        subjects=subjects[:2]
    return subjects
    

def get_task_filenames(subject_list, task):
    '''
    this is useful for the script that makes intersect masks
    '''
    filenames = []
    for s in subject_list:
        f = sorted(glob.glob(f'{BASE_DIR_HBN}/derivatives/afni-smooth/{s}/func/*{task}*desc-clean.nii.gz'))
        if len(f) == 0:
            print(f'{BASE_DIR_HBN}/derivatives/afni-smooth/{s}/func/*{task}*desc-clean.nii.gz DNE')
            continue
        filenames += f
    return filenames
    
def get_subject_data(sub_id, task='', trim=False, file_idx=0):
    fn = get_task_filenames([sub_id], task)[0]
    print(fn)
    nii = nib.load(fn)
    if trim:
        nii = index_img(nii, np.arange(TRIM))
    return nii

def get_basedir():
    return BASE_DIR_HBN

def get_intersect_mask(subject_filter,task):
    fn = f'{ROOT}/task_dim/HBN/masks/HBN_intersect_mask_{subject_filter}_{task}.nii.gz'
    return nib.load(fn)

def has_repeat_files(subject, task):
    '''
    no one here has repeats
    '''
    return False

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

def fmriprep_confounds_threshold_fd(subject, task, fmriprep_dir='', threshold=3.0):
    """
    Load confounds file from fmriprep output and computes the % of timepoints exceeding a framewise displacement threshold.

    Parameters
    ----------
    bids_dir : str
        Path to the BIDS derivatives/fmriprep directory.
    subject : str
        Subject label (e.g., '01' or 'sub-01').
    task : str
        Task label (e.g., 'rest', 'movie').
    ses : str or None
        Session label (e.g., '01'), if applicable.
    run : str or int or None
        Run label (e.g., '01'), if applicable.

    Returns
    -------
    float
        Mean framewise displacement for the specified file.
    """
    if len(fmriprep_dir)==0: fmriprep_dir = MY_PREPROC_HBN
    subj = subject if subject.startswith('sub-') else f'sub-{subject}'
    pattern = os.path.join(
        fmriprep_dir, subj , 'ses*', 'func',
        f"{subj}_*task-{task}*desc-confounds_timeseries.tsv"
    )
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No confounds file found for pattern: {pattern}")
    confounds = pd.read_csv(files[0], sep='\t')
    if 'framewise_displacement' not in confounds.columns:
        raise ValueError("framewise_displacement column not found in confounds file.")
    num_exceeding = (confounds['framewise_displacement'].astype(float) > threshold).sum()
    return num_exceeding / len(confounds) 

def fmriprep_confounds_mean_fd(subject, task, fmriprep_dir=''):
    """
    Load confounds file from fmriprep output and compute mean framewise displacement.

    Parameters
    ----------
    bids_dir : str
        Path to the BIDS derivatives/fmriprep directory.
    subject : str
        Subject label (e.g., '01' or 'sub-01').
    task : str
        Task label (e.g., 'rest', 'movie').
    ses : str or None
        Session label (e.g., '01'), if applicable.
    run : str or int or None
        Run label (e.g., '01'), if applicable.

    Returns
    -------
    float
        Mean framewise displacement for the specified file.
    """
    if len(fmriprep_dir)==0: fmriprep_dir = MY_PREPROC_HBN
    subj = subject if subject.startswith('sub-') else f'sub-{subject}'
    pattern = os.path.join(
        fmriprep_dir, subj , 'ses*', 'func',
        f"{subj}_*task-{task}*desc-confounds_timeseries.tsv"
    )
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No confounds file found for pattern: {pattern}")
    confounds = pd.read_csv(files[0], sep='\t')
    if 'framewise_displacement' not in confounds.columns:
        raise ValueError("framewise_displacement column not found in confounds file.")
    return confounds['framewise_displacement'].astype(float).mean()


def get_subject_fmriprep_output_files(sub_id, task):
    print(f'{MY_PREPROC_HBN}/{sub_id}')
    nii_fn = sorted(glob.glob(f'{MY_PREPROC_HBN}/{sub_id}/*/func/*{task}*_space-MNI152Lin_desc-preproc_bold.nii.gz'))[0]
    conf_fn = sorted(glob.glob(f'{MY_PREPROC_HBN}/{sub_id}/*/func/*{task}*_desc-confounds_timeseries.tsv'))[0]
    mask_fn = sorted(glob.glob(f'{MY_PREPROC_HBN}/{sub_id}/*/func/*{task}*_space-MNI152Lin_desc-brain_mask.nii.gz'))[0]
    return nii_fn, conf_fn, mask_fn

def get_TR():
    return TR

def get_metric_SL_nii_subject(subject, task, metric, file_idx=0, filter_by_age=0, slrad=5):
    dirname = get_scratch_dir()
    task = task.lower()
    if metric == 'ISC':
        dirname = f'{dirname}/ISC/LOSO/results'
        filestr = f'filter_{p.subject_filter}'
    else:# metric in METHOD_NAMES:
        dirname = f'{dirname}/IDE/LOSO/results'
        filestr = f''
    try:
        f = sorted(glob.glob(f'{dirname}/{subject}_{task}*{metric}_whole_brain_SL_rad{slrad}.nii.gz'))[0]
    except:
        f = sorted(glob.glob(f'{dirname}/{subject}_{task.capitalize()}*{metric}_whole_brain_SL_rad{slrad}.nii.gz'))[0]
    return nib.load(f)

def get_metric_atlas_nii_subject(subject, task, metric, file_idx=0, filter_by_age=0, slrad=5):
    dirname = get_scratch_dir()
    if metric == 'ISC':
        dirname = f'{dirname}/ISC/LOSO_parcel/results/results_all'
        filestr = f'filter_{filter_by_age}_'
    else:# metric in METHOD_NAMES:
        dirname = f'{dirname}/IDE/LOSO_parcel/results'
        filestr = f''
    try:
        f = sorted(glob.glob(f'{dirname}/{subject}_{task.lower()}*_{filestr}{metric}.nii.gz'))[0]
        print(f'{dirname}/{subject}_{task.lower()}*_{filestr}{metric}.nii.gz')
    except:
        f = sorted(glob.glob(f'{dirname}/{subject}_{task}*_{filestr}{metric}.nii.gz'))[0]
    return nib.load(f)

def get_metric_atlas_df_subject(subject, task, metric, file_idx=0, filter_by_age=0, slrad=5):
    dirname = get_scratch_dir()
    if metric == 'ISC':
        dirname = f'{dirname}/ISC/LOSO_parcel/results/results_all'
        f = sorted(glob.glob(f'{dirname}/{subject}_{task}*_all_ISC_results.csv'))[0]
        return pd.read_csv(f,index_col=0)
    dirname = f'{dirname}/IDE/LOSO_parcel/results'
    f = sorted(glob.glob(f'{dirname}/{subject}_{task}*_all_IDE_results.csv'))[0]
    df = pd.read_csv(f, index_col=0)
    return df[df['ide_method']==metric].reset_index(drop=True)
