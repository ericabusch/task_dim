import argparse,itertools,os
import numpy as np
import subprocess

def generate_commands(command_call, script_name_full, things_to_loop_through, check_for_repeat):
    # Generate all combinations
    # Get the keys and values
    keys = list(things_to_loop_through.keys())
    values = list(things_to_loop_through.values())
    commands = []
    try:
        sub_idx = keys.index('i')
    except:
        check_for_repeat=False
    task_idx = keys.index('t')
    # Generate all combinations
    combinations = list(itertools.product(*values))
    # Format and print the combinations
    for combo in combinations:
        # Pair each value with its corresponding key
        formatted_combo = " ".join([f"-{key} {value}" for key, value in zip(keys, combo)])
        command = f'{command_call} {script_name_full} {formatted_combo}'
        
        # Check for repeats 
        if check_for_repeat:
            sidx = combo[sub_idx]
            sub = ALL_SUBJECTS[sidx]
            task = combo[task_idx]
            R = utils.has_repeat_files(sub, task)
        
            if R != 0:
                for i in range(R):
                    commands.append(command + f' -f {i}')
            else:    
                commands.append(command)
        else:
            commands.append(command)
    return commands

def insert(list1, to_insert, i):
    temp = list1[i:]
    list1[i:] = to_insert
    list1 += temp
    return list1

def insert_lines_above_match(file_path, match_string, lines_to_insert):
    # Read the file content
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Find the index of the line that matches the string
    for i, line in enumerate(lines):
        if match_string in line:
            # Insert the new lines above the matched line
            lines = insert(lines, lines_to_insert, i)
            break

    # Write the modified content back to the file
    with open(file_path, 'w') as file:
        for line in lines:
            file.write(line)


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate commands for all metrics.")
    parser.add_argument("-d", "--dataset", required=True, help="Name of the dataset.")
    parser.add_argument("-s", "--script_name", required=True, help="relative path of script to run")
    parser.add_argument("-t", "--task", required=False, default='all',type=str, help="Name of the task.")
    parser.add_argument("-a", "--atlas", required=False, default=0, type=int, help="Use atlas?")
    p = parser.parse_args()

    # import the right utils/config file
    if p.dataset.lower() == 'narratives': import narratives_utils as utils; import narratives_config as config
    elif p.dataset.lower() == 'adult_restmovie': import adult_restmovie_utils as utils; import adult_restmovie_config as config
    elif p.dataset.lower() == 'camcan': import camcan_utils as utils; import camcan_config as config
    elif p.dataset.lower() == 'infant_restmovie': import infant_restmovie_utils as utils; import infant_restmovie_config as config
    elif p.dataset.lower() == 'cneuromod': import cneuromod_utils as utils; import cneuromod_config as config
    elif p.dataset.lower() == 'partlycloudy': import partlycloudy_utils as utils; import partlycloudy_config as config
    elif p.dataset.lower() == 'hbn': import hbn_utils as utils; import hbn_config as config
    else: print(f'{p.dataset} not valid')  ; sys.exit(1)
    print(f'loaded {p.dataset}_utils')

    fileroot = f'{config.ROOT}/task_dim/'
    jobname = f'{p.dataset}'

    REPEAT_DATASETS = ['cneuromod', 'infant_restmovie']
    CHECK_FOR_REPEAT = False
    if p.dataset in REPEAT_DATASETS:
        CHECK_FOR_REPEAT = True

    # FIGURE OUT FILENAME TO WRITE COMMANDS
    command_filename = f'{fileroot}/joblists/{p.dataset}'
    if p.atlas == 1:
        command_filename+= '_atlas'
    else:
        command_filename+= '_searchlight'
    if 'isc' in p.script_name.lower():
        command_filename+= '_isc'
        jobname+= '_isc_'
    elif 'ide' in p.script_name.lower():
        command_filename+= '_ide'
        jobname+= '_ide_'
    elif 'aggregate' in p.script_name.lower():
        command_filename+= '_aggregate'
        jobname+= '_aggregate_'
    else:
        command_filename+= p.script_name.lower().split('.')[0]
    command_filename+='_joblist.txt'
    print(f'saving to {command_filename}')
    if '.py' not in p.script_name: p.script_name += '.py'

    if p.task == 'all':
        TASKS = utils.get_tasks()
        if type(TASKS) != list: TASKS = [TASKS]
        jobname+='all_tasks'
    else:
        TASKS = [p.task]
        jobname+=p.task
    print(f'looping through {TASKS} tasks')

    TO_LOOP = {'t':TASKS, 'd': [p.dataset]} 


    # look for instances where we need to be considering groups -- 
    if p.dataset.lower() in ['hbn', 'partlycloudy']:
        if ('isc' in p.script_name.lower()) or ('aggregate' in p.script_name.lower()):
            
            groups = utils.get_groups()
            overall_group_labels, overall_subject_indices = [], []
            # get number per group
            for g in groups:
                subjects = utils.get_intersecting_subjects(subject_filter=g)
                subject_indices = np.arange(len(subjects))
                group_labels = [g for i in range(len(subjects))]
                overall_group_labels += group_labels
                overall_subject_indices += [s for s in subject_indices]
            TO_LOOP['is'] = [overall_subject_indices, overall_group_labels]
                
            
    
    # If script name has ISC or IDE, we know we have to use subjects
    if 'isc' in p.script_name.lower()  or 'ide' in p.script_name.lower():

        ALL_SUBJECTS = utils.get_intersecting_subjects()
        TO_LOOP['i'] = np.arange(len(ALL_SUBJECTS))
        print(f'looping through {len(ALL_SUBJECTS)} subjects')

    if 'aggregate' in p.script_name.lower():
        M = config.IDE_METHODS + ['ISC']
        TO_LOOP['m'] = M 
        print(f'looping through {len(M)} metrics')

    
        
    if p.atlas == 0:
        # we know we're running SL and need to activate that command
        call = 'srun --mpi=pmi2 python -u'
    else:
        call = 'python -u'

    assert os.path.exists(f'{fileroot}/{p.script_name}')

    command_list = generate_commands(call, f'{fileroot}/{p.script_name}', TO_LOOP, CHECK_FOR_REPEAT)
    if os.path.exists(command_filename):
        os.remove(command_filename)
        
    # Write commands to a file or print them
    with open(command_filename, "w") as file:
        for command in command_list:
            file.write(command + "\n")
    print(f"Generated {len(command_list)} commands. Saved to {command_filename}.")

    # WRITE DSQ SUBMIT SCRIPT
    batchfile = command_filename.replace('joblists','submit_scripts').replace(p.dataset, f'dsq_{p.dataset}').replace('_joblist.txt','_submit.sh')
    dsq_command = f"dSQ --job-file {command_filename} --batch-file {batchfile} --job-name {jobname} --output log/%A_%3a.out --mail-type all"


    subprocess.run(dsq_command, shell=True, capture_output=True)

    lines_to_insert = ['# Set up the environment\n', 'module load miniconda\n', 'module load OpenMPI\n', 'conda activate env_tda\n']
    # edit the dsq file
    insert_lines_above_match(batchfile, "# DO NOT EDIT LINE BELOW", lines_to_insert)

    print(f'ran {dsq_command}')

