def _up(lms, tip, pip, margin=15):
    return lms[tip][1] < lms[pip][1] - margin

def detect(lms):
    index  = _up(lms, 8,  6)
    middle = _up(lms, 12, 10)
    ring   = _up(lms, 16, 14)
    pinky  = _up(lms, 20, 18)

    if not any([index, middle, ring, pinky]): return 'fist'
    if all([index, middle, ring, pinky]):     return 'palm'
    if index and middle and not ring and not pinky: return 'navigate'
    if index and not middle and not ring and not pinky: return 'draw'
    return 'none'

def tip(lms, finger=8):
    return lms[finger]