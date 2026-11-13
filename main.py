import json
import platform
from pathlib import Path


def load_dependencies():
    config_path = Path("config/dependencies.json")

    with open(config_path, "r") as file:
        config = json.load(file)

    return config["tools"]


def main():
    print("=" * 45)
    print("          eSim ToolGuard v1.0")
    print("=" * 45)

    print(f"Operating System: {platform.system()}")
    print(f"Python Version: {platform.python_version()}")

    tools = load_dependencies()

    print("\nConfigured Dependencies:")

    for tool in tools:
        print(f"- {tool['name']} ({tool['executable']})")

    print("\nToolGuard initialized successfully!")


if __name__ == "__main__":
    main()