from os.path import join, splitext, basename, exists
import sys, glob
import numpy as np
import pandas as pd
from functools import reduce
from math import ceil
from file_utils import *
from scipy.stats import zscore
import json
import argparse
import nltk
from nlp_utils import get_word_clusters
from itertools import groupby

def get_parser():
	"""
	Parse command line inputs for this function.

	Returns
	-------
	parser.parse_args() : argparse dict

	Notes
	-----
	# Argument parser follow template provided by RalphyZ.
	# https://stackoverflow.com/a/43456577
	"""
	parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
	optional = parser._action_groups.pop()
	required = parser.add_argument_group("Required Argument:")
	
	def convert_arg_line_to_args(arg_line):
		for arg in arg_line.split():
			if not arg.strip():
				continue
			yield arg
			
	parser.convert_arg_line_to_args = convert_arg_line_to_args
	
	required.add_argument(
		'--base_dir', 
		dest='BASE_DIR', 
		type=str, 
		nargs=1, 
		help="The path to the project directory.", 
		required=True
	)
	required.add_argument(
		'--narratives_dir',
		dest='NARRATIVES_DIR',
		type=str, 
		nargs=1,
		help="The path to the narratives dataset directory.", 
		required=True
	)
	required.add_argument(
		'--scratch_dir', 
		dest='SCRATCH_DIR', 
		type=str, 
		nargs=1,
		help='The path to a scratch directory where temporary files can be placed.', 
		required=True
	)
	required.add_argument(
		'--task_list', 
		dest='TASK_LIST', 
		nargs='+', 
		help='The tasks considered for this set of analyses.', 
		required=True
	)
	required.add_argument(
		'--analysis_name', 
		dest='ANALYSIS_NAME', 
		nargs='+', 
		help='The name of the current analysis. This will be used to set up directory structures.', 
		required=True
	)
	required.add_argument(
		'--signal_type', 
		dest='SIGNAL_TYPE', 
		type=str, 
		nargs=1, 
		help='The type of data to use for analyses.', 
		choices=['bold', 'bold-srm', 'bold-zscore', 'bold-srm_schaefer2018'], 
		required=True
	)
	required.add_argument(
		'--models', 
		dest='MODELS', 
		nargs='+',
		help='The type of GLM model to run for our data', 
		required=True
	)

	parser.add_argument_group("Optional Arguments:")  

	required.add_argument(
		'--zscore', 
		dest='ZSCORE',
		default=False,
		action='store_true',
		help='Whether or not to zscore regressors before running GLM.'
	)

	required.add_argument(
		'--impulse_function', 
		dest='IMPULSE_FUNCTION', 
		type=str, 
		nargs=1, 
		help="The impulse function for the GLM.", 
		required=True
	)
	optional.add_argument(
		'--filter_pos',
		dest='FILTER_POS',
		type=str, 
		nargs=1, 
		help='Apply filtering to words based on a part of speech.', 
		default=None
	)
	optional.add_argument(
		'--afni_pipe',
		dest='AFNI_PIPE',
		type=str, 
		nargs=1, 
		help='The type of preprocessed data to use for analyses. Default is smoothed data.', 
		default='afni-smooth'
	)
	optional.add_argument(
		'--space', 
		dest='SPACE', 
		type=str, 
		nargs=1,
		help='The space (standard/subject) of the data. Default is MNI152NLin2009cAsym.', 
		default='MNI152NLin2009cAsym',
	)
	optional.add_argument(
		"--coverage_threshold",
		dest="COVERAGE_THRESHOLD",
		type=int, 
		nargs=1,
		help="The percent coverage per ROI required to perform analyses.", 
		default=0.75
	)
	optional.add_argument(
		"--regressors",
		dest="REGRESSORS",
		nargs='+',
		help="The regressors to use in our model. This will vary depending on the analysis type.",
		default=["concreteness", "semd", "prevalence", "valence", "arousal", "dominance"]
	)
	optional.add_argument(
		"--regressors_of_interest",
		dest="REGRESSORS_OF_INTEREST",
		nargs='+',
		help="A list of regressors to use for univariate contrasts. Must be a subset of --regressors",
		default=["concreteness", "semd", "valence"]
	)
	optional.add_argument(
		"--features",
		dest="N_FEATURES",
		type=int,
		nargs=1,
		help="The number of SRM features to use (default is 50).",
		default=50,
	)
	optional.add_argument(
		"--iterations",
		dest="N_ITER",
		type=int,
		nargs=1,
		help="The number of iterations to use (default is 10).",
		default=10,
	)
	optional.add_argument(
		"--parcels",
		dest="N_PARCELS",
		type=int,
		nargs=1,
		help="The number of parcels to use (default is 100).",
		default=100,
	)
	optional.add_argument(
		"--concreteness_contrast_clusters",
		dest="CONCRETENESS_CONTRAST_CLUSTERS",
		type=int,
		nargs=1,
		help="If performing the concreteness contrast with clustering, the number of clusters to use.",
		default=2
	)
	optional.add_argument(
		"--timechunk_regressor",
		dest="TIMECHUNK_REGRESSOR",
		type=str,
		nargs=1,
		help="If performing time chunk analysis, the regressor to focus on.",
	)
	optional.add_argument(
		"--timechunk_percent",
		dest="TIMECHUNK_THRESHOLD_PERCENT",
		type=int,
		nargs=1,
		help="If performing time chunk analysis, the threshold percentile.",
	)
	optional.add_argument(
		"--timechunk_window_size",
		dest="TIMECHUNK_WINDOW_SIZE",
		type=int,
		nargs=1,
		help="If performing time chunk analysis, set the size of the smoothing window in seconds.",
	)
	
	optional.add_argument(
		"--concreteness_contrast_controls",
		dest="CONCRETENESS_CONTRAST_CONTROLS",
		type=str,
		nargs='+',
		help="The control regressors to add to the concreteness contrast.",
		default=[]
	)

	optional.add_argument(
		"--models_dir",
		dest="MODELS_DIR",
		type=str,
		nargs=1,
		help="The directory where NLP models are downloaded and loaded.",
		default=''
	)
	
	optional.add_argument(
		"--model_name",
		dest="MODEL_NAME",
		type=str,
		nargs=1,
		help="The name of the NLP model to load.",
		default=''
	)
	
	return parser

