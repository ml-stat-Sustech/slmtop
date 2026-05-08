# slmtop

`slmtop` is a small Python CLI for day-to-day Slurm resource inspection.
It focuses on the views people usually need before submitting or debugging jobs:

- nvitop-like top view: node resources above current job requests
- free GPU model/count per node
- current queue resource requests, including GPU, CPU, memory, nodes, and time limit
- node GPU and CPU allocation/free capacity

It uses Slurm's own commands (`scontrol`, `squeue`, `sinfo`) and has no runtime
Python dependencies.

## Install

From this directory:

```bash
python3 -m pip install .
```

For editable development:

```bash
python3 -m pip install -e .
```

## Usage

Show node resources above current job requests:

```bash
slmtop
```

The output is split into a compact resource dashboard and a job table:

```text
slmtop  nodes 2  |  gpu free 9/16  |  cpu free 144/256

NODE    GPU_USE               CPU_FREE  CPU_USE           STATE
------  --------------------  --------  ----------------  -----
gpu001  [########..] 6/8 75%  32/128    [########..] 75%  MIXED
gpu002  [#.........] 1/8 12%  112/128   [#.........] 12%  IDLE

JOBID  USER   STATE    GPU  MEM   CPU  NODE/REASON  TIME  NAME
-----  -----  -------  ---  ----  ---  -----------  ----  -----
123    alice  RUNNING  4    128G  32   gpu001       2:31  train
```

Only show nodes with at least one free GPU in the top section:

```bash
slmtop --free
```

## Notes

Slurm clusters differ in how precisely they report allocated GPU types. If a
node has multiple GPU models but `AllocTRES` only says `gres/gpu=2`, Slurm does
not expose which model is allocated in that field. In that case `slmtop`
prints `?` for typed free GPU counts and adds a note.
