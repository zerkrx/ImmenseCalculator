# menu_manager.py
import os
import json

DATA_DIR = "data"
MENU_DIR = os.path.join(DATA_DIR, "menus")


def ensure_dirs():
    os.makedirs(MENU_DIR, exist_ok=True)


def load_menu_files():
    ensure_dirs()
    if not os.path.exists(MENU_DIR):
        return []
    return [f[:-5] for f in os.listdir(MENU_DIR) if f.endswith(".json")]


def load_menu(establishment_name):
    ensure_dirs()
    path = os.path.join(MENU_DIR, f"{establishment_name}.json")
    if not os.path.exists(path):
        # Default empty menu structure
        menu = {
            "sections": {
                "food": [],
                "drinks": {},
                "desserts": [],
                "animal_treats": [],
                "combos": {}
            },
            "item_limits": {},
            "discounts": {},
            "prices": {"food": 10, "drinks": 7, "animal_treat": 3, "combos": {}}
        }
        save_menu(menu, establishment_name)
        return menu
    with open(path, "r", encoding="utf-8") as fp:
        return json.load(fp)


def save_menu(menu, establishment_name):
    ensure_dirs()
    path = os.path.join(MENU_DIR, f"{establishment_name}.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(menu, fp, indent=4)


def save_menu_file(filename, data, directory="menus"):
    """
    Save the menu data to a JSON file.
    :param filename: Name of the file to save (e.g., 'menu1.json')
    :param data: Data to be saved in dictionary form
    :param directory: Directory to save the files (default is 'menus')
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
    filepath = os.path.join(directory, filename)
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Menu saved successfully to {filepath}")
    except Exception as e:
        print(f"Failed to save menu file {filepath}: {e}")


def delete_menu_file(establishment_name):
    """Deletes the menu file for the given establishment name."""
    path = os.path.join(MENU_DIR, f"{establishment_name}.json")
    try:
        os.remove(path)
        print(f"Deleted menu file: {path}")
    except FileNotFoundError:
        print(f"Menu file not found: {path}")
    except Exception as e:
        print(f"Error deleting menu file: {e}")