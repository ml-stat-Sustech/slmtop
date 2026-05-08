from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GpuResource:
    gpu_type: str
    total: int
    allocated: int | None
    free: int | None
    note: str = ""


@dataclass(frozen=True)
class NodeResource:
    name: str
    state: str
    partition: str = "-"
    cpu_total: int = 0
    cpu_allocated: int = 0
    mem_total_mb: int = 0
    mem_allocated_mb: int = 0
    mem_free_mb: int | None = None
    gpus: tuple[GpuResource, ...] = field(default_factory=tuple)

    @property
    def cpu_free(self) -> int:
        return max(self.cpu_total - self.cpu_allocated, 0)

    @property
    def mem_unallocated_mb(self) -> int:
        return max(self.mem_total_mb - self.mem_allocated_mb, 0)


@dataclass(frozen=True)
class JobResource:
    job_id: str
    user: str
    state: str
    partition: str
    name: str
    nodes: str
    node_count: int | None
    cpus: int | None
    memory: str
    gpu_request: str
    time_used: str
    time_limit: str
    reason: str


@dataclass(frozen=True)
class PartitionResource:
    partition: str
    availability: str
    time_limit: str
    nodes: int
    state: str
    node_list: str
