!::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
!
!    This file is part of ICTP RegCM.
!
!    Use of this source code is governed by an MIT-style license that can
!    be found in the LICENSE file or at
!
!         https://opensource.org/licenses/MIT.
!
!    ICTP RegCM is distributed in the hope that it will be useful,
!    but WITHOUT ANY WARRANTY; without even the implied warranty of
!    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
!
!::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

program regcm
!
!**********************************************************************
!
!     Used module declarations
!
!**********************************************************************
!
  use mod_intkinds
  use mod_realkinds
  use mod_date
  use mod_stdio
  use mod_constants
  use mod_dynparam
  use mod_regcm_interface
  use mod_runparams
#ifndef MPI_SERIAL
  use mpi
#endif
#ifdef OASIS
  use mod_oasis_interface
#endif

  implicit none

  real(rk8) :: timestr, timeend
  type(rcm_time_interval) :: tdif
  integer(ik4) :: ierr, iprov
  integer(ik4) :: bench_myid
  real(rk8) :: t_init_start, t_init_end, t_run_start, t_run_end
#ifdef OASIS
  integer :: localCommunicator
#endif
#ifdef MPI_SERIAL
  include 'mpif.h'
  integer(ik4), parameter :: mpi_thread_single = 0
#endif
!
!**********************************************************************
!
! Model Initialization
!
!**********************************************************************
!
#ifndef OASIS
  call mpi_init_thread(mpi_thread_funneled,iprov,ierr)
  if ( ierr /= mpi_success ) then
    write(stderr,*) 'Cannot initilize MPI'
    stop
  end if
  call mpi_comm_rank(mpi_comm_world,bench_myid,ierr)
  t_init_start = mpi_wtime()
  call RCM_initialize()
#else
  !
  ! OASIS Initialization
  !
  call oasisxregcm_init(localCommunicator)
  call mpi_comm_rank(mpi_comm_world,bench_myid,ierr)
  t_init_start = mpi_wtime()
  call RCM_initialize(localCommunicator)
#endif
  t_init_end = mpi_wtime()
  if ( bench_myid == 0 ) then
    write(stdout,'(a,f14.3)') 'INIT_WALLTIME=', t_init_end - t_init_start
    write(stdout,'(a,f14.3)') 'INIT_IO_READ_WALLTIME=', init_io_read_walltime
    write(stdout,'(a,f14.3)') 'INIT_IO_WRITE_WALLTIME=', init_io_write_walltime
  end if
!
!**********************************************************************
!
! Model Run
!
!**********************************************************************
!
  timestr = d_zero
  tdif = idate2 - idate1
  timeend = tohours(tdif) * secph

  t_run_start = mpi_wtime()
  call RCM_run(timestr, timeend)
  t_run_end = mpi_wtime()
  if ( bench_myid == 0 ) then
    write(stdout,'(a,f14.3)') 'RUN_WALLTIME=', t_run_end - t_run_start
    write(stdout,'(a,f14.3)') 'RUN_IO_READ_WALLTIME=', run_io_read_walltime
    write(stdout,'(a,f14.3)') 'RUN_IO_WRITE_WALLTIME=', run_io_write_walltime
  end if
!
!**********************************************************************
!
! Model Finalize
!
!**********************************************************************
!
  call RCM_finalize()
#ifndef OASIS
  call mpi_finalize(ierr)
#else
  !
  ! OASIS Finalization
  !
  call oasisxregcm_finalize
#endif
!
end program regcm
! vim: tabstop=8 expandtab shiftwidth=2 softtabstop=2
