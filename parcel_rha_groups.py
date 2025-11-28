#!/usr/bin/env python
"""
Hyperalignment Analysis Script with K-Fold Cross-Validation

This script runs hyperalignment analysis on neuroimaging data with k-fold cross-validation,
computes ISC before and after hyperalignment, and generates visualizations.

Usage:
    python run_hyperalignment_analysis.py -d <dataset> -g <subject_filter> [options]
    
Example:
    python run_hyperalignment_analysis.py -d hbn -g U22
    python run_hyperalignment_analysis.py -d narratives -g adults -t story
    python run_hyperalignment_analysis.py -d partlycloudy -g children -n 10
"""

import argparse
import sys, os
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import KFold
from nilearn.image import concat_imgs, math_img
from nilearn.maskers import NiftiMasker
import matplotlib.pyplot as plt
import plotting_helpers
from joblib import Parallel, delayed

# Import hyperalignment module
from RepBiomrkr import hyperalignment as hyp
# import hyperalignment as hyp


# Valid datasets
VALID_DATASETS = ['hbn', 'partlycloudy', 'adult_restmovie', 'infant_restmovie', 'narratives']
SEED=4

def load_all_data(subjects, task, concat=False):
    """
    Load neuroimaging data for multiple subjects.
    
    Parameters
    ----------
    subjects : list
        List of subject IDs
    task : str
        Task name (e.g., 'movieTP')
    concat : bool
        Whether to concatenate images
        
    Returns
    -------
    list or NiftiImage
        List of images or concatenated image
    """
    image_list = [] 
    for s in subjects:
        nii = utils.get_subject_data(sub_id=s, task=task)
        image_list.append(nii)
    if concat:
        return concat_imgs(image_list)
    return image_list


def run_hyperalignment_kfold(dss, n_folds=5, verbose=True):
    """
    Run hyperalignment with k-fold cross-validation across subjects
    
    Parameters
    ----------
    dss : np.ndarray
        Data array of shape (n_subjects, n_voxels, n_timepoints)
    n_folds : int
        Number of folds for cross-validation
    verbose : bool
        Whether to print progress
        
    Returns
    -------
    list of dict
        Results for each fold containing ISC values
    """
    n_subjects = dss.shape[0]
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=SEED)
    
    fold_results = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(range(n_subjects))):
        if verbose:
            print(f"  Processing fold {fold_idx + 1}/{n_folds}")
        
        # Split data
        training_dss = dss[train_idx]
        testing_dss = dss[test_idx]
        
        # Train hyperalignment on training data
        hyp_model = hyp.Hyperalignment(verbose=0)
        hyp_model.fit(training_dss)
        
        # Apply transformations to testing data
        testing_dss_aligned = []
        for ds in testing_dss:
            dsR, R = hyp_model.transform_new_dataset(ds)
            testing_dss_aligned.append(dsR)
        testing_dss_aligned = np.array(testing_dss_aligned)
        
        # Compute ISC on testing data (raw and aligned)
        isc_raw = hyp_model._run_isc(testing_dss)
        isc_ha = hyp_model._run_isc(testing_dss_aligned)
        
        fold_results.append({
            'fold': fold_idx,
            'isc_raw': isc_raw,
            'isc_ha': isc_ha
        })
    
    return fold_results

