# loads in result files for all subjects
# creates a numpy file with vectorized results for all subjects
# and an average brain volume
import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import os, sys, glob
import nilearn 
import nibabel as nib
from scipy import stats
from nilearn import plotting
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker
from nilearn.image import concat_imgs

def load_mask_sl_data_file(mask_coords, subject, task, metric, file_idx=0, filter_by_age=0, slrad=5):
    try:
        nii = utils.get_metric_SL_nii_subject(subject, task, metric, file_idx=file_idx, filter_by_age=filter_by_age, slrad=slrad)
    except:
        nii = None
        print(f'couldnt find SL ', subject, task, metric)
    if nii == None:
        z = np.zeros(len(mask_coords[0]))
        z[:] = np.nan
        return z
    x = nii.get_fdata()
    vec = x[mask_coords[0][:], mask_coords[1][:], mask_coords[2][:]]
    return vec

def load_atlas(atlas_name='Schaefer'):
    if atlas_name == 'Schaefer':
        ATLAS = nilearn.datasets.fetch_atlas_schaefer_2018(resolution_mm=2, yeo_networks=17)
        ATLAS.labels = np.insert(ATLAS.labels, 0, 'Background')
        
    else:
        print(f'{atlas_name} not implemented')
    return ATLAS

def load_mask_parcel_data_file(subject, task, metric, file_idx=0, filter_by_age=0):
    atlas=load_atlas()
    masker = NiftiLabelsMasker(atlas.maps, labels=atlas.labels, standardize=False)
    nii = utils.get_metric_atlas_nii_subject(subject, task, metric, file_idx=file_idx, filter_by_age=filter_by_age)   
    masked_data = masker.fit_transform(nii)
    return np.squeeze(masked_data),masker

def vec2vol(values, mask_nii):
    mask_coords = np.where(mask_nii.get_fdata() == 1)
    X = np.zeros_like(mask_nii.get_fdata())
    X[mask_coords] = values
    vol = nib.Nifti1Image(X, affine=mask_nii.affine)
    vol.header.set_zooms(mask_nii.header.get_zooms())
    return vol

def load_parcel_data_to_aggregate(subject_list, task, metric, filter_by_age=0, with_repeats=False):
    parcelwise_data, maskers = [], []
    for sub_id in subject_list:
        if with_repeats and utils.has_repeat_files(sub_id, task) > 0:
            for i in range(utils.has_repeat_files(sub_id, task)):
                n,m = load_mask_parcel_data_file(sub_id, task, metric, file_idx=i, filter_by_age=filter_by_age)
                parcelwise_data.append(n)
                maskers.append(m)
        else:
            try:
                n,m = load_mask_parcel_data_file(sub_id, task, metric, file_idx=0, filter_by_age=filter_by_age)
                parcelwise_data.append(n)
                maskers.append(m)
            except:
                print(f'could not load {sub_id} {metric}')
            
    return parcelwise_data, maskers

def load_SL_data_to_aggregate(subject_list, mask_coords, task, metric, filter_by_age=0, with_repeats=False, slrad=5):
    data = []
    for sub_id in subject_list:
        if with_repeats and utils.has_repeat_files(sub_id, task) > 0:
            for i in range(utils.has_repeat_files(sub_id, task)):
                n = load_mask_sl_data_file(mask_coords, sub_id, task, metric, file_idx=i, filter_by_age=filter_by_age, slrad=slrad)
                data.append(n)
        else:
            n = load_mask_sl_data_file(mask_coords, sub_id, task, metric, file_idx=0, filter_by_age=filter_by_age, slrad=slrad)
            data.append(n)
    return data

