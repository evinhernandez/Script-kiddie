from __future__ import annotations

AUTH = {"X-API-Key": "test-key"}


class TestCreateJob:
    def test_create_job(self, client):
        resp = client.post(
            "/jobs",
            json={"target_path": "/workspace", "ruleset": "rulesets/owasp-llm-top10.yml"},
            headers=AUTH,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data

    def test_create_job_missing_api_key(self, client):
        resp = client.post("/jobs", json={"target_path": "/workspace"})
        assert resp.status_code == 401

    def test_create_job_bad_api_key(self, client):
        resp = client.post(
            "/jobs",
            json={"target_path": "/workspace"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401

    def test_create_job_path_traversal_rejected(self, client):
        resp = client.post(
            "/jobs",
            json={"target_path": "/etc/passwd"},
            headers=AUTH,
        )
        assert resp.status_code == 400

    def test_create_job_ruleset_traversal_rejected(self, client):
        resp = client.post(
            "/jobs",
            json={"target_path": "/workspace", "ruleset": "../../etc/passwd"},
            headers=AUTH,
        )
        assert resp.status_code == 400


class TestListJobs:
    def test_list_empty(self, client):
        resp = client.get("/jobs", headers=AUTH)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_after_create(self, client):
        client.post(
            "/jobs",
            json={"target_path": "/workspace"},
            headers=AUTH,
        )
        resp = client.get("/jobs", headers=AUTH)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_list_requires_auth(self, client):
        resp = client.get("/jobs")
        assert resp.status_code == 401

    def test_list_limit_bounds(self, client):
        resp = client.get("/jobs?limit=0", headers=AUTH)
        assert resp.status_code == 422

        resp = client.get("/jobs?limit=501", headers=AUTH)
        assert resp.status_code == 422


class TestGetJob:
    def test_get_existing(self, client):
        create_resp = client.post(
            "/jobs",
            json={"target_path": "/workspace"},
            headers=AUTH,
        )
        job_id = create_resp.json()["job_id"]
        resp = client.get(f"/jobs/{job_id}", headers=AUTH)
        assert resp.status_code == 200
        assert resp.json()["id"] == job_id

    def test_get_nonexistent(self, client):
        resp = client.get("/jobs/nonexistent", headers=AUTH)
        assert resp.status_code == 404

    def test_get_requires_auth(self, client):
        resp = client.get("/jobs/some-id")
        assert resp.status_code == 401


class TestGetResults:
    def test_results_existing(self, client):
        create_resp = client.post(
            "/jobs",
            json={"target_path": "/workspace"},
            headers=AUTH,
        )
        job_id = create_resp.json()["job_id"]
        resp = client.get(f"/jobs/{job_id}/results", headers=AUTH)
        assert resp.status_code == 200
        data = resp.json()
        assert "findings" in data
        assert "model_calls" in data

    def test_results_nonexistent(self, client):
        resp = client.get("/jobs/nonexistent/results", headers=AUTH)
        assert resp.status_code == 404
