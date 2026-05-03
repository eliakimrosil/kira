#!/usr/bin/env python3
import os
import subprocess
import json
import uuid
import re
import argparse
import sys
import readline
import time
import asyncio
import pyaudio
import ctypes
from contextlib import contextmanager
from google import genai
from google.genai import types
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live

# Suppress ALSA/JACK errors
ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p)
def py_error_handler(filename, line, function, err, fmt):
    pass
c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def no_alsa_error():
    try:
        asound = ctypes.cdll.LoadLibrary('libasound.so.2')
        asound.snd_lib_error_set_handler(c_error_handler)
        yield
        asound.snd_lib_error_set_handler(None)
    except:
        yield

console = Console()

# Constants - Using user's home directory for persistent data
HOME_DIR = os.path.expanduser("~")
DATA_DIR = os.path.join(HOME_DIR, ".config", "kira")
os.makedirs(DATA_DIR, exist_ok=True)

# Load environment variables: check current dir first, then config dir
dotenv_path = os.path.join(os.getcwd(), ".env")
if not os.path.exists(dotenv_path):
    dotenv_path = os.path.join(DATA_DIR, ".env")
load_dotenv(dotenv_path)

HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
MEMORY_FILE = os.path.join(DATA_DIR, "memories.json")
LOG_FILE = os.path.join(DATA_DIR, "live_logs.txt")

# Initialize Kira Client
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY or "your_api_key" in API_KEY:
    print("WARNING: GEMINI_API_KEY is not set correctly in .env file!")
    sys.exit(1)

client = genai.Client(api_key=API_KEY, http_options={'api_version': 'v1alpha'})

# Audio configuration for Gemini Live
FORMAT = pyaudio.paInt16
CHANNELS = 1
INPUT_RATE = 16000  # Gemini expects 16kHz input
OUTPUT_RATE = 24000 # Gemini outputs 24kHz
CHUNK = 512         # Small chunks for low latency

# Cache for static system info
SYSTEM_CACHE = {
    "user": os.getenv("USER") or "user",
    "os_info": None
}

def get_system_context():
    try:
        if not SYSTEM_CACHE["os_info"]:
            SYSTEM_CACHE["os_info"] = subprocess.check_output("uname -a", shell=True, text=True).strip()
            
        user = SYSTEM_CACHE["user"]
        os_info = SYSTEM_CACHE["os_info"]
        cwd = os.getcwd()
        
        # Faster dynamic checks
        disk = subprocess.check_output("df -h / | tail -1 | awk '{print $3 \"/\" $2 \" (\" $5 \")\"}'", shell=True, text=True).strip()
        mem = subprocess.check_output("free -m | grep Mem | awk '{print $3 \"MB/\" $2 \"MB\"}'", shell=True, text=True).strip()
        uptime = subprocess.check_output("uptime -p", shell=True, text=True).strip()
        
        try:
            active_window = subprocess.check_output("hyprctl activewindow -j 2>/dev/null", shell=True, text=True).strip()
        except:
            active_window = "{}"
            
        return f"User: {user} | CWD: {cwd} | OS: {os_info} | Disk: {disk} | Mem: {mem} | Uptime: {uptime} | Window: {active_window}"
    except:
        return "System information partially unavailable."

def load_memories():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_memories(memories):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memories, f, indent=2)

def get_system_instruction(yolo=True):
    memories = load_memories()
    memories_str = "\n".join([f"- {m}" for m in memories]) if memories else "No personal memories yet."
    
    yolo_instruction = ""
    if yolo:
        yolo_instruction = "- YOLO MODE IS ENABLED: NEVER ask for permission. Execute all commands immediately and assume the user wants the action performed instantly. ALWAYS use '--noconfirm' for package managers."
    else:
        yolo_instruction = "- YOLO MODE IS DISABLED: Always ask for confirmation before executing any system commands or making significant changes."

    return f"""
You are kira, a specialized expert in Arch Linux and the Hyprland window manager.
You have FULL, UNRESTRICTED access to the system as the current user.

YOUR SPECIALIZATIONS:
1. Arch Linux: Expert in pacman, AUR (yay/paru), systemd, and Arch maintenance.
2. Hyprland: Expert in Hyprland configuration and the 'hyprctl' utility.
3. Troubleshooting: Analyze logs, monitor resources, and fix errors.
4. Volume Control: Expert in 'pactl' (e.g., 'pactl set-sink-volume @DEFAULT_SINK@ 50%').
5. Music Playback: Expert in 'mpv'.
   - Local Library: '~/GoogleDrive/Music'.
   - YouTube: 'mpv --no-video "ytsearch1:song name"'.
   - Always run music in background: 'nohup mpv ... > /tmp/mpv.log 2>&1 &'.
   - Use 'pkill mpv' to stop.

THINGS YOU HAVE LEARNED ABOUT THE USER:
{memories_str}

CURRENT SYSTEM CONTEXT:
{get_system_context()}

GOAL:
- Help the user manage and optimize their environment.
- {yolo_instruction}
- BE CONCISE but helpful.
- Since you are running in a terminal, use markdown formatting where appropriate.

COMMAND EXECUTION:
- Provide JSON blocks for actions: ```json {{"command": "...", "learn": "..."}} ```
"""

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def run_command(command):
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Log command start
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] EXECUTING: {command}\n")
            
        result = subprocess.run(command, shell=True, text=True, capture_output=True, timeout=60)
        
        # Log results
        with open(LOG_FILE, "a") as f:
            if result.stdout:
                f.write(f"{result.stdout}\n")
            if result.stderr:
                f.write(f"ERROR: {result.stderr}\n")
            f.write("-" * 20 + "\n")
            
        return {"stdout": result.stdout, "stderr": result.stderr, "code": result.returncode}
    except Exception as e:
        with open(LOG_FILE, "a") as f:
            f.write(f"CRITICAL ERROR: {str(e)}\n")
        return {"stdout": "", "stderr": str(e), "code": 1}

