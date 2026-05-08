from __future__ import annotations

import subprocess
import sys


class SlurmError(RuntimeError):
    pass


def run_slurm(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.PIPE)
    except FileNotFoundError as exc:
        raise SlurmError(f"cannot find {cmd[0]!r} in PATH") from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or str(exc)
        raise SlurmError(message) from exc


def exit_on_slurm_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SlurmError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    return wrapper
