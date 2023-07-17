import os,sys,glob
import numpy as np
import pandas as pd
sys.path.insert(0,'..')
sys.path.insert(0,'TPHATE/')
import phate
import TPHATE.tphate 
from TPHATE.tphate import tphate
import searchlights as sls
from joblib import Parallel, delayed
import utils, config
import warnings
warnings.filterwarnings("ignore")

global ds

def run_sl_tphate(idx, searchlight_vertices, hemi):
    warnings.filterwarnings("ignore")
    searchlight_data = ds[:, searchlight_vertices]
    if np.linalg.norm(searchlight_data) == 0:
        return np.nan, np.nan
    op = tphate.TPHATE(verbose=0, n_jobs=-1, smooth_window=2).fit(searchlight_data)
    eb = op.transform(searchlight_data)
    return op.optimal_t, op.dropoff

def run_sl_phate(idx, searchlight_vertices, hemi):
    searchlight_data = ds[:, searchlight_vertices]
    op = phate.PHATE(verbose=0, n_jobs=-1).fit(searchlight_data)
    eb = op.transform(searchlight_data)
    return op.optimal_t

if __name__ == "__main__":
    sub_id = int(sys.argv[1])
    task = sys.argv[2]
    hemi = sys.argv[3]
    
    if len(sys.argv) > 4:
        run = int(sys.argv[4])
    else:
        run=None
    
    radius = 18
    searchlights = sls.get_searchlights(hemi, radius)
    TOTAL_RUNS = config.RUNS[task]
    all_runs = np.arange(1,TOTAL_RUNS+1)
    if run != None:
        to_run = [run]
        runstr = f'_run-{run}'
    else:
        to_run = all_runs
        runstr = ''
    outfn = f'StudyForrest/results/sub-{sub_id:02d}_ses-{task}{runstr}_optimal_t_whole_brain_SL_rad{radius}_{hemi}h.npy'
    ds = np.nan_to_num(utils._get_forrest_data(sub_id, hemi, to_run, task, True, False))
    print(f'ds shape={ds.shape}, {outfn}')

    joblist = [] 
    for i, sl in enumerate(searchlights):
        joblist.append(delayed(run_sl_tphate)(i, sl, hemi))
    print(f"Starting {len(joblist)} jobs")
    with Parallel(n_jobs=16) as parallel:
        results = parallel(joblist)
    res = np.array(results)
    np.save(outfn, res)