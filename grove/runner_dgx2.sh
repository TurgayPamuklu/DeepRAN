#!/bin/bash
# 
# Slurm script for DGX machine in TETAM
#
# Example job submission script
#
#
#   - Set name of the job below changing "Slurm" value.
#   - Set the requested number of tasks (cpu cores) with --ntasks parameter.
#   - Set the required time limit for the job with --time parameter.
#   - Put this script and all the input file under the same directory.
#   - Set the required parameters, input and output file names below.
#   - If you do not want mail please remove the line that has --mail-type
#   - Put this script and all the input file under the same directory.
#   - Partition :: short 2hours mid 1 day long 7 days longer 30 days
#   - Submit this file using:
#      sbatch runner_dgx2.sh


# -= Resources =-
#
#SBATCH --job-name=icc2021
##SBATCH --cpus-per-task=1
#SBATCH --cpus-per-task=48
##SBATCH --gpus-per-task=1
#SBATCH --mem=100G
#SBATCH --time=7-00:00:00
##SBATCH --time=01:59:00
##SBATCH --partition=short
##SBATCH --partition=mid
#SBATCH --partition=long
#SBATCH --output=/cta/users/tpamuklu/slurm_outputs/output-%j.out
#SBATCH --error=/cta/users/tpamuklu/slurm_outputs/error-%j.err
#SBATCH --mail-type=ALL
#SBATCH --mail-user=pamuklu@gmail.com

################################################################################



srun /cta/users/tpamuklu/libraries/python3_env/bin/python ml_qlearning.py
# srun /cta/users/tpamuklu/libraries/python3_env/bin/python monitor.py