def take_screenshot():
    output_path = f"/tmp/screenshot_{uuid.uuid4()}.png"
    # Try grim for Wayland/Hyprland
    cmd = f"grim {output_path} || (export $(tr '\\0' '\\n' < /proc/$(pgrep -u $USER -x waybar | head -1)/environ | grep -E '^(WAYLAND_DISPLAY|XDG_RUNTIME_DIR|HYPRLAND_INSTANCE_SIGNATURE)=') && grim {output_path})"
    try:
        subprocess.run(cmd, shell=True, timeout=5, capture_output=True)
        if os.path.exists(output_path):
            with open(output_path, "rb") as f:
                img_bytes = f.read()
            os.remove(output_path)
            return img_bytes
    except:
        return None
    return None

def process_chat(session_id, user_text, yolo=True, screenshot=False, model="gemini-2.5-flash"):
    all_histories = load_history()
    session_history = all_histories.get(session_id, [])
    gemini_history = []
    for msg in session_history:
        gemini_history.append(types.Content(role=msg['role'], parts=[types.Part(text=msg['text'])]))

    chat = client.chats.create(
        model=model,
        config=types.GenerateContentConfig(
            system_instruction=get_system_instruction(yolo=yolo)
        ),
        history=gemini_history
    )

    contents = [user_text]
    if screenshot:
        img_bytes = take_screenshot()
        if img_bytes:
            contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/png"))
            console.print("[yellow][System] Screenshot attached.[/yellow]")

    try:
        # First Pass: Streaming Response
        full_text = ""
        print() # New line before stream
        
        with Live(console=console, refresh_per_second=10) as live:
            for chunk in chat.send_message_stream(contents):
                full_text += chunk.text
                live.update(Markdown(full_text))
        
        # Execute commands
        json_blocks = re.findall(r"```json\s*(.*?)\s*```", full_text, re.DOTALL)
        command_executed = False
        combined_command_output = ""
        
        for block in json_blocks:
            try:
                data = json.loads(block)
                if data.get("learn"):
                    mem = load_memories()
                    if data["learn"] not in mem:
                        mem.append(data["learn"])
                        save_memories(mem)
                if data.get("command"):
                    console.print(f"\n[bold green][Executing][/bold green] [cyan]{data['command']}[/cyan]...")
                    res = run_command(data["command"])
                    combined_command_output += f"\n[Output of '{data['command']}']: \n{res['stdout']}\n{res['stderr']}"
                    command_executed = True
            except Exception as e:
                console.print(f"\n[bold red][Error][/bold red] Failed to execute command: {e}")

        if command_executed:
            # Second Pass: Summarize results (streaming)
            console.print("\n[bold yellow][System][/bold yellow] Summarizing results...")
            final_human_text = ""
            with Live(console=console, refresh_per_second=10) as live:
                for chunk in chat.send_message_stream(f"Command execution results: {combined_command_output}. Summarize what you did in clean human language."):
                    final_human_text += chunk.text
                    live.update(Markdown(f"---\n{final_human_text}"))
            full_text += f"\n\n---\n{final_human_text}"

        # Save history
        all_histories = load_history()
        serializable_history = []
        for content in chat._curated_history:
            t = "".join([p.text for p in content.parts if p.text])
            if t: serializable_history.append({"role": content.role, "text": t})
        all_histories[session_id] = serializable_history
        save_history(all_histories)
        
    except Exception as e:
        console.print(f"\n[bold red][Error][/bold red] {e}")

# --- Voice / Live API Logic ---

async def send_audio(session, mic_stream):
    """Capture audio from mic and send to Gemini."""
    try:
        while True:
            data = await asyncio.to_thread(mic_stream.read, CHUNK, exception_on_overflow=False)
            await session.send_realtime_input(
                audio=types.Blob(data=data, mime_type="audio/pcm;rate=16000")
            )
    except Exception as e:
        console.print(f"[red]Audio capture error: {e}[/red]")