def generate_visualizations(results_df, fn_stem):
    
    # Create visualizations
    print("\nGenerating visualizations...")
    # Compute mean ISC across folds for each parcel
    mean_results = results_df.groupby('parcel_number').agg({
        'isc_raw': 'mean',
        'isc_ha': 'mean'
    }).reset_index()

    # Create parcel-wise arrays for visualization
    n_parcels = len(atlas_df)
    isc_raw_map = np.zeros(n_parcels)
    isc_ha_map = np.zeros(n_parcels)

    for _, row in mean_results.iterrows():
        parcel_idx = int(row['parcel_number']) - 1
        isc_raw_map[parcel_idx] = row['isc_raw']
        isc_ha_map[parcel_idx] = row['isc_ha']

    isc_diff_map = isc_ha_map - isc_raw_map
    # generate surface plots 
    generate_surface_plot(data_fn, image_fn, atlas, cmap, cbar_range, surf_type='fslr', target_density='32k', include_cbar=False, title=None,method='nearest', threshold=None, mask_medial_wall=True) 
    isc_raw_fn = f'{utils.get_results_dir()}/plots/{fn_stem}_mean_isc_raw.png'
    isc_ha_fn = f'{utils.get_results_dir()}/plots/{fn_stem}_mean_isc_ha.png'
    isc_diff_fn = f'{utils.get_results_dir()}/plots/{fn_stem}_mean_isc_diff.png'

    isc_range = plotting_helpers.get_global_value_range([isc_raw_map, isc_ha_map], return_int=False, return_symmetric=False)
    diff_range = plotting_helpers.get_global_value_range([isc_diff_map], return_int=False, return_symmetric=True)


    plotting_helpers.generate_surface_plot(isc_raw_map, isc_raw_fn, atlas='Schaefer', cmap='magma', surf_type='fsaverage', method='nearest', target_density='41k', include_cbar=True, cbar_range=isc_range, title=f'{fn_stem} raw isc')
    plotting_helpers.generate_surface_plot(isc_ha_map, isc_ha_fn, atlas='Schaefer', cmap='magma', surf_type='fsaverage', method='nearest', target_density='41k', include_cbar=True, cbar_range=isc_range, title=f'{fn_stem} ha isc')        
    plotting_helpers.generate_surface_plot(isc_diff_map, isc_diff_fn, atlas='Schaefer', cmap=plotting_helpers.diverging_colormap_bp(), surf_type='fsaverage', method='nearest', target_density='41k', include_cbar=True, cbar_range=diff_range, title=f'{fn_stem} HA_ISC - RAW_ISC')

    # Create comparison plot
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
    all_raw = results_df['isc_raw'].values
    all_ha = results_df['isc_ha'].values
    sns.scatterplot(x=all_raw, y=all_ha,  alpha=0.6, c='r')
    max_val = max(all_raw.max(), all_ha.max())
    min_val = min(all_raw.min(), all_ha.min())
    ax.plot([min_val, max_val], [min_val, max_val], 'k--', label='Identity')
    ax.set_xlabel('ISC (Raw)')
    ax.set_ylabel('ISC (Hyperaligned)')
    ax.set_title(f'ISC Comparison: {fn_stem}')
    ax.grid(True, alpha=0.3)
    output_comparison = f'{utils.get_results_dir()}/plots/{fn_stem}_isc_comparison.png'
    plt.savefig(output_comparison, dpi=300, bbox_inches='tight')
    print(f"Comparison plot saved to: {output_comparison}")
    return
 

