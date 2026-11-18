import os
import urllib.request
import tempfile
import py7zr

from pathlib import Path
import shutil
import subprocess


def check_winget():
    """Check whether winget is available."""

    return shutil.which("winget") is not None


def install_with_winget(package_id):
    """Install a package using Windows Package Manager."""

    if not check_winget():
        return {
            "success": False,
            "message": "winget is not installed or unavailable."
        }

    command = [
        "winget",
        "install",
        "--id", package_id,
        "--exact",
        "--source", "winget",
        "--accept-source-agreements",
        "--accept-package-agreements"
    ]

    try:
        print(f"\nStarting installation: {package_id}")

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=1800,
            check=False
        )

        if result.returncode == 0:
            return {
                "success": True,
                "message": "Installation completed successfully."
            }

        return {
            "success": False,
            "message": result.stderr.strip() or result.stdout.strip()
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "Installation timed out."
        }

    except OSError as error:
        return {
            "success": False,
            "message": str(error)
        }


def confirm_installation(tool_name):
    """Ask the user before installing a tool."""

    choice = input(
        f"\nDo you want to install {tool_name}? (y/n): "
    ).strip().lower()

    return choice == "y"

def install_tool(tool):

    provider = tool.get("installer")

    if provider == "winget":
        return install_with_winget(
            tool.get("package_id")
        )

    elif provider == "official_archive":
        return install_ngspice(tool)

    return {
        "success": False,
        "message": f"Unsupported installer: {provider}"
    }

def install_ngspice(tool):
    """Download and extract official Ngspice Windows binaries."""

    if os.name != "nt":
        return {
            "success": False,
            "message": "This installer currently supports Windows only."
        }

    download_url = tool.get("download_url")
    configured_dir = tool.get("install_dir")

    if not download_url or not configured_dir:
        return {
            "success": False,
            "message": "Ngspice download configuration is incomplete."
        }

    install_dir = Path(
        os.path.expandvars(configured_dir)
    )

    if not install_dir.is_absolute():
        return {
            "success": False,
            "message": "Installation directory must be absolute."
        }

    if not confirm_installation("Ngspice"):
        return {
            "success": False,
            "message": "Installation cancelled by user."
        }

    archive_path = None
    staging_dir = None

    try:
        install_dir.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # Check available disk space before downloading.
        free_space = shutil.disk_usage(
            install_dir.parent
        ).free

        print(f"\nAvailable disk space: {free_space / (1024**2):.1f} MB")

        print("\nDownloading Ngspice...")

        # Use a temporary archive so we don't retain
        # unnecessary downloaded files.
        with tempfile.NamedTemporaryFile(
            suffix=".7z",
            delete=False
        ) as archive:
            archive_path = Path(archive.name)

        request = urllib.request.Request(
            download_url,
            headers={"User-Agent": "eSim-ToolGuard/1.0"}
        )

        with urllib.request.urlopen(
            request,
            timeout=30
        ) as response:

            with open(archive_path, "wb") as file:
                shutil.copyfileobj(response, file)

        if archive_path.stat().st_size == 0:
            raise ValueError("Downloaded archive is empty.")

        print("Download completed.")

        # Extract into a temporary staging directory.
        staging_dir = Path(
            tempfile.mkdtemp(prefix="esim_ngspice_")
        )

        print("\nExtracting Ngspice archive...")

        with py7zr.SevenZipFile(
            archive_path,
            mode="r"
        ) as archive:

            archive.extractall(path=staging_dir)

        # Locate the executable inside the extracted files.
        executables = list(
            staging_dir.rglob("ngspice.exe")
        )

        if not executables:
            raise FileNotFoundError(
                "ngspice.exe was not found in the archive."
            )

        # Find the executable's installation root.
        executable = executables[0]
        source_root = executable.parent.parent

        # Move the extracted installation tree into place.
        if install_dir.exists():
            shutil.rmtree(install_dir)

        shutil.move(
            str(source_root),
            str(install_dir)
        )

        final_executable = (
            install_dir /
            "bin" /
            "ngspice.exe"
        )

        if not final_executable.exists():
            raise FileNotFoundError(
                "Ngspice executable missing after extraction."
            )

        # Verify the installation.
        result = subprocess.run(
            [str(final_executable), "-v"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False
        )

        version_output = (
            result.stdout.strip()
            or result.stderr.strip()
        )

        if result.returncode != 0 or not version_output:
            raise RuntimeError(
                "Ngspice installation verification failed."
            )

        return {
            "success": True,
            "message": "Ngspice installed and verified.",
            "path": str(final_executable),
            "version": version_output.splitlines()[0]
        }

    except Exception as error:

        return {
            "success": False,
            "message": f"Ngspice installation failed: {error}"
        }

    finally:

        # Clean up temporary files.
        if archive_path and archive_path.exists():
            archive_path.unlink()

        if staging_dir and staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)
