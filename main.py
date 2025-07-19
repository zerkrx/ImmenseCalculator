# main.py
import tkinter as tk
from landing_page import LandingPage

def main():
    root = tk.Tk()
    root.geometry("450x220")
    root.title("Bartender App - Establishment Selection")
    LandingPage(root)
    root.mainloop()

if __name__ == "__main__":
    main()