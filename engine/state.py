import time
import random


class GameState:
    def __init__(self):
        self.state = "IDLE"
        self.state_time = 0
        self.last_stroke_time = 0
        self.player_ready = True

        self.player_x = 5
        self.ai_x = 5
        self.target_player_x = 5

        self.shuttle_x = 5
        self.shuttle_y = 650

        self.to_ai_x = 5
        self.to_player_x = 5

        self.shot_type = "NORMAL"

    # ---------------- UTIL ----------------
    def random_target(self):
        return random.uniform(1.5, 8.5)

    # ---------------- PLAYER HIT ----------------
    def start_player_hit(self, now, shot_type="NORMAL"):
        self.shot_type = shot_type

        # Adjust target based on shot
        if shot_type == "DROP":
            self.to_ai_x = self.player_x + (self.random_target() - self.player_x) * 0.4
        else:
            self.to_ai_x = self.random_target()

        self.state = "TO_AI"
        self.state_time = now
        self.last_stroke_time = now
        self.player_ready = False

        print(f"🏸 Player hits ({shot_type})")

    # ---------------- AI SHOT CHOICE (STEP 3.1) ----------------
    def choose_ai_shot(self, incoming_shot):
        if incoming_shot == "SMASH":
            return random.choice(["CLEAR", "DROP"])

        if incoming_shot == "DROP":
            return random.choice(["DROP", "CLEAR"])

        if incoming_shot == "CLEAR":
            return random.choice(["SMASH", "CLEAR"])

        return "CLEAR"

    # ---------------- UPDATE LOOP ----------------
    def update(self, now, constants):
        PLAYER_Y = constants["PLAYER_Y"]
        AI_Y = constants["AI_Y"]

        BASE_SHUTTLE_TIME = constants["SHUTTLE_TIME"]
        AI_REACT_TIME = constants["AI_REACT_TIME"]
        CATCH_RADIUS = constants["CATCH_RADIUS"]

        # Shot-based shuttle timing
        shot = getattr(self, "shot_type", "NORMAL")
        SHOT_TIME_MODIFIERS = constants.get("SHOT_TIME_MODIFIERS", {})
        SHUTTLE_TIME = BASE_SHUTTLE_TIME * SHOT_TIME_MODIFIERS.get(shot, 1.0)

        # ---------------- PLAYER → AI ----------------
        if self.state == "TO_AI":
            t = min((now - self.state_time) / SHUTTLE_TIME, 1)

            self.shuttle_x = self.player_x + t * (self.to_ai_x - self.player_x)
            self.shuttle_y = PLAYER_Y - t * (PLAYER_Y - AI_Y)

            if t >= 1:
                self.ai_x = self.to_ai_x
                self.shuttle_x, self.shuttle_y = self.ai_x, AI_Y
                self.state = "AI_WAIT"
                self.state_time = now

        # ---------------- AI WAIT (STEP 3.2) ----------------
        elif self.state == "AI_WAIT":
            incoming = getattr(self, "shot_type", "NORMAL")

            # Reaction timing
            if incoming == "SMASH":
                react_time = AI_REACT_TIME * 1.4
            elif incoming == "DROP":
                react_time = AI_REACT_TIME * 0.6
            else:
                react_time = AI_REACT_TIME * 0.9

            if now - self.state_time > react_time:
                # AI chooses its OWN return shot
                ai_shot = self.choose_ai_shot(incoming)
                self.shot_type = ai_shot

                # Positioning strategy
                if ai_shot == "DROP":
                    self.to_player_x = (
                        self.ai_x + (self.player_x - self.ai_x) * 0.6
                    )
                else:
                    self.to_player_x = self.random_target()

                self.state = "TO_PLAYER"
                self.state_time = now

                print(f"🤖 AI hits back ({ai_shot})")

        # ---------------- AI → PLAYER ----------------
        elif self.state == "TO_PLAYER":
            t = min((now - self.state_time) / SHUTTLE_TIME, 1)

            self.shuttle_x = self.ai_x + t * (self.to_player_x - self.ai_x)
            self.shuttle_y = AI_Y + t * (PLAYER_Y - AI_Y)

            if t >= 1:
                if abs(self.shuttle_x - self.player_x) < CATCH_RADIUS:
                    print("🏆 Rally WON")
                else:
                    print("❌ Rally LOST")

                self.state = "IDLE"
                self.player_ready = False
