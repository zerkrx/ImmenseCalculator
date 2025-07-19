import os
import sys
import platform
import tempfile
import threading
import subprocess
import requests
import tkinter as tk
from tkinter import messagebox
from packaging import version  # require `pip install packaging`

# Current app version - keep this in sync with your releases
APP_VERSION = "1.1.0"

# GitHub repo info
GITHUB_USER = "zerkrx"
GITHUB_REPO = "ImmenseCalculator"

# GitHub API endpoints
GITHUB_API_RELEASES_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"

class Updater:
    def __init__(self, root=None, current_version=APP_VERSION):
        self.root = root
        self.current_version = current_version
        self.latest_version = None
        self.installer_url = None
        self.installer_filename = None

    def fetch_latest_release_info(self):
        try:
            headers = {'Accept': 'application/vnd.github.v3+json'}
            response = requests.get(GITHUB_API_RELEASES_URL, headers=headers, timeout=10)
            response.raise_for_status()

            release_info = response.json()
            tag_name = release_info.get("tag_name", "")
            if tag_name.startswith("v"):
                tag_name = tag_name[1:]  # strip leading 'v'

            self.latest_version = tag_name

            # Find installer asset - prefer .exe for Windows
            assets = release_info.get("assets", [])

            # Platform detection for choosing appropriate installer if you want per OS.
            # For now, just choose first .exe asset (simple)
            installer_asset = None
            for asset in assets:
                name = asset.get("name", "").lower()
                if name.endswith(".exe"):
                    installer_asset = asset
                    break

            if not installer_asset:
                print("[Updater] No suitable installer (.exe) found in latest release assets.")
                return False

            self.installer_url = installer_asset.get("browser_download_url")
            self.installer_filename = installer_asset.get("name")

            return True
        except Exception as e:
            print(f"[Updater] Failed to fetch release info: {e}")
            return False

    def is_update_available(self):
        if self.latest_version is None:
            return False
        try:
            current_ver = version.parse(self.current_version)
            latest_ver = version.parse(self.latest_version)
            return latest_ver > current_ver
        except Exception as e:
            print(f"[Updater] Version comparison failed: {e}")
            return False

    def prompt_update(self):
        if not self.root:
            print("[Updater] No root window to prompt update.")
            return

        msg = (
            f"A new version of ImmenseCalculator is available!\n\n"
            f"Current version: {self.current_version}\n"
            f"Latest version: {self.latest_version}\n\n"
            f"Do you want to download and install the update now?"
        )
        ans = messagebox.askyesno("Update Available", msg)
        if ans:
            threading.Thread(target=self.download_and_install, daemon=True).start()

    def download_and_install(self):
        try:
            tmp_dir = tempfile.gettempdir()
            installer_path = os.path.join(tmp_dir, self.installer_filename)
            print(f"[Updater] Downloading installer to: {installer_path}")

            with requests.get(self.installer_url, stream=True) as r:
                r.raise_for_status()
                total_length = r.headers.get('content-length')
                total_length = int(total_length) if total_length else None

                with open(installer_path, "wb") as f:
                    downloaded = 0
                    chunk_size = 8192
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_length:
                                percent = int(downloaded * 100 / total_length)
                                print(f"\r[Updater] Downloaded {percent}%...", end="", flush=True)
                print("\n[Updater] Download complete.")

            # Run installer
            print("[Updater] Launching installer...")
            if platform.system() == "Windows":
                # Use ShellExecute to ensure .exe runs properly
                os.startfile(installer_path)
            else:
                # For other OS, just popen the file (you can extend support if needed)
                subprocess.Popen([installer_path], shell=True)

            # Exit current app immediately
            print("[Updater] Exiting app for update...")
            os._exit(0)

        except Exception as e:
            print(f"[Updater] Update failed: {e}")
            if self.root:
                self.root.after(0, lambda: messagebox.showerror("Update Failed", f"Could not update the app:\n{e}"))

def check_for_updates(root=None):
    updater = Updater(root)
    success = updater.fetch_latest_release_info()
    if not success:
        if root:
            root.after(0, lambda: messagebox.showinfo("Update", "Could not check for updates at this time."))
        return

    if updater.is_update_available():
        if root:
            updater.prompt_update()
        else:
            print(f"Update available: {updater.latest_version} (current: {updater.current_version})")
    else:
        print("No updates available. You have the latest version.")