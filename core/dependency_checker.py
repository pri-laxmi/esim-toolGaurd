
import json
import shutil
import subprocess
import os
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = PROJECT_ROOT / "config" / "dependencies.json"


def load_dependencies():
    """Load configured dependencies from JSON."""

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            config = json.load(file)

        if not isinstance(config, dict):
            raise ValueError("Invalid dependency configuration: root must be an object.")
        tools = config.get("tools", [])
        if not isinstance(tools, list):
            raise ValueError("Invalid dependency configuration: 'tools' must be a list.")
        return tools

    except FileNotFoundError:
        raise FileNotFoundError(
            f"Dependency configuration not found: {CONFIG_PATH}"
        )

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid dependency configuration: {error}"
        )
    except PermissionError as error:
        raise PermissionError(
            f"Cannot read dependency configuration: {CONFIG_PATH}"
        ) from error


def get_tool_version(executable, version_args, version_pattern=None):
    """Retrieve the installed tool's version."""

    try:
        result = subprocess.run(
            [executable, *version_args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )

        if result.returncode != 0:
            return "Version check failed"

        output = result.stdout.strip() or result.stderr.strip()

        if output:
            if version_pattern:
                match = re.search(version_pattern, output, flags=re.IGNORECASE)
                if match:
                    return match.group(1) if match.lastindex else match.group(0)
                return "Version unrecognized"
            for line in output.splitlines():
                if line.strip():
                    return line.strip()

        return "Version unavailable"

    except subprocess.TimeoutExpired:
        return "Version check timed out"

    except (OSError, ValueError, TypeError, re.error):
        return "Version check failed"


def find_executable(tool):
    """Find a tool in PATH, then in its configured installation directory."""

    executable = tool.get("executable")
    if not isinstance(executable, str) or not executable.strip():
        return None

    executable = executable.strip()
    try:
        executable_path = shutil.which(executable)
    except (OSError, ValueError, TypeError):
        executable_path = None
    if executable_path:
        return executable_path

    try:
        install_dirs = []
        install_dir = tool.get("install_dir")
        if install_dir:
            # Expand Windows environment variables (and user-home shorthand).
            install_dirs.append(Path(os.path.expandvars(install_dir)).expanduser())
        for configured_root in tool.get("install_search_roots", []):
            if isinstance(configured_root, str) and configured_root.strip():
                root = Path(os.path.expandvars(configured_root)).expanduser()
                install_dirs.append(root)
                try:
                    # KiCad installers place binaries in a versioned child,
                    # for example KiCad/10.0/bin/kicad-cli.exe.
                    install_dirs.extend(child for child in root.iterdir() if child.is_dir())
                except OSError:
                    continue
        install_dirs.extend(_registry_install_dirs(tool))

        for install_path in install_dirs:
            for candidate in (install_path / "bin" / executable,
                              install_path / executable):
                if candidate.is_file():
                    return str(candidate.resolve())
    except (OSError, ValueError, TypeError):
        return None
    return None


def _registry_install_dirs(tool):
    """Return Windows install locations matching a configured app name."""
    return [location for location, _ in _registry_install_details(tool)]


def _registry_version_for_executable(tool, executable_path):
    """Read DisplayVersion when a matching registered app exposes it."""
    try:
        executable_path = Path(executable_path).resolve()
        for location, version in _registry_install_details(tool):
            if not version:
                continue
            for candidate in (location / "bin" / tool["executable"],
                              location / tool["executable"]):
                if candidate.resolve() == executable_path:
                    return version
    except (OSError, KeyError, TypeError, ValueError):
        pass
    return None


def _registry_install_details(tool):
    """Return matching (install location, display version) registry entries."""
    display_name = tool.get("registry_display_name")
    if os.name != "nt" or not display_name:
        return []

    try:
        import winreg
    except ImportError:
        return []

    uninstall_keys = (
        r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
        r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    )
    matches = []
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for key_name in uninstall_keys:
            try:
                with winreg.OpenKey(hive, key_name) as uninstall_key:
                    entry_count = winreg.QueryInfoKey(uninstall_key)[0]
                    for index in range(entry_count):
                        try:
                            entry_name = winreg.EnumKey(uninstall_key, index)
                            with winreg.OpenKey(uninstall_key, entry_name) as entry:
                                name = winreg.QueryValueEx(entry, "DisplayName")[0]
                                try:
                                    location = winreg.QueryValueEx(entry, "InstallLocation")[0]
                                except OSError:
                                    location = None
                                try:
                                    version = winreg.QueryValueEx(entry, "DisplayVersion")[0]
                                except OSError:
                                    version = None
                            if (isinstance(name, str) and display_name.casefold() in name.casefold()
                                    and isinstance(location, str) and location.strip()):
                                matches.append((
                                    Path(os.path.expandvars(location)).expanduser(),
                                    version if isinstance(version, str) else None,
                                ))
                        except (OSError, ValueError, TypeError):
                            # Uninstall entries commonly omit one or both values.
                            continue
            except OSError:
                # A hive/view may be unavailable due to permissions or OS edition.
                continue
    return matches


def check_tool(tool):
    """Check whether an individual dependency is installed."""

    if not isinstance(tool, dict):
        raise ValueError("Each dependency entry must be a JSON object.")

    name = tool.get("name", "Unknown tool")

    executable_path = find_executable(tool)

    if executable_path is None:
        return {
            "name": name,
            "detected": False,
            "installed": False,
            "compatible": False,
            "status": "Missing",
            "version": "Not Available",
            "path": None,
            "required": tool.get("required", True)
        }

    # Prefer the registered version for packages that provide one. This is
    # fast and avoids starting CLIs that initialize user-specific settings.
    registry_version = _registry_version_for_executable(tool, executable_path)
    if registry_version:
        version = registry_version
        version_source = "registry"
    else:
        version = get_tool_version(
            executable_path,
            tool.get("version_args", []),
            tool.get("version_pattern"),
        )
        version_source = "command"

    if version in (
        "Version unavailable", "Version check timed out", "Version check failed",
        "Version unrecognized",
    ):
        return {
            "name": name,
            "detected": True,
            "installed": False,
            "compatible": False,
            "status": version,
            "version": version,
            "version_source": version_source,
            "path": executable_path,
            "required": tool.get("required", True),
        }

    # get_tool_version applies a tool-specific output pattern; the returned
    # value is the version token itself, so parse it generically here.
    parsed_version = _parse_version(version)
    if parsed_version is None:
        return {
            "name": name,
            "detected": True,
            "installed": False,
            "compatible": False,
            "status": "Version unrecognized",
            "version": version,
            "version_source": version_source,
            "path": executable_path,
            "required": tool.get("required", True),
        }

    requirement = tool.get("version_requirement")
    try:
        compatible = _meets_version_requirement(parsed_version, requirement)
    except (TypeError, ValueError) as error:
        return {
            "name": name,
            "detected": True,
            "installed": False,
            "compatible": False,
            "status": f"Invalid version requirement: {error}",
            "version": version,
            "version_source": version_source,
            "path": executable_path,
            "required": tool.get("required", True),
        }

    status = "Installed" if compatible else "Incompatible version"

    return {
        "name": name,
        "detected": True,
        "installed": compatible,
        "compatible": compatible,
        "status": status,
        "version": version,
        "version_source": version_source,
        "path": executable_path,
        "required": tool.get("required", True)
    }


def _parse_version(value, pattern=None):
    """Extract a numeric version tuple using the configured pattern."""
    if not isinstance(value, str):
        return None
    if pattern:
        try:
            match = re.search(pattern, value, flags=re.IGNORECASE)
        except re.error:
            return None
        if not match:
            return None
        version = match.group(1) if match.lastindex else match.group(0)
    else:
        match = re.search(r"\d+(?:\.\d+)*", value)
        if not match:
            return None
        version = match.group(0)
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError:
        return None


def _meets_version_requirement(version, requirement):
    """Compare a parsed version with configured minimum and maximum bounds."""
    if requirement is None:
        return True
    if not isinstance(requirement, dict):
        raise ValueError("requirement must be an object")

    def normalize(parts, length):
        return parts + (0,) * (length - len(parts))

    minimum_value = requirement.get("minimum")
    maximum_value = requirement.get("maximum")
    bounds = [
        _parse_version(minimum_value) if minimum_value is not None else None,
        _parse_version(maximum_value) if maximum_value is not None else None,
    ]
    if minimum_value is not None and bounds[0] is None:
        raise ValueError(f"invalid minimum version {minimum_value!r}")
    if maximum_value is not None and bounds[1] is None:
        raise ValueError(f"invalid maximum version {maximum_value!r}")

    width = max([len(version), *(len(bound) for bound in bounds if bound is not None)])
    comparable = normalize(version, width)
    minimum, maximum = (
        normalize(bound, width) if bound is not None else None for bound in bounds
    )
    return not (
        (minimum is not None and comparable < minimum)
        or (maximum is not None and comparable > maximum)
    )


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
    detected_count = 0

    for tool in results:

        if tool["installed"]:
            print(f"\n[OK] {tool['name']}")
            print("     Status: Installed")
            print(f"     Version: {tool['version']}")
            print(f"     Path: {tool['path']}")
            installed_count += 1

        else:
            print(f"\n[!] {tool['name']}")
            print(f"     Status: {tool.get('status', 'Missing')}")
            print(f"     Version: {tool['version']}")
            if tool.get("detected") and tool.get("path"):
                print(f"     Path: {tool['path']}")
        if tool.get("detected", tool["installed"]):
            detected_count += 1

    print("\n" + "-" * 45)
    print("SUMMARY")
    print("-" * 45)

    print(f"Total Dependencies : {len(results)}")
    print(f"Compatible         : {installed_count}")
    print(f"Incompatible       : {detected_count - installed_count}")
    print(f"Missing            : {len(results) - detected_count}")

    print("-" * 45)


if __name__ == "__main__":
    dependency_results = check_all_dependencies()
    print_dependency_report(dependency_results)