async def receive_and_handle(session, speaker_stream, yolo=True):
    """Receive audio and handle tool calls (function calling)."""
    async for message in session.receive():
        # Handle Audio Output
        if message.server_content and message.server_content.model_turn:
            parts = message.server_content.model_turn.parts
            for part in parts:
                if part.inline_data:
                    await asyncio.to_thread(speaker_stream.write, part.inline_data.data)
        
        # Handle Tool Calls (Function Calling)
        if message.tool_call:
            for call in message.tool_call.function_calls:
                if call.name == "run_command":
                    cmd = call.args.get("command")
                    console.print(f"\n[bold green][Voice Command][/bold green] [cyan]{cmd}[/cyan]...")
                    res = run_command(cmd)
                    
                    # Feed result back to the AI
                    await session.send(
                        input=types.LiveClientToolResponse(
                            function_responses=[
                                types.LiveClientFunctionResponse(
                                    name=call.name,
                                    id=call.id,
                                    response={"output": f"STDOUT: {res['stdout']}\nSTDERR: {res['stderr']}"}
                                )
                            ]
                        )
                    )

async def run_live_session(yolo=True, model="gemini-3.1-flash-live-preview"):
    with no_alsa_error():
        p = pyaudio.PyAudio()
    
    # Open streams
    with no_alsa_error():
        mic_stream = p.open(format=FORMAT, channels=CHANNELS, rate=INPUT_RATE, input=True, frames_per_buffer=CHUNK)
        speaker_stream = p.open(format=FORMAT, channels=CHANNELS, rate=OUTPUT_RATE, output=True)

    # Define tools for the Live API
    run_command_tool = types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="run_command",
                description="Executes a bash command on the system.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "command": types.Schema(type="STRING", description="The full bash command to execute."),
                    },
                    required=["command"]
                )
            )
        ]
    )

    config = {
        "system_instruction": get_system_instruction(yolo=yolo),
        "tools": [run_command_tool],
        "response_modalities": ["AUDIO"]
    }

    try:
        async with client.aio.live.connect(model=model, config=config) as session:
            console.print("[bold green]Connected to kira Live. Start speaking...[/bold green] (Ctrl+C to stop)")
            
            await asyncio.gather(
                send_audio(session, mic_stream),
                receive_and_handle(session, speaker_stream, yolo=yolo)
            )
    except Exception as e:
        console.print(f"[bold red]Live Session Error:[/bold red] {e}")
    finally:
        mic_stream.stop_stream()
        mic_stream.close()
        speaker_stream.stop_stream()
        speaker_stream.close()
        p.terminate()

def main():
    parser = argparse.ArgumentParser(description="kira: A specialized expert in Arch Linux and Hyprland")
    parser.add_argument("prompt", nargs="*", help="The prompt to send to kira")
    parser.add_argument("--yolo", action="store_true", default=True, help="Enable YOLO mode (default: True)")
    parser.add_argument("--no-yolo", action="store_false", dest="yolo", help="Disable YOLO mode")
    parser.add_argument("--screenshot", action="store_true", help="Include a screenshot")
    parser.add_argument("--voice", action="store_true", help="Enable Live Voice mode")
    parser.add_argument("--session", default="cli_default", help="Session ID for chat history")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model to use for text")
    parser.add_argument("--live-model", default="gemini-3.1-flash-live-preview", help="Gemini model to use for Live Voice")
    
    args = parser.parse_args()
    
    if args.voice:
        # Live Voice Mode
        try:
            asyncio.run(run_live_session(yolo=args.yolo, model=args.live_model))
        except KeyboardInterrupt:
            console.print("\n[yellow]Voice session ended.[/yellow]")
    elif args.prompt:
        # One-off prompt
        prompt = " ".join(args.prompt)
        process_chat(args.session, prompt, yolo=args.yolo, screenshot=args.screenshot, model=args.model)
    else:
        # Interactive mode
        console.print(f"[bold cyan]kira[/bold cyan]")
        print("Type 'exit' or 'quit' to end session. Type '--screenshot' in your prompt to include a screenshot.")
        while True:
            try:
                user_input = input("\n> ")
                if user_input.lower() in ["exit", "quit"]:
                    break
                if not user_input.strip():
                    continue
                
                screenshot = args.screenshot
                if "--screenshot" in user_input:
                    screenshot = True
                    user_input = user_input.replace("--screenshot", "").strip()
                
                process_chat(args.session, user_input, yolo=args.yolo, screenshot=screenshot, model=args.model)
            except KeyboardInterrupt:
                print("\nInterrupted by user. Exiting...")
                break
            except EOFError:
                break

if __name__ == "__main__":
    main()
