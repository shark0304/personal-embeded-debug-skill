from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DETECT_PATH = ROOT / "scripts" / "project" / "detect_project_context.py"
CREATE_PATH = ROOT / "scripts" / "project" / "create_project_adapter.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


detect_mod = load_module(DETECT_PATH, "detect_project_context")
create_mod = load_module(CREATE_PATH, "create_project_adapter")


def test_detects_zephyr_project(tmp_path: Path) -> None:
    (tmp_path / "west.yml").write_text("manifest:\n  remotes: []\n", encoding="utf-8")
    (tmp_path / "prj.conf").write_text("CONFIG_I2C=y\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")

    context = detect_mod.detect_project_context(tmp_path)

    assert context["primary_adapter"] == "zephyr"
    zephyr = context["adapters"][0]
    assert zephyr["id"] == "zephyr"
    assert "west.yml" in zephyr["evidence"]
    assert any(command["command"].startswith("west build") for command in zephyr["safe_commands"])


def test_detects_esp_idf_project(tmp_path: Path) -> None:
    (tmp_path / "sdkconfig").write_text("CONFIG_IDF_TARGET_ESP32=y\n", encoding="utf-8")
    (tmp_path / "main").mkdir()
    (tmp_path / "main" / "CMakeLists.txt").write_text("idf_component_register(SRCS \"main.c\")\n", encoding="utf-8")

    context = detect_mod.detect_project_context(tmp_path)

    assert context["primary_adapter"] == "esp-idf"
    adapter = context["adapters"][0]
    assert adapter["id"] == "esp-idf"
    assert any(command["risk"] == "hardware-write" for command in adapter["safe_commands"])


def test_detects_stm32cube_project(tmp_path: Path) -> None:
    (tmp_path / "demo.ioc").write_text("ProjectManager.ProjectName=demo\n", encoding="utf-8")
    (tmp_path / "Core" / "Src").mkdir(parents=True)
    (tmp_path / "Core" / "Src" / "main.c").write_text("int main(void) { while (1) {} }\n", encoding="utf-8")
    (tmp_path / "Drivers" / "CMSIS").mkdir(parents=True)
    (tmp_path / "STM32H743.ld").write_text("MEMORY {}\n", encoding="utf-8")

    context = detect_mod.detect_project_context(tmp_path)

    assert context["primary_adapter"] == "stm32cube"
    assert any(adapter["id"] == "cmake-baremetal" or adapter["id"] == "make-baremetal" for adapter in context["adapters"]) is False


def test_detects_linux_module_project(tmp_path: Path) -> None:
    (tmp_path / "Kbuild").write_text("obj-m += demo_driver.o\n", encoding="utf-8")
    (tmp_path / "demo_driver.c").write_text("MODULE_LICENSE(\"GPL\");\n", encoding="utf-8")

    context = detect_mod.detect_project_context(tmp_path)

    assert context["primary_adapter"] == "embedded-linux"
    adapter = context["adapters"][0]
    assert adapter["id"] == "embedded-linux"
    assert any(command["risk"] == "kernel-runtime-change" for command in adapter["safe_commands"])


def test_detects_platformio_project(tmp_path: Path) -> None:
    (tmp_path / "platformio.ini").write_text("[env:nucleo_f401re]\nplatform = ststm32\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.cpp").write_text("int main() { return 0; }\n", encoding="utf-8")

    context = detect_mod.detect_project_context(tmp_path)

    assert context["primary_adapter"] == "platformio"
    assert context["adapters"][0]["id"] == "platformio"


def test_create_project_adapter_writes_guardrails(tmp_path: Path) -> None:
    (tmp_path / "FreeRTOSConfig.h").write_text("#define configUSE_PREEMPTION 1\n", encoding="utf-8")
    context = detect_mod.detect_project_context(tmp_path)
    out_dir = tmp_path / "debug" / "embedded_debug_adapter"

    create_mod.create_adapter(tmp_path, out_dir, context, overwrite=True)

    context_file = out_dir / "project_debug_context.json"
    adapter_file = out_dir / "PROJECT_DEBUG_ADAPTER.md"
    risk_file = out_dir / "command_risk_policy.md"
    assert json.loads(context_file.read_text(encoding="utf-8"))["primary_adapter"] == "freertos"
    assert "debugger-attached" in adapter_file.read_text(encoding="utf-8")
    assert "hardware-write" in risk_file.read_text(encoding="utf-8")
