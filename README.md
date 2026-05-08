# slmtop

`slmtop` is a small Python CLI for day-to-day Slurm resource inspection.
It focuses on the views people usually need before submitting or debugging jobs:

- nvitop-like top view: node resources above current job requests
- free GPU model/count per node
- current queue resource requests, including GPU, CPU, memory, nodes, and time limit
- node CPU and memory allocation/free capacity

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

Only show nodes with at least one free GPU in the top section:

```bash
slmtop --free
```

## Notes

Slurm clusters differ in how precisely they report allocated GPU types. If a
node has multiple GPU models but `AllocTRES` only says `gres/gpu=2`, Slurm does
not expose which model is allocated in that field. In that case `slmtop`
prints `?` for typed free GPU counts and adds a note.

For memory, `ALLOC_MEM` means Slurm-allocated memory from `AllocMem`, while
`FREE_MEM` is the operating system's reported free memory from `FreeMem`.