def post_process_kwargs(kwargs):
	
	str_map = lambda x: ' '.join(x) if isinstance(x, list) else x
	float_map = lambda x: float(x) if isinstance(x, list) else float(x)
	int_map = lambda x:  x[0] if isinstance(x, list) else x
	sorted_list = lambda x: sorted(x)
	
	type_fns = {'AFNI_PIPE': str_map,
				'BASE_DIR': str_map,
				'NARRATIVES_DIR': str_map,
				'MODELS_DIR': str_map,
				'SPACE': str_map,
				'TASK_LIST': sorted_list,
				'COVERAGE_THRESHOLD': float_map,
				'N_PARCELS': int_map,
				'N_FEATURES': int_map,
				'N_ITER': int_map,
				'SCRATCH_DIR': str_map,
				'SIGNAL_TYPE': str_map,
				'CONCRETENESS_CONTRAST_CLUSTERS': int_map,
				'MODEL_NAME': str_map,
				'IMPULSE_FUNCTION': str_map,
				'FILTER_POS': str_map,
				'TIMECHUNK_REGRESSOR': str_map,
				'TIMECHUNK_WINDOW_SIZE': int_map,
				'TIMECHUNK_THRESHOLD_PERCENT': int_map,
	}
	
	for arg in vars(kwargs):
		attr = getattr(kwargs, arg)
		if arg in type_fns.keys():
			setattr(kwargs, arg, type_fns[arg](attr))

	if (str(kwargs.N_PARCELS) not in kwargs.SIGNAL_TYPE) and ('schaefer2018' in kwargs.SIGNAL_TYPE) :
		kwargs.SIGNAL_TYPE = kwargs.SIGNAL_TYPE + f'-{kwargs.N_PARCELS}parcels'
	
	if kwargs.SIGNAL_TYPE not in kwargs.ANALYSIS_NAME:
		kwargs.ANALYSIS_NAME.append(kwargs.SIGNAL_TYPE)

	if 'timechunk' in kwargs.ANALYSIS_NAME:
		kwargs.ANALYSIS_NAME.append(f'windowsize_{kwargs.TIMECHUNK_WINDOW_SIZE}')
	
	return kwargs

