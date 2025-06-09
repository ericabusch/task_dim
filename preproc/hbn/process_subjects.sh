#!/bin/bash

# Script: process_subject.sh
# Description: Process subject files across directories and run analysis program
# Usage: ./process_subject.sh SUBJECT_ID SESSION_ID

# Exit on any error
set -e

SUBJECT_ID=$1
SESSION_ID=$2

# Configuration - Modify these variables as needed
INPUT_DIR="/gpfs/milgram/scratch60/casey/elb77/HBN/HBN_BIDS"
OUTPUT_DIR="/gpfs/milgram/project/casey/elb77/HBN_Prep" 
FS_DIR="/gpfs/milgram/project/casey/elb77/HBN_Prep/sourcedata/freesurfer/sub-${SUBJECT_ID}/scripts"
REQUIRED_FILES=("*task-rest_run-1_space-MNI152Lin_desc-preproc_bold.nii.gz" "*task-movieTP_space-MNI152Lin_desc-preproc_bold.nii.gz" "*_task-rest_run-1_desc-confounds_timeseries.tsv" "*_task-movieTP_desc-confounds_timeseries.tsv")  # Files to check for in DIRECTORY1
WORK_DIR="/gpfs/milgram/scratch60/turk-browne/elb77/workdir3/sub-${SUBJECT_ID}_WORK_DIR"
CFG="/gpfs/milgram/pi/turk-browne/users/elb77/task_dim/preproc/hbn/joblists/bids_config.json"
TARGET_FILE=("IsRunning.lh+rh")         # File to delete in FS_DIR
PROGRAM_PATH="fmriprep"
PROGRAM_ARGS=(${INPUT_DIR} ${OUTPUT_DIR} "participant" "-w ${WORK_DIR}" "--fs-license-file /home/elb77/license.txt" "--skip_bids_validation" "--output-spaces MNI152Lin" "--ignore fieldmaps t2w"  "--nprocs 16" "--bids-filter-file ${CFG}")         # Program arguments

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${color} ${message}${NC}"
}

# Function to load required modules
load_modules() {
    print_status "$YELLOW" "Loading required modules..."
    module purge
    module load fmriprep/23.2.1     
    print_status "$GREEN" "Modules loaded successfully"
}

# Function to check if required files exist for subject in output_dir; ends if true
check_required_files() {
    local subject_dir="${OUTPUT_DIR}/sub-${SUBJECT_ID}/ses-${SESSION_ID}/func"
    
    print_status "$YELLOW" "Checking for required files in ${subject_dir}..."
    
    if [[ ! -d "$subject_dir" ]]; then
        print_status "$RED" "Subject directory not found: ${subject_dir}"
        return 1
    fi
    
    for pattern in "${REQUIRED_FILES[@]}"; do
        local found=false
        local match_count=0
        
        # Use find to safely handle wildcard patterns
        while IFS= read -r -d '' file; do
            if [[ -f "$file" ]]; then
                print_status "$GREEN" "Found match for pattern '${pattern}': ${file}"
                found=true
                ((match_count++))
            fi
        done < <(find "$subject_dir" -maxdepth 1 -name "$pattern" -type f -print0 2>/dev/null)
        
        if [[ "$found" = false ]]; then
            print_status "$RED" "No files found matching pattern: ${pattern}"
            return 1
        fi
        
        print_status "$GREEN" "Pattern '${pattern}' matched ${match_count} file(s)"
    done
    
    print_status "$GREEN" "All required file patterns found for subject ${SUBJECT_ID}"
    return 0
}

# Function to clean up files in DIRECTORY2
cleanup_files() {
    local subject_dir="${FS_DIR}/sub-${SUBJECT_ID}"
    
    print_status "$YELLOW" "Cleaning up files in ${subject_dir}..."
    
    if [[ ! -d "$subject_dir" ]]; then
        print_status "$GREEN" "Cleanup directory not found; skipping)"
        return 0
    fi
    
    local files_deleted=0
    for pattern in "${TARGET_FILES[@]}"; do
        # Use find to handle glob patterns safely
        while IFS= read -r -d '' file; do
            if [[ -f "$file" ]]; then
                print_status "$YELLOW" "Deleting: ${file}"
                rm -f "$file"
                ((files_deleted++))
            fi
        done < <(find "$subject_dir" -name "$pattern" -type f -print0 2>/dev/null)
    done
    
    print_status "$GREEN" "Cleanup complete. Deleted ${files_deleted} files"
}

# Function to clean up files after success
cleanup_workdir_final() {
    local subject_dir="${WORK_DIR}"
    
    print_status "$YELLOW" "Deleting files in ${subject_dir}..."
    
    if [[ ! -d "$subject_dir" ]]; then
        print_status "$GREEN" "Directory not found; skipping"
        return 0
    fi
    rm -rf $subject_dir
    
    local files_deleted=0
    for pattern in "${TARGET_FILES[@]}"; do
        # Use find to handle glob patterns safely
        while IFS= read -r -d '' file; do
            if [[ -f "$file" ]]; then
                print_status "$YELLOW" "Deleting: ${file}"
                rm -f "$file"
                ((files_deleted++))
            fi
        done < <(find "$subject_dir" -name "$pattern" -type f -print0 2>/dev/null)
    done
    
    print_status "$GREEN" "Cleanup complete for ${SUBJECT_ID}"
}

# Function to run the main program
run_fmriprep() {
    
    print_status "$YELLOW" "Running program for subject ${SUBJECT_ID}..."
    
    # Run the program with specified arguments and subject ID
    print_status "$YELLOW" "Executing: ${PROGRAM_PATH} ${PROGRAM_ARGS[*]} --participant-label=${SUBJECT_ID}"

    if "$PROGRAM_PATH" "${PROGRAM_ARGS[@]}" "--participant-label=${SUBJECT_ID}"; then
        print_status "$GREEN" "Program completed successfully"
        
        return 0
    else
        print_status "$RED" "Program failed with exit code $?"
        return 1
    fi
}

# Main script execution
main() {
    # Check command line arguments
    if [[ $# -ne 2 ]]; then
        echo "Please provide SUBJECT_ID and SESSION_ID"
        exit 1
    fi
    
    SUBJECT_ID=$1
    SESSION_ID=$2

    print_status "$GREEN" "Starting processing for subject: ${SUBJECT_ID}"
    
    # Step 1: Check for required files in DIRECTORY1
    if check_required_files "$SUBJECT_ID"; then
        print_status "$GREEN" "Already successfully ran fmriprep; exiting"
        cleanup_workdir_final
        exit 0
    fi
    
    # Step 2: Load modules (only reached if required files not found)
    load_modules
    
    # Step 3: Clean up files in DIRECTORY2
    cleanup_files "$SUBJECT_ID"
    
    # Step 4: Run the main program
    if run_fmriprep "$SUBJECT_ID"; then
        print_status "$GREEN" "All processing completed for ${SUBJECT_ID}"
        cleanup_workdir_final
        exit 0
    else
        print_status "$RED" "Processing failed for ${SUBJECT_ID}"
        exit 1
    fi
    
}

# Run main function with all command line arguments
main "$@" 