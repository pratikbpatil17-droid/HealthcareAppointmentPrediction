import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier


MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "no_show_model.pkl")


def train_model():
    # Sample training data
    data = {
        "reminder_sent": [
            1, 1, 0, 0, 1,
            1, 0, 1, 0, 0,
            1, 1, 0, 0, 1,
            0, 1, 0, 1, 1
        ],
        "previous_no_shows": [
            0, 1, 2, 3, 0,
            0, 2, 1, 3, 2,
            0, 1, 4, 2, 0,
            3, 0, 2, 1, 0
        ],
        "waiting_days": [
            2, 5, 10, 20, 3,
            1, 15, 4, 25, 12,
            2, 6, 18, 30, 1,
            14, 3, 8, 5, 2
        ],
        "no_show": [
            0, 0, 1, 1, 0,
            0, 1, 0, 1, 1,
            0, 0, 1, 1, 0,
            1, 0, 1, 0, 0
        ]
    }

    df = pd.DataFrame(data)

    X = df[
        [
            "reminder_sent",
            "previous_no_shows",
            "waiting_days"
        ]
    ]

    y = df["no_show"]

    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42
    )

    model.fit(X, y)

    os.makedirs(MODEL_DIR, exist_ok=True)

    joblib.dump(model, MODEL_PATH)

    print("ML model trained successfully!")
    print(f"Model saved at: {MODEL_PATH}")


def load_model():
    if not os.path.exists(MODEL_PATH):
        train_model()

    return joblib.load(MODEL_PATH)


def predict_no_show(
    reminder_sent,
    previous_no_shows,
    waiting_days
):
    model = load_model()

    input_data = pd.DataFrame(
        [[
            int(reminder_sent),
            int(previous_no_shows),
            int(waiting_days)
        ]],
        columns=[
            "reminder_sent",
            "previous_no_shows",
            "waiting_days"
        ]
    )

    probability = model.predict_proba(input_data)[0][1]

    if probability >= 0.70:
        risk_level = "High"
    elif probability >= 0.40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return probability, risk_level


if __name__ == "__main__":
    train_model()

    probability, risk = predict_no_show(
        reminder_sent=0,
        previous_no_shows=2,
        waiting_days=10
    )

    print(f"No-show probability: {probability:.2%}")
    print(f"Risk level: {risk}")