"""Terminal view of configured and detected tools."""

from core.dependency_checker import check_all_dependencies


def get_installed_tools():
    """Return only tools that were successfully detected."""
    return [tool for tool in check_all_dependencies() if tool["installed"]]


def display_installed_tools():
    """Print status for every configured tool and an installation summary."""
    results = check_all_dependencies()
    print("\n" + "=" * 45)
    print("       eSim ToolGuard - Installed Tools")
    print("=" * 45)

    for tool in results:
        if tool["installed"]:
            print(f"\n[OK] {tool['name']}")
            print("     Status: Installed")
            print(f"     Version: {tool['version']}")
            print(f"     Path: {tool['path']}")
        else:
            print(f"\n[!] {tool['name']}")
            print(f"     Status: {tool.get('status', 'Missing')}")
            print(f"     Version: {tool['version']}")
            print(f"     Path: {tool.get('path') or 'Not Found'}")

    installed_count = sum(tool["installed"] for tool in results)
    detected_count = sum(tool.get("detected", tool["installed"]) for tool in results)
    total_count = len(results)
    print("\n" + "-" * 45)
    print("SUMMARY")
    print("-" * 45)
    print(f"Total Configured Tools : {total_count}")
    print(f"Compatible Tools       : {installed_count}")
    print(f"Version Incompatible   : {detected_count - installed_count}")
    print(f"Missing Tools          : {total_count - detected_count}")
    print("-" * 45)
    return results


if __name__ == "__main__":
    display_installed_tools()
