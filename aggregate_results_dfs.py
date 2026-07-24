import numpy as np
import pandas as pd
import argparse
import os, sys, glob 

if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument('-d','--dataset',type=str)
	parser.add_argument('-v','--verbose', type=int, default=1)
	p = parser.parse_args()

	if p.dataset.lower() == 'narratives': import narratives_utils as utils; from naratives_config import *
	elif p.dataset.lower() == 'rest_movie': import adult_restmovie_utils as utils; from adult_restmovie_config import *
	elif p.dataset.lower() == 'infant_rest_movie':  import infant_restmovie_utils as utils; from infant_restmovie_config import *
	elif p.dataset.lower() == 'partly_cloudy':  import partlycloudy_utils as utils; from partlycloudy_config import *
	elif p.dataset.lower() == 'hbn':  import hbn_utils as utils; from hbn_config import * 
	else: print(f'{p.dataset} not valid');  sys.exit(1)

	isc_fns = sorted(glob.glob(f'{utils.get_scratch_dir()}/ISC/LOSO_parcel/results/results_all/*all_ISC_results.csv'))
	ide_fns = sorted(glob.glob(f'{utils.get_scratch_dir()}/IDE/LOSO_parcel/results/*all_IDE_results.csv'))
	print(f'{utils.get_scratch_dir()}/ISC/LOSO_parcel/results/*all_ISC_results.csv')
	if p.verbose: print(f'found ISC={len(isc_fns)} and IDE={len(ide_fns)}')

	# load and reformat files
	major_df = []
	for f in isc_fns:
		temp = pd.read_csv(f,index_col=0)
		if temp['score'][0] == 1: 
			print(f'skipping {f}')
			continue
		regions = temp['region_name'].values
		hemis = [r.split('_')[1] for r in regions]
		networks = [r.split('_')[2] for r in regions]
		temp['metric']=np.repeat('ISC',len(temp))
		temp['file_idx']=np.repeat(0, len(temp))
		temp['dataset']=np.repeat(p.dataset, len(temp))
		temp['network'] = networks
		temp['hemisphere'] = hemis
		temp['is_dim_metric']=np.repeat(0, len(temp))
		if p.dataset.lower()=='partly_cloudy':
			s=f.split('/')[-1].split('_pixar')[0]
			g=utils.get_subject_group(s)
			temp['group']=np.repeat(g,len(temp))
			a = utils.get_subject_age(s)
			temp['age']=np.repeat(a, len(temp))
		if p.dataset.lower() == 'hbn':
			s=f.split('/')[-1].split('_')[0]
			g=utils.get_subject_group(s)
			temp['group']=np.repeat(g,len(temp))
			a = utils.get_subject_age(s)
			temp['age']=np.repeat(a, len(temp))
		major_df.append(temp)

	for f in ide_fns:
		temp = pd.read_csv(f,index_col=0)
		try:
			file_idx = f.split('/')[-1].split('file_idx_')[1].split('_')[0]
		except:
			file_idx=0
		temp.rename(columns={'ide_method': 'metric', 'id_estimate':'score'}, inplace=True)

		temp['file_idx']=np.repeat(file_idx, len(temp))
		temp['dataset']=np.repeat(p.dataset, len(temp))
		regions = temp['region_name'].values
		hemis = [r.split('_')[1] for r in regions]
		networks = [r.split('_')[2] for r in regions]
		temp['network'] = networks
		temp['hemisphere'] = hemis
		temp['is_dim_metric']=np.repeat(1, len(temp))
		if p.dataset.lower()=='partly_cloudy':
			s=f.split('/')[-1].split('_pixar')[0]
			g=utils.get_subject_group(s)
			temp['group']=np.repeat(g,len(temp))
			a = utils.get_subject_age(s)
			temp['age']=np.repeat(a, len(temp))
		if p.dataset.lower() == 'hbn':
			s=f.split('/')[-1].split('_')[0]
			g=utils.get_subject_group(s)
			temp['group']=np.repeat(g,len(temp))
			a = utils.get_subject_age(s)
			temp['age']=np.repeat(a, len(temp))
		major_df.append(temp)

	df = pd.concat(major_df)
	print(f'saving df of shape {df.shape}')
	outfn = f'{utils.get_results_dir()}/parcelwise_results_ISC_IDE.csv'
	df.to_csv(outfn)
	
