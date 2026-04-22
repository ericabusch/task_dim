from os.path import join
import numpy as np
import os

NJOBS=16
VERBOSE=True

# check if running on milgram or misha
if 'milgram' in os.uname()[1]:
    ROOT = '/gpfs/milgram/project/turk-browne/users/elb77/'
    SCRATCH_DIR = '/gpfs/milgram/scratch60/turk-browne/elb77/task_dim_sandbox'
else:
    ROOT = '/gpfs/radev/home/elb77/project/task_dim'
    SCRATCH_DIR = f'/gpfs/radev/scratch60/turk-browne/elb77/task_dim_sandbox'

KNN=5
THRESHOLD=0.9
IDE_METHODS = ['TPHATE_DiffOp_IDE','PHATE_DiffOp_IDE', 'MiND_ML','PCA','MLE','lPCA']
DATASET_NAME='infant_restmovie'
# 
INFANT_SLEEP_DIR='/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Infant_Sleep/preprocessed_standard/nonlinear_alignment/'
AERONAUT_B_RM_DIR='/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Infant_Aeronaut/preprocessed_standard/nonlinear_alignment/'
MICKEY_B_RM_DIR='/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Infant_Mickey/preprocessed_standard/nonlinear_alignment/'
RM_INFANT_OUTDIR = f'{ROOT}/task_dim/infant_restmovie'
RM_INFANT_DATA_DIRS={'sleep':INFANT_SLEEP_DIR, 'aeronaut':AERONAUT_B_RM_DIR, 'mickey':MICKEY_B_RM_DIR}
RM_INFANT_STRING_MATCH={t:'*_fslmotion_thr0.2_Only.nii.gz' for t in RM_INFANT_DATA_DIRS.keys()}#'aeronaut':'Z','mickey':'Z'}

SLEEP_INFANT_SUBJECTS_2 = ['s0307_1_1', 's2307_1_1', 's8187_1_4', 's4107_1_1', 's8687_2_2',
       's2057_1_2', 's6057_1_4', 's6057_1_7', 's2067_1_2', 's2097_1_4',
       's3097_1_4', 's3097_1_4', 's5927_1_1', 's9986_1_1', 's9986_1_4',
       's9986_1_5', 's2986_1_1', 's2986_1_2', 's7286_2_2', 's7286_2_3']

# the ones that were only included in the RM dataset -- use these subjects, with repeats
AERO_INFANT_RM_SUBSET_2 = ['s8687_1_3', 's8687_1_4', 's8687_1_5', 's8687_1_7', 's8687_2_1',
       's6687_1_3', 's6687_1_4', 's6687_1_5', 's6687_1_6', 's4607_1_5',
       's6607_1_2', 's0607_1_2', 's1607_1_4', 's3607_1_2', 's2057_1_2',
       's6057_1_1', 's6057_1_2', 's0057_1_3', 's7017_1_1', 's7017_1_2',
       's8037_1_2', 's2037_1_2', 's5037_1_1', 's7067_1_3', 's4047_1_1',
       's3097_1_1']
MICKEY_INFANT_RM_SUBSET_2 =['s0307_2_1', 's0307_2_1', 's8187_1_8', 's2307_1_2', 's2307_1_2',
       's6687_1_1', 's8687_1_2', 's0687_1_2']
RM_INFANT_OVERLAPPING_SUBJECTS = {'mickey_sleep': ['s8187_1','s2307_1'], 
'aeronaut_sleep':['s8687_2','s2057_1','s6057_1','s3097_1'], 
'aeronaut_mickey':['s6687_1','s8687_1']}

INFANT_SUBJECTS_TASKS = {"sleep": SLEEP_INFANT_SUBJECTS_2, 
						 "aeronaut":AERO_INFANT_RM_SUBSET_2, 
						 "mickey":MICKEY_INFANT_RM_SUBSET_2} # all mickey infants saw it twice in a row (148 trs) so just include 74

SLEEP_INFANT_INTERSECT_MASK = f'{RM_INFANT_OUTDIR}/masks/InfantRestMovie_intersect_mask_sleep.nii.gz'
AERONAUT_INFANT_INTERSECT_MASK = f'{RM_INFANT_OUTDIR}/masks/InfantRestMovie_intersect_mask_aeronaut.nii.gz'
MICKEY_INFANT_INTERSECT_MASK = f'{RM_INFANT_OUTDIR}/masks/InfantRestMovie_intersect_mask_mickey.nii.gz'

INFANT_INTERSECT_MASKS = {"sleep":SLEEP_INFANT_INTERSECT_MASK, "aeronaut":AERONAUT_INFANT_INTERSECT_MASK,"mickey": MICKEY_INFANT_INTERSECT_MASK}
SLEEP_TIMEPOINTS = np.array([ 66,  61, 179,  62, 157,  86, 151, 151, 153, 155, 150, 150, 151, 155, 155, 153,  97, 155, 161, 162])
RM_INFANT_TIMEPOINTS={'sleep':61, 'aeronaut':93, 'mickey':74}
RM_INFANT_RESULTS_DIR = f'{RM_INFANT_OUTDIR}/results/'
RM_INFANT_MULTIPLE_FILES = {"sleep": {"s2986_1":4, "s3097_1":2, "s6057_1":4, "s7286_2":2, "s9986_1":3}, 
"mickey": {"s0307_2":2, "s2307_1":2},
'aeronaut':{'s1607_1':2, 's6057_1':2, "s6687_1":4, "s7017_1":2, "s8687_1":4}}



INFANT_AERO_DIR = '/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/Movies/Aeronaut/preprocessed_standard/nonlinear_alignment/'
INFANT_MICKEY_DIR = '/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/Movies/Mickey/preprocessed_standard/nonlinear_alignment/'



# this is without the session number per infant
SLEEP_INFANT_SUBJECTS = ["s0307_1", "s2057_1","s2067_1","s2097_1","s2307_1","s2986_1","s2986_1","s3097_1", "s4107_1", "s5927_1", "s6057_1", "s6057_1", "s7286_2", "s8187_1", "s8687_2", "s9986_1"]
# the ones that were only included in the RM dataset -- use these subjects
AERO_INFANT_RM_SUBSET= ["s0057_1", "s0607_1", "s1607_1", "s2037_1", "s2057_1", "s3097_1", "s3607_1", "s4047_1", "s4607_1", "s5037_1","s6057_1","s6607_1","s6687_1","s7017_1","s7067_1","s8037_1","s8687_1"]
MICKEY_INFANT_RM_SUBSET=["s0307_2","s2307_1","s6687_1","s8187_1","s8687_1"]





# This is the full dataset -- dont use!
MICKEY_INFANT_SUBJECTS = ['s0307_1','s0307_2','s0687_1','s1187_1','s2307_1','s2687_1',
's5187_1','s5687_1','s6607_1','s6687_1','s8187_1','s8607_1','s8687_1']
AERO_INFANT_SUBJECTS = ['s0057_1','s0607_1','s0687_1','s1607_1','s2037_1','s2047_1','s2057_1','s2067_1','s2097_1','s2687_1','s3097_1','s3607_1','s4047_1','s4607_1','s5037_1','s6017_1',
's6057_1','s6607_1','s6687_1','s6687_1','s7017_1','s7057_1','s7067_1','s8037_1','s8077_1','s8687_1','s8687_2','s9057_1']
INFANT_PARTICIPANT_DATA = {'sleep':'/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Infant_Sleep/infant_sleep_participants.csv',
 'aeronaut':'/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Infant_Aeronaut/infant_aeronaut_participants.csv',
 'mickey':'/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Infant_Mickey/infant_mickey_participants.csv'
 }
