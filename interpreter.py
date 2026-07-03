from dotenv import load_dotenv
load_dotenv()

import cv2
import time
import google.generativeai as genai
import PIL.Image
import json
import os

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash-lite")

PROMPT = """Hand-drawn sketch, white lines on black.

Look at the whole composition — shapes, motion, density, and how elements relate — not just isolated symbols. The same object can suggest different moods depending on context.

Pick a PRIMARY mood and, if the sketch feels like a blend, a SECONDARY mood, from:
calm, dreamy, romantic, melancholic, energetic, dark, happy, peaceful, nostalgic, intense, adventurous, mysterious, heartbreak

If the sketch clearly leans one way, set secondary the same as primary.

Reply ONLY with JSON, no extra text:
{"label": "2-4 word description", "mood": "primary mood", "mood2": "secondary mood", "tags": ["tag1", "tag2", "tag3"]}"""

def interpret(canvas_image, retries=2):
    small = cv2.resize(canvas_image, (320, 360))
    img   = PIL.Image.fromarray(cv2.cvtColor(small, cv2.COLOR_BGR2RGB))

    for attempt in range(retries + 1):
        try:
            res = model.generate_content([PROMPT, img])
            raw = res.text.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(raw)
        except Exception as e:
            msg = str(e)
            if "ResourceExhausted" in msg or "quota" in msg.lower():
                if attempt < retries:
                    time.sleep(2)  # brief wait, then retry once or twice
                    continue
            print("=== GEMINI CALL FAILED ===")
            print(repr(e))
            print("===========================")
            break

    return {'label': 'A sketch', 'mood': 'mysterious', 'mood2': 'mysterious', 'tags': ['ambient']}