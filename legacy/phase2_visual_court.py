import cv2
import time
import random
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ---------------- CONSTANTS ----------------
COURT_WIDTH = 10
SCREEN_W, SCREEN_H = 600, 800

PLAYER_Y = 650
AI_Y = 150

SHUTTLE_TIME = 0.8
AI_REACT_TIME = 0.4
COOLDOWN = 0.8

MOVE_THRESHOLD = 0.035
NEUTRAL_THRESHOLD = 0.012

HAND_SENSITIVITY = 1.8
SMOOTHING = 0.35
MAX_PLAYER_SPEED = 1.0

CATCH_RADIUS = 0.8

# ---------------- GAME STATE ----------------
state = "IDLE"   # IDLE → TO_AI → AI_WAIT → TO_PLAYER
state_time = 0

last_stroke_time = 0
player_ready = True

player_x = COURT_WIDTH / 2
ai_x = COURT_WIDTH / 2

target_player_x = player_x

shuttle_x = player_x
shuttle_y = PLAYER_Y

to_ai_x = ai_x
to_player_x = player_x

# ---------------- HAND TRACKING ----------------
base_options = python.BaseOptions(
    model_asset_path="models/hand_landmarker.task"
)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1
)
detector = vision.HandLandmarker.create_from_options(options)
cap = cv2.VideoCapture(0)

prev_x, prev_y = None, None

# ---------------- HELPERS ----------------
def to_px(x_unit):
    return int(50 + x_unit * ((SCREEN_W - 100) / COURT_WIDTH))

def clamp(val, minv, maxv):
    return max(minv, min(maxv, val))

def detect_stroke(dx, dy):
    return abs(dx) > MOVE_THRESHOLD or abs(dy) > MOVE_THRESHOLD

def random_target():
    return random.uniform(1.5, 8.5)

# ---------------- MAIN LOOP ----------------
print("🎮 Badminton – AI fully plays, logs only (press q to quit)")

while True:
    ret, cam = cap.read()
    if not ret:
        break

    cam = cv2.flip(cam, 1)
    rgb = cv2.cvtColor(cam, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = detector.detect(mp_image)

    now = time.time()

    # ---------- HAND INPUT ----------
    if result.hand_landmarks:
        hand = result.hand_landmarks[0]
        cx = sum(lm.x for lm in hand) / len(hand)
        cy = sum(lm.y for lm in hand) / len(hand)

        mapped_x = (cx - 0.5) * HAND_SENSITIVITY + 0.5
        mapped_x = clamp(mapped_x, 0, 1)
        target_player_x = mapped_x * COURT_WIDTH

        if prev_x is not None:
            dx, dy = cx - prev_x, cy - prev_y

            if state == "IDLE" and not player_ready:
                if abs(dx) < NEUTRAL_THRESHOLD and abs(dy) < NEUTRAL_THRESHOLD:
                    player_ready = True
                    print("🟢 Player ready")

            elif state == "IDLE" and player_ready and now - last_stroke_time > COOLDOWN:
                if detect_stroke(dx, dy):
                    to_ai_x = random_target()
                    state = "TO_AI"
                    state_time = now
                    last_stroke_time = now
                    player_ready = False
                    print("🏸 Player hits")

        prev_x, prev_y = cx, cy

    # ---------- PLAYER MOVEMENT ----------
    delta = target_player_x - player_x
    delta = clamp(delta, -MAX_PLAYER_SPEED, MAX_PLAYER_SPEED)
    player_x += delta * SMOOTHING

    # ---------- STATE MACHINE ----------
    if state == "TO_AI":
        t = min((now - state_time) / SHUTTLE_TIME, 1.0)
        shuttle_x = player_x + t * (to_ai_x - player_x)
        shuttle_y = PLAYER_Y - t * (PLAYER_Y - AI_Y)

        if t >= 1.0:
            ai_x = to_ai_x
            shuttle_x, shuttle_y = ai_x, AI_Y
            state = "AI_WAIT"
            state_time = now

    elif state == "AI_WAIT":
        shuttle_x, shuttle_y = ai_x, AI_Y
        if now - state_time >= AI_REACT_TIME:
            to_player_x = random_target()
            state = "TO_PLAYER"
            state_time = now
            print("🤖 AI hits back")

    elif state == "TO_PLAYER":
        t = min((now - state_time) / SHUTTLE_TIME, 1.0)
        shuttle_x = ai_x + t * (to_player_x - ai_x)
        shuttle_y = AI_Y + t * (PLAYER_Y - AI_Y)

        if t >= 1.0:
            if abs(shuttle_x - player_x) < CATCH_RADIUS:
                shuttle_x, shuttle_y = player_x, PLAYER_Y
                print("🏆 Rally WON")
            else:
                print("❌ Rally LOST")

            state = "IDLE"
            player_ready = False

    # ---------- DRAW ----------
    frame = cam.copy()

    cv2.rectangle(frame, (50, 50), (SCREEN_W - 50, SCREEN_H - 50), (0, 200, 0), 2)
    cv2.line(frame, (50, SCREEN_H // 2), (SCREEN_W - 50, SCREEN_H // 2), (200, 200, 200), 1)

    cv2.circle(frame, (to_px(player_x), PLAYER_Y), 15, (255, 0, 0), -1)
    cv2.circle(frame, (to_px(ai_x), AI_Y), 15, (0, 0, 255), -1)
    cv2.circle(frame, (to_px(shuttle_x), int(shuttle_y)), 8, (255, 255, 255), -1)

    cv2.imshow("Badminton – Correct Rally Logic", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
