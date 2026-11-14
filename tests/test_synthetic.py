"""Regression tests for the offline, synthetic parts of the prototype.

Each script is run as the README describes (from its own directory), but on a
copy of the repository in a temporary directory so committed results are not
overwritten. JSON products must match the committed versions; these are the
numbers quoted in README "Key numbers" and docs/01-02.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


def run(script, cwd, *args):
    p = subprocess.run([sys.executable, script, *args], cwd=cwd,
                       capture_output=True, text=True, timeout=900)
    assert p.returncode == 0, p.stdout[-2000:] + p.stderr[-2000:]
    return p.stdout


@pytest.fixture
def work(tmp_path):
    for d in ["forward", "modflow", "analysis", "pipeline"]:
        shutil.copytree(ROOT / d, tmp_path / d,
                        ignore=shutil.ignore_patterns("mf6_ws", "__pycache__"))
    return tmp_path


def assert_json_close(new, ref, rtol=1e-9, path=""):
    if isinstance(ref, dict):
        assert set(new) == set(ref), f"keys differ at {path}"
        for k in ref:
            assert_json_close(new[k], ref[k], rtol, f"{path}/{k}")
    elif isinstance(ref, list):
        assert len(new) == len(ref), f"length differs at {path}"
        for i, (a, b) in enumerate(zip(new, ref)):
            assert_json_close(a, b, rtol, f"{path}[{i}]")
    elif isinstance(ref, (int, float)) and not isinstance(ref, bool):
        assert np.isclose(new, ref, rtol=rtol, atol=0), f"{path}: {new} != {ref}"
    else:
        assert new == ref, f"{path}: {new!r} != {ref!r}"


def load(p):
    return json.loads(Path(p).read_text())


def test_stretching_recovers_synthetic_dvv(work):
    out = run("dvv_stretch.py", work / "pipeline")
    assert "all synthetic stretching tests passed" in out


def test_phase_test_detects_aquifer_and_rejects_snow_only(work):
    out = run("phase_test.py", work / "analysis", "--selftest")
    assert "selftest passed" in out


def test_forward_model_reproduces_committed_results(work):
    run("forward_dvv.py", work / "forward")
    assert_json_close(load(work / "forward/forward_results.json"),
                      load(ROOT / "forward/forward_results.json"))


def test_band_design_reproduces_committed_results(work):
    run("band_design.py", work / "forward")
    assert_json_close(load(work / "forward/band_design.json"),
                      load(ROOT / "forward/band_design.json"))


@pytest.mark.skipif(shutil.which("mf6") is None, reason="mf6 binary not on PATH")
def test_modflow_hillslope_and_coupling_reproduce_committed_results(work):
    run("hillslope_mf6.py", work / "modflow")
    assert_json_close(load(work / "modflow/hillslope_results.json"),
                      load(ROOT / "modflow/hillslope_results.json"))
    run("couple_dvv.py", work / "modflow")
    assert_json_close(load(work / "modflow/coupled_dvv.json"),
                      load(ROOT / "modflow/coupled_dvv.json"))
