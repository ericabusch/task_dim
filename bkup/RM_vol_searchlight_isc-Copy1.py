import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os, sys, glob
import nilearn 
import nibabel as nib
import config
import RM_utils as utils
from nilearn import datasets
from scipy import stats
from nilearn import plotting
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker
from brainiak.searchlight.searchlight import Searchlight
import TPHATE.tphate 
from TPHATE.tphate import tphate
import scprep
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings("ignore")
# Load in MPI
from mpi4py import MPI

# Load and prepare data for one subject
def load_data(sub_id, task):
    
    # Load bold data and some header information so that we can save searchlight results as nifti later.
    nii = utils.get_subject_data(sub_id, task, trim=True)
    # Load mask
    brain_mask = utils.get_mask(task)
    masker_wb = NiftiMasker(mask_img=brain_mask, standardize=True)
    masked_normed = masker_wb.fit_transform(nii)
    masked_nii = masker_wb.inverse_transform(masked_normed)
    
    bold_data = masked_nii.get_fdata()
    affine_mat = masked_nii.affine
    dimensions = masked_nii.header.get_zooms() 
    
    return bold_data, brain_mask.get_fdata(), affine_mat, dimensions

    
def isc_kernel(data, sl_mask, myrad, bcvar):
    num_voxels_in_sl = sl_mask.shape[0] * sl_mask.shape[1] * sl_mask.shape[2]
    n_timepoints = data[0].shape[-1]
    idx = np.arange(len(data))
    ISC_results = [] # will store for each fold
    for test_idx in idx: # hold out 1 subject
        train_idx = np.setdiff1d(idx, test_idx)
        # get all training data as a 3D array - train_subs x timepoints x voxels
        train_data = np.array([data[i].reshape(num_voxels_in_sl, n_timepoints).T for i in train_idx])
        # average across subjects
        train_data = np.nan_to_num(np.nanmean(train_data, axis=0))
        # test subject data
        test_data = np.nan_to_num(np.array(data[test_idx].reshape(num_voxels_in_sl, n_timepoints).T))
        
        # check for unique values 
        n1 = np.linalg.norm(train_data)
        n2 = np.linalg.norm(test_data)
        if n1 == 0 or n2 == 0:
            r = np.nan
        else:
            # flatten both of these and correlate
            r = np.corrcoef(train_data.ravel(), test_data.ravel())[0,1]
        ISC_results.append(r)
    return ISC_results
        

if __name__ == "__main__":
    task = sys.argv[1]
    sl_rad = int(sys.argv[2])
    
    comm = MPI.COMM_WORLD
    rank = comm.rank
    size = comm.size
    max_blk_edge = 5
    pool_size = 1
    
    data,bcvar,masks,affines,dimsizes = [],[],[],[],[]
    
    SUBJECTS = config.RM_SUBJECTS[task]
    
    for sub_id in SUBJECTS:
        if rank == 0:
            data_i, wb_mask, affine_mat, dimsize = load_data(sub_id, task)
            data.append(data_i)
            masks.append(wb_mask)
            affines.append(affine_mat)
            dimsizes.append(dimsize)
            bcvar.append([])
        else:
            data.append(None)
            wb_mask = utils.get_mask(task)
            wb_mask = wb_mask.get_fdata()
        
    
    # set up searchlight
    sl = Searchlight(sl_rad=sl_rad,max_blk_edge=max_blk_edge)
    if rank == 0:
        print(f'starting searchlight with {np.sum(wb_mask)} voxels')
    sl.distribute(data, wb_mask)
    sl.broadcast(bcvar)
    
    mask = utils.get_mask(task)
    
    # Run the searchlight analysis
    print(f"Begin Searchlight in rank {rank}")
    all_sl_result = sl.run_searchlight(isc_kernel, pool_size=pool_size)
    print(f"End Searchlight in rank {rank}")
    coords = np.where(wb_mask==1)
    cmap='magma'
    if rank == 0: 
        result_vec = all_sl_result[wb_mask==1]
        result_vec = [len(SUBJECTS)*[0] if not n else n for n in result_vec] # replace all None
        avg_vol = np.zeros((len(SUBJECTS), wb_mask.shape[0], wb_mask.shape[1], wb_mask.shape[2]))
        for i, subject in enumerate(SUBJECTS):
            aff = affines[i]
            dimsize=dimsizes[i]
            
            result_vol = np.zeros_like(wb_mask)
            res = [r[i] for r in result_vec]
            result_vol[coords] = res
            result_vol = result_vol.astype('double')
            result_vol = np.nan_to_num(result_vol)
            minn,maxx=np.min(result_vol), np.max(result_vol)
            avg_vol[i] = result_vol
            output_name = f'./RestMovie/results/sub-{subject:02d}_{task}_ISC_whole_brain_SL_rad{sl_rad}.nii.gz'
            sl_nii = nib.Nifti1Image(result_vol, aff)

            # mask non-brain
            masker_wb_plot = NiftiMasker(mask_img=mask, standardize=False)
            masked_sl_res = masker_wb_plot.fit_transform(sl_nii)
            masked_sl_res = masker_wb_plot.inverse_transform(masked_sl_res).get_fdata()[:,:,:,0]
            sl_nii = nib.Nifti1Image(masked_sl_res, affine_mat)

            sl_nii.header.set_zooms(dimsize[:3])
            nib.save(sl_nii, output_name) 
            print(f"Saved result to {output_name}; plotting")
            
            title = f'{task} sub {sub_id} ISC sl radius={sl_rad}'
            plotting.plot_glass_brain(output_name,output_file=output_name.replace('.nii.gz', '_glass.png').replace('results','plots'), colorbar=True, cmap=cmap, vmin=minn, vmax=maxx, title=title)
            plotting.plot_stat_map(output_name,output_file=output_name.replace('.nii.gz', '_statmap.png').replace('results','plots'), colorbar=True, cmap=cmap, threshold=minn, vmax=maxx, title=title)
            
        # now save the average volume
        output_name = f'./RestMovie/results/average_{task}_ISC_whole_brain_SL_rad{sl_rad}.nii.gz'
        avg_vol = np.nanmean(avg_vol, axis=0)
        sl_nii = nib.Nifti1Image(avg_vol, aff)
        # mask non-brain
        masker_wb_plot = NiftiMasker(mask_img=mask, standardize=False)
        masked_sl_res = masker_wb_plot.fit_transform(sl_nii)
        masked_sl_res = masker_wb_plot.inverse_transform(masked_sl_res).get_fdata()[:,:,:,0]
        sl_nii = nib.Nifti1Image(masked_sl_res, affine_mat)
        sl_nii.header.set_zooms(dimsize[:3])
        nib.save(sl_nii, output_name) 
        print(f"Saved result to {output_name}; plotting")
        title = f'{task} average ISC sl radius={sl_rad}'
        plotting.plot_glass_brain(output_name,output_file=output_name.replace('.nii.gz', '_glass.png').replace('results','plots'), colorbar=True, cmap=cmap, vmin=minn, vmax=maxx, title=title)
        plotting.plot_stat_map(output_name,output_file=output_name.replace('.nii.gz', '_statmap.png').replace('results','plots'), colorbar=True, cmap=cmap, threshold=minn, vmax=maxx, title=title)    