import time
import random


class GameState:
    def __init__(self):
        self.state = "IDLE"
        self.state_time = 0
        self.last_stroke_time = 0
        self.player_ready = True

        # X positions (court width = 10 units)
        self.player_x = 5
        self.ai_x = 5
        self.target_player_x = 5

        # Y positions (2.5D)
        self.player_y = 650
        self.ai_y = 150

        # Smooth movement targets
        self.target_player_y = self.player_y
        self.target_ai_y = self.ai_y

        # Shuttle
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

        if shot_type == "DROP":
            self.to_ai_x = self.player_x + (self.random_target() - self.player_x) * 0.4
        else:
            self.to_ai_x = self.random_target()

        self.state = "TO_AI"
        self.state_time = now
        self.last_stroke_time = now
        self.player_ready = False

        print(f"🏸 Player hits ({shot_type})")

    # ---------------- AI SHOT CHOICE ----------------
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

        # ---- 2.5D COURT ZONES ----
        PLAYER_BASE_Y = PLAYER_Y
        PLAYER_NET_Y = PLAYER_Y - 80
        PLAYER_BACK_Y = PLAYER_Y + 40

        AI_BASE_Y = AI_Y
        AI_NET_Y = AI_Y + 80
        AI_BACK_Y = AI_Y - 40

        # ---- Timing ----
        BASE_SHUTTLE_TIME = constants["SHUTTLE_TIME"]
        AI_REACT_TIME = constants["AI_REACT_TIME"]
        CATCH_RADIUS = constants["CATCH_RADIUS"]

        shot = getattr(self, "shot_type", "NORMAL")
        SHOT_TIME_MODIFIERS = constants.get("SHOT_TIME_MODIFIERS", {})
        SHUTTLE_TIME = BASE_SHUTTLE_TIME * SHOT_TIME_MODIFIERS.get(shot, 1.0)

        # ---------------- PLAYER → AI ----------------
        if self.state == "TO_AI":
            t = min((now - self.state_time) / SHUTTLE_TIME, 1)

            if shot == "DROP":
                start_y = PLAYER_NET_Y
                self.target_player_y = PLAYER_NET_Y
            elif shot == "CLEAR":
                start_y = PLAYER_BACK_Y
                self.target_player_y = PLAYER_BACK_Y
            else:
                start_y = PLAYER_BASE_Y
                self.target_player_y = PLAYER_BASE_Y

            self.shuttle_x = self.player_x + t * (self.to_ai_x - self.player_x)
            self.shuttle_y = start_y - t * (start_y - AI_Y)

            if t >= 1:
                if shot == "DROP":
                    self.target_ai_y = AI_NET_Y
                elif shot == "CLEAR":
                    self.target_ai_y = AI_BACK_Y
                else:
                    self.target_ai_y = AI_BASE_Y

                self.ai_x = self.to_ai_x
                self.shuttle_x, self.shuttle_y = self.ai_x, self.ai_y
                self.state = "AI_WAIT"
                self.state_time = now

        # ---------------- AI WAIT ----------------
        elif self.state == "AI_WAIT":
            incoming = shot

            if incoming == "SMASH":
                react_time = AI_REACT_TIME * 1.4
            elif incoming == "DROP":
                react_time = AI_REACT_TIME * 0.6
            else:
                react_time = AI_REACT_TIME * 0.9

            if now - self.state_time > react_time:
                ai_shot = self.choose_ai_shot(incoming)
                self.shot_type = ai_shot

                if ai_shot == "DROP":
                    self.to_player_x = self.ai_x + (self.player_x - self.ai_x) * 0.6
                    self.target_ai_y = AI_NET_Y
                elif ai_shot == "CLEAR":
                    self.to_player_x = self.random_target()
                    self.target_ai_y = AI_BACK_Y
                else:
                    self.to_player_x = self.random_target()
                    self.target_ai_y = AI_BASE_Y

                self.state = "TO_PLAYER"
                self.state_time = now

                print(f"🤖 AI hits back ({ai_shot})")

        # ---------------- AI → PLAYER ----------------
        elif self.state == "TO_PLAYER":
            t = min((now - self.state_time) / SHUTTLE_TIME, 1)

            if shot == "DROP":
                ai_start_y = AI_NET_Y
            elif shot == "CLEAR":
                ai_start_y = AI_BACK_Y
            else:
                ai_start_y = AI_BASE_Y

            self.shuttle_x = self.ai_x + t * (self.to_player_x - self.ai_x)
            self.shuttle_y = ai_start_y + t * (PLAYER_Y - ai_start_y)

            # ---------- EARLY CATCH CHECK (NO CROSSING) ----------
            # Dynamic catch radius
            dynamic_radius = CATCH_RADIUS

            if shot == "SMASH":
                dynamic_radius *= 0.65
            elif shot == "DROP":
                dynamic_radius *= 1.25

            movement_speed = abs(self.target_player_x - self.player_x)
            dynamic_radius -= movement_speed * 0.4
            dynamic_radius = max(0.3, dynamic_radius)

            # Distance to player
            dist_x = abs(self.shuttle_x - self.player_x)
            dist_y = abs(self.shuttle_y - self.player_y)

            # If shuttle is close enough → CATCH EARLY
            if dist_x < dynamic_radius and dist_y < 35:
                # Snap shuttle to player (stick effect)
                self.shuttle_x = self.player_x
                self.shuttle_y = self.player_y

                print("🏆 Rally WON")

                if shot == "DROP":
                    self.target_player_y = PLAYER_NET_Y
                elif shot == "CLEAR":
                    self.target_player_y = PLAYER_BACK_Y
                else:
                    self.target_player_y = PLAYER_BASE_Y

                self.state = "IDLE"
                self.player_ready = False

            # Else, allow shuttle to continue and possibly miss
            elif t >= 1:
                print("❌ Rally LOST")

                self.state = "IDLE"
                self.player_ready = False

        # ---------------- SMOOTH ZONE TRANSITION ----------------
        Y_SMOOTHING = 0.15  # adjust 0.1–0.2 if needed

        self.player_y += (self.target_player_y - self.player_y) * Y_SMOOTHING
        self.ai_y += (self.target_ai_y - self.ai_y) * Y_SMOOTHING
