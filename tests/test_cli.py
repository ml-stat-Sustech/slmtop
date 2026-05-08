from slm.cli import main


def test_default_cli_shows_nodes_and_jobs(monkeypatch, capsys):
    node_raw = """NodeName=gpu001 CPUAlloc=2 CPUTot=8 RealMemory=64000 AllocMem=16000 FreeMem=45000 State=MIXED Partitions=gpu
   Gres=gpu:a100:4(S:0-3)
   AllocTRES=cpu=2,mem=16000M,gres/gpu=1
"""
    job_raw = "123|alice|R|gpu|train|gpu001|1|8|64G|gpu:a100:1|0:10|1:00:00|gpu001\n"

    def fake_run(cmd):
        if cmd[0] == "scontrol":
            return node_raw
        return job_raw

    monkeypatch.setattr("slm.cli.run_slurm", fake_run)

    assert main([]) == 0
    output = capsys.readouterr().out
    assert "NODE RESOURCES" not in output
    assert "JOBS" not in output
    assert "JOBID" in output
    assert "PARTITION" in output
    assert "1/4 25%" in output
    assert "RUNNING" in output
    assert "STATE" in output
    assert "gpu:a100:1" not in output
    assert "a100:" not in output


def test_free_cli_filters_nodes(monkeypatch, capsys):
    node_raw = """NodeName=gpu001 CPUAlloc=2 CPUTot=8 RealMemory=64000 AllocMem=16000 FreeMem=45000 State=MIXED Partitions=gpu
   Gres=gpu:a100:4(S:0-3)
   AllocTRES=cpu=2,mem=16000M,gres/gpu=4
NodeName=gpu002 CPUAlloc=2 CPUTot=8 RealMemory=64000 AllocMem=16000 FreeMem=45000 State=MIXED Partitions=gpu
   Gres=gpu:a100:4(S:0-3)
   AllocTRES=cpu=2,mem=16000M,gres/gpu=1
"""
    job_raw = "123|alice|R|gpu|train|gpu001|1|8|64G|gpu:a100:1|0:10|1:00:00|gpu001\n"

    def fake_run(cmd):
        if cmd[0] == "scontrol":
            return node_raw
        return job_raw

    monkeypatch.setattr("slm.cli.run_slurm", fake_run)

    assert main(["--free"]) == 0
    output = capsys.readouterr().out
    nodes_section = output.split("JOBID", 1)[0]
    assert "gpu001" not in nodes_section
    assert "gpu002" in nodes_section


def test_job_gpu_count_accepts_gres_gpu_format(monkeypatch, capsys):
    node_raw = """NodeName=gpu001 CPUAlloc=2 CPUTot=8 RealMemory=64000 AllocMem=16000 FreeMem=45000 State=MIXED Partitions=gpu
   Gres=gpu:a100:4(S:0-3)
   AllocTRES=cpu=2,mem=16000M,gres/gpu=1
"""
    job_raw = "123|alice|R|gpu|train|gpu001|1|8|64G|gres/gpu:1|0:10|1:00:00|gpu001\n"

    def fake_run(cmd):
        if cmd[0] == "scontrol":
            return node_raw
        return job_raw

    monkeypatch.setattr("slm.cli.run_slurm", fake_run)

    assert main([]) == 0
    output = capsys.readouterr().out
    assert "gres/gpu:1" not in output
    assert "RUNNING  1    64G" in output
