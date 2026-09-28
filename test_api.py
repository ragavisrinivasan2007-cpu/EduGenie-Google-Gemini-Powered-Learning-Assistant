import os

os.environ["DEMO_MODE"] = "true"
os.environ["GEMINI_API_KEY"] = ""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["demo_mode"] is True


def test_qna():
    response = client.get("/qna", params={"question": "What is AI?"})
    assert response.status_code == 200
    assert "answer" in response.json()


def test_explain():
    response = client.post("/explain", json={"topic": "Photosynthesis"})
    assert response.status_code == 200
    assert response.json()["topic"] == "Photosynthesis"


def test_summary():
    response = client.post(
        "/summarize",
        json={
            "text": (
                "Photosynthesis is the process by which green plants use light energy "
                "to convert carbon dioxide and water into glucose and oxygen."
            )
        },
    )
    assert response.status_code == 200
    assert "summary" in response.json()


def test_quiz():
    response = client.post(
        "/quiz",
        json={
            "text": "The Earth revolves around the Sun.",
            "question_count": 3,
        },
    )
    assert response.status_code == 200

    questions = response.json()["questions"]
    assert len(questions) == 3

    for question in questions:
        assert len(question["options"]) == 4
        assert question["answer"] in question["options"]


def test_learning_recommendations():
    response = client.get(
        "/learn/recommendations",
        params={"topic": "SQL"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["topic"] == "SQL"
    assert len(data["steps"]) >= 1
    assert len(data["adaptive_tips"]) >= 1
