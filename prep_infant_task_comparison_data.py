import numpy as np
import pandas as pd
import infant_restmovie_config as config
import infant_restmovie_utils as utils
from nilearn import image 
import nibabel as nib
from nilearn.masker import NiftiMasker

task0 = 'sleep'
task1='aeronaut'
main_mask = utils.create_task_intersect_mask(task0, task1)
masker = NiftiMasker(mask_img=main_mask)
stacked_volumes = []
task_labels = []
subjects0 = utils.get_intersecting_subjects(task0)
subjects1 = utils.get_intersecting_subjects(task1)

for sub in subjects0:
    v = utils.get_metric_SL_nii_subject(sub, task0, metric='TPHATE_DiffOp_IDE')
    stacked_volumes.append(v)
    task_labels.append(1)

for sub in subjects1:
    v = utils.get_metric_SL_nii_subject(sub, task1, metric='TPHATE_DiffOp_IDE')
    stacked_volumes.append(v)
    task_labels.append(-1)

stacked_volumes = image.concat_imgs(stacked_volumes)
masked_flatten = masker.fit_transform(stacked_volumes)
masked_volumes = masker.inverse_transform(masked_flatten)
masked_volumes.to_filename(f'{config.get_results_dir()}/task_comparison/{task0}_{task1}_data_masked.nii.gz')
