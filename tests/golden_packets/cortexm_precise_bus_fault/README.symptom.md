# cortexm_precise_bus_fault

Symptom: Cortex-M project enters HardFault after enabling a peripheral driver. Fault dump shows `PRECISERR` and a valid BFAR.

Expected behavior: report should require symbolication of stacked PC and validation of BFAR ownership before claiming root cause.