def expand_to_atlas_volume(vector, fitted_masker):
    return fitted_masker.inverse_transform(vector)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dataset',type=str)
    parser.add_argument('-t','--task', type=str)
    parser.add_argument('-m', '--metric', type=str)
    parser.add_argument('-a','--use_atlas',type=int,default=1)
    parser.add_argument('-r','--sl_rad', type=int, default=5)
    parser.add_argument('-v','--verbose', type=int, default=1)
    parser.add_argument('-o', '--overwrite', type=int, default=1)
    parser.add_argument('-p', '--plot', type=int, default=1)
    parser.add_argument('-s','--subject_filter',type=str, default="0")
    p = parser.parse_args()
    
    if p.task.lower() == 'moviedm':
        print(f'exiting moviedm')
        sys.exit()
    # import the right utils file
    if p.dataset.lower() == 'narratives': import narratives_utils as utils; import narratives_config as config
    elif p.dataset.lower() == 'adult_restmovie': import adult_restmovie_utils as utils; import adult_restmovie_config as config
    elif p.dataset.lower() == 'camcan': import camcan_utils as utils; import camcan_config as config
    elif p.dataset.lower() == 'infant_restmovie': import infant_restmovie_utils as utils; import infant_restmovie_config as config; p.subject_filter=p.task
    elif p.dataset.lower() == 'cneuromod': import cneuromod_utils as utils; import cneuromod_config as config
    elif p.dataset.lower() == 'partlycloudy': import partlycloudy_utils as utils; import partlycloudy_config as config
    elif p.dataset.lower() == 'hbn': import hbn_utils as utils; import hbn_config as config
    else: print(f'{p.dataset} not valid'); sys.exit(1)
    if p.verbose: print(f'loaded {p.dataset}_utils')
    VERBOSE=config.VERBOSE
    
    if p.dataset.lower() == 'hbn':
        brain_mask = utils.get_intersect_mask(task=p.task, subject_filter=p.subject_filter)
    else:
        brain_mask = utils.get_intersect_mask(subject_filter=p.subject_filter)
    mask_coords = np.where(brain_mask.get_fdata() == 1)
    all_subjects = utils.get_intersecting_subjects(subject_filter=p.subject_filter)

    if p.verbose: print(f'Loading {p.dataset} {p.task} filter={p.subject_filter} {p.metric}, atlas={p.use_atlas}; n_voxels={np.shape(mask_coords)}, n_subjects={len(all_subjects)}')

    if not p.use_atlas:
        vectors = load_SL_data_to_aggregate(all_subjects, mask_coords, p.task, p.metric, filter_by_age=p.subject_filter, with_repeats=p.metric != "ISC", slrad=p.sl_rad)
    else:
        vectors, maskers = load_parcel_data_to_aggregate(all_subjects, p.task, p.metric, filter_by_age=p.subject_filter, with_repeats=p.metric != "ISC")


    subject_vectors=np.array(vectors)
    if p.verbose: print(f'Loaded {len(subject_vectors)} files; final shape: {subject_vectors.shape}; unique subjects: {len(all_subjects)}')
    os.makedirs(f'{utils.get_results_dir()}/results_volumes', exist_ok=True)
    os.makedirs(f'{utils.get_results_dir()}/all_subject_arrays', exist_ok=True)

    # save results in vector form
    outdir=f'{utils.get_results_dir()}/all_subject_arrays'

    outfn = f'{outdir}/{p.task.lower()}_{p.metric}_all_subject_results.npy'
    if p.dataset.lower() in ['partlycloudy', 'hbn']: 
        outfn=outfn.replace(p.task.lower(), f'{p.task.lower()}_subject_filter_{p.subject_filter}')
    if p.use_atlas:
        outfn=outfn.replace('.npy','_atlas.npy')
    np.save(outfn, vectors)

    # save the average
    outfn = f'{outdir}/{p.task.lower()}_{p.metric}_average_results.npy'
    if p.dataset.lower() in ['partlycloudy', 'hbn']: 
        outfn=outfn.replace(p.task.lower(), f'{p.task.lower()}_subject_filter_{p.subject_filter}')
    if p.use_atlas:
        outfn=outfn.replace('.npy','_atlas.npy')
    np.save(outfn, np.nanmean(subject_vectors, axis=0))

    # if SL results, can just stack; if parcel, need to unmask
    # stack all the results
    outdir = f'{utils.get_results_dir()}/results_volumes'
    if not p.use_atlas:
        cc_img = concat_imgs([vec2vol(subject_vectors[i], brain_mask) for i in range(len(subject_vectors))])
        outfn = f'{outdir}/{p.task.lower()}_{p.metric}_all_subjects_results.nii.gz'
        if p.dataset.lower() in ['partlycloudy', 'hbn']: 
            outfn=outfn.replace(p.task.lower(), f'{p.task.lower()}_subject_filter_{p.subject_filter}')
        nib.save(cc_img, outfn)

        # average
        avg = np.nanmean(subject_vectors, axis=0)
        avg_nii = vec2vol(avg, brain_mask)
        outfn = f'{outdir}/{p.task.lower()}_{p.metric}_average_results.nii.gz'
        if p.dataset.lower() in ['partlycloudy', 'hbn']: 
            outfn=outfn.replace(p.task.lower(), f'{p.task.lower()}_subject_filter_{p.subject_filter}')

        nib.save(avg_nii, outfn)
    else:
        cc_img = concat_imgs([expand_to_atlas_volume(subject_vectors[i], maskers[i]) for i in range(len(subject_vectors))])
        outfn = f'{outdir}/{p.task.lower()}_{p.metric}_all_subjects_results_atlas.nii.gz'
        if p.dataset.lower() in ['partlycloudy', 'hbn']: 
            outfn=outfn.replace(p.task.lower(), f'{p.task.lower()}_subject_filter_{p.subject_filter}')
        nib.save(cc_img, outfn)
        # average
        avg = np.nanmean(subject_vectors, axis=0)
        avg_nii = expand_to_atlas_volume(avg, maskers[0])
        outfn = f'{outdir}/{p.task.lower()}_{p.metric}_average_results_atlas.nii.gz'
        if p.dataset.lower() in ['partlycloudy', 'hbn']: 
            outfn=outfn.replace(p.task.lower(), f'{p.task.lower()}_subject_filter_{p.subject_filter}')

        nib.save(avg_nii, outfn)
    
    if p.verbose: print(f'saved res of shape {avg_nii.shape} to {outfn}')
    
    if p.plot: 
        if p.verbose: print(f"plotting")
        title = f'{p.dataset} {p.task} {p.metric} avg'
        outfn = outfn.replace('.nii.gz','.png')
        cmap = utils.get_brain_cmap()
        plotting.plot_img_on_surf(avg_nii, 
                                  views=['lateral','medial'], 
                                  inflate=True, 
                                  bg_on_data=False, 
                                          alpha=0.8,
                                  output_file=outfn,
                                  cmap=cmap,
                                  darkness=0.8, 
                                  threshold=0, title=f'{title}'
                                 )
    
    


