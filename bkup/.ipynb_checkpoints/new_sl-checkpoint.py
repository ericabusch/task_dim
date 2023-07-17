import os, sys, glob, pickle
import numpy as np
import matplotlib.pyplot as plt
sys.path.insert(0,'..')
sys.path.insert(0,'TPHATE/')
import TPHATE.tphate
from TPHATE.tphate import tphate
import searchlights as sls
from brainplotlib import brain_plot
from joblib import Parallel, delayed
import utils, config
from config import NODES_LH, NODES_RH
import warnings
warnings.filterwarnings("ignore")
warnings.filterwarnings(action='ignore', category=RuntimeWarning)


global ds, sl_embedding_ds, dss, searchlight_list

scratch = '/gpfs/milgram/scratch60/turk-browne/elb77/task_dimension/analysis_results/'

def run_sl_tphate(idx, searchlight):
    global sl_embedding_ds
    sl_data = ds[:, searchlight]
    import warnings
    warnings.filterwarnings("ignore")
    warnings.filterwarnings(action='ignore', category=RuntimeWarning)
    if np.all(sl_data == 0):
        print(f"All zeros @ idx {idx}; returning")
        return np.nan, np.nan
    tphate_op = tphate.TPHATE(verbose=0, n_landmark=len(sl_data)).fit(sl_data)
    dropoff = tphate_op.dropoff
    dim = tphate_op._find_optimal_t()
    embedding = tphate.TPHATE(verbose=0, n_landmark=len(sl_data), t=dim).fit_transform(sl_data)
    sl_embedding_ds[idx] = embedding
    return dropoff, dim

def run_wb_tphate():
    tphate_op = tphate.TPHATE(verbose=0, n_landmark=len(ds)).fit(ds)
    dropoff = tphate_op.dropoff
    dim = tphate_op._find_optimal_t()
    embedding = tphate.TPHATE(verbose=0, n_landmark=len(ds), t=dim).fit_transform(ds)
    return dropoff, dim, embedding

def run_sl_isc(sl):
    searchlight_data = dss[:, :, sl]
    results = np.zeros((dss.shape[0]))
    for s in range(dss.shape[0]):
        others = np.setdiff1d(np.arange(dss.shape[0]), s)
        test_data = searchlight_data[s].ravel()
        train_data = np.mean(searchlight_data[others],axis=0).ravel()
        results[s] = np.corrcoef(test_data, train_data)[0,1]
    return results

def drive_jobs(result_rootname, scratch_rootname):
    global ds, sl_embedding_ds, dss,searchlight_list
    searchlight_list = sls.get_searchlights(hemi, radius, 'fsaverage')
#     idx=np.array([0,1,10,3225,5724,7904,1000])
#     searchlight_list=[searchlight_list[i] for i in idx]
    sl_embedding_ds = [[] for i in range(len(searchlight_list))]
    ds = np.nan_to_num(ds)
    joblist = []
    for i, sl in enumerate(searchlight_list):
        joblist.append(delayed(run_sl_tphate)(i, sl))
    print(f'starting jobs')
    with Parallel(n_jobs=16) as parallel:
        results = parallel(joblist)
    res = np.array(results)
    np.save(f'{result_rootname}_autocorr_{hemi}h.npy', res[:,0])
    np.save(f'{result_rootname}_dimensionality_{hemi}h.npy', res[:,1])
    with open(f'{scratch_rootname}_sl_embeddings_{hemi}h.pkl', 'wb') as f:
        pickle.dump(sl_embedding_ds, f)
    print(f'done searchlights {scratch_rootname}')
    # now do whole-brain
    dropoff, dim, embedding = run_wb_tphate()
    np.save(f'{result_rootname}_autocorr_{hemi}h_whole_brain.npy', np.array([dropoff]))
    np.save(f'{result_rootname}_dimensionality_{hemi}h_whole_brain.npy', np.array([dim]))
    np.save(f'{result_rootname}_embedding_{hemi}h_whole_brain.npy', np.array([embedding]))
    print(f'done whole brain: drop={dropoff}, dim={dim}')


def load_data_subj_run():
    global ds
    ds = utils._get_forrest_data(subject=subject, side=hemi, runs=[run], session=session, z=True, mask=True)
    NODES = NODES_LH if hemi == 'l' else NODES_RH
    ds = ds[:,:NODES]
    print(f'Running single subject, single run, ds of shape {ds.shape}')
    out_root = f'results/sub-{subject:02d}_ses-{session}_run-{run:02d}_rad{radius}'
    scratch_root = f'{scratch}/sub-{subject:02d}_ses-{session}_run-{run:02d}_rad{radius}'
    drive_jobs(out_root, scratch_root)
    
