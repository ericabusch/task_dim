import numpy as np
import pandas as pd
# %load_ext autoreload
# %autoreload 2
import matplotlib.pyplot as plt
import seaborn as sns
import os, sys, glob
import nilearn 
import nibabel as nib
from nibabel import processing
import config
import RM_utils as utils
from nilearn import datasets
from scipy import stats
from nilearn import plotting
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker
import TPHATE.tphate 
from TPHATE.tphate import tphate
import scprep
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings("ignore")
from scipy.spatial.distance import pdist, cdist, squareform
from nilearn.image import math_img
from joblib import Parallel, delayed

def embed_tphate_roi(X, sub, task, roi):
    outfn = f'RestMovie/data/embeddings/sub-{sub:02d}_{task}_tphate_embedding_2d_t4_{roi}.npy'
    op = tphate.TPHATE(verbose=0).fit(X)
    e = op.transform(X)
    opt_t = op.optimal_t
    drop = op.dropoff
    x = tphate.TPHATE(verbose=0, n_components=2, t=4).fit_transform(X)
    np.save(outfn, x)

    title=f'sub {sub} {roi}'
    if opt_t !=None: title+=f' drop={drop}, opt_t={opt_t}'

    filename=f'RestMovie/plots/sub-{sub:02d}_{task}_tphate_{roi}_{ATLAS_NAME}.png'
    
    return opt_t, drop

def run_subject_HarOxf(sub_id, task):
    ATLAS = nilearn.datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr25-2mm')
    ATLAS_NAME="HarvardOxford"
    atlas_df = pd.DataFrame(ATLAS)
    atlas_image = nib.load(ATLAS.filename)
    dim_res, ac_res = [], []
    
    nii = utils.get_subject_data(sub_id, task, trim=True)
    # apply whole-brain mask, then invert
    wb_mask = utils.get_mask(task)
    masker_wb = NiftiMasker(mask_img=wb_mask, standardize=True)
    masked_nii = masker_wb.fit_transform(nii)
    nii = masker_wb.inverse_transform(masked_nii)
    
    dim_vol = None
    AC_vol = None
    for roi_id in atlas_df.index[1:]:
        roi_mask_img = math_img(f"img == {roi_id}", img=atlas_image)
        masker = NiftiMasker(roi_mask_img, standardize=True)
        roi_data = masker.fit_transform(nii)
        tokens = atlas_df.iloc[roi_id]['labels'][1]
        roi_str = '_'.join(tokens)
        d,a = embed_tphate_roi(roi_data, sub_id, task, roi_str)
        
        dim_res.append(d)
        ac_res.append(a)
        
        exp_dim = np.repeat(d, roi_data.shape[1]).reshape(1,-1).astype("double")
        exp_ac = np.repeat(a, roi_data.shape[1]).reshape(1,-1).astype("double")
        
        temp_dim = masker.inverse_transform(exp_dim)
        temp_ac = masker.inverse_transform(exp_ac)
        
        if dim_vol == None:
            dim_vol = temp_dim
        else:
            dim_vol = math_img(f'img1 + img2', img1 = dim_vol, img2=temp_dim)
        
        if AC_vol == None:
            AC_vol = temp_ac
        else:
            AC_vol = math_img(f'img1 + img2', img1 = AC_vol, img2=temp_ac)
    # at the end, save this

    outfn = f'RestMovie/results/PARCEL_HarvardOxford/sub-{sub_id:02d}_{task}_tphate_optt_{ATLAS_NAME}.nii.gz'
    nib.save(dim_vol,outfn)
    outfn = f'RestMovie/results/PARCEL_HarvardOxford/sub-{sub_id:02d}_{task}_tphate_autocorr_{ATLAS_NAME}.nii.gz'
    nib.save(AC_vol,outfn)
    print(f'Done {sub_id} {task}')
    return dim_res, ac_res 

