import subprocess
import sys
import os
import tkinter as tk
from tkinter import messagebox

def is_git_repo(path):
    git_dir = os.path.join(path, '.git')
    return os.path.isdir(git_dir)

def run_git_command(args, cwd=None):
    result = subprocess.run(['git'] + args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def check_for_updates(repo_path):
    if not is_git_repo(repo_path):
        messagebox.showerror("Update Error", "Current directory is not a git repository. Auto-update requires git clone.")
        return False

    # Fetch latest refs
    out, err, code = run_git_command(['fetch'], cwd=repo_path)
    if code != 0:
        messagebox.showerror("Git Fetch Error", f"Failed to fetch updates.\nError: {err}")
        return False

    # Check if the local branch is behind remote
    out_local, err, _ = run_git_command(['rev-parse', 'HEAD'], cwd=repo_path)
    out_remote, err, _ = run_git_command(['rev-parse', '@{u}'], cwd=repo_path)
    if out_local != out_remote:
        answer = messagebox.askyesno("Update Available", "A new version is available. Do you want to update now?")
        if answer:
            # Pull the changes
            out_pull, err_pull, code_pull = run_git_command(['pull'], cwd=repo_path)
            if code_pull != 0:
                messagebox.showerror("Git Pull Error", f"Failed to pull updates.\nError: {err_pull}")
                return False
            
            # Optional: install requirements (if you have a requirements.txt)
            req_file = os.path.join(repo_path, 'requirements.txt')
            if os.path.isfile(req_file):
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', req_file])
                except Exception as e:
                    messagebox.showwarning("Requirements Install", f"Failed to install requirements:\n{e}")

            messagebox.showinfo("Update Complete", "Application updated to the latest version. Please restart the app.")
            return True
        else:
            return False
    else:
        messagebox.showinfo("No Update", "Your app is already up to date.")
        return False