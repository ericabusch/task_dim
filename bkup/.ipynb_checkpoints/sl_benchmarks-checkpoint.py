import os,sys,glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
sys.path.insert(0,'..')
sys.path.insert(0,'TPHATE/')
from sklearn.decomposition import PCA
import searchlights as sls
from brainplotlib import brain_plot
import pickle
from joblib import Parallel, delayed
import svc_analysis as sva
import utils, config
import warnings
warnings.filterwarnings("ignore")

global ds, labels
N_REPS=1000
N_FOLDS=3



def run_spatial_correlation(X):
    idx = np.triu_indices(X.shape[1])
    return np.nanmean(np.corrcoef(X.T)[idx])
    
def run_sl_full(idx, searchlight, hemi):
    searchlight_data=ds[:, searchlight]
    
    # run spatial correlation
    corr = run_spatial_correlation(searchlight_data)
    # run analyses
    if labels.ndim == 1:
        clf_acc, clf_p = sva.clf_wrapper(searchlight_data, labels, n_folds=5, num_reps=0, balance=False)
        print(idx, clf_acc, clf_p, corr)
        return searchlight_data.shape[1], clf_acc, clf_p, corr
    
    clf_acc1, clf_p1 = sva.clf_wrapper(embed, labels[:,0], n_folds=N_FOLDS, num_reps=N_REPS, balance=True)
    clf_acc2, clf_p2 = sva.clf_wrapper(embed, labels[:,1], n_folds=N_FOLDS, num_reps=N_REPS, balance=True)
    clf_acc3, clf_p3 = sva.clf_wrapper(embed, labels[:,2], n_folds=N_FOLDS, num_reps=N_REPS, balance=True)
    print(idx, searchlight_data.shape[1], clf_acc1, clf_p1, corr)
    return searchlight_data.shape[1], clf_acc1, clf_p1,clf_acc2, clf_p2, clf_acc3, clf_p3, corr
    
    
def run_sl_pca(idx, searchlight, hemi):
    searchlight_data=ds[:, searchlight]
    warnings.filterwarnings("ignore")
    
    # now take that and embed the data
    pca = PCA().fit(searchlight_data)
    # how many components to keep?
    dim = np.sum(np.cumsum(pca.explained_variance_ratio_) <= .9)
    embed = pca.transform(searchlight_data)[:,:dim]
    
    # run spatial correlation
    corr = run_spatial_correlation(embed)
    # run analyses
    if labels.ndim == 1:
        clf_acc, clf_p = sva.clf_wrapper(embed, labels, n_folds=5, num_reps=0, balance=False)
        print(idx, dim, clf_acc, clf_p, corr)
        return dim, clf_acc, clf_p, corr
    
    clf_acc1, clf_p1 = sva.clf_wrapper(embed, labels[:,0], n_folds=N_FOLDS, num_reps=N_REPS, balance=True)
    clf_acc2, clf_p2 = sva.clf_wrapper(embed, labels[:,1], n_folds=N_FOLDS, num_reps=N_REPS, balance=True)
    clf_acc3, clf_p3 = sva.clf_wrapper(embed, labels[:,2], n_folds=N_FOLDS, num_reps=N_REPS, balance=True)
    print(idx, dim, clf_acc1, clf_p1, corr)
    return dim, clf_acc1, clf_p1,clf_acc2, clf_p2, clf_acc3, clf_p3, corr

def drive_jobs():
    global ds, labels
    slsl = sls.get_searchlights(hemi, 20, 'fsaverage')
    TOTAL_RUNS = config.RUNS[task]
    all_runs = np.arange(1,TOTAL_RUNS+1)
    
    if run!= None:
        to_run = [run]
        runstr = f'_run-{run}'
    else:
        to_run = all_runs
        runstr = ''
        
    ds = utils._get_forrest_data(SUBJECT, hemi, to_run, task, True, False)
    
    if task == 'localizer':
        labels = utils.load_subject_localizer_labels(SUBJECT, 'all')
    else:
        regressors = ["IoE_coded", "FoT_coded", "ToD_coded"]
        labels = pd.read_csv(config.FEATURES_FILE)
        if run != None:
            labels = labels[labels['RunLabel']==run]
        labels=labels[regressors].values
        
    
    print(f"Data {ds.shape}, labels {labels.shape}")

    joblist = []
    params = []
    for i, sl in enumerate(slsl):
        joblist.append(delayed(run_sl_pca)(i, sl, hemi))

    print(f"Starting {len(joblist)} jobs")
    with Parallel(n_jobs=16) as parallel:
        results = parallel(joblist)

    res = np.array(results) # will be (9372+9370, 5)
    
    out = f'results/sub-{SUBJECT}_ses-{task}_sl_pca_res{runstr}_{hemi}h.npy'
    np.save(out, res)
    
    joblist = []
    params = []
    for i, sl in enumerate(slsl):
        joblist.append(delayed(run_sl_full)(i, sl, hemi))

    print(f"Starting {len(joblist)} jobs voxel")
    with Parallel(n_jobs=16) as parallel:
        results = parallel(joblist)

    res = np.array(results) # will be (9372+9370, 5)
    
    out = f'results/sub-{SUBJECT}_ses-{task}_sl_full_res{runstr}_{hemi}h.npy'
    np.save(out, res)
    
        
    
if __name__ == '__main__':
    subid = int(sys.argv[1])
    task = sys.argv[2]
    hemi = sys.argv[3]
    run = int(sys.argv[4])
    SUBJECT = subid
    print(subid, task)
    drive_jobs()
    
        

        
        
                           
        
    
    
