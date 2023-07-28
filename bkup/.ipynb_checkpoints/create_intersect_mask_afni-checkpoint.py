# adapted from TLB ; uses AFNI

from os import makedirs, getcwd
from os.path import join, exists, dirname, basename
import sys
import glob
from subprocess import run
import shutil, argparse
import config


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", type=str)
    parser.add_argument("-f", "--subject_filter", type=int, default=0)
    parser.add_argument("-v", "--verbose", type=bool, default=True)
    p = parser.parse_args()
    dataset = p.dataset
    subject_filter=p.subject_filter
    verbose = p.verbose
    
    ## read in the filename for the arguments
    if dataset.lower() == 'camcan':
        import camcan_utils as utils
    elif dataset.lower() == 'narratives':
        import narratives_utils as utils
    else:
        import RM_utils as utils
    if verbose: print(f'imported utils for {dataset}; filter={subject_filter}')
    
    # load the list of subjects that are across all provided tasks
    tasks = utils.get_tasks()
    subject_list = utils.get_intersecting_subjects(subject_filter=subject_filter)
    
    if verbose: print(f'found {tasks} with {len(subject_list)} subjects')
    
    count_dir = join('masks', 'counts')
    makedirs(count_dir, exist_ok=True)
    count_fns = []
    for task in tasks:
        if subject_filter != 0 :
            fn = f'{count_dir}/{task}_filter_{subject_filter}_intersect_subject_gcount.nii.gz'
        else:
            fn = f'{count_dir}/{task}_all_intersect_subject_gcount.nii.gz'
        if verbose: print(f'save counts to {fn}')
        task_filenames = get_task_filenames(subject_list, task)
        
        
    

    # set general paths and subdirectory paths
    analysis_dir = join(kwargs.BASE_DIR, 'narratives_analysis')
    derivatives_dir = join(analysis_dir, 'derivatives')
    masks_dir = join(derivatives_dir, 'results', 'masks')
    all_mask_fns = []

    for task in kwargs.TASK_LIST:
        if not exists(join(masks_dir, 'counts')): makedirs(join(masks_dir, 'counts'))
    
        task_fns = [join(kwargs.NARRATIVES_DIR, 'derivatives', 'fmriprep', sub, 'func',
                           f'{sub}_task-{task}_space-{kwargs.SPACE}_res-native_desc-brain_mask.nii.gz') for sub in sub_list]

        count_fn = join(masks_dir, 'counts', f'group-{kwargs.SPACE}_res-{task}_desc-gcount.nii.gz')
        fns = ' '.join(task_fns)
        cmd = f'3dmerge -overwrite -prefix {count_fn} -gcount -ghits {len(sub_list)} {fns}' 

        run(cmd, shell=True)

        mni_mask_fn = join(kwargs.NARRATIVES_DIR, 'derivatives', kwargs.AFNI_PIPE, f'tpl-{kwargs.SPACE}', f'tpl-{kwargs.SPACE}_res-{task}_desc-brain_mask.nii.gz')
        task_mask_fn = join(masks_dir, f'group-{kwargs.SPACE}_res-{task}_desc-brain_mask-group.nii.gz')
        cmd = f'3dcalc -overwrite -prefix {task_mask_fn} -a {count_fn} -b {mni_mask_fn} -expr \'step(a)*step(b)\''

        run(cmd, shell=True)

        all_mask_fns.append(task_mask_fn)

    all_task_mask_fn = join(masks_dir, f'group-{kwargs.SPACE}_res-{all_tasks}_desc-brain_mask-group.nii.gz')
    fns = ' '.join(all_mask_fns)
    cmd = f'3dmerge -overwrite -prefix {all_task_mask_fn} -gcount -ghits {len(kwargs.TASK_LIST)}  {fns}'

    run(cmd, shell=True)

    cmd = f'3dcalc -overwrite -prefix {all_task_mask_fn} -a {all_task_mask_fn} -expr \'step(a)\''

    run(cmd, shell=True)