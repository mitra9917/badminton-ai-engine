import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time

# Load hand model
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
MOVE_THRESHOLD = 0.03
COOLDOWN = 1.0  # seconds
last_stroke_time = 0

def get_stroke(direction):
    return {
        "LEFT": "Cross‑court shot",
        "RIGHT": "Straight shot",
        "UP": "Smash",
        "DOWN": "Drop shot"
    }.get(direction, None)

print("Play badminton with your hand 🏸  Press 'q' to quit.")

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

    stroke_text = "Waiting..."

    if result.hand_landmarks:
        hand = result.hand_landmarks[0]
        cx = sum(lm.x for lm in hand) / len(hand)
        cy = sum(lm.y for lm in hand) / len(hand)

        if prev_x is not None:
            dx = cx - prev_x
            dy = cy - prev_y

            direction = None
            if abs(dx) > abs(dy):
                if dx > MOVE_THRESHOLD:
                    direction = "RIGHT"
                elif dx < -MOVE_THRESHOLD:
                    direction = "LEFT"
            else:
                if dy < -MOVE_THRESHOLD:
                    direction = "UP"
                elif dy > MOVE_THRESHOLD:
                    direction = "DOWN"

            now = time.time()
            if direction and now - last_stroke_time > COOLDOWN:
                stroke = get_stroke(direction)
                stroke_text = f"You played: {stroke}"
                print(stroke_text)
                last_stroke_time = now

        prev_x, prev_y = cx, cy

    cv2.putText(
        frame,
        stroke_text,
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 255),
        2
    )

    cv2.imshow("Badminton Stroke Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