def get_intersecting_subjects(narratives_dir, task_list):
	'''
	Find subjects intersecting across narratives tasks.
	
	Inputs:
		- narratives_dir: base directory of the Narratives dataset
		- task_list: list of tasks to find intersecting subjects across.
		
	Outputs:
		- intersection: a sorted list of subject names across tasks.
	'''
	
	#load the information of which subjects did which tasks
	with open(join(narratives_dir, 'code', 'task_meta.json')) as f:
		task_meta = json.load(f)
		
	#find each task we're curious about in the meta file
	task_info = list(map(task_meta.get, task_list))
	
	# take the intersection of subjects between 
	intersection = set.intersection(*map(set, map(dict.keys, task_info)))
	
	return sorted(list(intersection))

def preproc_narrative_transcript(narratives_dir, task, word_time='Onset'):
	from text_utils import get_pos_tags, get_lemma
	# tagset gives you explanations of each of the POS tags
	tags_explained = nltk.data.load('help/tagsets/upenn_tagset.pickle')

	# path to the directory of transcripts --> load gentle align file containing words and timings
	gentle_dir = join(narratives_dir, 'stimuli', 'gentle')
	gentle_timings = load_gentle_align(gentle_dir, task)
	
	#get the times and text from the aligned file
	#get the times and text from the aligned file
	times = gentle_timings[word_time].to_numpy()
	durations = gentle_timings['duration'].to_numpy()
	text = [' '.join(gentle_timings['Word-Written'].tolist())]
	
	#get POS tags -> we don't need to strip punctuation because we created the transcript from separate words (no punc)
	words, tags = zip(*get_pos_tags(text, strip_punc=False))
	
	# use the word tags to get lemmas, zip together with the time at which the word occurred
	lemmas = [get_lemma(word, tag) for word, tag in zip(words, tags)]
	
	# get parts of speech
	pos = [tags_explained[tag][0].split(',')[0] for tag in tags]
	
	return times, durations, words, lemmas, pos

def get_events_timings(path, sub, task, delimiter=None):
	events_fname = join(path, f'{sub}', 'func', f'{sub}_task-{task}_events.tsv')
	
	return pd.read_csv(events_fname,delimiter=delimiter)

def load_word_metrics(path):
	'''
	Load specified word metrics.
	
	Parameters
	----------
	path : str
		Path to the metrics files

	Returns
	-------
	metric_dict : dict
		A dictionary with metric names as keys and associated pandas
		DataFrame as values.
	
	'''

	#list of our metrics of interest paired with columns of dataframe to select for measures
	metrics = {
		'concreteness': ['Conc.M'],
		'prevalence': ['Prevalence', 'FreqZipfUS'],
		'valence': ['V.Mean.Sum', 'A.Mean.Sum', 'D.Mean.Sum'],
		'semantic_diversity': ['SemD']
	}
	
	metric_dict = {m: load_csv(path, m) for m in metrics.keys()}

	#fix semd dataframe to match the other metrics
	metric_dict['semantic_diversity'] = metric_dict['semantic_diversity'].dropna(how='all').dropna(axis=1, how='all').rename(columns={'!term':'Word'})

	#to generate a merged dataframe, then set the index to words and set column names
	common_metrics = get_merged_df(metrics, metric_dict, common_col='Word', how='outer')
	common_metrics = common_metrics.set_index('Word')
	common_metrics.columns = ['concreteness', 'prevalence', 'frequency', 'valence', 'arousal', 'dominance', 'semd']
	
	return common_metrics

def get_common_items(metric_dict, common_col):
	'''
	From the metrics that were loaded, find common words across datasets
	with associated measures.
	
	Parameters
	----------
	metric_dict : dict
		The return of load_metrics. A dictionary with metric names as 
		keys and and associated pandas DataFrame as values. Return of
		load_metrics.
		
	common_col : str
		A column to compare across metric DataFrames.
		
	Returns
	-------
	common_items : list of str
		Common items shared across metric DataFrames.
		
	'''
	
	for i, metric in enumerate(metric_dict):
		if i == 0:
			common_items = set(metric_dict[metric][common_col])
			continue

		common_items = common_items.intersection(metric_dict[metric][common_col])
	
	#remove first item (returning nan)
	return list(common_items)[1:]

