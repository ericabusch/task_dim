'''
figures out what subjects for what tasks go into what file list for intersect mask 
'''
import os, sys, glob, argparse
from config import *


def get_filenames(dataset, subject_list):
	tasks = utils.get_tasks()
	filenames = []
	for task in tasks:
		fns = utils.get_task_filenames(subject_list, task)
		print(f'loaded {len(fns)} for {task}')
		filenames += fns
	return filenames


def write_filelist(out_filename, list_of_files):
	with open(out_filename, 'w') as f:
		for fn in list_of_files:
			f.write(fn+'\n')
	if VERBOSE: print(f'wrote to {out_filename}')

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-d','--dataset',type=str)
	p = parser.parse_args()

	# import the right utils file
    if p.dataset.lower() == 'narratives': import narratives_utils as utils; import narratives_config as config
    elif p.dataset.lower() == 'adult_restmovie': import adult_restmovie_utils as utils; import adult_restmovie_config as config
    elif p.dataset.lower() == 'camcan': import camcan_utils as utils; import camcan_config as config
    elif p.dataset.lower() == 'infant_restmovie': import infant_restmovie_utils as utils; import infant_restmovie_config as config
    elif p.dataset.lower() == 'cneuromod': import cneurmod_utils as utils; import cneuromod_config as config
    elif p.dataset.lower() == 'partlycloudy': import partlycloudy_utils as utils; import partlycloudy_config as config
    elif p.dataset.lower() == 'hbn': import hbn_utils as utils; import hbn_config as config
    else: print(f'{p.dataset} not valid'); sys.exit(1)
    if p.verbose: print(f'loaded {p.dataset}_utils')
    VERBOSE=config.VERBOSE
	
	if p.dataset.lower() != 'infant_restmovie':
		all_subjects = utils.get_intersecting_subjects(subject_filter=0)
		all_filenames = get_filenames(p.dataset, all_subjects)
		out_filename = f'{utils.get_out_dir()}/files_for_3mm_intersect_mask.txt'
		if VERBOSE: print(f'writing {len(all_filenames)} names to {out_filename}')
		write_filelist(out_filename, all_filenames)
	else:
		tasks = utils.get_tasks()
		for t in tasks:
			subject_list = config.INFANT_SUBJECTS_TASKS[t] 
			fns = utils.get_task_filenames(subject_list, t)
			out_filename = f'{utils.get_out_dir()}/files_for_intersect_mask_{t}.txt'
			write_filelist(out_filename, fns)
			
