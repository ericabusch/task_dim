# volume tphate optimal dimensionality script
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
import warnings
warnings.filterwarnings("ignore")
# Load in MPI
from mpi4py import MPI

def load_data(sub_id, task):
    
    # Load bold data and some header information so that we can save searchlight results as nifti later.
    nii = utils.get_subject_data(sub_id, task)
    # Load mask
    brain_mask = utils.get_intersect_mask(subject_filter=p.subject_filter)
    masker_wb = NiftiMasker(mask_img=brain_mask, standardize=True)
    masked_normed = masker_wb.fit_transform(nii)
    masked_nii = masker_wb.inverse_transform(masked_normed)
    
    bold_data = masked_nii.get_fdata()
    affine_mat = masked_nii.affine
    dimensions = masked_nii.header.get_zooms() 
    
    return bold_data, brain_mask.get_fdata(), affine_mat, dimensions


def tphate_kernel(data, sl_mask, myrad, bcvar):
    data=data[0]
    
    # make sure there's a constant # voxels
    num_voxels_in_sl = sl_mask.shape[0] * sl_mask.shape[1] * sl_mask.shape[2]

    n_timepoints = data.shape[-1]
    data_arr = np.nan_to_num(data.reshape(num_voxels_in_sl, n_timepoints).T) # data should already be normed
    
    # check for unique input values 
    if np.linalg.norm(data_arr) == 0: return np.nan, np.nan
    
    op = tphate.TPHATE(verbose=0, n_jobs=-1, smooth_window=2)
    eb = op.fit_transform(data_arr)
    return op.optimal_t, op.dropoff

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dataset',type=str)
    parser.add_argument('-t','--task', type=str)
    parser.add_argument('-i', '--subject_idx', type=int)
    parser.add_argument('-r','--sl_rad', type=int, default=5)
    parser.add_argument('-s','--subject_filter', type=int, default=0)
    parser.add_argument('-v','--verbose', type=int, default=1)
    parser.add_argument('-o', '--overwrite', type=int, default=0)
    parser.add_argument('-p', '--plot', type=int, default=0)
    p = parser.parse_args()

    # set some stuff
    comm = MPI.COMM_WORLD
    rank = comm.rank
    size = comm.size
    max_blk_edge = 5
    pool_size = 2

    # import the right utils file
    if p.dataset.lower() == 'narratives': import narratives_utils as utils
    elif p.dataset.lower() == 'rest_movie': import RM_utils as utils
    elif p.dataset.lower() == 'camcan': import camcan_utils as utils
    else: print(f'{p.dataset} not valid');  sys.exit(1)
    if p.verbose and rank == 0: print(f'loaded {p.dataset}_utils')

     # load target subject
    ALL_SUBJECTS = utils.get_intersecting_subjects(subject_filter=p.subject_filter)
    # make sure the desired subject exists
    if len(ALL_SUBJECTS) < p.subject_idx:
        print(f'test subject idx {p.subject_idx} not in list of len {len(ALL_SUBJECTS)}')
        sys.exit(2)
    this_subject = ALL_SUBJECTS[p.subject_idx]
    results_outdir = os.path.join(utils.get_results_dir(), 'TPHATE_optt', 'LOSO')
    plot_outdir = os.path.join(utils.get_results_dir().replace('results', 'plots'), 'TPHATE_optt', 'LOSO')
    os.makedirs(results_outdir, exist_ok=True)
    os.makedirs(plot_outdir, exist_ok=True)
    output_name = os.path.join(results_outdir, f'{this_subject}_{p.task}_tphate')
    if not p.overwrite:
        fns = glob.glob(output_name+'*')
        if len(fns) != 0:
            if rank == 0: print(f'already ran {output_name}')
            sys.exit(0)
    if p.verbose and rank == 0: print(f'running {output_name}')

    data,masks,affines,dimsizes,bcvar = [],[],[],[],[]
    if rank == 0:
        data_i, wb_mask, affine_mat, dimsize = load_data(this_subject, p.task)
        data.append(data_i)
        masks.append(wb_mask)
        affines.append(affine_mat)
        dimsizes.append(dimsize)
        bcvar.append([])
        if p.verbose: print(f"Number of WB voxels: {np.sum(wb_mask == 1)}\nRunning subject {this_subject} task {p.task} slrad {p.sl_rad}")
    else:
        data.append(None)
        wb_mask = utils.get_intersect_mask(subject_filter=p.subject_filter)
        wb_mask = wb_mask.get_fdata()
        
    # set up searchlight
    sl = Searchlight(sl_rad=p.sl_rad, max_blk_edge=max_blk_edge)
    sl.distribute(data, wb_mask)
    sl.broadcast(bcvar)
    
    brain_mask = utils.get_intersect_mask(subject_filter=p.subject_filter)

    if p.verbose: print(f"Begin Searchlight in rank {rank}")
    all_sl_result = sl.run_searchlight(tphate_kernel, pool_size=pool_size)
    if p.verbose: print(f"End Searchlight in rank {rank}")
    coords = np.where(wb_mask==1)

    if rank != 0: print(f'exiting rank {rank}'); sys.exit(0)

    if rank == 0: 
        if p.verbose: print(f'results of shape: {np.shape(all_sl_result)}')
        result_vec = all_sl_result[coords]
        result_vec = [2*[0] if not n else n for n in result_vec] # replace all None

        for i, nm, cmap in zip([0,1], ['optt', 'autocorr'], ['magma', 'viridis']):
            result_vol = np.zeros_like(wb_mask)
            res = [r[i] for r in result_vec]
            result_vol[coords] = res
            result_vol = result_vol.astype('double')
            result_vol = np.nan_to_num(result_vol)
            minn,maxx=np.min(result_vol), np.max(result_vol)

            out_fn = f'{output_name}_{nm}_whole_brain_SL_rad{p.sl_rad}.nii.gz'
            sl_nii = nib.Nifti1Image(result_vol, affine_mat)
            # mask non-brain
            masker_wb_plot = NiftiMasker(mask_img=brain_mask, standardize=False)
            masked_sl_res = masker_wb_plot.fit_transform(sl_nii)
            masked_sl_res = masker_wb_plot.inverse_transform(masked_sl_res).get_fdata()[:,:,:,0]
            if p.verbose: print(f'shape after inverse: {masked_sl_res.shape}')
            sl_nii = nib.Nifti1Image(masked_sl_res, affine_mat)

            sl_nii.header.set_zooms(dimsize[:3])
            nib.save(sl_nii, out_fn) 
            if p.plot: 
                if p.verbose: print(f"Saved result to {out_fn}; plotting")
                title = f'{p.dataset} {p.task} {this_subject} tphate {nm} sl radius={p.sl_rad}'
                plotting.plot_stat_map(out_fn, output_file=output_name.replace('.nii.gz', '_statmap.png').replace('results','plots'), colorbar=True, threshold=0, cmap=cmap, title=title)




