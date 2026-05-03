# Kira

Kira is a specialized expert assistant for Arch Linux and the Hyprland window manager, powered by Gemini 2.5.

## Features
- **Arch Linux Specialist:** Expert in `pacman`, `yay`, `systemd`.
- **Hyprland Expert:** Control your environment via `hyprctl`.
- **YOLO Mode:** Automated command execution for efficiency.
- **Persistent Memory:** Learns and remembers your preferences.
- **Screenshot Support:** Grab screenshots directly from the CLI.
- **Beautiful UI:** Uses `rich` for markdown and streaming.

## Installation

### Prerequisites
- Python 3.8+
- Arch Linux (recommended)
- A Gemini API Key

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/eliakimrosil/Kira.git
   cd Kira
   ```
2. Create and configure `.env`:
   ```bash
   mkdir -p ~/.config/kira
   # Copy .env.example to ~/.config/kira/.env and add your GEMINI_API_KEY
   ```
3. Install the package:
   - **Professional Arch way:**
     ```bash
     makepkg -si
     ```
   - **Manual Python way:**
     ```bash
     pip install .
     ```

## Usage
Run the assistant directly:
```bash
kira "check my system disk space"
```

Or enter interactive mode:
```bash
kira
```
