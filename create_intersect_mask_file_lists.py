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
	if p.dataset.lower() == 'narratives': import narratives_utils as utils
	elif p.dataset.lower() == 'rest_movie': import RM_utils as utils
	elif p.dataset.lower() == 'camcan': import camcan_utils as utils
	elif p.dataset.lower() == 'infantrestmovie': import RM_infant_utils as utils
	elif p.dataset.lower() == 'cneuromod': import CNM_utils as utils
	else: print(f'{p.dataset} not valid');  sys.exit(1)
	if VERBOSE: print(f'loaded {p.dataset}_utils')
	
	if p.dataset.lower() != 'infantrestmovie':
		all_subjects = utils.get_intersecting_subjects(subject_filter=0)
		all_filenames = get_filenames(p.dataset, all_subjects)
		out_filename = f'{utils.get_out_dir()}/files_for_3mm_intersect_mask.txt'
		if VERBOSE: print(f'writing {len(all_filenames)} names to {out_filename}')
		write_filelist(out_filename, all_filenames)
	else:
		tasks = utils.get_tasks()
		for t in tasks:
			subject_list = INFANT_SUBJECTS_TASKS[t]
			fns = utils.get_task_filenames(subject_list, t)
			out_filename = f'{utils.get_out_dir()}/files_for_intersect_mask_{t}.txt'
			write_filelist(out_filename, fns)
			
