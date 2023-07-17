from os import makedirs, getcwd
from os.path import join, exists, dirname, basename
import sys
import glob
from subprocess import run
import shutil

#add paths to custom modules
sys.path.append("./utils/")

from narratives_utils import get_parser, post_process_kwargs, get_intersecting_subjects

if __name__ == "__main__":
    
    ## read in the filename for the arguments
    config_fn = sys.argv[1]

    args = get_parser().parse_args([f'@{config_fn}'])
    kwargs = post_process_kwargs(args)
    
    all_tasks = '-'.join(kwargs.TASK_LIST)

    # load the list of subjects that are across all provided tasks
    sub_list = get_intersecting_subjects(kwargs.NARRATIVES_DIR, kwargs.TASK_LIST)

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
        cmd = f'3dmerge -overwrite -prefix {count_fn} -gcount -ghits {len(sub_list)} {fns}' # -ghits {len(sub_list)} 

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