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
            count_fn = f'{count_dir}/{task}_filter_{subject_filter}_intersect_subject_gcount.nii.gz'
        else:
            count_fn = f'{count_dir}/{task}_all_intersect_subject_gcount.nii.gz'
        if verbose: print(f'save counts to {count_fn}')
        task_filenames = get_task_filenames(subject_list, task)
        if verbose: print(f'found {len(task_filenames)} files')
        fns = ' '.join(task_filenames)
        cmd = f'3dmerge -overwrite -prefix {count_fn} -gcount -ghits {len(subject_list)} {fns}' 
        run(cmd, shell=True)


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