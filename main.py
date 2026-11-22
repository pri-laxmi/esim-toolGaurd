"""Central command-line interface for eSim ToolGuard."""

from core.dependency_checker import (
    check_all_dependencies,
    load_dependencies,
    print_dependency_report,
)
from core.installer import install_tool
from core.tool_manager import display_installed_tools
from utils.logger import get_logs, log_action, log_error, setup_logger


def _pause():
    try:
        input("\nPress Enter to return to the main menu...")
    except (EOFError, KeyboardInterrupt):
        print()


def _check_dependencies():
    try:
        results = check_all_dependencies()
        print_dependency_report(results)
        installed = sum(tool["installed"] for tool in results)
        log_action(f"Dependency check completed: {installed}/{len(results)} detected.")
    except Exception as error:
        print(f"\nUnable to check dependencies: {error}")
        log_error(f"Dependency check failed: {error}")


def _install_a_tool():
    try:
        tools = load_dependencies()
        if not tools:
            print("No tools are configured for installation.")
            log_action("Installation menu opened; no tools are configured.")
            return

        detected = {tool["name"]: tool for tool in check_all_dependencies()}
        print("\nAvailable tools:")
        for index, tool in enumerate(tools, start=1):
            status = " (already installed)" if detected.get(tool["name"], {}).get("installed") else ""
            print(f"  {index}. {tool['name']}{status}")

        selection = input("Select a tool number (or 0 to cancel): ").strip()
        if not selection.isdigit():
            print("Invalid selection. Enter a number from the list.")
            log_error(f"Invalid tool selection: {selection!r}")
            return
        choice = int(selection)
        if choice == 0:
            print("Installation cancelled.")
            log_action("Tool installation cancelled at selection.")
            return
        if choice < 1 or choice > len(tools):
            print("Invalid selection. No tool has that number.")
            log_error(f"Tool selection out of range: {choice}")
            return

        tool = tools[choice - 1]
        if detected.get(tool["name"], {}).get("installed"):
            print(f"{tool['name']} is already detected; skipping reinstallation.")
            log_action(f"Installation skipped; {tool['name']} is already detected.")
            return

        confirmation = input(f"Install {tool['name']}? (y/n): ").strip().lower()
        if confirmation not in ("y", "yes"):
            print("Installation cancelled.")
            log_action(f"Installation of {tool['name']} cancelled by user.")
            return

        log_action(f"Installation attempt started for {tool['name']}.")
        result = install_tool(tool, confirmed=True)
        if result.get("success"):
            print(f"\nSuccess: {result.get('message', 'Installation completed.')}")
            log_action(f"Installation succeeded for {tool['name']}: {result.get('message', '')}")
        else:
            print(f"\nInstallation failed: {result.get('message', 'Unknown error')}")
            log_error(f"Installation failed for {tool['name']}: {result.get('message', 'Unknown error')}")
    except Exception as error:
        print(f"\nUnable to install tool: {error}")
        log_error(f"Tool installation flow failed: {error}")


def _view_installed_tools():
    try:
        display_installed_tools()
        log_action("Installed tools list viewed.")
    except Exception as error:
        print(f"\nUnable to display installed tools: {error}")
        log_error(f"Installed tools display failed: {error}")


def _view_logs():
    # Write first so this visit is included in the displayed log history.
    log_action("Action logs viewed.")
    print("\n" + "=" * 45)
    print("       eSim ToolGuard - Action Logs")
    print("=" * 45)
    logs = get_logs()
    if logs.strip():
        print(logs, end="" if logs.endswith("\n") else "\n")
    else:
        print("No action logs are available yet.")


def _show_menu():
    print("\nMain Menu")
    print("1. Check Dependencies")
    print("2. Install a Tool")
    print("3. View Installed Tools")
    print("4. View Action Logs")
    print("5. Exit")


def main():
    setup_logger()
    print("=" * 45)
    print("          eSim ToolGuard v1.0")
    print("=" * 45)
    log_action("Application started.")

    while True:
        _show_menu()
        try:
            choice = input("\nSelect an option (1-5): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting eSim ToolGuard.")
            log_action("Application exited by keyboard interruption or end of input.")
            break

        if choice == "1":
            _check_dependencies()
            _pause()
        elif choice == "2":
            _install_a_tool()
            _pause()
        elif choice == "3":
            _view_installed_tools()
            _pause()
        elif choice == "4":
            _view_logs()
            _pause()
        elif choice == "5":
            print("\nThank you for using eSim ToolGuard.")
            log_action("Application exited normally.")
            break
        else:
            print("Invalid menu selection. Enter a number from 1 to 5.")
            log_error(f"Invalid menu selection: {choice!r}")


if __name__ == "__main__":
    main()