def get_merged_df(metrics, metric_dict, common_col, how='outer'):
	'''
	Get a single DataFrame of all requested metrics.
	
	Parameters
	----------
	
	metrics : dict
		A dictionary containing an identifier for each metric and the
		named column(s) of the loaded metric file containing the measure(s)
		of interest.
		
	metric_dict : dict
		The return of load_metrics. A dictionary with metric names as 
		keys and and associated pandas DataFrame as values. Return of
		load_metrics.
		
	common_col : str
		A column shared across all metrics to compare and merge over.
		
	how : str
		The type of merge to be conducted. Options are 'inner', 'left',
		'right', 'outer', and 'cross'. 
		
		
	Returns
	-------
	df : pandas DataFrame
		Merged DataFrame composed of the ones provided within metric_dict.
	
	'''
	df_stack = []
	for metric, df in metric_dict.items():
		cols = [common_col, *metrics[metric]]
		metric_cols = [*metrics[metric]]

		df_trimmed = df[cols]
		df_stack.append(df_trimmed)

	df = reduce(lambda df1,df2: pd.merge(df1,df2, how=how), df_stack)
	
	return df

def load_gentle_align(path, task):
	# use gentle file as transcript so number of words is the same
	gentle_fname = 'align'
	gentle_align_path = join(path, task)

	gentle_columns = ['Word-Written', 'Word-Vocab', 'Onset', 'Offset']

	#load the aligned timings of each word to the stimulus 
	gentle_timings = load_csv(gentle_align_path, gentle_fname, columns=gentle_columns)

	#average onset and offset to get midpoint of each word
	gentle_timings['avg'] = gentle_timings[['Onset', 'Offset']].mean(axis=1)
	gentle_timings['duration'] = gentle_timings['Offset'] - gentle_timings['Onset']

	#drop words we don't have timings for cause we can't align measures to stimulus
	gentle_timings = gentle_timings.dropna()
	
	return gentle_timings

def filter_pos(df, pos_list, pos_filter):
	df = df.dropna(how='all')
	df['pos'] = pos_list
	df = df[df['pos'] == pos_filter]
	df = df.drop('pos', axis=1)
	return df

def make_top_bottom_word_regressors(df, words, percent, regressor, keep_cols=[]):
	
	df['words'] = words
	df_temp = df[[regressor, 'words']].dropna().drop_duplicates().sort_values(by=regressor, ascending=False)
	df_temp[[*keep_cols]] = df[[*keep_cols]]
	df = df_temp
	
	# take the top the top words and replace concreteness values with 1
	top_df = df.head(round(len(df)*(percent/100)))
	top_df[regressor] = 1

	# grab the top words
	top_words = top_df['words'].to_frame()
	
	# take only the concreteness regressor and turn into column
	top_df = top_df[[regressor, *keep_cols]]
	top_df.columns = [f'{regressor}-top-{percent}perc', *keep_cols]
	
	# grab the regressor values for bottom words and turn into a separate frame
	bottom_df = df.tail(round(len(df)*(percent/100)))
	bottom_df[regressor] = 1

	# grab the bottom words
	bottom_words = bottom_df['words'].to_frame()

	bottom_df = bottom_df[[regressor, *keep_cols]]
	bottom_df.columns = [f'{regressor}-bottom-{percent}perc', *keep_cols]

	# #merge back into a single dataframe
	df_regressor = pd.concat([top_df, bottom_df], axis=0).sort_index()
	df_words = pd.concat([top_words, bottom_words], axis=0).sort_index()

	return df_regressor, df_words

