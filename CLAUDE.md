# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a neuroimaging research project studying **intrinsic dimensionality (IDE)** of fMRI BOLD signals across developmental datasets. The core question is how neural representational geometry (measured via IDE) varies across tasks (rest vs. naturalistic movie) and ages.

Datasets analyzed: HBN (Healthy Brain Network), Narratives, adult_restmovie, infant_restmovie, CNeuroMod, PartlyCloudy, CamCan.

## Environment

```bash
conda activate dim_env   # primary env (environment.yml)
# Older submit scripts reference: conda activate env_tda
```

Key dependencies: `nilearn`, `nibabel`, `tphate`, `scikit-dimension`, `brainiak` (for searchlight MPI), `mpi4py`, `pingouin`, `statsmodels`, `brainspace`, `neuromaps`.

This code runs on Yale HPC clusters (Milgram or Grace/Radev) but config files also support local execution. Detection order:
1. `'milgram' in os.uname()[1]` → Milgram HPC paths
2. `os.path.exists('/gpfs/radev')` → Grace/Radev HPC paths
3. `else` → local: `ROOT` is set to the parent of the repo using `__file__`, `SCRATCH_DIR` to `task_dim/scratch/` inside the repo

MPI-dependent scripts (`searchlight_IDE_methods.py`, `searchlight_isc.py`) require HPC; atlas/parcelwise scripts can run locally if data is accessible.

## Architecture

### Dataset abstraction pattern

Every dataset has a matching `{dataset}_config.py` and `{dataset}_utils.py`. All utils files expose the same interface:

| Function | Purpose |
|---|---|
| `get_intersecting_subjects(subject_filter)` | Returns sorted list of subject IDs |
| `get_tasks()` | Returns list of task strings |
| `get_subject_data(sub_id, task, ...)` | Loads and returns a NIfTI image |
| `get_intersect_mask(...)` | Returns the group brain mask NIfTI |
| `get_scratch_dir()` | Returns scratch results directory |
| `get_results_dir()` | Returns permanent results directory |
| `has_repeat_files(sub, task)` | Returns 0 or count of repeated runs |

Config files define: `ROOT`, `SCRATCH_DIR`, `KNN`, `THRESHOLD`, `IDE_METHODS`, `TR`.

The analysis scripts import utils dynamically based on a `-d/--dataset` argument:
```python
if p.dataset.lower() == 'hbn': import hbn_utils as utils; import hbn_config as config
```

### Analysis pipeline

1. **Preprocessing**: `clean_fmri_data.py` (confound regression, filtering, smoothing via nilearn); `create_intersect_mask.sh` (FSL-based intersection of brain masks across subjects)

2. **Per-subject dimensionality estimation** (two spatial approaches):
   - `searchlight_IDE_methods.py` — whole-brain searchlight using BrainIAK + MPI (`srun --mpi=pmi2 python -u`)
   - `atlas_IDE_methods.py` — parcelwise (Schaefer 2018 atlas) without MPI

3. **Per-subject ISC** (inter-subject correlation, LOSO):
   - `searchlight_isc.py` — searchlight ISC (MPI)
   - `atlas_isc.py` — parcelwise ISC

4. **Aggregation**:
   - `aggregate_subject_results.py` — stacks per-subject NIfTI/numpy files into group arrays
   - `aggregate_results_dfs.py` — consolidates per-subject CSV result files into one master dataframe

5. **Statistics**: `stats_helpers.py` provides `parcelwise_regression()`, `parcelwise_partial_correlation()`, permutation tests, FDR correction. `parcelwise_regressions.py` and `parcelwise_correlations.py` run these analyses.

6. **Age analyses**: `age_dimensionality.py` correlates IDE maps with age across subjects.

### IDE methods (`ide_helpers.py`)

The `METHODS` dict maps method names to functions. Active methods per dataset are set in `config.IDE_METHODS`. Current defaults: `['TPHATE_DiffOp_IDE', 'PCA']`.

- `TPHATE_DiffOp_IDE`: fits TPHATE, uses eigenvalue spectrum of diffusion operator
- `PCA`: cumulative explained variance threshold (default `THRESHOLD=0.9`)
- Others available: `MiND_ML`, `MLE`, `lPCA`, `CorrInt`, `KNN`

## HPC Job Submission

Jobs use Yale's dSQ (dead-simple queue) on SLURM.

**Step 1 — Generate job list and SLURM submit script:**
```bash
python generate_dsq_joblists.py -d hbn -s atlas_IDE_methods.py -a 1
# -d: dataset name
# -s: script to run
# -a: 1=atlas (parcelwise), 0=searchlight
```
Writes to `joblists/{dataset}_{atlas|searchlight}_{isc|ide}_joblist.txt` and `submit_scripts/dsq_{dataset}_..._submit.sh`.

**Step 2 — Submit:**
```bash
sbatch submit_scripts/dsq_hbn_atlas_ide_submit.sh
```

Searchlight scripts use MPI and need `srun --mpi=pmi2`; this is handled automatically in `generate_dsq_joblists.py`. Atlas scripts run as plain `python -u`.

## Output structure (under `SCRATCH_DIR/{dataset}/`)

```
IDE/LOSO/results/           # searchlight per-subject .nii.gz files
IDE/LOSO_parcel/results/    # atlas per-subject .csv and .nii.gz
ISC/LOSO/results/           # searchlight ISC per-subject .nii.gz
ISC/LOSO_parcel/results/    # atlas ISC per-subject .csv and .nii.gz
```

Aggregated outputs go to `utils.get_results_dir()/all_subject_arrays/` (.npy) and `result_volumes/` (.nii.gz).

Compiled cross-dataset results live in `compiled/results/` as CSVs.

## Notes

- `subject_filter` is used to subset subjects by age group (e.g., `'U_08'` for 8-year-olds in HBN). Pass `'0'` or `'all'` for no filter.
- Datasets with repeated runs (cneuromod, infant_restmovie) use `has_repeat_files()` and a `-f/--file_idx` argument.
- The `joblists/` directory contains pre-generated command lists; regenerate with `generate_dsq_joblists.py` when subjects or scripts change.
- `compiled_results_analysis.ipynb` and `visualizations.ipynb` are the primary analysis notebooks.
