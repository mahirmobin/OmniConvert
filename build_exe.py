import os
import sys
from pathlib import Path
from PIL import Image
import customtkinter
import tkinterdnd2
import PyInstaller.__main__

def prepare_icon():
    img = Image.open("icon.png")
    img.save("icon.ico", format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32)])
    return "icon.ico"

def main():
    icon_path = prepare_icon()
    
    ctk_path = str(Path(customtkinter.__file__).parent)
    tkdnd_path = str(Path(tkinterdnd2.__file__).parent)
    desktop_path = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    
    # Exclude massive unrelated python site-packages that PyInstaller might traverse recursively
    excludes = [
        "--exclude-module", "torch",
        "--exclude-module", "tensorflow",
        "--exclude-module", "numpy",
        "--exclude-module", "scipy",
        "--exclude-module", "matplotlib",
        "--exclude-module", "pandas",
        "--exclude-module", "cv2",
        "--exclude-module", "keras",
        "--exclude-module", "sklearn"
    ]
    
    args = [
        "main.py",
        "--onefile",
        "--windowed",
        "--name", "OmniConvert",
        "--icon", icon_path,
        "--add-data", f"{ctk_path};customtkinter/",
        "--add-data", f"{tkdnd_path};tkinterdnd2/",
        "--distpath", desktop_path,
        "--clean",
        "--noconfirm"
    ] + excludes
    
    print(f"Building PyInstaller bundle to: {desktop_path} ... (ignoring heavy numerical tools)")
    PyInstaller.__main__.run(args)

if __name__ == "__main__":
    main()