def main(dataset, task, subject_filter='', n_folds=5):
    """
    Main analysis pipeline.
    
    Parameters
    ----------
    dataset : str
        Dataset name (e.g., 'hbn', 'narratives')
    subject_filter : str
        Age group filter (e.g., 'U22')
    task : str
        Task name
    n_folds : int
        Number of cross-validation folds
    """
    print("="*60)
    print(f"Hyperalignment Analysis")
    print(f"Dataset: {dataset}")
    print(f"Group: {subject_filter}")
    print(f"Task: {task}")
    print("="*60)
    
    # Load atlas (check if config has load_atlas function, otherwise use utils)
    atlas_image, atlas_df = utils.load_atlas()
    
    # Get subjects for age group
    print(f"\nDetermining subjects for age group {subject_filter}...")
    subjects = utils.get_intersecting_subjects(subject_filter=subject_filter)
    print(f"Found {len(subjects)} subjects")
    
    # Load data
    print(f"\nLoading data for task: {task}...")
    data_list = load_all_data(subjects, task)
    print(f"\Data of shape: {len(data_list)}, {data_list[0].shape}")
    
    # Initialize results list
    all_results = []
    
    os.makedirs(f'{utils.get_out_dir()}/temp/', exist_ok=True)
    os.makedirs(f'{utils.get_out_dir()}/results/plots', exist_ok=True)
    
    
    # Process each parcel
    print(f"\nProcessing {len(atlas_df)} parcels...")
    for r in range(1, len(atlas_df) + 1):
        parcel_name = atlas_df.iloc[r - 1]['parcel_name'] if 'parcel_name' in atlas_df.columns else f"Parcel_{r}"
        print(f"\nParcel {r}/{len(atlas_df)}: {parcel_name}")
        
        try:
            # Create ROI mask
            roi_mask_img = math_img(f"img == {r}", img=atlas_image)
            roi_masker = NiftiMasker(roi_mask_img, standardize=True)
            
            # Extract data for this parcel
            dss = np.array([roi_masker.fit_transform(ds) for ds in data_list])
            np.save(f'{utils.get_out_dir()}/temp/parcel_{r:03d}_{subject_filter}.npy', dss)
            n_subjects, n_voxels, n_timepoints = dss.shape
            print(f"  Data shape: {dss.shape} (subjects x voxels x timepoints)")
            
            # Run k-fold cross-validation
            fold_results = run_hyperalignment_kfold(dss, n_folds=n_folds, verbose=True)
            
            # Store results
            for fold_result in fold_results:
                all_results.append({
                    'dataset': dataset,
                    'subject_filter': subject_filter,
                    'parcel_number': r,
                    'parcel_name': parcel_name,
                    'fold': fold_result['fold'],
                    'isc_raw': fold_result['isc_raw'],
                    'isc_ha': fold_result['isc_ha']
                })
        
        except Exception as e:
            print(f"  Error processing parcel {r}: {e}")
            continue
    
    # Convert to DataFrame
    outfn_stem = f'{dataset}_{task}_{subject_filter}'
    print("\nCreating results DataFrame...")
    results_df = pd.DataFrame(all_results)
    # Save results
    output_csv = f'{utils.get_results_dir()}/{outfn_stem}.csv'
    results_df.to_csv(output_csv, index=False)
    print(f"Results saved to: {output_csv}")
    generate_visualizations(results_df, outfn_stem)
    print("\n" + "="*60)
    print(f"Analysis complete {outfn_stem}")
    print(f"Mean ISC (Raw): {results_df['isc_raw'].mean():.4f} ± {results_df['isc_raw'].std():.4f}")
    print(f"Mean ISC (HA): {results_df['isc_ha'].mean():.4f} ± {results_df['isc_ha'].std():.4f}")
    print("="*60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dataset', type=str, choices=VALID_DATASETS, required=True)
    parser.add_argument('-g','--subject_filter', type=str, required=True)
    parser.add_argument('-t','--task', type=str, required=True, default='movieTP')
    parser.add_argument('-k','--k_folds', type=int, default=5)
    parser.add_argument('-v','--verbose', type=int, default=1)
    p = parser.parse_args()
    
    # import the right utils/config file
    if p.dataset.lower() == 'narratives': import narratives_utils as utils; import narratives_config as config
    elif p.dataset.lower() == 'adult_restmovie': import adult_restmovie_utils as utils; import adult_restmovie_config as config
    elif p.dataset.lower() == 'infant_restmovie': import infant_restmovie_utils as utils; import infant_restmovie_config as config; p.subject_filter=p.task
    elif p.dataset.lower() == 'partlycloudy': import partlycloudy_utils as utils; import partlycloudy_config as config
    elif p.dataset.lower() == 'hbn': import hbn_utils as utils; import hbn_config as config
    else: print(f'{p.dataset} not valid'); sys.exit(1)
    if p.verbose: print(f'loaded {p.dataset}_utils')
    
    try:
        main(
            dataset=p.dataset,
            subject_filter=p.subject_filter,
            task=p.task,
            n_folds=p.k_folds,
        )
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
