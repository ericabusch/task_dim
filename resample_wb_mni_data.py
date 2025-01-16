# resample from high resolution to 3mm MNI space, to match rest-movie dataset
import numpy as np
import os,sys,glob,argparse
from config import *
import nibabel as nib
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker

from nilearn.datasets import load_mni152_template
from nilearn.image import resample_to_img


def run_resampling(infilename, outfilename, maskfilename, template):
    orig = nib.load(infilename)
    # apply wb mask
    mask = nib.load(maskfilename)
    masker_wb = NiftiMasker(mask_img=mask, standardize=True)
    masked_normed = masker_wb.fit_transform(orig)
    masked_orig = masker_wb.inverse_transform(masked_normed)
    # resample to lower dim
    resampled = resample_to_img(orig, template, interpolation="nearest", force_resample=True)
    nib.save(resampled, outfilename)
    if VERBOSE: print(f'saved to {outfilename}, shape {resampled.shape}')

def write_filelist(out_filename, list_of_files):
    with open(out_filename, 'w') as f:
        for fn in list_of_files:
            f.write(fn+'\n')
    if VERBOSE: print(f'wrote to {out_filename}')

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dataset',type=str)
    parser.add_argument('-v','--verbose', type=int, default=1)
    parser.add_argument('-r', '--resolution', type=int, default=3)
    p = parser.parse_args()

    if p.dataset.lower() == 'narratives': import narratives_utils as utils
    elif p.dataset.lower() == 'cneuromod': import CNM_utils as utils
    else: print(f'{p.dataset} not valid');  sys.exit(1)
    if p.verbose: print(f'loaded {p.dataset} utils')

    template = load_mni152_template(p.resolution)
    subject_list = utils.get_intersecting_subjects()

    new_filenames = []

    for task in utils.get_tasks():
        for sub_id in subject_list:
            nii_fns, conf_fns, new_fns, mask_fns = utils.get_subject_data_fmriprep_output(sub_id, task)
            for nifn, confn, newfn, masfn in zip(nii_fns, conf_fns, new_fns, mask_fns):
                run_resampling(nifn, newfn, masfn, template)
                new_filenames.append(newfn)
    # write out files to intersect mask
    out_filename = f'{utils.get_out_dir()}/files_for_3mm_intersect_mask.txt'
    write_filelist(out_filename, new_filenames)
