from __future__ import annotations

import importlib.util
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Check:
    name: str
    status: str  # ok, warn, error
    detail: str
    fix: str = ""


def _run(cmd: List[str], timeout: int = 8) -> Optional[str]:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=timeout, text=True)
        return out.strip()
    except Exception:
        return None


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def detect_nvidia_vram_gb() -> Optional[float]:
    if not shutil.which("nvidia-smi"):
        return None
    out = _run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"])
    if not out:
        return None
    try:
        values = [float(x.strip()) / 1024 for x in out.splitlines() if x.strip()]
        return max(values) if values else None
    except ValueError:
        return None


def run_doctor() -> List[Check]:
    checks: List[Check] = []
    py = sys.version_info
    if py >= (3, 10):
        checks.append(Check("Python", "ok", f"{platform.python_version()}"))
    else:
        checks.append(Check("Python", "warn", f"{platform.python_version()} detected", "Unsloth Core currently recommends newer Python via `uv venv unsloth_env --python 3.13`."))

    system = platform.system()
    machine = platform.machine()
    checks.append(Check("Platform", "ok", f"{system} {machine}"))

    vram = detect_nvidia_vram_gb()
    if vram:
        checks.append(Check("NVIDIA GPU", "ok", f"Detected ~{vram:.1f}GB VRAM"))
    elif system == "Darwin" and machine == "arm64":
        checks.append(Check("Apple Silicon", "warn", "Detected macOS arm64", "Unsloth Studio supports macOS workflows; Unsloth Core training support may differ by model/runtime. Start with Studio or MLX-compatible paths."))
    else:
        checks.append(Check("GPU", "warn", "No NVIDIA GPU detected via nvidia-smi", "Use Colab/RunPod/Lambda, Docker with --gpus all, or Unsloth Studio where appropriate."))

    for cmd in ["uv", "git"]:
        if shutil.which(cmd):
            checks.append(Check(cmd, "ok", f"found at {shutil.which(cmd)}"))
        else:
            checks.append(Check(cmd, "warn", "not found", f"Install {cmd}; for uv: curl -LsSf https://astral.sh/uv/install.sh | sh"))

    modules = ["torch", "unsloth", "datasets", "transformers", "trl", "accelerate", "bitsandbytes"]
    for mod in modules:
        if _has_module(mod):
            checks.append(Check(mod, "ok", "importable"))
        else:
            checks.append(Check(mod, "warn", "not installed in this Python environment", "This is OK for project generation. For actual training, install Unsloth in a GPU environment with `uv pip install unsloth --torch-backend=auto`."))

    if os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN"):
        checks.append(Check("Hugging Face token", "ok", "HF token env var detected"))
    else:
        checks.append(Check("Hugging Face token", "warn", "no HF_TOKEN detected", "Set HF_TOKEN if using gated models like Llama or pushing to the Hub."))

    return checks


def format_checks(checks: List[Check]) -> str:
    icon = {"ok": "✅", "warn": "⚠️ ", "error": "❌"}
    lines = []
    for c in checks:
        lines.append(f"{icon.get(c.status, '•')} {c.name}: {c.detail}")
        if c.fix:
            lines.append(f"   fix: {c.fix}")
    return "\n".join(lines)
