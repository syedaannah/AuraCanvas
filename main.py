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

W, H   = 1280, 720
CW     = W // 2
PW     = W // 2

DRAWING   = 'drawing'
THINKING  = 'thinking'
PLAYLIST  = 'playlist'

PALM_HOLD = 1.5
MISS_THR  = 4

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

def draw_panel(panel, state, result, tracks, sel):
    panel[:] = (15, 15, 18)

    if state == DRAWING:
        cv2.putText(panel, "Draw, then open palm",
                    (40, H//2), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (60,60,60), 2)
        return

    if state in (THINKING, 'processing'):
        dots = "." * (int(time.time() * 2) % 4)
        cv2.putText(panel, f"Reading sketch{dots}",
                    (40, H//2), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (180,180,190), 2)
        return

    if state == PLAYLIST and result:
        cv2.putText(panel, result['mood'].capitalize(),
                    (40, 65), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255,255,255), 2)
        cv2.putText(panel, result['label'],
                    (40, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (120,120,120), 1)
        cv2.line(panel, (40, 118), (PW-40, 118), (40,40,48), 1)

        y = 145
        for i, t in enumerate(tracks):
            selected = (i == sel)
            row_h    = 88 if selected else 58

            if selected:
                cv2.rectangle(panel, (28, y), (PW-28, y+row_h), (32,32,40), -1)
                cv2.rectangle(panel, (28, y), (32, y+row_h), (180,160,255), -1)
                cv2.putText(panel, t['title'],  (48, y+row_h//2-8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.72, (180,160,255), 2)
                cv2.putText(panel, t['artist'], (48, y+row_h//2+20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)
                cv2.putText(panel, "▶ playing preview", (48, y+row_h//2+38),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100,100,120), 1)
            else:
                cv2.putText(panel, t['title'],  (48, y+row_h//2-6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (130,130,130), 1)
                cv2.putText(panel, t['artist'], (48, y+row_h//2+18),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.44, (70,70,70), 1)

            y += row_h + 5

        cv2.putText(panel, "index + middle to navigate",
                    (40, H-22), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (50,50,55), 1)

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
            state = 'processing'   # immediately leave THINKING so this block can't fire again
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