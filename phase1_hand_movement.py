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
MOVE_THRESHOLD = 0.03  # sensitivity

print("Move your hand. Press 'q' to quit.")

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

    if result.hand_landmarks:
        hand = result.hand_landmarks[0]

        # Palm center (average of landmarks)
        cx = sum(lm.x for lm in hand) / len(hand)
        cy = sum(lm.y for lm in hand) / len(hand)

        if prev_x is not None:
            dx = cx - prev_x
            dy = cy - prev_y

            if abs(dx) > abs(dy):
                if dx > MOVE_THRESHOLD:
                    direction = "RIGHT"
                elif dx < -MOVE_THRESHOLD:
                    direction = "LEFT"
                else:
                    direction = "STILL"
            else:
                if dy < -MOVE_THRESHOLD:
                    direction = "UP"
                elif dy > MOVE_THRESHOLD:
                    direction = "DOWN"
                else:
                    direction = "STILL"

            cv2.putText(
                frame,
                f"Direction: {direction}",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

        prev_x, prev_y = cx, cy

    cv2.imshow("Hand Movement Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
