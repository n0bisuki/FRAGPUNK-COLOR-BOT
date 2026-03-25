# Terminal UI rendering
from termcolor import colored
import platform
from util.setting import DISCORD
# Unified logging helpers
LOG_COLORS = {
    "INFO": ("green", "white"),
    "ALERT": ("red", "yellow"),
    "ERROR": ("red", "white"),
    "WARN": ("yellow", "white"),
    "SUCCESS": ("green", "white"),
    "DEBUG": ("cyan", "white"),
}

def log(level: str, message: str, end: str = "\n"):
    level = (level or "INFO").upper()
    left, right = LOG_COLORS.get(level, ("white", "white"))
    print(f"{colored(f'[{level}]', left)} {colored(str(message), right)}", end=end)

# Convenience wrappers
def info(msg: str, end: str = "\n"): log("INFO", msg, end=end)
def success(msg: str, end: str = "\n"): log("SUCCESS", msg, end=end)
def warn(msg: str, end: str = "\n"): log("WARN", msg, end=end)
def alert(msg: str, end: str = "\n"): log("ALERT", msg, end=end)
def error(msg: str, end: str = "\n"): log("ERROR", msg, end=end)

def display_banner():
    print(colored(r"""
  _________.__                     .__               .__  __          
 /   _____/|__| ____    ____  __ __|  | _____ _______|__|/  |_ ___.__.
 \_____  \ |  |/    \  / ___\|  |  \  | \__  \\_  __ \  \   __<   |  |
 /        \|  |   |  \/ /_/  >  |  /  |__/ __ \|  | \/  ||  |  \___  |
/_______  /|__|___|  /\___  /|____/|____(____  /__|  |__||__|  / ____|
        \/         \//_____/                 \/                \/     
                    _______                                           
                    \      \   _______  _______                       
                    /   |   \ /  _ \  \/ /\__  \                      
                   /    |    (  <_> )   /  / __ \_                    
                   \____|__  /\____/ \_/  (____  /                    
                           \/                  \/                                     
    """, "magenta"))

    print( colored(
        "This product is controlled by Singularity.\nDo not use it if supplied by someone else.\nWe are not responsible for any consequences.\n", "red"))
    print(colored("[Discord Server]", "red"), colored(DISCORD, "blue"))


def display_os_warning():
    system = platform.system()
    if system != "Windows":
        print(colored("[Alert]", "red"), colored("Unsupported OS detected. Only Windows is allowed.", "yellow"))
        return False
    return True


def display_custom_windows_warning():
    print(colored("[Warning]", "red"), colored("Custom/Optimized Windows detected! Execution paused.", "yellow"))


def display_version(version):
    print(colored("[INFO]", "green"), colored(f"VERSION: {version}", "white"))

def display_version_mishmatch(version,version2):
    print(colored("[INFO]", "red"), colored(f"Version Mishmatch : {version} -> {version2}", "white"))


def display_license_error():
    print(colored("[Alert]", "red"), colored("The license you provided is not valid!", "white"))


def display_lifetime():
    print(colored("[ALERT]", "green") + f" Days Left: ", colored("LIFE-TIME", "green"))


def display_days_left(days):
    print(colored("[ALERT]", "yellow") + f" Days Left: {days:,}")


def display_invalid_env():
    print(colored("[Alert]", "red"), colored("Env path is not valid!", "white"))


def display_download_success(name):
    print(colored(f"[✔] {name} Downloaded Successfully", "green"))


def display_download_failure(name, error=""):
    print(colored(f"[✘] Failed to Download {name}", "red"), error)


def display_license_expired():
    print(colored(f"[✘] The license you provided is not valid!", "red"))

def display_license_valid(remaining_days):
    print(colored(f"[✔] Days Left: {remaining_days}", "green"))
 
def display_serial_port_not_found():
    print(colored("[Error]", "red"), colored("Serial port not found!", "white"))
    