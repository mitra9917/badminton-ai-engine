import cv2
import time
import numpy as np

from engine.shots import classify_shot
from vision.hand_tracking import HandTracker
from engine.state import GameState

# ---------------- CONSTANTS ----------------
CONSTANTS = {
    "COURT_WIDTH": 10,
    "SCREEN_W": 600,
    "SCREEN_H": 800,
    "PLAYER_Y": 680,
    "AI_Y": 200,
    "SHUTTLE_TIME": 0.65,
    "AI_REACT_TIME": 0.4,
    "COOLDOWN": 0.8,
    "MOVE_THRESHOLD": 0.035,
    "NEUTRAL_THRESHOLD": 0.012,
    "HAND_SENSITIVITY": 1.8,
    "SMOOTHING": 0.35,
    "MAX_PLAYER_SPEED": 0.9,
    "CATCH_RADIUS": 0.8
}

# ---------------- INIT ----------------
cap = cv2.VideoCapture(0)
tracker = HandTracker()
game = GameState()

# ---------------- HELPERS ----------------
def clamp(val, minv, maxv):
    return max(minv, min(maxv, val))

def detect_stroke(dx, dy):
    if dx is None or dy is None:
        return False
    return abs(dx) > CONSTANTS["MOVE_THRESHOLD"] or abs(dy) > CONSTANTS["MOVE_THRESHOLD"]

def to_px(x_unit):
    return int(
        50 + x_unit * ((CONSTANTS["SCREEN_W"] - 100) / CONSTANTS["COURT_WIDTH"])
    )

# ---------------- GROUND VIEW PROJECTION ----------------
def project_to_ground_view(x_unit, y_px):
    depth = (y_px - 100) / (CONSTANTS["SCREEN_H"] - 200)
    depth = max(0, min(1, depth))

    scale = 0.45 + depth * 0.75
    center_x = CONSTANTS["SCREEN_W"] // 2
    flat_x = to_px(x_unit)

    proj_x = int(center_x + (flat_x - center_x) * scale)
    proj_y = int(y_px * (0.8 + depth * 0.2))

    return proj_x, proj_y, scale

# ---------------- AVATAR DRAW ----------------
def draw_avatar(vis, x, y, scale, color, facing="up"):
    x = int(x)
    y = int(y)

    head_r = int(8 * scale)
    body_len = int(28 * scale)

    # Head
    cv2.circle(vis, (x, y - body_len), head_r, color, -1)

    # Body
    cv2.line(vis, (x, y - body_len + head_r), (x, y + body_len), color, 3)

    # Arm / racket
    arm_offset = int(40 * scale)
    arm_end = (x, y - arm_offset) if facing == "up" else (x, y + arm_offset)
    cv2.line(vis, (x, y), arm_end, color, 2)
    cv2.circle(vis, arm_end, int(5 * scale), (200, 200, 200), -1)

    # Reach (yellow)
    cv2.circle(vis, (x, y), int(60 * scale), (0, 255, 255), 2)

print("🎮 Badminton Game — Ground View Camera")

# ---------------- MAIN LOOP ----------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    cx, cy, dx, dy = tracker.get_hand_data(frame)
    now = time.time()

    # -------- HAND INPUT --------
    if cx is not None:
        mapped_x = (cx - 0.5) * CONSTANTS["HAND_SENSITIVITY"] + 0.5
        mapped_x = clamp(mapped_x, 0, 1)
        game.target_player_x = mapped_x * CONSTANTS["COURT_WIDTH"]

    # -------- PLAYER READY --------
    if game.state == "IDLE" and not game.player_ready:
        if dx is not None and dy is not None:
            if abs(dx) < CONSTANTS["NEUTRAL_THRESHOLD"] and abs(dy) < CONSTANTS["NEUTRAL_THRESHOLD"]:
                game.player_ready = True

    # -------- PLAYER HIT --------
    elif (
        game.state == "IDLE"
        and game.player_ready
        and now - game.last_stroke_time > CONSTANTS["COOLDOWN"]
    ):
        if detect_stroke(dx, dy):
            shot = classify_shot(dx, dy)
            game.start_player_hit(now, shot if shot else "NORMAL")

    # -------- PLAYER MOVEMENT --------
    delta = clamp(
        game.target_player_x - game.player_x,
        -CONSTANTS["MAX_PLAYER_SPEED"],
        CONSTANTS["MAX_PLAYER_SPEED"],
    )
    game.player_x += delta * CONSTANTS["SMOOTHING"]

    # -------- GAME UPDATE --------
    game.update(now, CONSTANTS)

    # -------- DRAW --------
    vis = frame.copy()

    # -------- COURT (GROUND VIEW TRAPEZOID) --------
    # Near side (player side) – MUCH wider
    near_left  = (20, 740)
    near_right = (580, 740)

    # Far side (AI side) – wider but still narrow for perspective
    far_left   = (170, 180)
    far_right  = (430, 180)

    court = np.array([near_left, near_right, far_right, far_left], np.int32)
    cv2.polylines(vis, [court], True, (0, 200, 0), 2)

    # -------- NET (HEIGHT ILLUSION) --------

    # -------- NET (FULL WIDTH + HEIGHT + MESH) --------

    # Net depth (slightly toward AI side for ground view)
    net_y = 365

    # Net must match court width at this depth
    net_left_x  = far_left[0] 
    net_right_x = far_right[0] 

    # Net visual height
    net_height = 32

    # Mesh spacing (smaller = finer mesh)
    mesh_step = 6

    # -------- Bottom tape / shadow (ground contact) --------
    cv2.line(
        vis,
        (net_left_x, net_y + 3),
        (net_right_x, net_y + 3),
        (110, 110, 110),
        2,
    )

    # -------- Vertical mesh lines --------
    for x in range(net_left_x, net_right_x, mesh_step):
        # Perspective tilt: lines converge upward
        tilt = int((x - net_left_x) * 0.04)
        cv2.line(
            vis,
            (x, net_y),
            (x + tilt, net_y - net_height),
            (170, 170, 170),
            1,
        )

    # -------- Horizontal mesh lines --------
    for i in range(0, net_height, mesh_step):
        shade = 190 - i * 2
        left = net_left_x + i // 3
        right = net_right_x - i // 3
        cv2.line(
            vis,
            (left, net_y - i),
            (right, net_y - i),
            (shade, shade, shade),
            1,
        )

    # -------- Top tape (white, crisp) --------
    cv2.line(
        vis,
        (net_left_x + net_height // 3, net_y - net_height),
        (net_right_x - net_height // 3, net_y - net_height),
        (255, 255, 255),
        2,
    )



    # -------- PLAYERS --------
    player_y = getattr(game, "player_y", CONSTANTS["PLAYER_Y"])
    ai_y = getattr(game, "ai_y", CONSTANTS["AI_Y"])

    px, py, ps = project_to_ground_view(game.player_x, player_y)
    draw_avatar(vis, px, py, ps, (255, 0, 0), "up")

    ax, ay, as_ = project_to_ground_view(game.ai_x, ai_y)
    draw_avatar(vis, ax, ay, as_, (0, 0, 255), "down")

    # -------- SHUTTLE --------
    sx, sy, ss = project_to_ground_view(game.shuttle_x, game.shuttle_y)
    cv2.circle(vis, (sx, sy), max(3, int(8 * ss)), (255, 255, 255), -1)

    cv2.imshow("Badminton Game — Ground View", vis)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
