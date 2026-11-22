# eSim ToolGuard 🛠️
### Automated Tool Manager for eSim

**eSim ToolGuard** is a Python-based command-line application designed to simplify the installation, detection, and management of external tools required by eSim.

Managing external dependencies such as Ngspice and KiCad manually can be tedious. ToolGuard aims to automate this process by providing dependency detection, version compatibility checks, installation workflows, installed-tool tracking, and persistent action logging through a simple CLI.

---

## ✨ Features

### 1. Dependency Checker
- Automatically checks whether required external tools are available on the system.
- Detects executable paths using system PATH and configured installation locations.
- Retrieves installed tool versions.
- Compares detected versions against configured version requirements.
- Reports missing tools, unavailable versions, and incompatible versions.

### 2. Automated Tool Installation
- Supports multiple installation strategies.
- Uses **Windows Package Manager (winget)** for supported applications such as KiCad.
- Supports an archive-based installation workflow for Ngspice.
- Checks installation prerequisites before proceeding.
- Requests user confirmation before installation.

### 3. Safe Installation and Recovery
- Uses a staging directory for new Ngspice installations.
- Verifies the new installation before replacing the existing one.
- Preserves the previous installation through a backup.
- Restores the previous installation if the replacement operation fails.
- Helps prevent failed installation attempts from destroying an existing working installation.

### 4. Version Compatibility Management
- Defines version requirements for individual tools in the configuration file.
- Checks whether the detected version satisfies the configured requirement.
- Does not treat a tool as compatible when its version command fails or its version cannot be determined.

### 5. Installed Tools Manager
- Displays detected tools.
- Shows available version and executable path information.
- Provides a consolidated overview of the dependency status.

### 6. Action Logging
- Maintains a persistent action log.
- Records important operations, installation attempts, and errors.
- Includes timestamps and log severity levels.
- Allows users to view previous actions directly through the CLI.

### 7. Command-Line Interface
Provides an interactive menu to access the application's main functionalities without manually executing individual modules.

---

## 🏗️ System Architecture

ToolGuard follows a modular architecture in which each component handles a specific responsibility.

```text
                  USER
                    |
                    v
          +-------------------+
          |    main.py        |
          |   CLI Interface   |
          +-------------------+
                    |
          +---------+----------+
          |         |          |
          v         v          v
     Dependency  Installer  Tool Manager
      Checker
          |         |          |
          +---------+----------+
                    |
          +---------+----------+
          |                    |
          v                    v
   dependencies.json       Logger
   Tool Configuration         |
                              v
                       actions.log
```

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `main.py` | Main CLI and application control |
| `dependency_checker.py` | Executable detection and version compatibility checks |
| `installer.py` | Tool installation and safe replacement workflows |
| `tool_manager.py` | Installed-tool inventory |
| `logger.py` | Persistent action and error logging |
| `system_info.py` | System information and platform-related utilities |
| `dependencies.json` | Tool metadata and installation configuration |

---

## 📁 Project Structure

```text
esim-toolguard/
│
├── config/
│   └── dependencies.json
│
├── core/
│   ├── dependency_checker.py
│   ├── installer.py
│   └── tool_manager.py
│
├── utils/
│   ├── logger.py
│   └── system_info.py
│
├── tests/
│   ├── test_dependency_checker.py
│   ├── test_installer.py
│   └── test_tool_manager.py
│
├── logs/
│   └── actions.log
│
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## ⚙️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application development |
| JSON | Tool configuration and metadata |
| subprocess | Executing system commands |
| shutil | Executable discovery and file operations |
| pathlib | Cross-platform path handling |
| logging | Persistent action logging |
| winget | Windows package management |
| py7zr | Extraction of 7z archives |
| pytest | Automated testing |

---

## 🚀 Getting Started

### Prerequisites

Before running eSim ToolGuard, ensure that you have:

- Windows 11 (current development environment).
- Python 3.10 or later.
- pip (Python package installer).
- Git.
- Windows Package Manager (winget) for supported package installations.

### 1. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
```

Navigate into the project directory:

