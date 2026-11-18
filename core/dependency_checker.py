
import json
import shutil
import subprocess
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = PROJECT_ROOT / "config" / "dependencies.json"


def load_dependencies():
    """Load configured dependencies from JSON."""

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            config = json.load(file)

        return config.get("tools", [])

    except FileNotFoundError:
        raise FileNotFoundError(
            f"Dependency configuration not found: {CONFIG_PATH}"
        )

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid dependency configuration: {error}"
        )


def get_tool_version(executable, version_args):
    """Retrieve the installed tool's version."""

    try:
        result = subprocess.run(
            [executable, *version_args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )

        output = result.stdout.strip() or result.stderr.strip()

        if output:
            for line in output.splitlines():
                if line.strip():
                    return line.strip()

        return "Version unavailable"

    except subprocess.TimeoutExpired:
        return "Version check timed out"

    except OSError:
        return "Version check failed"


def find_executable(tool):
    """Find a tool in PATH, then in its configured installation directory."""

    executable = tool["executable"]
    executable_path = shutil.which(executable)
    if executable_path:
        return executable_path

    install_dir = tool.get("install_dir")
    if not install_dir:
        return None

    # Expand Windows environment variables (and any user-home shorthand).
    install_path = Path(os.path.expandvars(install_dir)).expanduser()
    for candidate in (install_path / "bin" / executable,
                      install_path / executable):
        if candidate.is_file():
            return str(candidate.resolve())
    return None


def check_tool(tool):
    """Check whether an individual dependency is installed."""

    name = tool["name"]
    executable = tool["executable"]

    executable_path = find_executable(tool)

    if executable_path is None:
        return {
            "name": name,
            "installed": False,
            "version": "Not Available",
            "path": None,
            "required": tool.get("required", True)
        }

    version = get_tool_version(
        executable_path,
        tool.get("version_args", [])
    )

    return {
        "name": name,
        "installed": True,
        "version": version,
        "path": executable_path,
        "required": tool.get("required", True)
    }


def check_all_dependencies():
    """Check every configured dependency."""

    dependencies = load_dependencies()

    results = []

    for tool in dependencies:
        results.append(check_tool(tool))

    return results


def print_dependency_report(results):
    """Display dependency status in the terminal."""

    print("\n" + "=" * 45)
    print("       eSim ToolGuard - Dependency Check")
    print("=" * 45)

    installed_count = 0
    missing_count = 0

    for tool in results:

        if tool["installed"]:
            print(f"\n[OK] {tool['name']}")
            print("     Status: Installed")
            print(f"     Version: {tool['version']}")
            print(f"     Path: {tool['path']}")
            installed_count += 1

        else:
            print(f"\n[!] {tool['name']}")
            print("     Status: Missing")
            print(f"     Version: {tool['version']}")
            missing_count += 1

    print("\n" + "-" * 45)
    print("SUMMARY")
    print("-" * 45)

    print(f"Total Dependencies : {len(results)}")
    print(f"Installed          : {installed_count}")
    print(f"Missing            : {missing_count}")

    print("-" * 45)


if __name__ == "__main__":
    dependency_results = check_all_dependencies()
    print_dependency_report(dependency_results)
