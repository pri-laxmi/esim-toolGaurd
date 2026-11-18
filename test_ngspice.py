import json
from core.installer import install_tool

with open("config/dependencies.json", "r") as file:
    config = json.load(file)

ngspice = next(
    tool for tool in config["tools"]
    if tool["name"] == "Ngspice"
)

result = install_tool(ngspice)

print("\nInstallation Result")
print("-------------------")
print("Success:", result["success"])
print("Message:", result["message"])