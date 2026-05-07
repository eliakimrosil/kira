# 🤖 Kira

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Arch Linux](https://img.shields.io/badge/platform-Arch%20Linux-blueviolet.svg)](https://archlinux.org/)

**Kira** is a specialized expert assistant for Arch Linux and the Hyprland window manager, powered by Google's Gemini 2.0. It's designed to help you manage your system, troubleshoot issues, and automate tasks through a beautiful CLI interface.

---

## ✨ Features

-   **Arch Linux Specialist:** Deep knowledge of `pacman`, `yay`, and `systemd` configurations.
-   **Hyprland Expert:** Seamless integration with `hyprctl` for window management and workspace control.
-   **System Automation:** "YOLO Mode" for automated command execution (use with caution!).
-   **Hardware Control:** Manage Bluetooth devices via `bluetoothctl` and monitor system resources.
-   **Persistent Memory:** Kira learns from your interactions and adapts to your preferences.
-   **Multimedia Integration:** Built-in screenshot support and `mpv` integration for music/video.
-   **Beautiful UI:** Powered by `rich` for elegant markdown rendering and status indicators.

---

## 🚀 Installation

### 🏔️ On Arch Linux (Recommended)

Kira is built for Arch. You can install it using `makepkg`:

```bash
git clone https://github.com/eliakimrosil/Kira.git
cd Kira
makepkg -si
```

### 🐍 Generic Python Installation

For other distributions or if you prefer `pip`:

```bash
git clone https://github.com/eliakimrosil/Kira.git
cd Kira
pip install .
```

---

## ⚙️ Configuration

Kira requires a Gemini API Key.

1.  Obtain an API key from [Google AI Studio](https://aistudio.google.com/).
2.  Create a configuration directory:
    ```bash
    mkdir -p ~/.config/kira
    ```
3.  Set up your environment variables:
    ```bash
    cp .env.example ~/.config/kira/.env
    # Edit ~/.config/kira/.env and add your GEMINI_API_KEY
    ```

---

## 🛠️ Usage

### Interactive Mode
Simply run `kira` to enter the interactive shell:
```bash
kira
```

### Command Mode
Ask Kira a quick question or give a command directly:
```bash
kira "How do I check my system logs for errors in the last 10 minutes?"
kira "Set my secondary monitor to 144Hz"
```

---

## 📦 Project Structure

-   `src/kira/`: Core logic and source code.
-   `PKGBUILD`: Arch Linux package build script.
-   `pyproject.toml`: Python project metadata and dependencies.
-   `Makefile`: Shortcuts for common development tasks.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Made with ❤️ by Master Kim*
