# partly cloudy utils
import json, glob
from os.path import join, exists
import os
import nibabel as nib
import numpy as np
from partlycloudy_config import *
import pandas as pd
import seaborn as sns
import matplotlib
from nilearn.image import index_img, math_img
# from ide_helpers import METHOD_NAMES
import nilearn.datasets
from nilearn.maskers import NiftiMasker

def determine_intersecting_subjects(subject_filter='all'):
    if subject_filter=='all' or subject_filter == '0': 
    	return get_intersecting_subjects()
    par_df = pd.read_csv(f'{PC_PARTICIPANT_DF}')
    participants = par_df[par_df['AgeGroup']==subject_filter]['participant_id'].values
    participants=participants[participants!='sub-pixar053']
    return sorted(list(participants))

def get_sample_data(sample_sub_idx = 0 , roi_id=10):
    samp_subject = get_intersecting_subjects()[sample_sub_idx]
    data = get_subject_data(samp_subject)
    atlas_image, atlas_df = load_atlas()
    roi_mask_img = math_img(f"img == {roi_id}", img=atlas_image)
    masker = NiftiMasker(roi_mask_img, standardize=True)
    roi_data = masker.fit_transform(data)
    return roi_data

def get_groups():
    return PC_AGE_GROUPS

def load_atlas(atlas_name='Schaefer'):
    if atlas_name == 'Schaefer':
        ATLAS = nilearn.datasets.fetch_atlas_schaefer_2018(resolution_mm=2)
        ATLAS.labels = np.insert(ATLAS.labels, 0, 'Background')
        atlas_image = nib.load(ATLAS.maps)
        atlas_df = pd.DataFrame(ATLAS)
    else:
        print(f'{atlas_name} not implemented')
    return atlas_image, atlas_df

def load_ide_isc_atlas_df():
    df = pd.read_csv(f'{get_results_dir()}/parcelwise_results_ISC_IDE.csv',index_col=0)
    return df

def get_subject_age(subject_id):
    par_df = pd.read_csv(f'{PC_PARTICIPANT_DF}')
    age = par_df[par_df['participant_id']==subject_id]['Age'].item()
    return age

def get_subject_group(subject_id):
    par_df = pd.read_csv(f'{PC_PARTICIPANT_DF}')
    age_group = par_df[par_df['participant_id']==subject_id]['AgeGroupV2'].item()
    return age_group

def get_intersecting_subjects(subject_filter='all'):
	if subject_filter == 'all' or subject_filter == '0':
		subs = [f'sub-pixar{i:03d}' for i in range(1,156) if i != 53]
		return subs
	return determine_intersecting_subjects(subject_filter)

def get_tasks():
    return 'pixar'

def get_results_dir():
    d = PC_RESULTS_DIR
    if not exists(d): os.makedirs(d, exist_ok=True)
    return d

def get_out_dir():
    d = PC_OUTDIR
    if not exists(d): os.makedirs(d, exist_ok=True)
    return d

def get_scratch_dir():
    d = f'{SCRATCH_DIR}/partly_cloudy/'
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

def get_task_filenames(subject_list, task='pixar'):
    '''
    this is useful for the script that makes intersect masks
    '''
    filenames = []
    for s in subject_list:
        f = sorted(glob.glob(f'{PC_DATA_DIR}/{s}*.nii.gz'))
        if len(f) == 0:
            print(f'{PC_DATA_DIR}/{s}*.nii.gz')
            continue
        filenames += f
    return filenames
    
def get_subject_data(sub_id, task='', trim=True, file_idx=0):
    if 'pixar' not in sub_id:
        sub_id = f'sub-pixar{sub_id:03d}'
    fn = get_task_filenames([sub_id])[0]
    nii = nib.load(fn)
    return nii

def get_basedir():
    return BASE_DIR_PARTLY_CLOUDY

def get_intersect_mask(subject_filter=0):
    fn = PC_INTERSECT_MASK
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

def get_metric_SL_nii_subject(subject, task, metric, file_idx=0, filter_by_age=0, slrad=5):
    dirname = get_scratch_dir()
    task = task.lower()
    if metric == 'ISC':
        dirname = f'{dirname}/ISC/LOSO/results'
        filestr = ''
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
    task = task.lower()
    if metric == 'ISC':
        dirname = f'{dirname}/ISC/LOSO_parcel/results'
        filestr = ''
    else:# metric in METHOD_NAMES:
        dirname = f'{dirname}/IDE/LOSO_parcel/results'
        filestr = f''
    try:
        f = sorted(glob.glob(f'{dirname}/{subject}_{task.capitalize()}*_{metric}.nii.gz'))[0]
    except:
        f = sorted(glob.glob(f'{dirname}/{subject}_{task.lower()}*_{metric}.nii.gz'))[0]
    return nib.load(f)