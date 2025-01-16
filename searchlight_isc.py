# volume searchlight ISC script
import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import os, sys, glob
import nilearn 
import nibabel as nib
import config
from nilearn import datasets
from scipy import stats
from nilearn import plotting
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker
from brainiak.searchlight.searchlight import Searchlight
import tphate
import scprep
from nibabel.nifti1 import Nifti1Image

from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings("ignore")
# Load in MPI
from mpi4py import MPI

def load_data(sub_id, task):
    
    # Load bold data and some header information so that we can save searchlight results as nifti later.
    nii = utils.get_subject_data(sub_id, task, trim=True)
    # Load mask
    brain_mask = utils.get_intersect_mask(subject_filter=p.subject_filter)
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
    # check for unique values 
    n1 = np.linalg.norm(train_data)
    n2 = np.linalg.norm(test_data)
    if n1 == 0 or n2 == 0: r = np.nan 
    else: r = np.corrcoef(train_data, test_data)[0,1]  # flatten both of these and correlate
    return r

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dataset',type=str)
    parser.add_argument('-t','--task', type=str)
    parser.add_argument('-i', '--held_out_idx', type=int)
    parser.add_argument('-r','--sl_rad', type=int, default=5)
    parser.add_argument('-s','--subject_filter', type=str, default="0")
    parser.add_argument('-v','--verbose', type=int, default=1)
    parser.add_argument('-o', '--overwrite', type=int, default=1)
    parser.add_argument('-p', '--plot', type=int, default=0)
    p = parser.parse_args()

    # set some stuff
    comm = MPI.COMM_WORLD
    rank = comm.rank
    size = comm.size
    max_blk_edge = 5
    pool_size = 2
    percent_active=.10

    # import the right utils file
    if p.dataset.lower() == 'narratives': import narratives_utils as utils
    elif p.dataset.lower() == 'rest_movie': import RM_utils as utils
    elif p.dataset.lower() == 'camcan': import camcan_utils as utils
    elif p.dataset.lower() == 'infant_rest_movie': import RM_infant_utils as utils
    elif p.dataset.lower() == 'cneuromod': import CNM_utils as utils
    else: print(f'{p.dataset} not valid');  sys.exit(1)
    if p.verbose and rank == 0: print(f'loaded {p.dataset}_utils')

    # load subjects
    ALL_SUBJECTS = utils.get_intersecting_subjects(subject_filter=p.subject_filter)
    # make sure the desired subject exists
    if len(ALL_SUBJECTS) < p.held_out_idx:
        print(f'test subject idx {p.held_out_idx} not in list of len {len(ALL_SUBJECTS)}')
        sys.exit(2)
    test_subject = ALL_SUBJECTS[p.held_out_idx]
    train_subjects = [s for s in np.setdiff1d(ALL_SUBJECTS, test_subject)]
    outdir = os.path.join(utils.get_scratch_dir(), 'ISC', 'LOSO', 'results')
    plot_outdir = os.path.join(utils.get_scratch_dir().replace('results', 'plots'), 'ISC', 'LOSO')
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(plot_outdir, exist_ok=True)
    
    output_name = os.path.join(outdir, f'{test_subject}_filter_{p.subject_filter}_{p.task}_ISC_whole_brain_SL_rad{p.sl_rad}.nii.gz')

    if not p.overwrite and os.path.exists(output_name):
        if rank == 0: print(f'already ran {output_name}')
        sys.exit(0)
    if p.verbose and rank == 0: print(f'running {output_name}')
    
    data_list,masks,affines,dimsizes,bcvar = [],[],[],[],[]

    if rank == 0:
        test_data, wb_mask, affine_mat, dimsize = load_data(test_subject, p.task)
        data_list.append(test_data)
        masks.append(wb_mask)
        affines.append(affine_mat)
        dimsizes.append(dimsize)
        bcvar.append([])
    else:
        data_list.append(None)
        wb_mask = utils.get_intersect_mask(subject_filter=p.subject_filter).get_fdata()

    train_data = None
    if rank == 0:
        masks.append(wb_mask)
        affines.append(affine_mat)
        dimsizes.append(dimsize)
        bcvar.append([])
        # load in the data for each subject
        for i, train_sub in enumerate(train_subjects):
            d, _, _, _ = load_data(train_sub, p.task)
            if i == 0: train_data = d
            else: train_data = np.add(train_data, d)
        train_data /= len(train_subjects)
    data_list.append(train_data)
    
    brain_mask = utils.get_intersect_mask(subject_filter=p.subject_filter)
    if rank == 0 and p.verbose: print(f'{np.sum(wb_mask)} voxels in mask')
    # set up searchlight
    sl = Searchlight(sl_rad=p.sl_rad, max_blk_edge=max_blk_edge, min_active_voxels_proportion=percent_active)

    if rank == 0 and p.verbose: print(f'starting searchlight with {np.sum(wb_mask)} voxels')
    sl.distribute(data_list, wb_mask)
    sl.broadcast(bcvar)

    # Run the searchlight analysis
    if p.verbose: print(f"Begin Searchlight in rank {rank}")
    sl_result = sl.run_searchlight(isc_kernel, pool_size=pool_size)
    if p.verbose: print(f"End Searchlight in rank {rank}")
    coords = np.where(wb_mask==1)
    cmap = 'magma'

    if rank != 0: print(f'exiting rank {rank}'); sys.exit(0)

    # save and plot results on rank 1
    result_vec = sl_result[wb_mask==1]
    new_output = output_name.replace('.nii.gz','vectorized.npy')
    np.save(new_output, result_vec)
    if p.verbose: print(f'result vec of shape: {result_vec.shape}; saving to {new_output}')
    result_vol = np.zeros((wb_mask.shape[0], wb_mask.shape[1], wb_mask.shape[2]))
    aff = affines[0]
    dimsize = dimsizes[0]
    result_vol[coords] = result_vec
    result_vol = np.nan_to_num(result_vol.astype('double'))
    sl_nii = nib.Nifti1Image(result_vol, aff)
    # mask non-brain
    masker_wb_plot = NiftiMasker(mask_img=brain_mask, standardize=False)
    masked_sl_res = masker_wb_plot.fit_transform(sl_nii)
    masked_sl_res = masker_wb_plot.inverse_transform(masked_sl_res).get_fdata()[:,:,:,0]
    sl_nii = nib.Nifti1Image(masked_sl_res, affine_mat)
    sl_nii.header.set_zooms(dimsize[:3])
    nib.save(sl_nii, output_name) 
    
    if p.plot: 
        if p.verbose: print(f"Saved result to {output_name}; plotting")
        title = f'{p.dataset} {p.task} sub {test_subject} ISC sl radius={p.sl_rad}'
        plotting.plot_stat_map(output_name,output_file=output_name.replace('.nii.gz', '_statmap.png').replace('results','plots'), colorbar=True, cmap=cmap, threshold=0,  title=title)