def run_subject_dest(sub_id, task): 
    ATLAS = datasets.fetch_atlas_destrieux_2009(lateralized=True)
    ATLAS_NAME="Destrieux"
    atlas_df = pd.DataFrame(ATLAS)
    atlas_image = nib.load(ATLAS.maps)
    dim_res, ac_res = [], []
    
    nii = utils.get_subject_data(sub_id, task, trim=True)
    print(f"Original shape: {nii.shape}")
    # apply whole-brain mask, then invert
    wb_mask = utils.get_mask(task)
    masker_wb = NiftiMasker(mask_img=wb_mask, standardize=True)
    masked_nii = masker_wb.fit_transform(nii)
    nii = masker_wb.inverse_transform(masked_nii)
    print(f"New shape: {nii.shape}")

    dim_vol = None
    AC_vol = None
    for roi_id in atlas_df.index[1:]:
        if roi_id == 42 or roi_id == 117:
            dim_res.append(np.nan) 
            ac_res.append(np.nan) 
            continue
        roi_mask_img = math_img(f"img == {roi_id}", img=atlas_image)
        masker = NiftiMasker(roi_mask_img, standardize=True)
        roi_data = masker.fit_transform(nii)
        tokens = atlas_df.iloc[roi_id]['labels'][1]
        roi_str = tokens#'_'.join(tokens)
        d,a = embed_tphate_roi(roi_data, sub_id, task, roi_str)
        
        dim_res.append(d)
        ac_res.append(a)
        
        exp_dim = np.repeat(d, roi_data.shape[1]).reshape(1,-1).astype("double")
        exp_ac = np.repeat(a, roi_data.shape[1]).reshape(1,-1).astype("double")
        
        temp_dim = masker.inverse_transform(exp_dim)
        temp_ac = masker.inverse_transform(exp_ac)
        
        if dim_vol == None:
            dim_vol = temp_dim
        else:
            dim_vol = math_img(f'img1 + img2', img1 = dim_vol, img2=temp_dim)
        
        if AC_vol == None:
            AC_vol = temp_ac
        else:
            AC_vol = math_img(f'img1 + img2', img1 = AC_vol, img2=temp_ac)
    # at the end, save this

    outfn = f'RestMovie/results/PARCEL_Destrieux/sub-{sub_id:02d}_{task}_tphate_optt_{ATLAS_NAME}.nii.gz'
    nib.save(dim_vol,outfn)
    outfn = f'RestMovie/results/PARCEL_Destrieux/sub-{sub_id:02d}_{task}_tphate_autocorr_{ATLAS_NAME}.nii.gz'
    nib.save(AC_vol,outfn)
    print(f'Done {sub_id} {task}')
    return dim_res, ac_res

