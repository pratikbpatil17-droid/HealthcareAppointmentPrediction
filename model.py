import os
import joblib
import numpy as np

from sklearn.ensemble import RandomForestClassifier

MODEL_PATH = "models/no_show_model.pkl"


def train_model():
    os.makedirs("models", exist_ok=True)

    # Sample training data
    # Features:
    # reminder_sent, previous_no_shows, waiting_days

    X = np.array([
        [1, 0, 1],
        [1, 0, 2],
        [1, 0, 3],
        [1, 1, 2],
        [1, 1, 5],
        [0, 0, 2],
        [0, 1, 3],
        [0, 2, 7],
        [0, 3, 10],
        [1, 2, 8],
        [1, 3, 10],
        [0, 4, 15],
        [1, 0, 4],
        [0, 0, 10],
        [0, 2, 12]
    ])

    # 0 = Show
    # 1 = No Show

    y = np.array([
        0,
        0,
        0,
        0,
        1,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        1,
        1
    ])

    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42
    )

    model.fit(X, y)

    joblib.dump(model, MODEL_PATH)

    return model


def load_model():

    if not os.path.exists(MODEL_PATH):
        return train_model()

    return joblib.load(MODEL_PATH)


def predict_no_show(reminder_sent, previous_no_shows, waiting_days):

    model = load_model()

    data = np.array([[
        reminder_sent,
        previous_no_shows,
        waiting_days
    ]])

    probability = model.predict_proba(data)[0][1]

    if probability >= 0.70:
        risk = "High"
    elif probability >= 0.40:
        risk = "Medium"
    else:
        risk = "Low"

    return round(probability * 100, 2), risk