def make_top_bottom_clusters(df, cluster_cols, words, word_groups, model, clustering, keep_cols=[], norm=True):
	
	'''
	Cluster words in the top-bottom word DataFrame. Returns
	a DataFrame with regressors divided as clusters.
	'''
	df_vals = []
	df_words = []

	# we will cluster each column
	for col in cluster_cols:

		# find the indices for the given column
		col_idxs = df.index.get_indexer(df[df[col]==1].index)

		# select the words and which story they belong to
		col_words = words[col_idxs]
		col_groups = word_groups[col_idxs]
		col_values = df.iloc[col_idxs][[*keep_cols, col]].values

		# for the set of words, create k number of clusters
		# keep the labels so we can understand the assignment of stories to words
		word_clusters, labels, _ = get_word_clusters(model=model, cluster=clustering, words=col_words)

		# create a dataframe containing all of the info about words, their clusters, story, and times
		df_col = pd.DataFrame([*col_values.T, col_groups, labels, col_words]).T
		df_col.columns = [*keep_cols, 'value', 'group', 'cluster', 'word']
		df_col.index = col_idxs # set indices to match the original dataframe

		# go through each current cluster
		for c in df_col['cluster'].unique():
			col_name = '-'.join([col, f'WC{c+1}']) # create the name for the column

			# slide the dataframe based on cluster --> keep time, value and story
			temp_vals = df_col[df_col['cluster']==c][[*keep_cols, 'value', 'group']]
			temp_vals.columns = [*keep_cols, col_name, 'group']

			temp_words = df_col[df_col['cluster']==c][['word', 'group']]
			temp_words.columns = [col_name, 'group']

			# add to the overall dataframe stack
			df_vals.append(temp_vals)
			df_words.append(temp_words)

	# # create a single dataframe reorganized with column names as word clusters
	vals_stack = pd.concat(df_vals).sort_index()
	words_stack = pd.concat(df_words).sort_index()
	stack = [vals_stack, words_stack]
	
	# divide the dataframes into groups
	group_vals, group_words = [[d[d['group']==s].drop('group',axis=1) for s in np.unique(word_groups)] for d in stack]
	
	return group_vals, group_words

