import json

from core.installer import install_tool


def main():
    with open("config/dependencies.json", "r", encoding="utf-8") as file:
        config = json.load(file)

    kicad = next(
        tool for tool in config["tools"]
        if tool["name"] == "KiCad"
    )
    result = install_tool(kicad)

    print("\nInstallation Result")
    print("-------------------")
    print("Success:", result["success"])
    print("Message:", result["message"])


if __name__ == "__main__":
    main()
