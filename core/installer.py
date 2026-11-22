import os
import urllib.request
import tempfile

from pathlib import Path
import shutil
import subprocess
import re
import uuid

from utils.logger import log_action, log_error


def check_winget():
    """Check whether winget is available."""
    try:
        return shutil.which("winget") is not None
    except OSError as error:
        log_error(f"Unable to check for winget: {error}")
        return False


def install_with_winget(package_id):
    """Install a package using Windows Package Manager."""

    if not isinstance(package_id, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._-]*", package_id
    ):
        message = "Invalid winget package ID."
        log_error(message)
        return {"success": False, "message": message}

    if not check_winget():
        log_error("winget installation failed: winget is not installed or unavailable.")
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
            log_action(f"winget installation succeeded for {package_id}.")
            return {
                "success": True,
                "message": "Installation completed successfully."
            }

        message = result.stderr.strip() or result.stdout.strip() or "winget installation failed."
        log_error(f"winget installation failed for {package_id}: {message}")
        return {
            "success": False,
            "message": message
        }

    except subprocess.TimeoutExpired:
        log_error(f"winget installation timed out for {package_id}.")
        return {
            "success": False,
            "message": "Installation timed out."
        }

    except OSError as error:
        log_error(f"winget installation failed for {package_id}: {error}")
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

def install_tool(tool, confirmed=False):

    if not isinstance(tool, dict):
        message = "Invalid tool configuration."
        log_error(message)
        return {"success": False, "message": message}

    provider = tool.get("installer")
    name = tool.get("name", "Unknown tool")
    log_action(f"Installation requested for {name}.")

    if provider == "winget":
        result = install_with_winget(tool.get("package_id"))

    elif provider == "official_archive":
        result = install_ngspice(tool, confirmed=confirmed)

    else:
        result = {
            "success": False,
            "message": f"Unsupported installer: {provider}"
        }

    if result.get("success"):
        log_action(f"Installation completed for {name}.")
    elif "winget installation" not in result.get("message", "").lower():
        log_error(f"Installation failed for {name}: {result.get('message', 'Unknown error')}")
    return result

def install_ngspice(tool, confirmed=False):
    """Download and extract official Ngspice Windows binaries."""

    try:
        import py7zr
    except ImportError:
        return {
            "success": False,
            "message": "The py7zr package is required to install Ngspice."
        }

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

    if not confirmed and not confirm_installation("Ngspice"):
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

        # Extract beside the target so the final directory rename stays on
        # the same volume and can be rolled back without copying files.
        staging_dir = Path(
            tempfile.mkdtemp(
                prefix=".esim_ngspice_staging_",
                dir=str(install_dir.parent),
            )
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

        # Find and verify the new installation before touching the current one.
        executable = executables[0]
        source_root = executable.parent.parent
        staged_executable = source_root / "bin" / "ngspice.exe"
        if not staged_executable.is_file():
            raise FileNotFoundError(
                "Ngspice executable missing from the extracted installation."
            )

        # Verify the staged binary before replacing an existing installation.
        result = subprocess.run(
            [str(staged_executable), "-v"],
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

        backup_dir = _swap_install_directory(source_root, install_dir)
        if backup_dir is not None:
            try:
                _remove_path(backup_dir)
            except OSError as error:
                # The replacement is already verified and active. Keep the
                # backup if cleanup fails so it can still be recovered.
                log_error(f"Ngspice installed, but old backup could not be removed: {error}")

        return {
            "success": True,
            "message": "Ngspice installed and verified.",
            "path": str(install_dir / "bin" / "ngspice.exe"),
            "version": version_output.splitlines()[0]
        }

    except Exception as error:

        return {
            "success": False,
            "message": f"Ngspice installation failed: {error}"
        }

    finally:

        # Clean up temporary files.
        if archive_path:
            try:
                if archive_path.exists():
                    archive_path.unlink()
            except OSError as error:
                log_error(f"Ngspice archive cleanup failed: {error}")
        if staging_dir:
            try:
                if staging_dir.exists():
                    _remove_path(staging_dir)
            except OSError as error:
                log_error(f"Ngspice staging cleanup failed: {error}")


def _swap_install_directory(staged_install, install_dir):
    """Atomically activate a staged install, restoring the old one on error."""
    backup_dir = None
    if install_dir.exists():
        backup_dir = install_dir.with_name(
            f"{install_dir.name}.backup-{uuid.uuid4().hex}"
        )
        install_dir.rename(backup_dir)

    try:
        staged_install.rename(install_dir)
    except OSError as install_error:
        if backup_dir is not None:
            try:
                if install_dir.exists():
                    _remove_path(install_dir)
                backup_dir.rename(install_dir)
            except OSError as rollback_error:
                raise RuntimeError(
                    f"Replacement failed and rollback could not complete; "
                    f"the previous installation remains at {backup_dir}: {rollback_error}"
                ) from install_error
        raise
    return backup_dir


def _remove_path(path):
    """Remove a file, symlink, or directory tree."""
    if path.is_symlink() or not path.is_dir():
        if path.exists() or path.is_symlink():
            path.unlink()
    elif path.exists():
        shutil.rmtree(path)
