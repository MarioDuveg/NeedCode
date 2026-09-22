from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_problem_list_hides_test_data():
    response = client.get("/api/problems")
    assert response.status_code == 200
    problems = response.json()
    assert len(problems) == 3
    assert all(p["test_count"] == 10 for p in problems)
    assert all("tests" not in p for p in problems)


def test_rejects_imports():
    response = client.post(
        "/api/submit",
        json={"problem": "suffix-array", "code": "import os\ndef suffix_array(s): return []"},
    )
    assert response.status_code == 400
    assert "imports" in response.json()["detail"]


def test_correct_small_suffix_solution_gets_partial_credit_or_better():
    # Deliberately simple implementation: correctness is what matters here,
    # while the largest hidden cases may reject inefficient strategies.
    code = "def suffix_array(s):\n    return sorted(range(len(s)), key=lambda i: s[i:])\n"
    response = client.post("/api/submit", json={"problem": "suffix-array", "code": code})
    assert response.status_code == 200
    data = response.json()
    assert data["score"] >= 4
    assert data["total"] == 10
