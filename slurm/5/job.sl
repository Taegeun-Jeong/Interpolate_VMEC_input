#!/bin/bash
#SBATCH --job-name=desc          # Job name
#SBATCH --output=output.log      # Standard output file
#SBATCH --error=error.log        # Error log file
#SBATCH --ntasks=1               # Number of tasks
#SBATCH --cpus-per-task=1        # CPUs per task
#SBATCH --time=01:30:00          # Maximum runtime (HH:MM:SS)
#SBATCH --partition=all.q        # Partition name
#SBATCH --nodelist=gpu01     # Specific node (if needed)

# Execute the main Python script
python /home/taegeun/project/DESC_source/PPCF_revision_202503/make_interpolated_boundary/python/change_DESC_to_VMEC.py

# Notify via Slack after completion
python /home/taegeun/slurm/slack_send_notification.py "$SLURM_JOB_ID" "COMPLETED"