def run_subject_shaefer(sub_id, task): 
    ATLAS = nilearn.datasets.fetch_atlas_schaefer_2018()
    ATLAS.labels = np.insert(ATLAS.labels, 0, 'Background')
    ATLAS_NAME = 'Shaefer'
    atlas_image = nib.load(ATLAS.maps)
    atlas_df = pd.DataFrame(ATLAS)
    dim_res, ac_res = [], []
    
    nii = utils.get_subject_data(sub_id, task, trim=True)
    print(f"Original shape: {nii.shape}")
    # apply whole-brain mask, then invert
    wb_mask = utils.get_mask(task)
    masker_wb = NiftiMasker(mask_img=wb_mask, standardize=True)
    masked_nii = masker_wb.fit_transform(nii)
    nii = masker_wb.inverse_transform(masked_nii)
    print(f"New shape: {nii.shape}")

    dim_vol = None
    AC_vol = None
    for roi_id in atlas_df.index[1:]:
        roi_mask_img = math_img(f"img == {roi_id}", img=atlas_image)
        masker = NiftiMasker(roi_mask_img, standardize=True)
        roi_data = masker.fit_transform(nii)
        tokens = atlas_df.iloc[roi_id]['labels']
        roi_str = tokens.decode("UTF-8")
        d,a = embed_tphate_roi(roi_data, sub_id, task, roi_str)
        
        dim_res.append(d)
        ac_res.append(a)
        
        exp_dim = np.repeat(d, roi_data.shape[1]).reshape(1,-1).astype("double")
        exp_ac = np.repeat(a, roi_data.shape[1]).reshape(1,-1).astype("double")
        
        temp_dim = masker.inverse_transform(exp_dim)
        temp_ac = masker.inverse_transform(exp_ac)
        
        if dim_vol == None:
            dim_vol = temp_dim
        else:
            dim_vol = math_img(f'img1 + img2', img1 = dim_vol, img2=temp_dim)
        
        if AC_vol == None:
            AC_vol = temp_ac
        else:
            AC_vol = math_img(f'img1 + img2', img1 = AC_vol, img2=temp_ac)
    # at the end, save this

    outfn = f'RestMovie/results/PARCEL_Shaefer/sub-{sub_id:02d}_{task}_tphate_optt_{ATLAS_NAME}.nii.gz'
    nib.save(dim_vol,outfn)
    outfn = f'RestMovie/results/PARCEL_Shaefer/sub-{sub_id:02d}_{task}_tphate_autocorr_{ATLAS_NAME}.nii.gz'
    nib.save(AC_vol,outfn)
    print(f'Done {sub_id} {task}')
    return dim_res, ac_res
        
        


if __name__ == "__main__":
    ATLAS_NAME = sys.argv[1]
    
    results_df = pd.DataFrame(columns=['subject','roi_name','roi_id','task','dimension','autocorr'])
    
    if ATLAS_NAME == 'HarvardOxford':
        func = run_subject_HarOxf
        ATLAS = nilearn.datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr25-2mm')
        atlas_df = pd.DataFrame(ATLAS)
        ROI_ids = atlas_df.index[1:].values
        labels = atlas_df.iloc[ROI_ids]['labels'].values
    elif ATLAS_NAME == "Shaefer":
        func = run_subject_shaefer
        ATLAS = nilearn.datasets.fetch_atlas_schaefer_2018()
        ATLAS.labels = np.insert(ATLAS.labels, 0, 'Background')
        atlas_df = pd.DataFrame(ATLAS)
        ROI_ids = atlas_df.index[1:].values
        labels = atlas_df.iloc[ROI_ids]['labels'].values.astype(str)
    else:
        func = run_subject_dest 
        ATLAS = datasets.fetch_atlas_destrieux_2009(lateralized=True)
        atlas_df = pd.DataFrame(ATLAS)
        ROI_ids = atlas_df.index[1:].values
        ROI_ids = [R  for R in ROI_ids if R != 42 or R != 117]
        labels = atlas_df.iloc[ROI_ids]['labels'].values
    print(f'Running atlas {ATLAS_NAME} with {len(labels)} labels')
    
    joblist = []
    parameters = []
    for task, subject_list in config.RM_SUBJECTS.items():
        for s in subject_list:
            joblist.append(delayed(func)(s, task))
            parameters.append([task,s])
        
    print(f"starting {len(joblist)} jobs")        
    with Parallel(n_jobs=16) as parallel:
        results = parallel(joblist)
    print(f"finished {len(joblist)} jobs")      
    results = np.array(results)
    print(f"results of shape: {results.shape}")
    print(f"parameters of shape: {np.shape(parameters)}")
    for i in range(len(results)):
        r = results[i]
        p = parameters[i]
        temp = pd.DataFrame({'subject':np.repeat(p[1], r.shape[1]), 
                             'roi_id':ROI_ids,
                             'roi_name':labels,
                             'task':np.repeat(p[0],r.shape[1]),
                             'dimension':r[0,:],
                             'autocorr':r[1,:]})
        results_df = pd.concat([results_df, temp])
    results_df.to_csv(f'./RestMovie/results/{ATLAS_NAME}_parcel_tphate_results.csv')
                