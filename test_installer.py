import json

from core.installer import install_tool


with open("config/dependencies.json", "r") as file:
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