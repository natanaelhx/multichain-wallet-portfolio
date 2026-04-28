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


def _missing_imports_in_python(python_bin: Path) -> list[str]:
    missing: list[str] = []
    for module, package in REQUIRED_IMPORTS.items():
        probe = subprocess.run(
            [str(python_bin), "-c", f"import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('{module}') else 1)"],
            cwd=str(workspace_dir()),
            text=True,
            capture_output=True,
        )
        if probe.returncode != 0:
            missing.append(package)
    return missing


def _record_bootstrap_warning(exc: BaseException) -> None:
    os.environ["MWP_BOOTSTRAP_WARNING"] = (
        "Não foi possível preparar o venv local automaticamente; "
        f"seguindo com fallback compatível quando possível: {exc}"
    )


def ensure_runtime() -> None:
    """Prepare and enter the skill-local Python runtime when needed.

    This keeps the skill compatible with PEP 668 environments where installing
    into system Python is blocked. The first real execution creates
    `workspace/.venv`, installs `requirements.txt` only when packages are truly
    missing, then re-execs `run.py` with the venv Python. Later executions reuse
    the same venv without forcing a pip self-upgrade.
    """
    if os.environ.get("MWP_SKIP_BOOTSTRAP") == "1":
        return
    if in_expected_venv() and not missing_imports():
        return
    if not missing_imports() and not venv_python().exists():
        return

    py = venv_python()
    try:
        if not py.exists():
            if venv_dir().exists():
                shutil.rmtree(venv_dir())
            _run([sys.executable, "-m", "venv", str(venv_dir())])

        venv_missing = _missing_imports_in_python(py) if py.exists() else list(REQUIRED_IMPORTS.values())
        if venv_missing:
            req = requirements_file()
            if not req.exists():
                raise RuntimeError(f"requirements.txt não encontrado em {req}")
            _run([str(py), "-m", "pip", "install", "-r", str(req)])

        if Path(sys.executable).resolve() != py.resolve() and not _missing_imports_in_python(py):
            os.execv(str(py), [str(py), *sys.argv])
    except Exception as exc:
        _record_bootstrap_warning(exc)
        return


def runtime_status() -> dict:
    py = venv_python()
    venv_exists = py.exists()
    venv_missing = _missing_imports_in_python(py) if venv_exists else list(REQUIRED_IMPORTS.values())
    return {
        "venv_path": str(venv_dir()),
        "venv_python": str(py),
        "venv_exists": venv_exists,
        "active_python": sys.executable,
        "in_skill_venv": in_expected_venv(),
        "missing_packages": missing_imports(),
        "target_runtime_missing_packages": venv_missing,
        "target_runtime_ready": venv_exists and not venv_missing,
        "bootstrap_warning": os.environ.get("MWP_BOOTSTRAP_WARNING"),
    }
