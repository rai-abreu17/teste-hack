import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FirmwareSensorHostTests(unittest.TestCase):
    def test_sim_sensor_acquisition_contract(self):
        compiler = shutil.which("g++")
        if compiler is None:
            self.skipTest("g++ is not available for the host C++ check")
        output = ROOT / "build" / "tests"
        output.mkdir(parents=True, exist_ok=True)
        executable = output / "firmware_sensor_host.exe"
        subprocess.run(
            [
                compiler,
                "-std=c++11",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-I",
                str(ROOT / "tests" / "firmware_fakes"),
                "-I",
                str(ROOT / "wokwi"),
                str(ROOT / "wokwi" / "SimTofSensor.cpp"),
                str(ROOT / "tests" / "firmware_sensor_host.cpp"),
                "-o",
                str(executable),
            ],
            check=True,
        )
        completed = subprocess.run(
            [str(executable)], check=True, capture_output=True, text=True
        )
        self.assertIn("host checks passed", completed.stdout)

    def test_build_stage_contains_sensor_sources(self):
        subprocess.run(
            ["python", str(ROOT / "tools" / "build_firmware.py"), "--stage-only"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        stage = ROOT / "build" / "arduino" / "BoxFlow"
        expected = {
            "BoxFlow.ino",
            "config.h",
            "ITofSensor.h",
            "SimTofSensor.h",
            "SimTofSensor.cpp",
        }
        self.assertTrue(expected.issubset({path.name for path in stage.iterdir()}))
        sketch = (stage / "BoxFlow.ino").read_text(encoding="utf-8")
        self.assertIn("#define BOXFLOW_SIM 1", sketch)
        self.assertIn("#error", sketch)


if __name__ == "__main__":
    unittest.main(verbosity=2)
