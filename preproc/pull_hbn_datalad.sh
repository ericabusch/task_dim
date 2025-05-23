#!/bin/bash
# #SBATCH --output log/%j_pull_data.out
# #SBATCH --job-name pull_hbn_datalad
# #SBATCH --ntasks=1
# #SBATCH -t 24:00:00 
# #SBATCH --mem-per-cpu 2G
# #SBATCH --partition=psych_day
# #SBATCH --account=turk-browne
# #SBATCH --mail-type ALL

# module load miniconda
# source activate ~/miniconda3/
# eval "$(ssh-agent -s)"

this_chunk=$1
total_chunks=10
OUTDIR=/gpfs/milgram/scratch60/turk-browne/elb77/HBN/HBN_BIDS/
cd $OUTDIR
echo $pwd
FILENAME=/gpfs/milgram/pi/turk-browne/users/elb77/task_dim/HBN/datalad_files_to_get.txt
total_lines=$(wc -l < "$FILENAME")
echo "processing $FILENAME with $total_lines lines"

# Calculate the number of lines per chunk
chunk_lines=$(( (total_lines + total_chunks - 1) / total_chunks ))  # Round up to ensure all lines are included

# Function to process a specific chunk
process_chunk() {
    chunk=$1
    start_line=$(( (chunk - 1) * chunk_lines + 1 ))
    end_line=$(( chunk * chunk_lines ))

    # Ensure the end_line does not exceed the total number of lines
    if (( end_line > total_lines )); then
        end_line=$total_lines
    fi
    echo "Current directory:"
    pwd
    echo "Processing chunk $chunk (lines $start_line to $end_line):"
    sed -n "${start_line},${end_line}p" "$FILENAME" | while IFS= read -r line; do
        # Process each line here
        datalad get "$line"
        echo "got $line"
    done
}

process_chunk "$this_chunk"
