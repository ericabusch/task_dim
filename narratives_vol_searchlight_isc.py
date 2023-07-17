import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os, sys, glob
import nilearn 
import nibabel as nib
import config
import narratives_utils as utils
from nilearn import datasets
from scipy import stats
from nilearn import plotting
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker
from brainiak.searchlight.searchlight import Searchlight
import tphate
import scprep
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings("ignore")
# Load in MPI
from mpi4py import MPI

# Load and prepare data for one subject
def load_data(sub_id, task):
    
    # Load bold data and some header information so that we can save searchlight results as nifti later.
    nii = utils.get_subject_data(sub_id, task)
    # Load mask
    brain_mask = utils.get_mask()
    masker_wb = NiftiMasker(mask_img=brain_mask, standardize=True)
    masked_normed = masker_wb.fit_transform(nii)
    masked_nii = masker_wb.inverse_transform(masked_normed)
    
    bold_data = masked_nii.get_fdata()
    affine_mat = masked_nii.affine
    dimensions = masked_nii.header.get_zooms() 
    
    return bold_data, brain_mask.get_fdata(), affine_mat, dimensions

    
def isc_kernel(data, sl_mask, myrad, bcvar):
    num_voxels_in_sl = sl_mask.shape[0] * sl_mask.shape[1] * sl_mask.shape[2]
    test_data = np.nan_to_num(data[0].ravel()) # flatten into  timepointsxvoxels
    train_data = np.nan_to_num(data[1].ravel()) # flatten into timepointsxvoxels
    n_timepoints = test_data.shape[-1]
    # check for unique values 
    n1 = np.linalg.norm(train_data)
    n2 = np.linalg.norm(test_data)
    if n1 == 0 or n2 == 0:
        r = np.nan
    else:
        # flatten both of these and correlate
        r = np.corrcoef(train_data, test_data)[0,1]
    return r
    
        

if __name__ == "__main__":
    task = sys.argv[1].upper()
    sl_rad = int(sys.argv[2])
    held_out_idx = int(sys.argv[3])
    percent_active = float(sys.argv[4])
    
    comm = MPI.COMM_WORLD
    rank = comm.rank
    size = comm.size
    max_blk_edge = 5
    pool_size = 2
    if rank == 0:
        print(comm, rank, size)
        
    data_list,masks,affines,dimsizes,bcvar = [],[],[],[],[]
    
    SUBJECTS = config.NARRATIVES_SUBJECTS
    test_subject = SUBJECTS[held_out_idx]
    print(SUBJECTS, test_subject)
    train_subjects = [s for s in np.setdiff1d(SUBJECTS, test_subject)]
    output_name = f'./Narratives/results/sub-{test_subject:02d}_{task}_ISC_whole_brain_SL_rad{sl_rad}_{percent_active}p.nii.gz'

    if os.path.exists(output_name):
        if rank == 0: print(f"already ran! {output_name}")
        sys.exit(0)
    
    # load test data
    if rank == 0:
        test_data, wb_mask, affine_mat, dimsize = load_data(test_subject, task)
        data_list.append(test_data)
        masks.append(wb_mask)
        affines.append(affine_mat)
        dimsizes.append(dimsize)
        bcvar.append([])
    else:
        data_list.append(None)
        wb_mask = utils.get_mask().get_fdata()
    
    train_data = None
    if rank == 0:
        masks.append(wb_mask)
        affines.append(affine_mat)
        dimsizes.append(dimsize)
        bcvar.append([])
        # load in the data for each subject
        for i, train_sub in enumerate(train_subjects):
            d, _,_,_ = load_data(train_sub, task)
            if i == 0:
                train_data = d
            else:
                train_data = np.add(train_data, d)
        train_data /= len(train_subjects)
        print(f'on rank zero, train_data shape {train_data.shape}, mean = {np.nanmean(train_data)}')
    data_list.append(train_data)
    mask = utils.get_mask()
    wb_mask = mask.get_fdata()
    
    # set up searchlight
    sl = Searchlight(sl_rad=sl_rad, max_blk_edge=max_blk_edge, min_active_voxels_proportion=percent_active)
    if rank == 0:
        print(f'starting searchlight with {np.sum(wb_mask)} voxels')
    sl.distribute(data_list, wb_mask)
    sl.broadcast(bcvar)
    
    # Run the searchlight analysis
    print(f"Begin Searchlight in rank {rank}")
    sl_result = sl.run_searchlight(isc_kernel, pool_size=pool_size)
    print(f"End Searchlight in rank {rank}")
    coords = np.where(wb_mask==1)
    cmap='magma'
    if rank == 0: 
        result_vec = sl_result[wb_mask==1]
        print(f'result vec of shape: {result_vec.shape}')
        result_vol = np.zeros((wb_mask.shape[0], wb_mask.shape[1], wb_mask.shape[2]))
        aff = affines[0]
        dimsize = dimsizes[0]
        result_vol[coords] = result_vec
        result_vol = np.nan_to_num(result_vol.astype('double'))
        output_name = f'./Narratives/results/sub-{test_subject:02d}_{task}_ISC_whole_brain_SL_rad{sl_rad}_{percent_active}p.nii.gz'
        sl_nii = nib.Nifti1Image(result_vol, aff)
        # mask non-brain
        masker_wb_plot = NiftiMasker(mask_img=mask, standardize=False)
        masked_sl_res = masker_wb_plot.fit_transform(sl_nii)
        masked_sl_res = masker_wb_plot.inverse_transform(masked_sl_res).get_fdata()[:,:,:,0]
        sl_nii = nib.Nifti1Image(masked_sl_res, affine_mat)
        sl_nii.header.set_zooms(dimsize[:3])
        nib.save(sl_nii, output_name) 
        print(f"Saved result to {output_name}; plotting")

        title = f'{task} sub {test_subject} ISC sl radius={sl_rad}'
        plotting.plot_stat_map(output_name,output_file=output_name.replace('.nii.gz', '_statmap.png').replace('results','plots'), colorbar=True, cmap=cmap, threshold=0,  title=title)
    else:
        print(f"Exiting rank {rank}")