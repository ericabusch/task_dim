# healthy brain
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
    '''
    right now includes 614 subjects with all three tasks complete
    '''
    if subject_filter=='all' or subject_filter == '0': 
    	return get_intersecting_subjects()
    par_df = pd.read_csv(f'{BASIC_PARTICIPANT_DF}')
    par_df = par_df[par_df['confirmed_3_tasks']]
    participants = par_df[par_df['AgeGroup1']==subject_filter]['subject_id'].values
    return sorted(list(participants))

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

def get_intersecting_subjects(subject_filter='all'):
    if subject_filter == 'all' or subject_filter == '0':
        par_df = pd.read_csv(f'{BASIC_PARTICIPANT_DF}')
        par_df = par_df[par_df['confirmed_3_tasks']]
        return par_df['subject_id'].values
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
        f = sorted(glob.glob(f'{BASE_DIR_HBN}/{task}/{s}*.nii.gz'))
        if len(f) == 0:
            print(f'{BASE_DIR_HBN}/{task}/{s} DNE')
            continue
        filenames += f
    return filenames
    
def get_subject_data(sub_id, task='', trim=True, file_idx=0):
    fn = get_task_filenames([sub_id], task)[0]
    nii = nib.load(fn)
    if trim:
        nii = index_img(nii, np.arange(TRIM))
    return nii

def get_basedir():
    return BASE_DIR_HBN

def get_intersect_mask(subject_filter=0):
    fn = HBN_INTERSECT_MASK
    return nib.load(fn)

def has_repeat_files(subject, task):
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
        filestr = f'filter_{filter_by_age}'
    else:# metric in METHOD_NAMES:
        dirname = f'{dirname}/IDE/LOSO_parcel/results'
        filestr = f''
    try:
        f = sorted(glob.glob(f'{dirname}/{subject}_{task.lower()}*_{filestr}{metric}.nii.gz'))[0]
        # print(f'{dirname}/{subject}_{task.lower()}*_{filestr}{metric}.nii.gz')
    except:
        f = sorted(glob.glob(f'{dirname}/{subject}_{task}*_{filestr}{metric}.nii.gz'))[0]
    return nib.load(f)