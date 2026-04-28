from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path


REQUIRED_IMPORTS = {
    "requests": "requests",
}


def workspace_dir() -> Path:
    return Path(__file__).resolve().parent


def venv_dir() -> Path:
    return workspace_dir() / ".venv"


def venv_python() -> Path:
    if os.name == "nt":
        return venv_dir() / "Scripts" / "python.exe"
    return venv_dir() / "bin" / "python"


def requirements_file() -> Path:
    return workspace_dir() / "requirements.txt"


def in_expected_venv() -> bool:
    try:
        return Path(sys.prefix).resolve() == venv_dir().resolve()
    except Exception:
        return False


def missing_imports() -> list[str]:
    return [package for module, package in REQUIRED_IMPORTS.items() if importlib.util.find_spec(module) is None]


def _run(command: list[str]) -> None:
    completed = subprocess.run(command, cwd=str(workspace_dir()), text=True, capture_output=True)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(f"comando falhou ({' '.join(command)}): {detail[:800]}")


def _record_bootstrap_warning(exc: BaseException) -> None:
    os.environ["MWP_BOOTSTRAP_WARNING"] = (
        "Não foi possível preparar o venv local automaticamente; "
        f"seguindo com fallback compatível quando possível: {exc}"
    )


def ensure_runtime() -> None:
    """Prepare and enter the skill-local Python runtime when needed.

    This keeps the skill compatible with PEP 668 environments where installing
    into system Python is blocked. The first real execution creates
    `workspace/.venv`, installs `requirements.txt`, then re-execs `run.py` with
    the venv Python. Later executions reuse the same venv.
    """
    if os.environ.get("MWP_SKIP_BOOTSTRAP") == "1":
        return
    if in_expected_venv() and not missing_imports():
        return
    if not missing_imports() and not venv_python().exists():
        # System/runtime Python already has the deps. This path is useful for
        # MQC images that ship a prepared /opt/venv and for local dev.
        return

    py = venv_python()
    try:
        if not py.exists():
            if venv_dir().exists():
                shutil.rmtree(venv_dir())
            _run([sys.executable, "-m", "venv", str(venv_dir())])

        if missing_imports() or not in_expected_venv():
            req = requirements_file()
            if not req.exists():
                raise RuntimeError(f"requirements.txt não encontrado em {req}")
            _run([str(py), "-m", "pip", "install", "--upgrade", "pip"])
            _run([str(py), "-m", "pip", "install", "-r", str(req)])

        if Path(sys.executable).resolve() != py.resolve():
            os.execv(str(py), [str(py), *sys.argv])
    except Exception as exc:
        # Some minimal containers expose Python without ensurepip/pip. The skill
        # still ships a stdlib HTTP fallback for requests, so do not crash before
        # the actual read-only collector has a chance to run.
        _record_bootstrap_warning(exc)
        return


def runtime_status() -> dict:
    return {
        "venv_path": str(venv_dir()),
        "venv_python": str(venv_python()),
        "venv_exists": venv_python().exists(),
        "active_python": sys.executable,
        "in_skill_venv": in_expected_venv(),
        "missing_packages": missing_imports(),
        "bootstrap_warning": os.environ.get("MWP_BOOTSTRAP_WARNING"),
    }
