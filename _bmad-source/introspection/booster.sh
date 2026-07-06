#!/bin/bash

#SBATCH --account=ICT26_MHPC_0
#SBATCH --out=logs/LOG_%x_%j.out
#SBATCH --err=logs/LOG_%x_%j.err
#SBATCH --job-name=node_intro_boost
#SBATCH --partition=boost_usr_prod
#SBATCH --qos=boost_qos_dbg
#SBATCH --nodes=1
#SBATCH --mem=0G
#SBATCH --gres=gpu:4
#SBATCH --exclusive
#SBATCH --time=00:10:00

cd "$SLURM_SUBMIT_DIR" || exit 1

mkdir -p booster

echo "===== hostname =====" > topo_info_booster.txt
hostname >> topo_info_booster.txt 2>&1

echo -e "\n===== date =====" >> topo_info_booster.txt
date >> topo_info_booster.txt 2>&1

echo -e "\n===== nvidia-smi -L =====" >> topo_info_booster.txt
nvidia-smi -L >> topo_info_booster.txt 2>&1
nvidia-smi -L > booster/gpu_list.txt 2>&1

echo -e "\n===== nvidia-smi topo -m =====" >> topo_info_booster.txt
nvidia-smi topo -m >> topo_info_booster.txt 2>&1
nvidia-smi topo -m > booster/gpu_topology.txt 2>&1

echo -e "\n===== numactl --hardware =====" >> topo_info_booster.txt
numactl --hardware >> topo_info_booster.txt 2>&1
numactl --hardware > booster/numa.txt 2>&1

echo -e "\n===== lscpu =====" >> topo_info_booster.txt
lscpu >> topo_info_booster.txt 2>&1
lscpu > booster/cpu.txt 2>&1

echo -e "\n===== ibstat =====" >> topo_info_booster.txt
ibstat >> topo_info_booster.txt 2>&1
ibstat > booster/infiniband.txt 2>&1

echo -e "\n===== ibdev2netdev =====" >> topo_info_booster.txt
ibdev2netdev >> topo_info_booster.txt 2>&1
ibdev2netdev > booster/ibdev2netdev.txt 2>&1

echo -e "\n===== ucx_info -d =====" >> topo_info_booster.txt
ucx_info -d >> topo_info_booster.txt 2>&1
ucx_info -d > booster/ucx_devices.txt 2>&1

echo -e "\n===== ompi_info | grep -i cuda =====" >> topo_info_booster.txt
(ompi_info | grep -i cuda) >> topo_info_booster.txt 2>&1
(ompi_info | grep -i cuda) > booster/ompi_cuda.txt 2>&1

echo -e "\n===== ompi_info | grep -i ucx =====" >> topo_info_booster.txt
(ompi_info | grep -i ucx) >> topo_info_booster.txt 2>&1
(ompi_info | grep -i ucx) > booster/ompi_ucx.txt 2>&1
