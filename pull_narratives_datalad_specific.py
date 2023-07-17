import os, sys, glob
from subprocess import call
import narratives_utils as utils

subjects = sorted(utils.get_intersecting_subjects(utils.datalad_dir, utils.target_tasks))
path = os.path.join(utils.datalad_dir, 'derivatives/afni-smooth')
file_format = "*_task-*_space-MNI152NLin2009cAsym_res-native_desc-clean_bold.nii.gz"

for sub in subjects:
    fns = glob.glob(os.path.join(path, sub, 'func', file_format))
    print(f'{sub} found {len(fns)} files')
    commands = [f'datalad get {f}' for f in fns]
    for c in commands:
        call(c, shell=True)
    for story in utils.target_tasks:
        fn = os.path.join(path, sub, 'func', f"*_task-{story}_space-MNI152NLin2009cAsym_res-native_desc-clean_bold.nii.gz")
        command = f'cp {fn} /gpfs/milgram/project/turk-browne/projects/Narratives/{story}/'
        call(command, shell=True)
        print(command)
                    
