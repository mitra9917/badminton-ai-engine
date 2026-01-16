import time
import random

COURT_WIDTH = 10  # units
PLAYER_X = COURT_WIDTH // 2
AI_X = COURT_WIDTH // 2

def simulate_shuttle(stroke):
    time.sleep(0.8)  # shuttle travel time

    if stroke == "Cross‑court shot":
        return random.randint(0, COURT_WIDTH // 2)
    elif stroke == "Straight shot":
        return random.randint(COURT_WIDTH // 2, COURT_WIDTH)
    elif stroke == "Smash":
        return random.randint(3, 7)
    elif stroke == "Drop shot":
        return random.randint(4, 6)
    else:
        return None

def ai_move(target_x):
    global AI_X
    print(f"AI moving from {AI_X} → {target_x}")
    AI_X = target_x

def ai_return():
    return random.choice([
        "Straight shot",
        "Cross‑court shot",
        "Drop shot"
    ])

print("🏸 Badminton Rally Started")

while True:
    stroke = input("You played (LEFT/RIGHT/UP/DOWN or q): ")

    if stroke == "q":
        break

    print("Shuttle in air...")
    landing_x = simulate_shuttle(stroke)

    ai_move(landing_x)
    time.sleep(0.5)

    ai_stroke = ai_return()
    print(f"🤖 AI returns with: {ai_stroke}")
    print("-" * 40)
