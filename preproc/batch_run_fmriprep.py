import sys, os
import argparse
from itertools import product
import subprocess
import json
import glob
sys.path.append('../')

PARTITION='psych_week'
TIME = "3-00:00:00"
N_NODES=1
N_TASKS=1
CPUS_PER_TASK=16
MEM_PER_CPU=20
DSQ_MODULES='module load fmriprep;'
JOB_CMD_ROOT = f'{DSQ_MODULES} fmriprep'
JOB_CMD_TAIL = '--skip_bids_validation --fs-license-file /home/elb77/license.txt --output-spaces MNI152NLin2009cAsym:res-native --bold2t1w-dof 12 --nprocs 16 --fs-no-reconall'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dataset', type=str)
    parser.add_argument('-o', '--overwrite', type=int, default=0)
    parser.add_argument('-b','--debug',type=int, default=0)
    parser.add_argument('-v','--verbose',type=int, default=1)
    p = parser.parse_args()
    
    if p.dataset.lower() == 'narratives':
        import narratives_utils as utils; import narratives_config as config
    elif p.dataset.lower() == 'hbn':
        import hbn_utils as utils; import hbn_config as config
    elif p.dataset.lower() == 'cneuromod':
        import cneuromod_utils as utils; import cneuromod_config as config
    elif p.dataset.lower() == 'camcan':
        import camcan_utils as utils; import camcan_config as config
    else:
        if p.verbose: print(f'{p.dataset} not supported; ending'); sys.exit()
    
    # make a set of directories
    fmriprep_outputs = f'{utils.get_fmriprep_input_dir()}/derivatives/fmriprep'
    fmriprep_inputs = utils.get_fmriprep_input_dir()
    fmriprep_workdir = f'/gpfs/milgram/scratch60/turk-browne/elb77/workdir/{p.dataset}'
    joblist_dir = f'{os.getcwd()}/{p.dataset}/joblists'
    dsq_dir = f'{os.getcwd()}/{p.dataset}/dsq_scripts/'
    log_dir = f'{os.getcwd()}/log'
    os.makedirs(fmriprep_outputs, exist_ok=True)
    os.makedirs(joblist_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(fmriprep_workdir, exist_ok=True)
    os.makedirs(dsq_dir, exist_ok=True)
    
    joblist_fn = os.path.join(joblist_dir, f'{p.dataset}_fmriprep_joblist.txt')
    
    if p.debug: joblist_fn = joblist_fn.replace(f'{p.dataset}_fmriprep', f'{p.dataset}_fmriprep_debug')
        
    subject_list = utils.get_fmriprep_subjects(debug=p.debug)
    task_list = utils.get_tasks()
    job_num = 0
    all_cmds = []

    for sub in subject_list:
        sub_dir = os.path.join(fmriprep_outputs, sub)
        file_exists = any(glob.glob(os.path.join(sub_dir, f'*{sub}*.html')))
        if p.overwrite or not file_exists:
            for task in task_list:
                cmd = f'{JOB_CMD_ROOT} {fmriprep_inputs} {fmriprep_outputs} participant --participant-label {sub} -t {task} -w {fmriprep_workdir} {JOB_CMD_TAIL}'
                all_cmds.append(cmd)
                job_num += 1
        else:
            if p.verbose: print(f'already running fmriprep for {sub}')
    
    if not all_cmds:
        print (f'No files needing preprocessing for {p.dataset} - overwrite if you want to redo preprocessing', flush=True)
        sys.exit(0)
    
    with open(joblist_fn, 'w') as f:
        for cmd in all_cmds:
            f.write(f"{cmd}\n")
    if p.verbose: print(f'created {joblist_fn} with {len(all_cmds)} jobs')
    
    dsq_base_string = f'{dsq_dir}/dsq_fmriprep'
    dsq_batch_fn = f'{dsq_base_string}_{p.dataset}'
    array_fmt_width = len(str(job_num))
        
    subprocess.run(f"dsq --job-file {joblist_fn} --batch-file {dsq_batch_fn}.sh "
        f"--status-dir {log_dir} --partition={PARTITION} --output={log_dir}/%A_%{array_fmt_width}a.txt "
        f"--time={TIME} --nodes={N_NODES} --ntasks={N_TASKS} "
        f"--cpus-per-task={CPUS_PER_TASK} --mem-per-cpu={MEM_PER_CPU}", shell=True)