def load_data_subj_allruns():
    global ds
    runs = np.arange(config.RUNS[session]) + 1
    ds = utils._get_forrest_data(subject=subject, side=hemi, runs=runs, session=session, z=True, mask=True)
    NODES = NODES_LH if hemi == 'l' else NODES_RH
    ds = ds[:,:NODES]
    print(f'Running single subject, all runs, ds of shape {ds.shape}')
    out_root = f'results/sub-{subject:02d}_ses-{session}_all-runs_rad{radius}'
    scratch_root = f'{scratch}/sub-{subject:02d}_ses-{session}_all-runs_rad{radius}'
    drive_jobs(out_root, scratch_root)
    

def load_data_avg_allruns():
    global ds, dss
    NODES = NODES_LH if hemi == 'l' else NODES_RH
    
    dss=[]
    runs = np.arange(config.RUNS[session]) + 1
    for subj in config.SUBJECTS:
        d = utils._get_forrest_data(subject=subj, side=hemi, runs=runs, session=session, z=True, mask=True)
        d = np.nan_to_num(d[:, :NODES])
        dss.append(d)
    dss = np.array(dss)
    print(f'dss of shape {dss.shape}')
    out_root = f'results/sub-AVG_ses-{session}_all-runs_rad{radius}'
    scratch_root = f'{scratch}/sub-AVG_ses-{session}_all-runs_rad{radius}'
    
    # run SL ISC here
    joblist = []
    searchlight_list = sls.get_searchlights(hemi, radius, 'fsaverage')
    for i, sl in enumerate(searchlight_list):
        joblist.append(delayed(run_sl_isc)(sl))
    print("Starting ISC jobs")    
    with Parallel(n_jobs=config.NJOBS) as parallel:
        SL_ISC = np.array(parallel(joblist))
    np.save(f'{out_root}_sl_isc_{hemi}h.npy', SL_ISC)
    print("Done isc; running other analyses")
    # now average and run the other analyses
    ds = np.mean(dss,axis=0)
    print(f'ds of shape {ds.shape}')
    drive_jobs(out_root, scratch_root)
    
def load_data_avg_run():
    global ds, dss
    NODES = NODES_LH if hemi == 'l' else NODES_RH

    dss=[]
    runs = np.arange(config.RUNS[session]) + 1
    for subj in config.SUBJECTS:
        d = utils._get_forrest_data(subject=subj, side=hemi, runs=[run], session=session, z=True, mask=True)
        d = d[:,:NODES]
        dss.append(d)
    dss = np.array(dss)
    print(f'Full dataset, single run, dss of shape {dss.shape}')
    out_root = f'results/sub-AVG_ses-{session}_run-{run:02d}_rad{radius}'
    scratch_root = f'{scratch}/sub-AVG_ses-{session}_run-{run:02d}_rad{radius}'
    
    # run SL ISC here
    searchlight_list = sls.get_searchlights(hemi, radius, 'fsaverage')
    joblist = []
    for i, sl in enumerate(searchlight_list):
        joblist.append(delayed(run_sl_isc)(sl))
    print("Starting ISC jobs")    
    with Parallel(n_jobs=config.NJOBS) as parallel:
        SL_ISC = np.array(parallel(joblist))
    np.save(f'{out_root}_sl_isc_{hemi}h.npy', SL_ISC)
    print("Done isc; running other analyses")
    # now average and run the other analyses
    ds = np.mean(dss,axis=0)
    print(f'Avg dataset, single run, ds of shape {ds.shape}')
    drive_jobs(out_root, scratch_root)
    

    
if __name__ == '__main__':
    subject = sys.argv[1]
    run = sys.argv[2]
    radius = int(sys.argv[3])
    hemi = sys.argv[4]
    session = sys.argv[5]
    
    print(f'subject: {subject}, run: {run}, radius: {radius}, hemi: {hemi}, session: {session}')
    if subject == 'average':
        if run == 'all':
            load_data_avg_allruns()
        else:
            run = int(run)
            load_data_avg_run()
    else:
        subject = config.SUBJECTS[int(subject)]
        if run == 'all':
            load_data_subj_allruns()
        else:
            run = int(run)
            load_data_subj_run()









