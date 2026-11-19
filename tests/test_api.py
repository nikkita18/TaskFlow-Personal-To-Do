import os
import tempfile
import unittest
import json
from app import create_app
import database

class TestTaskTrackerAPI(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "SECRET_KEY": "test-secret"
        })
        self.client = self.app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    # ------------------ Auth Tests ------------------

    def test_register_success(self):
        res = self.client.post("/api/auth/register", json={
            "email": "Test@Example.COM",
            "password": "Password123",
            "name": "Tester"
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["email"], "test@example.com")
        self.assertIn("id", data)
        self.assertNotIn("password", data)
        self.assertNotIn("password_hash", data)

    def test_register_validation_errors(self):
        # Multiple bad fields: bad email and bad password
        res = self.client.post("/api/auth/register", json={
            "email": "not-an-email",
            "password": "short"
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("errors", data)
        self.assertIn("email", data["errors"])
        self.assertIn("password", data["errors"])

    def test_register_duplicate_email(self):
        self.client.post("/api/auth/register", json={
            "email": "user@test.com",
            "password": "Password123"
        })
        res = self.client.post("/api/auth/register", json={
            "email": "USER@test.com",
            "password": "AnotherPassword456"
        })
        self.assertEqual(res.status_code, 409)
        self.assertIn("error", res.get_json())

    def test_login_success_and_logout(self):
        self.client.post("/api/auth/register", json={
            "email": "user@test.com",
            "password": "Password123"
        })
        res = self.client.post("/api/auth/login", json={
            "email": "user@test.com",
            "password": "Password123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("token", data)
        self.assertIn("expiresIn", data)
        token = data["token"]

        # Verify /api/auth/me works
        me_res = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.get_json()["email"], "user@test.com")

        # Logout session
        logout_res = self.client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(logout_res.status_code, 204)

        # Token is now invalid
        me_after_logout = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_after_logout.status_code, 401)

    def test_login_invalid_credentials_identical_message(self):
        # Register user
        self.client.post("/api/auth/register", json={
            "email": "realuser@test.com",
            "password": "Password123"
        })

        # Non-existent user
        res_unknown = self.client.post("/api/auth/login", json={
            "email": "fakeuser@test.com",
            "password": "Password123"
        })
        self.assertEqual(res_unknown.status_code, 401)

        # Real user, wrong password
        res_wrong_pw = self.client.post("/api/auth/login", json={
            "email": "realuser@test.com",
            "password": "WrongPassword999"
        })
        self.assertEqual(res_wrong_pw.status_code, 401)

        # CRITICAL requirement: exact same message for unknown email and bad password
        self.assertEqual(res_unknown.get_json()["error"], res_wrong_pw.get_json()["error"])

    def test_multi_session_isolation(self):
        self.client.post("/api/auth/register", json={
            "email": "sessionuser@test.com",
            "password": "Password123"
        })
        # Login twice (two sessions)
        res1 = self.client.post("/api/auth/login", json={"email": "sessionuser@test.com", "password": "Password123"})
        token1 = res1.get_json()["token"]
        res2 = self.client.post("/api/auth/login", json={"email": "sessionuser@test.com", "password": "Password123"})
        token2 = res2.get_json()["token"]

        # Logout token1
        self.client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token1}"})

        # Token1 is invalidated
        res_t1 = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token1}"})
        self.assertEqual(res_t1.status_code, 401)

        # Token2 remains valid!
        res_t2 = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token2}"})
        self.assertEqual(res_t2.status_code, 200)

    # ------------------ Task Tests ------------------

    def _login(self, email="tester@test.com", password="Password123"):
        self.client.post("/api/auth/register", json={"email": email, "password": password, "name": "Tester"})
        res = self.client.post("/api/auth/login", json={"email": email, "password": password})
        return res.get_json()["token"]

    def test_create_task_validation(self):
        token = self._login()
        headers = {"Authorization": f"Bearer {token}"}

        # Empty title and invalid due date and invalid priority
        res = self.client.post("/api/tasks", json={
            "title": "   ",
            "dueDate": "2026-13-45",
            "priority": "urgent"
        }, headers=headers)
        self.assertEqual(res.status_code, 400)
        errors = res.get_json().get("errors", {})
        self.assertIn("title", errors)
        self.assertIn("dueDate", errors)
        self.assertIn("priority", errors)

    def test_create_and_get_task(self):
        token = self._login()
        headers = {"Authorization": f"Bearer {token}"}

        res = self.client.post("/api/tasks", json={
            "title": "Fix network bug",
            "description": "Investigate routing loop",
            "dueDate": "2026-11-30",
            "priority": "high"
        }, headers=headers)
        self.assertEqual(res.status_code, 201)
        task = res.get_json()
        self.assertEqual(task["title"], "Fix network bug")
        self.assertEqual(task["description"], "Investigate routing loop")
        self.assertEqual(task["dueDate"], "2026-11-30")
        self.assertEqual(task["priority"], "high")
        self.assertEqual(task["done"], False)
        self.assertIn("id", task)
        self.assertIn("createdAt", task)

        # Fetch single task
        task_id = task["id"]
        get_res = self.client.get(f"/api/tasks/{task_id}", headers=headers)
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.get_json()["id"], task_id)

    def test_patch_task(self):
        token = self._login()
        headers = {"Authorization": f"Bearer {token}"}

        create_res = self.client.post("/api/tasks", json={"title": "Original Title"}, headers=headers)
        task_id = create_res.get_json()["id"]

        # Patch partially
        patch_res = self.client.patch(f"/api/tasks/{task_id}", json={
            "title": "Updated Title",
            "done": True,
            "priority": "low"
        }, headers=headers)
        self.assertEqual(patch_res.status_code, 200)
        updated = patch_res.get_json()
        self.assertEqual(updated["title"], "Updated Title")
        self.assertEqual(updated["done"], True)
        self.assertEqual(updated["priority"], "low")

        # Patch with no valid editable fields
        bad_patch = self.client.patch(f"/api/tasks/{task_id}", json={"unknownField": 123}, headers=headers)
        self.assertEqual(bad_patch.status_code, 400)

    def test_delete_task(self):
        token = self._login()
        headers = {"Authorization": f"Bearer {token}"}

        create_res = self.client.post("/api/tasks", json={"title": "Task to delete"}, headers=headers)
        task_id = create_res.get_json()["id"]

        del_res = self.client.delete(f"/api/tasks/{task_id}", headers=headers)
        self.assertEqual(del_res.status_code, 204)

        # Verify it's gone
        get_res = self.client.get(f"/api/tasks/{task_id}", headers=headers)
        self.assertEqual(get_res.status_code, 404)

    def test_cross_user_isolation(self):
        token_a = self._login("usera@test.com", "Password123")
        token_b = self._login("userb@test.com", "Password123")

        # User A creates a task
        res_a = self.client.post("/api/tasks", json={"title": "User A Private Task"}, headers={"Authorization": f"Bearer {token_a}"})
        task_id = res_a.get_json()["id"]

        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User B attempts to read User A's task -> Must be 404 (not 403)
        self.assertEqual(self.client.get(f"/api/tasks/{task_id}", headers=headers_b).status_code, 404)

        # User B attempts to update User A's task -> Must be 404
        self.assertEqual(self.client.patch(f"/api/tasks/{task_id}", json={"title": "Hacked"}, headers=headers_b).status_code, 404)

        # User B attempts to delete User A's task -> Must be 404
        self.assertEqual(self.client.delete(f"/api/tasks/{task_id}", headers=headers_b).status_code, 404)

        # Verify User A's task is untouched
        check_a = self.client.get(f"/api/tasks/{task_id}", headers={"Authorization": f"Bearer {token_a}"})
        self.assertEqual(check_a.status_code, 200)
        self.assertEqual(check_a.get_json()["title"], "User A Private Task")

    def test_task_filters_and_sorting(self):
        token = self._login()
        headers = {"Authorization": f"Bearer {token}"}

        # Create tasks
        t1 = self.client.post("/api/tasks", json={"title": "Buy Milk", "priority": "low", "dueDate": "2026-11-21"}, headers=headers).get_json()
        t2 = self.client.post("/api/tasks", json={"title": "Submit Assignment", "priority": "high", "dueDate": "2026-11-20"}, headers=headers).get_json()
        t3 = self.client.post("/api/tasks", json={"title": "Someday Project", "priority": "medium", "dueDate": None}, headers=headers).get_json()

        # Mark t1 as done
        self.client.patch(f"/api/tasks/{t1['id']}", json={"done": True}, headers=headers)

        # Filter: status=open
        open_res = self.client.get("/api/tasks?status=open", headers=headers)
        self.assertEqual(open_res.status_code, 200)
        open_ids = [t["id"] for t in open_res.get_json()]
        self.assertIn(t2["id"], open_ids)
        self.assertIn(t3["id"], open_ids)
        self.assertNotIn(t1["id"], open_ids)

        # Filter: status=done
        done_res = self.client.get("/api/tasks?status=done", headers=headers)
        self.assertEqual(len(done_res.get_json()), 1)
        self.assertEqual(done_res.get_json()[0]["id"], t1["id"])

        # Filter: search q="milk"
        q_res = self.client.get("/api/tasks?q=milk", headers=headers)
        self.assertEqual(len(q_res.get_json()), 1)
        self.assertEqual(q_res.get_json()[0]["id"], t1["id"])

        # Sorting: sort=dueDate&order=asc -> null due dates come LAST
        sort_res = self.client.get("/api/tasks?sort=dueDate&order=asc", headers=headers)
        sorted_tasks = sort_res.get_json()
        self.assertEqual(sorted_tasks[0]["id"], t2["id"])  # 2026-11-20
        self.assertEqual(sorted_tasks[1]["id"], t1["id"])  # 2026-11-21
        self.assertEqual(sorted_tasks[2]["id"], t3["id"])  # null dueDate comes last

        # Sorting: sort=priority&order=desc -> high (t2) > medium (t3) > low (t1)
        pri_res = self.client.get("/api/tasks?sort=priority&order=desc", headers=headers)
        pri_tasks = pri_res.get_json()
        self.assertEqual(pri_tasks[0]["priority"], "high")
        self.assertEqual(pri_tasks[1]["priority"], "medium")
        self.assertEqual(pri_tasks[2]["priority"], "low")

if __name__ == "__main__":
    unittest.main()
