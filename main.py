import cv2
import numpy as np
import time
import threading
import io
import os
import requests
import pygame

from hand_tracker import find_hands, draw_skeleton
from gestures    import detect, tip
from canvas      import Canvas
from interpreter import interpret
from music       import get_tracks
from text_render import put_text, text_width

W, H   = 1280, 720
CW     = W // 2
PW     = W // 2

DRAWING   = 'drawing'
THINKING  = 'thinking'
PLAYLIST  = 'playlist'

PALM_HOLD = 1.5
MISS_THR  = 4
FONT_PATH = "fonts/Basic-Regular.ttf"

MOOD_COLORS = {
    'calm':        (180, 140, 90),
    'peaceful':    (170, 150, 100),
    'dreamy':      (200, 120, 180),
    'romantic':    (100, 90, 220),
    'melancholic': (150, 100, 80),
    'heartbreak':  (100, 70, 140),
    'energetic':   (60, 160, 240),
    'happy':       (60, 200, 230),
    'nostalgic':   (110, 150, 200),
    'dark':        (90, 60, 110),
    'intense':     (50, 60, 200),
    'adventurous': (60, 180, 130),
    'mysterious':  (160, 90, 160),
}

def get_mood_color(mood):
    return MOOD_COLORS.get((mood or '').lower(), (150, 150, 150))

pygame.mixer.init()

def play(url):
    if not url: return
    def _():
        try:
            r = requests.get(url, timeout=10)
            pygame.mixer.music.load(io.BytesIO(r.content))
            pygame.mixer.music.play()
        except Exception:
            pass
    threading.Thread(target=_, daemon=True).start()

def stop():
    try: pygame.mixer.music.stop()
    except Exception: pass

def draw_icon(panel, cx, cy, playing, color):
    if playing:
        for i, h in enumerate([10, 16, 12]):
            x = cx - 8 + i * 8
            cv2.rectangle(panel, (x, cy + h//2), (x + 5, cy - h//2), color, -1)
    else:
        pts = np.array([[cx-7, cy-9], [cx-7, cy+9], [cx+9, cy]], np.int32)
        cv2.polylines(panel, [pts], True, color, 2)

def draw_panel(panel, state, result, tracks, sel):
    mood = result['mood'] if result else None
    accent = get_mood_color(mood)
    bg = tuple(int(c * 0.18) for c in accent)
    panel[:] = bg

    if state == DRAWING:
        put_text(panel, "Draw, then open palm", (40, H//2), FONT_PATH, 28, (90,90,90))
        return

    if state in (THINKING, 'processing'):
        dots = "." * (int(time.time() * 2) % 4)
        put_text(panel, f"Reading sketch{dots}", (40, H//2), FONT_PATH, 32, (200,200,200))
        return

    if state == PLAYLIST and result:
        put_text(panel, result['mood'].capitalize(), (40, 40), FONT_PATH, 56, (255,255,255))
        put_text(panel, result['label'], (40, 100), FONT_PATH, 20, (200,200,200))
        cv2.line(panel, (40, 130), (PW-40, 130), accent, 2)

        put_text(panel, "TITLE", (78, 148), FONT_PATH, 16, accent)
        put_text(panel, "ARTIST", (PW-48, 148), FONT_PATH, 16, accent, anchor="ra")

        y = 175
        row_h = 68
        for i, t in enumerate(tracks):
            playing = (i == sel)

            if playing:
                cv2.rectangle(panel, (28, y), (PW-28, y+row_h), tuple(int(c*0.4) for c in accent), -1)

            draw_icon(panel, 55, y + row_h//2, playing, accent if playing else (150,150,150))

            title_color = (255,255,255) if playing else (170,170,170)
            put_text(panel, t['title'], (78, y+row_h//2-16), FONT_PATH, 22, title_color)
            put_text(panel, t['artist'], (PW-48, y+row_h//2+10), FONT_PATH, 16, (140,140,140), anchor="ra")

            y += row_h + 6

        put_text(panel, "index + middle to navigate", (40, H-30), FONT_PATH, 14, (100,100,100))

def main():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Camera did not open. Try index 1 or 2, or close other apps using the webcam.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)

    canvas = Canvas(CW, H)
    state  = DRAWING
    result, tracks = None, []
    sel, last_sel  = 0, -1

    palm_t       = None
    interpreting = False
    fist_count   = 0
    draw_miss    = 0
    FIST_THR     = 8
    prev_my      = None

    while True:
        ok, frame = cap.read()
        if not ok:
            continue
        frame = cv2.flip(frame, 1)

        hands = find_hands(frame)
        left  = np.zeros((H, CW, 3), dtype=np.uint8)
        canvas.render(left)

        if hands:
            lms     = hands[0]
            scaled  = [(min(x, CW-1), y) for x, y in lms]
            draw_skeleton(left, [scaled])
            gesture = detect(scaled)

            if state == DRAWING and gesture == 'draw':
                pt = canvas.update(tip(scaled, 8))
                cv2.circle(left, pt, 8, (120,255,120), -1)
                palm_t = fist_count = draw_miss = 0

            elif gesture == 'fist':
                fist_count += 1
                canvas.end()
                draw_miss = 0
                if fist_count >= FIST_THR:
                    canvas.clear()
                    state  = DRAWING
                    result = None
                    tracks = []
                    stop()
                    fist_count = 0

            else:
                fist_count = 0
                if gesture == 'palm':
                    canvas.end()
                    draw_miss = 0
                else:
                    draw_miss += 1
                    if draw_miss > MISS_THR:
                        canvas.end()

            if gesture == 'palm' and state == DRAWING:
                now = time.time()
                if palm_t is None: palm_t = now
                frac  = min((now - palm_t) / PALM_HOLD, 1.0)
                angle = int(frac * 360)
                cv2.ellipse(left, (50, H-50), (28,28), -90, 0, angle, (200,200,200), 3)
                cv2.putText(left, "hold", (34, H-44),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38, (160,160,160), 1)
                if frac >= 1.0 and not canvas.empty():
                    state = THINKING
                    palm_t = None
            elif gesture != 'palm':
                palm_t = None

            if gesture == 'navigate' and state == PLAYLIST and tracks:
                my = tip(scaled, 12)[1]
                if prev_my is not None:
                    if my - prev_my >  8: sel = min(sel+1, len(tracks)-1)
                    if my - prev_my < -8: sel = max(sel-1, 0)
                prev_my = my
            else:
                prev_my = None

        else:
            canvas.lost()
            palm_t = prev_my = None
            fist_count = draw_miss = 0

        if state == THINKING and not interpreting:
            interpreting = True
            state = 'processing'
            snap = canvas.snapshot()
            def run(img):
                nonlocal result, tracks, sel, last_sel, state, interpreting
                result        = interpret(img)
                tracks        = get_tracks(result.get('mood',''), result.get('mood2',''))
                sel, last_sel = 0, -1
                state         = PLAYLIST
                interpreting  = False
            threading.Thread(target=run, args=(snap,), daemon=True).start()

        if state == PLAYLIST and sel != last_sel:
            stop()
            if tracks: play(tracks[sel]['preview'])
            last_sel = sel

        right   = np.zeros((H, PW, 3), dtype=np.uint8)
        draw_panel(right, state, result, tracks, sel)
        divider = np.full((H, 2, 3), 35, dtype=np.uint8)

        cv2.imshow("AuraCanvas", np.hstack([left, divider, right]))
        if cv2.waitKey(1) == 27: break

    stop()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()