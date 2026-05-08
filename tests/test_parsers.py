from slm.parsers import parse_nodes, parse_partitions, parse_squeue


def test_parse_nodes_with_typed_and_untyped_gpu_allocations():
    raw = """NodeName=gpu001 Arch=x86_64 CoresPerSocket=64
   CPUAlloc=32 CPUTot=128 RealMemory=512000 AllocMem=128000 FreeMem=350000 State=MIXED Partitions=gpu
   Gres=gpu:a100:8(S:0-7)
   CfgTRES=cpu=128,mem=512000M,billing=128,gres/gpu=8
   AllocTRES=cpu=32,mem=128000M,gres/gpu=2
NodeName=gpu002 Arch=x86_64 CoresPerSocket=64
   CPUAlloc=16 CPUTot=128 RealMemory=512000 AllocMem=64000 FreeMem=420000 State=MIXED Partitions=gpu
   Gres=gpu:h100:4(S:0-3),gpu:a100:4(S:0-3)
   AllocTRES=cpu=16,mem=64000M,gres/gpu:h100=1,gres/gpu:a100=2
NodeName=gpu003 Arch=x86_64 CoresPerSocket=64
   CPUAlloc=16 CPUTot=128 RealMemory=512000 AllocMem=64000 FreeMem=420000 State=MIXED Partitions=gpu
   Gres=gpu:h100:4(S:0-3),gpu:a100:4(S:0-3)
   AllocTRES=cpu=16,mem=64000M,gres/gpu=2
"""
    nodes = parse_nodes(raw)

    assert nodes[0].name == "gpu001"
    assert nodes[0].cpu_free == 96
    assert nodes[0].mem_unallocated_mb == 384000
    assert nodes[0].gpus[0].gpu_type == "a100"
    assert nodes[0].gpus[0].allocated == 2
    assert nodes[0].gpus[0].free == 6

    by_type = {gpu.gpu_type: gpu for gpu in nodes[1].gpus}
    assert by_type["a100"].free == 2
    assert by_type["h100"].free == 3

    assert nodes[2].gpus[0].free is None
    assert "typed allocation unavailable" in nodes[2].gpus[0].note


def test_parse_node_memory_allocation_from_alloc_tres_when_alloc_mem_is_zero():
    raw = """NodeName=gpu001 Arch=x86_64 CoresPerSocket=64
   CPUAlloc=32 CPUTot=128 RealMemory=512000 AllocMem=0 FreeMem=350000 State=MIXED Partitions=gpu
   Gres=gpu:a100:8(S:0-7)
   AllocTRES=cpu=32,mem=128G,gres/gpu=2
"""
    nodes = parse_nodes(raw)

    assert nodes[0].mem_allocated_mb == 131072
    assert nodes[0].mem_unallocated_mb == 380928


def test_parse_squeue_resources():
    raw = "123|alice|R|gpu|train|gpu001|1|8|64G|gpu:a100:1|00:10:00|1-00:00:00|gpu001\n"
    jobs = parse_squeue(raw)

    assert len(jobs) == 1
    assert jobs[0].job_id == "123"
    assert jobs[0].cpus == 8
    assert jobs[0].memory == "64G"
    assert jobs[0].gpu_request == "gpu:a100:1"


def test_parse_partitions():
    raw = "gpu*|up|7-00:00:00|12|mix|gpu[001-012]\n"
    partitions = parse_partitions(raw)

    assert partitions[0].partition == "gpu*"
    assert partitions[0].nodes == 12
    assert partitions[0].state == "mix"
