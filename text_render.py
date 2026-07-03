from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

_font_cache = {}

def _get_font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]

def put_text(panel, text, pos, font_path, size, color_bgr, anchor="la"):
    """
    Draws text using a custom TTF font onto an OpenCV (numpy BGR) image.
    anchor: PIL anchor string, e.g. "la" (left-ascender, default),
            "ra" (right-ascender) for right-aligned text.
    color_bgr: tuple like (255,255,255) in BGR order, matching your OpenCV colors.
    """
    font = _get_font(font_path, size)
    color_rgb = (color_bgr[2], color_bgr[1], color_bgr[0])  # BGR -> RGB for PIL

    img_pil = Image.fromarray(cv2.cvtColor(panel, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    draw.text(pos, text, font=font, fill=color_rgb, anchor=anchor)

    result = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    panel[:] = result  # write back into the same array in-place

def text_width(text, font_path, size):
    font = _get_font(font_path, size)
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]