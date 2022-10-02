import io
import os
import tkinter as tk
from typing import Dict, Literal, Tuple, Union

import cairosvg

from src.Utils.photoimage import IconImage, PhotoImage

images: Dict[str, Tuple[IconImage, PhotoImage]] = {}


def init_images() -> None:
    for file_path in os.listdir("Images/"):
        file_path = os.path.join("Images", file_path)
        if os.path.isfile(file_path) and file_path.endswith(".svg"):
            name = file_path.replace("Images/", "").replace(".svg", "")
            out = io.BytesIO()
            cairosvg.svg2png(url=file_path, write_to=out, unsafe=True, scale=5)  # Scale up and down to create sort of antialiasing
            # SVG created using Illustrator might trigger a false <ENTITY> problem
            images[name] = (IconImage(file=out), PhotoImage(file=out))


def get_image(image: str, img_type: Literal["image", "icon"] = "icon") -> Union[None, PhotoImage, IconImage, tk.Image]:
    if not image:
        return None
    if img_type == "image":
        return images[image][1]
    return images[image][0]