```bash
cd esim-toolguard
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it using PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python main.py
```

---

## 🖥️ Using the Application

After launching the application, the CLI displays an interactive menu.

The available operations include:

1. **Check Dependencies** – Detect required tools and validate their versions.
2. **Install a Tool** – Select and install a supported external tool.
3. **View Installed Tools** – Display the detected tools and their available information.
4. **View Action Logs** – Display previously recorded operations and errors.
5. **Exit** – Close the application.

Select the corresponding menu option and follow the prompts.

---

## 🔧 Configuration

ToolGuard uses:

```text
config/dependencies.json
```

This file stores metadata for each managed tool, including:

- Tool name.
- Executable name.
- Version command arguments.
- Required status.
- Version requirement.
- Installation provider.
- Package identifier or archive details.
- Installation directory, where applicable.

Example configuration structure:

```json
{
  "tools": [
    {
      "name": "Ngspice",
      "executable": "ngspice.exe",
      "version_args": ["-v"],
      "required": true,
      "installer": "official_archive"
    },
    {
      "name": "KiCad",
      "executable": "kicad-cli.exe",
      "version_args": ["version"],
      "required": true,
      "installer": "winget",
      "package_id": "KiCad.KiCad"
    }
  ]
}
```

**Note:** The actual configuration file may contain additional fields, including version requirements and installation paths. Refer to `config/dependencies.json` for the complete configuration used by the application.

---

## 🛡️ Installation Safety

One important design consideration in ToolGuard is protecting existing installations.

For Ngspice, the replacement process follows this sequence:

```text
Download New Archive
        |
        v
Extract to Staging Directory
        |
        v
Verify New Installation
        |
        v
Backup Existing Installation
        |
        v
Replace Existing Installation
        |
        v
    Successful?
      /     \
    Yes      No
     |        |
     v        v
 Remove    Restore Backup
 Backup   and Report Error
```

This approach reduces the risk of losing an existing working installation when an update or replacement fails.

---

## 🧪 Testing

ToolGuard includes automated tests for its core modules.

Install pytest if it is not already included in your dependencies:

```bash
pip install pytest
```

Run the test suite:

```bash
python -m pytest -v
```

### Suggested Testing Scenarios

| Component | Test scenarios |
|---|---|
| Dependency Checker | Installed tools, missing tools, version detection, incompatible versions |
| Installer | Installation success, cancellation, missing package manager, installation failure |
| Safe Replacement | Existing installation preservation, replacement failure, backup restoration |
| Tool Manager | Installed-tool listing and version information |
| CLI | Valid selections, invalid input, menu navigation |
| Logger | Action recording and log persistence |

External installation commands should be mocked during automated tests to avoid unwanted software installations.

---

## ⚠️ Current Scope and Limitations

- The current development and testing environment is Windows 11.
- Installation support depends on the availability of the configured installation provider.
- Actual installation success depends on network connectivity, available disk space, and system permissions.
- Version detection depends on the version output supported by each external tool.
- Automatic update discovery and advanced user-specific configuration management are not currently part of the prototype.
- Linux and macOS package-manager support can be added in future versions.

---

## 🔮 Future Enhancements

Potential improvements include:

- Automated update discovery and upgrade management.
- Linux support through package managers such as APT.
- macOS support through Homebrew.
- Advanced environment-variable and PATH management.
- Dependency relationship management and installation ordering.
- GUI-based tool management.
- Exportable diagnostic reports.

---

## 🎯 Project Objective

The primary objective of eSim ToolGuard is to reduce the manual effort involved in managing external dependencies required by eSim.

By combining dependency detection, version compatibility validation, safer installation workflows, and centralized action logging, the project provides a modular foundation that can be extended into a more comprehensive tool-management solution.

---

## 👩‍💻 Project Information

**Project:** eSim ToolGuard – Automated Tool Manager  
**Domain:** Software Development / Automation  
**Language:** Python  
**Interface:** Command-Line Interface (CLI)  
**Target Environment:** Windows 11

Developed as part of the **eSim Winter Internship 2026 – Task 5**.

---
