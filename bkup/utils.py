# functions specific to this project
import numpy as np
import glob,os
from config import RAW_DIR, LABELS_DIR, SESSIONS2TASK, PREPROC_DATA_DIR, SUBJECTS, NODES_LH, NODES_RH, VOL_DATA_DIR
from scipy.stats import zscore
import nibabel as nib
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker

def get_mask():
    dirname = './masks/'
    fn = sorted(glob.glob(f"{dirname}/StudyForrest*"))[0]
    return nib.load(fn)

def get_vol_data(sub_id, task, run=None, mask=True):
    dirname = VOL_DATA_DIR
    if run != None:
        fn = sorted(glob.glob(f"{dirname}/sub-{sub_id:02d}_ses-{task}*_run-{run}*"))[0]
    else:
        fn = sorted(glob.glob(f"{dirname}/sub-{sub_id:02d}_ses-{task}*"))[0]
    nii=nib.load(fn)
    return nii



def get_sl_dimensionality_map(sub_num, run_num, sl_rad, ses, hemi='b'):
    if hemi == 'b':
        lh = get_sl_dimensionality_map(sub_num, run_num, sl_rad, ses, 'lh')
        rh = get_sl_dimensionality_map(sub_num, run_num, sl_rad, ses, 'rh')
        return np.concatenate((lh,rh),axis=0)
    fn = f'./results/sub-{sub_num:02d}_ses-{ses}_run-{run_num:02d}_rad{sl_rad}_dimensionality_{hemi}.npy'
    return np.load(fn)


def get_subject_raw_files(sub_num, space='fsaverage5', hemi='lh', ses='localizer', run=None):
    H = 'L' if hemi == 'lh' else 'R' 
    if run == None:
        fns = sorted(glob.glob(f'{RAW_DIR}/sub-{sub_num:02d}/ses-{ses}/func/*_space-{space}_hemi-{H}_bold.func.gii'))
    else: 
        fns = glob.glob(f'{RAW_DIR}/sub-{sub_num:02d}/ses-{ses}/func/*run-{run}_space-{space}_hemi-{H}_bold.func.gii')[0]
    return fns

def get_confounds(sub_num, session, run):
    task = SESSIONS2TASK[session]
    fn = glob.glob(f'{RAW_DIR}/sub-{sub_num:02d}/ses-{session}/func/*ses-{session}_task-{task}_run-{run}_desc-confounds_timeseries.tsv')[0]
    return fn

def get_subject_localizer_labels(sub_num, run_num):
    return glob.glob(f'{LABELS_DIR}/sub-{sub_num:02d}_run_{run_num}_tr_labels.npy')[0]

def load_subject_localizer_labels(sub_num, run_num):
    if run_num == 'all':
        labels = np.concatenate([np.load(get_subject_localizer_labels(sub_num, r)) for r in np.arange(1,5)], axis=0)
    else:
        labels = np.load(get_subject_localizer_labels(sub_num, run_num))
    return labels
                         

# specific formatting for budapets data; only gets called internally.
def _get_forrest_data(subject, side, runs, session, z, mask):
    LR = side.upper()
    task=SESSIONS2TASK[session]
    if LR == 'B':
        return np.hstack([_get_forrest_data(subject, 'L', runs, session, z, mask),
         _get_forrest_data(subject, 'R', runs, session, z, mask)])
    hemi = f'{LR.lower()}h'
    N_NODES = NODES_LH if LR == 'L' else NODES_RH
    fns = [f'{PREPROC_DATA_DIR}/sub-{subject:02d}_ses-{session}_task-{task}_run-{r}_fsaverage5_cleaned_{hemi}.npy' for r in runs]
    ds = [np.nan_to_num(zscore(np.load(fn)[:, :N_NODES], axis=0)) for fn in fns]
    dss = np.concatenate(ds,axis=0)
    return dss

# runs indicates which runs we want to return.
# this will be useful for datafolding.
def get_train_data(side, runs, session, num_subjects=14, z=True, mask=False):
    dss = []
    for subj in SUBJECTS[:num_subjects]:
        data = _get_forrest_data(subj, side.upper(), runs, session, z, mask)
        idx = np.where(np.logical_not(np.all(data == 0, axis=0)))[0]

        dss.append(data)
    return np.array(dss)

def get_test_data(side, runs, session, num_subjects=14, z=True, mask=False):
    dss = []
    for subj in SUBJECTS[:num_subjects]:
        data = _get_forrest_data(subj, side.upper(), runs, session, z, mask)
        dss.append(data)
    return np.array(dss)

    