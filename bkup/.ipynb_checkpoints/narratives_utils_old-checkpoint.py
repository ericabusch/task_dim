import json
from os.path import join
import nibabel as nib
from config import *

target_tasks = ['black','bronx','forgot','piemanpni'] # have 45 overlapping subjects
datalad_dir = '/gpfs/milgram/scratch60/turk-browne/elb77/Narratives/narratives'

def get_intersecting_subjects(narratives_dir=None, task_list=[]):
    '''
    from TLB
    
    Find subjects intersecting across narratives tasks.

    Inputs:
        - narratives_dir: base directory of the Narratives dataset
        - task_list: list of tasks to find intersecting subjects across.

    Outputs:
        - intersection: a sorted list of subject names across tasks.
    '''
    if not narratives_dir:
        narratives_dir = datalad_dir
    if len(task_list) == 0:
        task_list = intersect_tasks
    #load the information of which subjects did which tasks
    with open(join(narratives_dir, 'code', 'task_meta.json')) as f:
        task_meta = json.load(f)

    #find each task we're curious about in the meta file
    task_info = list(map(task_meta.get, task_list))

    # take the intersection of subjects between 
    intersection = set.intersection(*map(set, map(dict.keys, task_info)))

    return sorted(list(intersection))

def get_mask():
    '''
    TLB Generated this mask
    '''
    dirname = './masks'
    fn = f'{dirname}/group-MNI152NLin2009cAsym_res-black-bronx-forgot-piemanpni_desc-brain_mask-group.nii.gz'
    return nib.load(fn)

def get_subject_data(sub_id, task):
    fn = glob.glob(NARRATIVES_DATA_DIRS[task.upper()]+f'/sub-{sub_id}*.nii.gz')[0]
    nii = nib.load(fn)
    return nii

def get_brain_cmap(mpl_colorname='inferno'):
    n = 40
    color_list = sns.color_palette(mpl_colorname,n)[0:n]
    indices = np.concatenate((np.arange(n-1, -1, -1), np.arange(0, n,1)))
    brain_cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", [color_list[i] for i in indices])
    return brain_cmap