from __future__ import annotations

import argparse

from .formatting import format_mb, print_table
from .models import NodeResource
from .parsers import parse_nodes, parse_squeue
from .slurm import SlurmError, run_slurm


SQUEUE_FORMAT = "%i|%u|%t|%P|%j|%N|%D|%C|%m|%b|%M|%l|%R"


def load_nodes(names: list[str]) -> list[NodeResource]:
    cmd = ["scontrol", "show", "node"]
    cmd.extend(names)
    return parse_nodes(run_slurm(cmd))


def load_jobs(args: argparse.Namespace):
    cmd = ["squeue", "-h", "-o", SQUEUE_FORMAT]
    return parse_squeue(run_slurm(cmd))


def node_top_rows(nodes: list[NodeResource], only_free_gpu: bool = False) -> list[list[str]]:
    rows: list[list[str]] = []
    for node in nodes:
        if only_free_gpu and not any(gpu.free and gpu.free > 0 for gpu in node.gpus):
            continue
        gpu_summary = ",".join(
            f"{gpu.gpu_type}:{gpu.free if gpu.free is not None else '?'}/{gpu.total}"
            for gpu in node.gpus
        ) or "-"
        rows.append(
            [
                node.name,
                node.state,
                node.partition,
                f"{node.cpu_allocated}/{node.cpu_total}",
                f"{node.cpu_free}/{node.cpu_total}",
                f"{format_mb(node.mem_allocated_mb)}/{format_mb(node.mem_total_mb)}",
                f"{format_mb(node.mem_unallocated_mb)}/{format_mb(node.mem_total_mb)}",
                gpu_summary,
            ]
        )
    return rows


def job_top_rows(jobs) -> list[list[str]]:
    return [
        [
            job.job_id,
            job.user,
            job.state,
            job.partition,
            job.nodes,
            str(job.cpus) if job.cpus is not None else "-",
            job.memory,
            job.gpu_request,
            job.time_used,
            job.time_limit,
            job.name,
        ]
        for job in jobs
    ]


def print_top(nodes: list[NodeResource], jobs, only_free_gpu: bool = False) -> None:
    print("Nodes")
    print_table(
        ["NODE", "STATE", "PARTITION", "CPU_ALLOC/TOTAL", "CPU_FREE/TOTAL", "MEM_ALLOC/TOTAL", "MEM_FREE/TOTAL", "GPU_FREE/TOTAL"],
        node_top_rows(nodes, only_free_gpu=only_free_gpu),
    )
    print()
    print("Jobs")
    print_table(
        ["JOBID", "USER", "ST", "PART", "NODE/REASON", "CPUS", "MEM", "GPU/GRES", "TIME", "LIMIT", "NAME"],
        job_top_rows(jobs),
    )


def cmd_top(args: argparse.Namespace) -> int:
    nodes = load_nodes([])
    jobs = load_jobs(args)
    print_top(nodes, jobs, only_free_gpu=args.free)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="slmtop",
        description="Show Slurm node resources above current job requests.",
    )
    parser.add_argument("--free", action="store_true", help="only show nodes with at least one free GPU")
    parser.set_defaults(func=cmd_top)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except SlurmError as exc:
        parser.exit(1, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
