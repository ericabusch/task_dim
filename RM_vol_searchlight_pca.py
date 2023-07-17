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
    nii = utils.get_subject_data(sub_id, task)
    # Load mask
    brain_mask = utils.get_mask(task)
    masker_wb = NiftiMasker(mask_img=brain_mask, standardize=True)
    masked_normed = masker_wb.fit_transform(nii)
    masked_nii = masker_wb.inverse_transform(masked_normed)
    
    bold_data = masked_nii.get_fdata()
    affine_mat = masked_nii.affine
    dimensions = masked_nii.header.get_zooms() 
    
    return bold_data, brain_mask.get_fdata(), affine_mat, dimensions

    
def pca_kernel(data, sl_mask, myrad, bcvar):
    data=data[0]
    num_voxels_in_sl = sl_mask.shape[0] * sl_mask.shape[1] * sl_mask.shape[2]
    n_timepoints = data.shape[-1]
    data_arr = np.nan_to_num(data.reshape(num_voxels_in_sl, n_timepoints).T) # data should already be normed
    
    # check for unique input values 
    if np.linalg.norm(data_arr) == 0:
        return np.nan, np.nan
    
    pca = PCA()
    pca.fit(data_arr)
    var_exp = np.cumsum(pca.explained_variance_ratio_)
    dim = np.where(var_exp >= CUTOFF)[0][0]
    return dim
    
if __name__ == "__main__":
    sub_id = int(sys.argv[1])
    task = sys.argv[2]
    cutoff_perc = int(sys.argv[3])
    sl_rad = 5
    CUTOFF= cutoff_perc/100.
    print(sub_id, task, sl_rad, CUTOFF, 'pca')
    
    comm = MPI.COMM_WORLD
    rank = comm.rank
    size = comm.size
    max_blk_edge = 5
    pool_size = 1
    
    nm=f'PCA_{cutoff_perc}p_var'
    results_path = f'./RestMovie/results/sub-{sub_id:02d}_{task}'
    output_name = f'{results_path}_{nm}_whole_brain_SL_rad{sl_rad}.nii.gz'
    if os.path.exists(output_name):
        print(f"Finished {output_name}; ending")
        sys.exit()
    
    data,bcvar,masks,affines,dimsizes = [],[],[],[],[]

    if rank == 0:
        data_i, wb_mask, affine_mat, dimsize = load_data(sub_id, task)
        data.append(data_i)
        masks.append(wb_mask)
        affines.append(affine_mat)
        dimsizes.append(dimsize)
        bcvar.append([])
        print(f"Number of WB voxels: {np.sum(wb_mask == 1)}")
        print(f"Running subject {sub_id} task {task} slrad {sl_rad}")
    else:
        data.append(None)
        wb_mask = utils.get_mask(task)
        wb_mask = wb_mask.get_fdata()
        
    
    
    # set up searchlight
    sl = Searchlight(sl_rad=sl_rad,max_blk_edge=max_blk_edge)
    sl.distribute(data, wb_mask)
    sl.broadcast(bcvar)
    
    brain_mask = utils.get_mask(task)
    
    # Run the searchlight analysis
    print(f"Begin Searchlight in rank {rank}")
    all_sl_result = sl.run_searchlight(pca_kernel, pool_size=pool_size)
    print(f"End Searchlight in rank {rank}")
    coords = np.where(wb_mask==1)
    results_path = f'./RestMovie/results/sub-{sub_id:02d}_{task}'
    if rank == 0: 
        result_vec = all_sl_result[coords]
        result_vec = [0 if not n else n for n in result_vec] # replace all None
        
        for i, nm, cmap in zip([0], [nm], ['viridis']):
            result_vol = np.zeros_like(wb_mask)
            #res = [r[i] for r in result_vec]
            result_vol[coords] = result_vec
            result_vol = result_vol.astype('double')
            result_vol = np.nan_to_num(result_vol)
            minn,maxx=np.min(result_vol), np.max(result_vol)

            output_name = f'{results_path}_{nm}_whole_brain_SL_rad{sl_rad}.nii.gz'
            sl_nii = nib.Nifti1Image(result_vol, affine_mat)

            # mask non-brain
            masker_wb_plot = NiftiMasker(mask_img=brain_mask, standardize=False)
            masked_sl_res = masker_wb_plot.fit_transform(sl_nii)
            masked_sl_res = masker_wb_plot.inverse_transform(masked_sl_res).get_fdata()[:,:,:,0]
            print(f'shape after inverse: {masked_sl_res.shape}')
            sl_nii = nib.Nifti1Image(masked_sl_res, affine_mat)

            sl_nii.header.set_zooms(dimsize[:3])
            nib.save(sl_nii, output_name) 
            print(f"Saved result to {output_name}; plotting")
            
            # title = f'{task} sub {sub_id} {nm} sl radius={sl_rad}'
            # plotting.plot_glass_brain(output_name,output_file=output_name.replace('.nii.gz', '_glass.png').replace('results','plots'), colorbar=True, cmap=cmap, vmin=minn, vmax=maxx, title=title)
            # plotting.plot_stat_map(output_name,output_file=output_name.replace('.nii.gz', '_statmap.png').replace('results','plots'), colorbar=True, cmap=cmap, threshold=minn, vmax=maxx, title=title)
            # print("Finished plotting")
            
            