#!/bin/bash

#SBATCH --account=ICT26_MHPC
#SBATCH --out=logs/LOG_%x_%j.out
#SBATCH --err=logs/LOG_%x_%j.err
#SBATCH --job-name=node_intro_dcgp
#SBATCH --partition=dcgp_usr_prod
#SBATCH --qos=dcgp_qos_dbg
#SBATCH --nodes=1
#SBATCH --exclusive
#SBATCH --time=00:05:00

# source /leonardo/home/userexternal/ctica000/MS_thesis/RegCM/modules_cuda

cd "$SLURM_SUBMIT_DIR" || exit 1

mkdir -p dcgp

echo "===== hostname =====" > topo_info_dcgp.txt
hostname >> topo_info_dcgp.txt 2>&1

echo -e "\n===== date =====" >> topo_info_dcgp.txt
date >> topo_info_dcgp.txt 2>&1

# echo -e "\n===== nvidia-smi -L =====" >> topo_info.txt
# nvidia-smi -L >> topo_info.txt 2>&1
# nvidia-smi -L > dcgp/gpu_list.txt 2>&1

# echo -e "\n===== nvidia-smi topo -m =====" >> topo_info.txt
# nvidia-smi topo -m >> topo_info.txt 2>&1
# nvidia-smi topo -m > dcgp/gpu_topology.txt 2>&1

echo -e "\n===== numactl --hardware =====" >> topo_info_dcgp.txt
numactl --hardware >> topo_info_dcgp.txt 2>&1
numactl --hardware > dcgp/numa.txt 2>&1

echo -e "\n===== lscpu =====" >> topo_info_dcgp.txt
lscpu >> topo_info_dcgp.txt 2>&1
lscpu > dcgp/cpu.txt 2>&1

echo -e "\n===== ibstat =====" >> topo_info_dcgp.txt
ibstat >> topo_info_dcgp.txt 2>&1
ibstat > dcgp/infiniband.txt 2>&1

echo -e "\n===== ibdev2netdev =====" >> topo_info_dcgp.txt
ibdev2netdev >> topo_info_dcgp.txt 2>&1
ibdev2netdev > dcgp/ibdev2netdev.txt 2>&1

echo -e "\n===== ucx_info -d =====" >> topo_info_dcgp.txt
ucx_info -d >> topo_info_dcgp.txt 2>&1
ucx_info -d > dcgp/ucx_devices.txt 2>&1

echo -e "\n===== ompi_info | grep -i cuda =====" >> topo_info_dcgp.txt
(ompi_info | grep -i cuda) >> topo_info_dcgp.txt 2>&1
(ompi_info | grep -i cuda) > dcgp/ompi_cuda.txt 2>&1

echo -e "\n===== ompi_info | grep -i ucx =====" >> topo_info_dcgp.txt
(ompi_info | grep -i ucx) >> topo_info_dcgp.txt 2>&1
(ompi_info | grep -i ucx) > dcgp/ompi_ucx.txt 2>&1
