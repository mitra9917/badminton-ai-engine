import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class HandTracker:
    def __init__(self):
        base_options = python.BaseOptions(
            model_asset_path="models/hand_landmarker.task"
        )
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.prev_x = None
        self.prev_y = None

    def get_hand_data(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )
        result = self.detector.detect(mp_image)

        if not result.hand_landmarks:
            return None, None, None, None

        hand = result.hand_landmarks[0]
        cx = sum(lm.x for lm in hand) / len(hand)
        cy = sum(lm.y for lm in hand) / len(hand)

        dx = dy = 0
        if self.prev_x is not None:
            dx = cx - self.prev_x
            dy = cy - self.prev_y

        self.prev_x, self.prev_y = cx, cy

        return cx, cy, dx, dy
