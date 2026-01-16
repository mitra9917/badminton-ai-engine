import cv2
import time
import random
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ---------------- GAME CONSTANTS ----------------
COURT_WIDTH = 10
SHUTTLE_TIME = 0.8      # shuttle flight time (seconds)
COOLDOWN = 1.0          # minimum time between strokes
MOVE_THRESHOLD = 0.03

# ---------------- GAME STATE ----------------
pending_shuttle = False
shuttle_start_time = 0
current_stroke = None
last_stroke_time = 0

# ---------------- HAND TRACKING SETUP ----------------
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

# ---------------- GAME LOGIC FUNCTIONS ----------------
def detect_stroke(dx, dy):
    if abs(dx) > abs(dy):
        if dx > MOVE_THRESHOLD:
            return "Straight shot"
        elif dx < -MOVE_THRESHOLD:
            return "Cross-court shot"
    else:
        if dy < -MOVE_THRESHOLD:
            return "Smash"
        elif dy > MOVE_THRESHOLD:
            return "Drop shot"
    return None

def shuttle_landing(stroke):
    if stroke == "Cross-court shot":
        return random.randint(0, COURT_WIDTH // 2)
    elif stroke == "Straight shot":
        return random.randint(COURT_WIDTH // 2, COURT_WIDTH)
    elif stroke == "Smash":
        return random.randint(3, 7)
    elif stroke == "Drop shot":
        return random.randint(4, 6)

def ai_return():
    return random.choice([
        "Straight shot",
        "Cross-court shot",
        "Drop shot"
    ])

print("🏸 LIVE BADMINTON RALLY (NON-BLOCKING) — Press 'q' to quit")

# ---------------- MAIN LOOP ----------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb
    )

    result = detector.detect(mp_image)
    display_text = "Waiting..."

    now = time.time()

    # ---------------- HAND PROCESSING ----------------
    if result.hand_landmarks:
        hand = result.hand_landmarks[0]
        cx = sum(lm.x for lm in hand) / len(hand)
        cy = sum(lm.y for lm in hand) / len(hand)

        if prev_x is not None:
            dx = cx - prev_x
            dy = cy - prev_y

            # -------- PLAYER STROKE (NON-BLOCKING) --------
            if not pending_shuttle and now - last_stroke_time > COOLDOWN:
                stroke = detect_stroke(dx, dy)
                if stroke:
                    current_stroke = stroke
                    shuttle_start_time = now
                    pending_shuttle = True
                    last_stroke_time = now

                    display_text = f"You: {stroke}"
                    print(display_text)

        prev_x, prev_y = cx, cy

    # ---------------- SHUTTLE & AI LOGIC ----------------
    if pending_shuttle and now - shuttle_start_time > SHUTTLE_TIME:
        landing = shuttle_landing(current_stroke)
        ai_stroke = ai_return()

        print(f"Shuttle lands at X={landing}")
        print(f"🤖 AI returns: {ai_stroke}")
        print("-" * 40)

        pending_shuttle = False

    # ---------------- RENDER ----------------
    cv2.putText(
        frame,
        display_text,
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 255),
        2
    )

    cv2.imshow("Badminton Live Rally (Smooth)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
