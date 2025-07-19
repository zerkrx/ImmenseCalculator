# main.py
import threading
import tkinter as tk
from landing_page import LandingPage
import updater

def main():
    root = tk.Tk()
    root.geometry("450x220")
    root.title("ImmenseCalculator - Establishment Selection")
    LandingPage(root)

    # Check for updates asynchronously, with GUI support
    threading.Thread(target=updater.check_for_updates, args=(root,), daemon=True).start()

    root.mainloop()

if __name__ == "__main__":
    main()