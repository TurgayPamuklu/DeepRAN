#!/bin/bash
# 
# Slurm Script for DGX Machine in TETAM
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
#      sbatch slurm_example.sh


# -= Resources =-
#
#SBATCH --job-name=season
#SBATCH --cpus-per-task=1
##SBATCH --gpus-per-task=1
#SBATCH --mem=120G
#SBATCH --time=23:50:00
##SBATCH --partition=short
#SBATCH --partition=mid
##SBATCH --partition=longer
#SBATCH --output=/raid/users/tpamuklu/slurm_outputs/output-%j.out
#SBATCH --error=/raid/users/tpamuklu/slurm_outputs/error-%j.err
#SBATCH --mail-type=ALL
#SBATCH --mail-user=pamuklu@gmail.com

################################################################################
source /etc/profile.d/z_compecta.sh
echo "source /etc/profile.d/z_compecta.sh"




# srun /raid/users/tpamuklu/libraries/python3_env/bin/python hcran_heuristic.py
# srun /raid/users/tpamuklu/libraries/python3_env/bin/python hcran_gurobi.py
srun /raid/users/tpamuklu/libraries/python36_env/bin/python crosshaul_gurobi.py
##### srun /raid/users/tpamuklu/libraries/python3_env/bin/python __init__.py
#########################################################################################
##### srun /raid/users/tpamuklu/libraries/gurobi_env/bin/python gurobi.py
##### srun /raid/users/tpamuklu/libraries/gurobi_env/bin/python hcran_heuristic.py
##### srun /raid/users/tpamuklu/libraries/gurobi_env/bin/python hcran_monitor.py
##### srun /raid/users/tpamuklu/libraries/gurobi_env/bin/python rfs_gurobi.py
##### srun /raid/users/tpamuklu/libraries/gurobi_env/bin/python hcran_gurobi.py
##### srun /raid/users/tpamuklu/libraries/gurobi_env/bin/python __init__.py
