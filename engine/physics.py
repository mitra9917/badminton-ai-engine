import math
import time

GRAVITY = -9.8   # units per second² (virtual)

class ShuttlePhysics3D:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0

        self.vx = 0
        self.vy = 0
        self.vz = 0

        self.start_time = 0
        self.active = False

    def launch(self, start_x, start_y, target_x, flight_time, arc_height):
        self.x = start_x
        self.y = start_y
        self.z = 0

        self.vx = (target_x - start_x) / flight_time
        self.vy = (start_y - start_y) / flight_time  # y handled externally
        self.vz = (2 * arc_height) / flight_time

        self.start_time = time.time()
        self.flight_time = flight_time
        self.active = True

    def update(self):
        if not self.active:
            return self.x, self.y, self.z, False

        t = time.time() - self.start_time
        if t > self.flight_time:
            self.z = 0
            self.active = False
            return self.x, self.y, self.z, False

        self.x += self.vx * 0.016  # approx 60 FPS
        self.z = self.vz * t + 0.5 * GRAVITY * t * t
        self.z = max(self.z, 0)

        return self.x, self.y, self.z, True
