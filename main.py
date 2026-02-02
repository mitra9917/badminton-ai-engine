import cv2
import time
from engine.shots import classify_shot
from vision.hand_tracking import HandTracker
from engine.state import GameState

# ---------------- CONSTANTS ----------------
CONSTANTS = {
    "COURT_WIDTH": 10,
    "SCREEN_W": 600,
    "SCREEN_H": 800,
    "PLAYER_Y": 650,
    "AI_Y": 150,
    "SHUTTLE_TIME": 0.65,
    "AI_REACT_TIME": 0.4,
    "COOLDOWN": 0.8,
    "MOVE_THRESHOLD": 0.035,
    "NEUTRAL_THRESHOLD": 0.012,
    "HAND_SENSITIVITY": 1.8,
    "SMOOTHING": 0.35,
    "MAX_PLAYER_SPEED": 0.9,
    "CATCH_RADIUS": 0.8,
    "SHOT_TIME_MODIFIERS": {
        "SMASH": 0.45,
        "CLEAR": 1.6,
        "DROP": 0.9,
        "NORMAL": 1.0,
    },
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
    depth = (y_px - 50) / (CONSTANTS["SCREEN_H"] - 100)
    depth = max(0, min(1, depth))

    scale = 0.5 + depth * 0.7
    center_x = CONSTANTS["SCREEN_W"] // 2
    flat_x = to_px(x_unit)

    proj_x = int(center_x + (flat_x - center_x) * scale)
    proj_y = int(y_px * (0.85 + depth * 0.15))

    return proj_x, proj_y, scale

# ---------------- AVATAR DRAW ----------------
def draw_avatar(vis, x, y, color, facing="up", show_reach=False, reach_radius=40):
    x = int(x)
    y = int(y)

    # Head
    cv2.circle(vis, (x, y - 18), 8, color, -1)

    # Body
    cv2.line(vis, (x, y - 10), (x, y + 18), color, 3)

    # Arm / racket
    arm_end = (x, y - 35) if facing == "up" else (x, y + 35)
    cv2.line(vis, (x, y), arm_end, color, 2)
    cv2.circle(vis, arm_end, 4, (200, 200, 200), -1)

    # Yellow wide reach circle
    if show_reach:
        cv2.circle(vis, (x, y), reach_radius + 20, (0, 255, 255), 2)

print("🎮 Badminton Game – Ground View Version")

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
                print("🟢 Player ready")

    # -------- PLAYER HIT --------
    elif (
        game.state == "IDLE"
        and game.player_ready
        and now - game.last_stroke_time > CONSTANTS["COOLDOWN"]
    ):
        if detect_stroke(dx, dy):
            shot = classify_shot(dx, dy)
            if shot:
                print(f"🏸 Shot played: {shot}")
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

    # Court
    cv2.rectangle(vis, (50, 50), (550, 750), (0, 200, 0), 2)
    cv2.line(vis, (50, 400), (550, 400), (200, 200, 200), 1)

    player_y = getattr(game, "player_y", CONSTANTS["PLAYER_Y"])
    ai_y = getattr(game, "ai_y", CONSTANTS["AI_Y"])

    # Player (near)
    px, py, pscale = project_to_ground_view(game.player_x, player_y)
    draw_avatar(vis, px, py, (255, 0, 0), "up", True, int(45 * pscale))

    # AI (far)
    ax, ay, ascale = project_to_ground_view(game.ai_x, ai_y)
    draw_avatar(vis, ax, ay, (0, 0, 255), "down", True, int(40 * ascale))

    # Shuttle
    sx, sy, sscale = project_to_ground_view(game.shuttle_x, game.shuttle_y)
    cv2.circle(vis, (sx, sy), max(3, int(8 * sscale)), (255, 255, 255), -1)

    cv2.imshow("Badminton Game – Ground View", vis)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
