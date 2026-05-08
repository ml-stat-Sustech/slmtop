from __future__ import annotations

import re

from .models import GpuResource, JobResource, NodeResource, PartitionResource


def split_csv_outside_parens(value: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    for i, char in enumerate(value):
        if char == "(":
            depth += 1
        elif char == ")" and depth:
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(value[start:i])
            start = i + 1
    parts.append(value[start:])
    return [part.strip() for part in parts if part.strip()]


def parse_int(value: str | None) -> int:
    if value is None:
        return 0
    match = re.match(r"\d+", value)
    return int(match.group(0)) if match else 0


def parse_memory_to_mb(value: str | None) -> int:
    if not value or value in {"0", "(null)", "N/A"}:
        return 0
    match = re.match(r"([0-9.]+)([KMGT]?)", value, re.IGNORECASE)
    if not match:
        return 0
    amount = float(match.group(1))
    unit = match.group(2).upper()
    factors = {"": 1, "K": 1 / 1024, "M": 1, "G": 1024, "T": 1024 * 1024}
    return int(amount * factors.get(unit, 1))


def parse_key_value_records(raw: str, start_key: str) -> list[dict[str, str]]:
    records: list[list[str]] = []
    current: list[str] = []

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(f"{start_key}=") and current:
            records.append(current)
            current = []
        current.append(stripped)

    if current:
        records.append(current)

    parsed: list[dict[str, str]] = []
    for record in records:
        data: dict[str, str] = {}
        for token in " ".join(record).split():
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            data[key] = value
        if data.get(start_key):
            parsed.append(data)
    return parsed


def parse_gpu_gres(gres: str) -> dict[str, int]:
    if not gres or gres == "(null)":
        return {}

    result: dict[str, int] = {}
    for item in split_csv_outside_parens(gres):
        item = re.sub(r"\(.*\)$", "", item)
        fields = item.split(":")
        if not fields or fields[0] != "gpu":
            continue

        if len(fields) == 2 and fields[1].isdigit():
            gpu_type = "gpu"
            count = int(fields[1])
        elif len(fields) >= 3 and fields[-1].isdigit():
            gpu_type = ":".join(fields[1:-1]) or "gpu"
            count = int(fields[-1])
        else:
            continue

        result[gpu_type] = result.get(gpu_type, 0) + count
    return result


def parse_alloc_tres(alloc_tres: str) -> tuple[dict[str, int], int | None]:
    typed: dict[str, int] = {}
    untyped_total: int | None = None
    if not alloc_tres or alloc_tres == "(null)":
        return typed, untyped_total

    for item in split_csv_outside_parens(alloc_tres):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        try:
            count = int(float(value))
        except ValueError:
            continue

        if key == "gres/gpu":
            untyped_total = count
        elif key.startswith("gres/gpu:"):
            gpu_type = key.removeprefix("gres/gpu:")
            typed[gpu_type] = typed.get(gpu_type, 0) + count

    return typed, untyped_total


def parse_alloc_tres_memory_mb(alloc_tres: str) -> int:
    if not alloc_tres or alloc_tres == "(null)":
        return 0

    for item in split_csv_outside_parens(alloc_tres):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        if key == "mem":
            return parse_memory_to_mb(value)
    return 0


def parse_nodes(raw: str) -> list[NodeResource]:
    nodes: list[NodeResource] = []
    for record in parse_key_value_records(raw, "NodeName"):
        totals = parse_gpu_gres(record.get("Gres", ""))
        typed_alloc, untyped_alloc = parse_alloc_tres(record.get("AllocTRES", ""))
        mem_allocated_mb = parse_int(record.get("AllocMem"))
        if mem_allocated_mb == 0:
            mem_allocated_mb = parse_alloc_tres_memory_mb(record.get("AllocTRES", ""))
        gpus: list[GpuResource] = []

        for gpu_type, total in sorted(totals.items()):
            note = ""
            allocated: int | None
            free: int | None
            if gpu_type in typed_alloc:
                allocated = typed_alloc[gpu_type]
                free = max(total - allocated, 0)
            elif untyped_alloc is not None and len(totals) == 1:
                allocated = untyped_alloc
                free = max(total - allocated, 0)
            elif untyped_alloc is not None:
                allocated = None
                free = None
                note = f"typed allocation unavailable; node alloc gpu={untyped_alloc}"
            else:
                allocated = 0
                free = total

            gpus.append(GpuResource(gpu_type, total, allocated, free, note))

        nodes.append(
            NodeResource(
                name=record.get("NodeName", "-"),
                state=record.get("State", "-").split("+", 1)[0],
                partition=record.get("Partitions", "-"),
                cpu_total=parse_int(record.get("CPUTot")),
                cpu_allocated=parse_int(record.get("CPUAlloc")),
                mem_total_mb=parse_int(record.get("RealMemory")),
                mem_allocated_mb=mem_allocated_mb,
                mem_free_mb=parse_int(record.get("FreeMem")) if "FreeMem" in record else None,
                gpus=tuple(gpus),
            )
        )
    return nodes


def parse_squeue(raw: str) -> list[JobResource]:
    jobs: list[JobResource] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        fields = line.rstrip("\n").split("|")
        if len(fields) < 12:
            continue
        jobs.append(
            JobResource(
                job_id=fields[0],
                user=fields[1],
                state=fields[2],
                partition=fields[3],
                name=fields[4],
                nodes=fields[5],
                node_count=parse_int(fields[6]) if fields[6] else None,
                cpus=parse_int(fields[7]) if fields[7] else None,
                memory=fields[8] or "-",
                gpu_request=fields[9] or "-",
                time_used=fields[10] or "-",
                time_limit=fields[11] or "-",
                reason=fields[12] if len(fields) > 12 and fields[12] else "-",
            )
        )
    return jobs


def parse_partitions(raw: str) -> list[PartitionResource]:
    partitions: list[PartitionResource] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        fields = line.rstrip("\n").split("|")
        if len(fields) < 6:
            continue
        partitions.append(
            PartitionResource(
                partition=fields[0],
                availability=fields[1],
                time_limit=fields[2],
                nodes=parse_int(fields[3]),
                state=fields[4],
                node_list=fields[5],
            )
        )
    return partitions
