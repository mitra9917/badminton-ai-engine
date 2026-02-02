import math

# ---------------- TUNED FOR MEDIAPIPE ----------------

SMASH_SPEED = 0.045      # lower than before
CLEAR_SPEED = 0.025
DROP_SPEED  = 0.015


UPWARD_DY = -0.08       # much less strict
DOWNWARD_DY = 0.08

def classify_shot(dx, dy):
    speed = math.sqrt(dx * dx + dy * dy)

    # Debug (keep for now)
    '''print(f"dx={dx:.4f}, dy={dy:.4f}, speed={speed:.4f}")'''

    # SMASH: fast + downward
    if speed > SMASH_SPEED and dy > DOWNWARD_DY:
        return "SMASH"

    # CLEAR: upward motion (direction more important than speed)
    if dy < UPWARD_DY and speed > CLEAR_SPEED:
        return "CLEAR"

    # DROP: slow controlled motion
    if speed > DROP_SPEED:
        return "DROP"

    return None
