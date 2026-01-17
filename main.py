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
    }
}

# ---------------- INIT ----------------
cap = cv2.VideoCapture(0)
tracker = HandTracker()
game = GameState()

def clamp(val, minv, maxv):
    return max(minv, min(maxv, val))

def detect_stroke(dx, dy):
    return abs(dx) > CONSTANTS["MOVE_THRESHOLD"] or abs(dy) > CONSTANTS["MOVE_THRESHOLD"]

def to_px(x_unit):
    return int(
        50
        + x_unit * ((CONSTANTS["SCREEN_W"] - 100) / CONSTANTS["COURT_WIDTH"])
    )

print("🎮 Badminton Game – STABLE BASE VERSION")

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

        # Player becomes ready again
        if game.state == "IDLE" and not game.player_ready:
            if (
                abs(dx) < CONSTANTS["NEUTRAL_THRESHOLD"]
                and abs(dy) < CONSTANTS["NEUTRAL_THRESHOLD"]
            ):
                game.player_ready = True
                print("🟢 Player ready")

        # Player hits shuttle
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

    cv2.rectangle(
        vis,
        (50, 50),
        (CONSTANTS["SCREEN_W"] - 50, CONSTANTS["SCREEN_H"] - 50),
        (0, 200, 0),
        2,
    )

    cv2.line(
        vis,
        (50, CONSTANTS["SCREEN_H"] // 2),
        (CONSTANTS["SCREEN_W"] - 50, CONSTANTS["SCREEN_H"] // 2),
        (200, 200, 200),
        1,
    )

    cv2.circle(
        vis,
        (to_px(game.player_x), CONSTANTS["PLAYER_Y"]),
        15,
        (255, 0, 0),
        -1,
    )

    cv2.circle(
        vis,
        (to_px(game.ai_x), CONSTANTS["AI_Y"]),
        15,
        (0, 0, 255),
        -1,
    )

    cv2.circle(
        vis,
        (to_px(game.shuttle_x), int(game.shuttle_y)),
        8,
        (255, 255, 255),
        -1,
    )

    cv2.imshow("Badminton Game", vis)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
