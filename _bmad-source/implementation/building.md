# Build notes

This document serves as a knowledge base when building the program. It contains compilation errors and diagnosis when building the program.

## Async NetCDF

```bash
mod_ncio.F90(992): error #9074: A scalar value is not considered contiguous in this context.   [PAI_FLAT]
      call map_prefetch_3d(icbc_prefetch%pai_flat,icbc_prefetch%pai,offset,n3)
-----------------------------------------^
mod_ncio.F90(992): error #8372: If the dummy argument is declared CONTIGUOUS, the actual argument must be simply contiguous.   [PAI_FLAT]
      call map_prefetch_3d(icbc_prefetch%pai_flat,icbc_prefetch%pai,offset,n3)
-----------------------------------------^
mod_ncio.F90(992): error #7496: A non-pointer actual argument shall have a TARGET attribute when associated with a pointer dummy argument.   [PAI_FLAT]
      call map_prefetch_3d(icbc_prefetch%pai_flat,icbc_prefetch%pai,offset,n3)
-----------------------------------------^
mod_ncio.F90(992): error #6634: The shape matching rules of actual arguments and dummy arguments have been violated.   [PAI_FLAT]
      call map_prefetch_3d(icbc_prefetch%pai_flat,icbc_prefetch%pai,offset,n3)
-----------------------------------------^
compilation aborted for mod_ncio.F90 (code 1)
```

That error is in mod_ncio.F90:873/992 — the ASYNC_NETCDF-gated ICBC prefetch code (the pai_flat field from your recent moloch/PAI work, commit 7f356f49a), not anything related to RRTMG or CLM. It looks like a real bug in that async-netcdf pointer-mapping code (contiguity/shape mismatch on pai_flat).

Solution: remove `--enable-async-netcdf` configure flag