def smooth_regressor(df, onsets, offset, window_size):
	'''
	Smooth regressors over a given timewindow (in seconds)
	Smoothing will occur over the columns axis
	'''
	
	arr = df.to_numpy().T
	
	# preallocate array to fill with smoothed values
	timeseries = np.empty((arr.shape[0], offset))
	timeseries[:] = np.nan
	
	for i in range(offset - window_size):
		# create the current timewindow
		window = np.logical_and(onsets >= i, onsets < i + window_size)
		
		# average over the window --> insert the values at the timepoint halfway through the window
		timeseries[:, i + window_size//2] = np.nanmean(arr[:, window], axis=1)
		
	df_smooth = pd.DataFrame(np.nan_to_num(timeseries).T, columns=[*df.columns])
		
	return df_smooth

def get_consecutive_chunks(seq, min_length=0, max_length=None):
	'''
	Find indices and lengths of consecutive True boolean chunks
	'''
	# if there's no max length, longest max is the whole sequence
	if not max_length:
		max_length = len(seq)
	
	chunks = []
	
	for k, g in groupby(enumerate(seq), lambda x:x[1]):
		if k:
			ind, bools = list(zip(*g))
			
			if (sum(bools) >= min_length and sum(bools) <= max_length):
				chunks.append((ind, sum(bools)))
	
	indices, lengths = zip(*chunks)
	return indices, lengths

def make_top_bottom_timechunks(df, regressor, percent, min_length=0, max_length=None, equal_lengths=True, max_indices=None, random_seed=None):
	
	# get top and bottom thresholds
	top_threshold = np.percentile(df, 100-percent, axis=0)
	bottom_threshold = np.percentile(df, percent, axis=0)
	
	# threshold dataframe for all regressors
	df_top_threshold = df >= top_threshold
	df_bottom_threshold = df <= bottom_threshold
	
	# get top bottom time chunks
	top_indices, _ = get_consecutive_chunks(df_top_threshold[regressor], min_length=min_length, max_length=max_length)
	bottom_indices, _ = get_consecutive_chunks(df_bottom_threshold[regressor], min_length=min_length, max_length=max_length)
	
	if equal_lengths:
		if not max_indices:
			max_indices = min([len(top_indices), len(bottom_indices)])

		# we set the random seed to ensure consistency between script runs
		np.random.seed(random_seed)
		
		# make sure the two arrays are the same sizes --> sample randomly
		top_indices = sorted(np.random.choice(top_indices, size=max_indices, replace=False))
		bottom_indices = sorted(np.random.choice(bottom_indices, size=max_indices, replace=False))
	
	df_top_chunks = get_timechunk_df(df[regressor], top_indices, col_name_base=f'{regressor}-top-{percent}perc')
	df_bottom_chunks = get_timechunk_df(df[regressor], bottom_indices, col_name_base=f'{regressor}-bottom-{percent}perc')
	
	return pd.concat([df_top_chunks, df_bottom_chunks]).sort_index(), max_indices

def get_timechunk_df(df, chunk_indices, col_name_base=None):
	'''
	Go through a list of timechunk indices, make a dataframe for each timechunk
	'''
	dfs = []
	
	for i, idxs in enumerate(chunk_indices):
		# if a name base was supplied, join the strings
		col_name = '-'.join([col_name_base, f'TC{i+1}']) if col_name_base else f'TC{i+1}'
		
		# make array of value, onset, duration
		# set the values at the starting index
		temp = pd.DataFrame(np.nan, index=range(1, len(df)+1), columns=[col_name, 'onset', 'duration'])
		temp.iloc[idxs[0]-1].at[col_name, 'onset', 'duration'] = [1, idxs[0], len(idxs)]
		dfs.append(temp)
		
	return pd.concat(dfs).dropna(how='all')

def derive_audiorms(path, fname):
	import librosa
	
	task_audio = join(path, fname)

	#use the native audio sampling rate to load in file
	audio, sr = librosa.load(task_audio, sr=None)
	
	#get the duration of the audio in s
	end_time = librosa.get_duration(audio, sr=sr)

	# this will generate a value every 0.25s
	audio_rms = librosa.feature.rms(audio, frame_length=sr, hop_length=int(sr/4)).flatten()[:-1]

	# create a timeseies for each rms value
	timeseries = np.arange(end_time, step=end_time/audio_rms.shape[0])
	
	#stack the times with the rms and make vertical
	return timeseries, audio_rms

def add_array_noise(array, sigma=0.25, mask=None):
	#create independent noise (drawn from gaussian distribution) -> do this for each regressor
	epsilon = sigma*np.random.randn(*array.shape)
	
	if mask is None:
		mask = np.ones(*array.shape)
		
	array[mask] = array[mask] + epsilon[mask]
	
	return array

def build_design_matrix(stimuli, times, measures, missing_val=np.nan, build_smooth_matrix=False):
	'''
	Given a list of stimuli and a lookup table of measures, build a design 
	matrix for the given stimuli.
	
	Parameters
	----------
	
	stims_times : list of tuples
		List of (stimulus, time) pairings. Each stimulus has an associated 
		time as a tuple.
		
	measures : pandas DataFrame
		A lookup table for the stimuli. Columns are measures and rows are 
		instances of the stimuli.
		
	missing_val: int
		For any value without a measure, use this value (e.g., nan, 0) to 
		fill the design matrix.
		
	Returns
	-------
	design_matrix : np.array
		An array composed of measures for any stimuli that existed in the
		lookup table.
	
	'''

	# create an empty matrix that we will fill with values sampled from our common metrics
	regressors = np.empty((len(stimuli), measures.shape[1]))

	# for each item in our list (whether it has a lemma or not -> this is necessary to align
	# to the fmri TRs)
	stim_ids = []
	
	for i, stim in enumerate(stimuli):
		# if word was a stopword or lemma was not found in the common metrics
		# just add a nan value across the design matrix
		if stim is None or not any(measures.index == stim):
			regressors[i,:] = missing_val #np.nan
			continue

		#otherwise values exist and we sample from our current metrics to fill the design matrix
		regressors[i,:] = measures[measures.index == stim].to_numpy()
		stim_ids.append(i)

	stim_ids = np.asarray(stim_ids)

	if build_smooth_matrix:
		#next build out the design matrix to a smooth form
		#time in seconds from start to finish of the stimulus
		timeseries=np.arange(ceil(times[-1]) + 1).astype(float)
		design_matrix=np.empty((regressors.shape[1], len(timeseries)))
		
		#fill the matrix from the start
		design_matrix[:] = missing_val
		
		#next, insert regressor values at given time points
		for i, time in enumerate(times):
			#find the nearest item to our current time
			nearest_time = np.where(time <= timeseries)[0][0]

			#sometimes the times may be equal
			if time == timeseries[nearest_time]:
				#just idx into the current time instead of inserting an element
				timeseries[nearest_time] = time
				design_matrix[:,nearest_time] = regressors[i,:]
				continue

			#update the timeseries to contain that time
			timeseries=np.insert(timeseries, nearest_time, time)

			#then insert the design matrix regressors onto the simulated timeseries
			design_matrix=np.insert(design_matrix, nearest_time, regressors[i,:], axis=1)
	else:
		timeseries = times
		design_matrix = regressors.T
		
	return timeseries, design_matrix, stim_ids