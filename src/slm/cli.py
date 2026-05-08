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


def usage_bar(used: int, total: int, width: int = 10) -> str:
    if total <= 0:
        return "[" + "?" * width + "]"
    filled = round((used / total) * width)
    filled = max(0, min(width, filled))
    return "[" + "#" * filled + "." * (width - filled) + "]"


def pct(used: int, total: int) -> str:
    if total <= 0:
        return "-"
    return f"{round((used / total) * 100):>3}%"


def gpu_summary(node: NodeResource) -> str:
    return ",".join(
        f"{gpu.gpu_type}:{gpu.free if gpu.free is not None else '?'}/{gpu.total}"
        for gpu in node.gpus
    ) or "-"


def resource_summary(nodes: list[NodeResource]) -> list[str]:
    total_nodes = len(nodes)
    cpu_total = sum(node.cpu_total for node in nodes)
    cpu_used = sum(node.cpu_allocated for node in nodes)
    mem_total = sum(node.mem_total_mb for node in nodes)
    mem_used = sum(node.mem_allocated_mb for node in nodes)
    gpu_total = 0
    gpu_free = 0
    unknown_gpu_free = False

    for node in nodes:
        for gpu in node.gpus:
            gpu_total += gpu.total
            if gpu.free is None:
                unknown_gpu_free = True
            else:
                gpu_free += gpu.free

    gpu_value = f"{gpu_free if not unknown_gpu_free else '?'}/{gpu_total}"
    return [
        f"nodes {total_nodes}",
        f"gpu free {gpu_value}",
        f"cpu free {max(cpu_total - cpu_used, 0)}/{cpu_total}",
        f"mem free {format_mb(max(mem_total - mem_used, 0))}/{format_mb(mem_total)}",
    ]


def node_top_rows(nodes: list[NodeResource], only_free_gpu: bool = False) -> list[list[str]]:
    rows: list[list[str]] = []
    for node in nodes:
        if only_free_gpu and not any(gpu.free and gpu.free > 0 for gpu in node.gpus):
            continue
        rows.append(
            [
                node.name,
                gpu_summary(node),
                f"{node.cpu_free}/{node.cpu_total}",
                usage_bar(node.cpu_allocated, node.cpu_total),
                pct(node.cpu_allocated, node.cpu_total),
                f"{format_mb(node.mem_unallocated_mb)}/{format_mb(node.mem_total_mb)}",
                usage_bar(node.mem_allocated_mb, node.mem_total_mb),
                pct(node.mem_allocated_mb, node.mem_total_mb),
                node.state,
            ]
        )
    return rows


def job_top_rows(jobs) -> list[list[str]]:
    return [
        [
            job.job_id,
            job.user,
            job.state,
            job.gpu_request,
            job.memory,
            str(job.cpus) if job.cpus is not None else "-",
            job.nodes,
            job.time_used,
            job.name,
        ]
        for job in jobs
    ]


def print_top(nodes: list[NodeResource], jobs, only_free_gpu: bool = False) -> None:
    visible_nodes = [
        node
        for node in nodes
        if not only_free_gpu or any(gpu.free and gpu.free > 0 for gpu in node.gpus)
    ]

    print("slmtop  " + "  |  ".join(resource_summary(visible_nodes)))
    print()
    print("NODE RESOURCES")
    print_table(
        ["NODE", "GPU_FREE/TOTAL", "CPU_FREE", "CPU_USE", "CPU%", "MEM_FREE", "MEM_USE", "MEM%", "STATE"],
        node_top_rows(visible_nodes),
    )
    print()
    print("JOBS")
    print_table(
        ["JOBID", "USER", "ST", "GPU", "MEM", "CPU", "NODE/REASON", "TIME", "NAME"],
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
