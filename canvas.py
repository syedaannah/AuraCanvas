import cv2
import numpy as np

class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.strokes, self.cur = [], None
        self.sx = self.sy = None
        self.missed = 0

    def update(self, pt):
        x, y = pt
        a = 0.35
        if self.sx is None:
            self.sx, self.sy = x, y
        else:
            self.sx = int(a * x + (1 - a) * self.sx)
            self.sy = int(a * y + (1 - a) * self.sy)
        if self.cur is None:
            self.cur = [(self.sx, self.sy)]
            self.strokes.append(self.cur)
        else:
            self.cur.append((self.sx, self.sy))
        self.missed = 0
        return (self.sx, self.sy)

    def end(self):
        self.cur = self.sx = self.sy = None

    def lost(self):
        self.missed += 1
        if self.missed > 12:
            self.end()

    def clear(self):
        self.strokes, self.cur = [], None
        self.sx = self.sy = None

    def render(self, frame):
        for s in self.strokes:
            for i in range(1, len(s)):
                cv2.line(frame, s[i-1], s[i], (255, 255, 255), 4)

    def snapshot(self):
        img = np.zeros((self.h, self.w, 3), dtype=np.uint8)
        self.render(img)
        return img

    def empty(self):
        return len(self.strokes) == 0