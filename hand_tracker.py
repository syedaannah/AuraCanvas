import cv2
import mediapipe as mp

_hands = mp.solutions.hands.Hands(
    static_image_mode=False, max_num_hands=1,
    min_detection_confidence=0.6, min_tracking_confidence=0.6
)
_connections = mp.solutions.hands.HAND_CONNECTIONS

def find_hands(frame):
    h, w = frame.shape[:2]
    res = _hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    if not res.multi_hand_landmarks:
        return []
    return [[(int(lm.x * w), int(lm.y * h)) for lm in hand.landmark]
            for hand in res.multi_hand_landmarks]

def draw_skeleton(frame, hands):
    for lms in hands:
        for s, e in _connections:
            cv2.line(frame, lms[s], lms[e], (0, 200, 200), 2)
        for p in lms:
            cv2.circle(frame, p, 4, (255, 255, 255), -1)