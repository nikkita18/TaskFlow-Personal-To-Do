"""
Seed script for TaskFlow
Populates the database with demo users and realistic sample tasks.
Run with: python seed.py
"""

from datetime import datetime, timedelta, timezone
from app import create_app
import models

def seed_database():
    app = create_app()
    with app.app_context():
        demo_email = "demo@taskflow.dev"
        demo_pw = "Password123"

        # Check if already seeded
        existing_user = models.get_user_by_email(demo_email)
        if existing_user:
            print(f"[Seed] User '{demo_email}' already exists. Skipping user creation.")
            user_id = existing_user["id"]
        else:
            user = models.create_user(demo_email, demo_pw, "Demo Candidate")
            user_id = user["id"]
            print(f"[Seed] Created demo user: {demo_email} (Password: {demo_pw})")

        now = datetime.now(timezone.utc)
        yesterday = (now - timedelta(days=2)).strftime("%Y-%m-%d")
        today = now.strftime("%Y-%m-%d")
        tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        next_week = (now + timedelta(days=7)).strftime("%Y-%m-%d")

        sample_tasks = [
            ("Prepare slides for CN recruitment", "Walk through architecture and SQLite design", today, "high", False),
            ("Submit assignment report", "Review edge cases and test coverage", yesterday, "high", False),  # Overdue
            ("Refactor API auth middleware", "Ensure constant-time verification and session revocation", yesterday, "medium", False), # Overdue
            ("Design phone-first responsive layouts", "CSS media queries down to 360px viewport", today, "high", True), # Completed
            ("Implement PBKDF2 password hashing", "Ensure >= 100,000 iterations and salt", today, "medium", True), # Completed
            ("Write unit tests for task sorting", "Verify null due dates sort to the bottom", tomorrow, "medium", False),
            ("Clean up Git commit history", "Ensure small atomic commits over 24-hour cycle", next_week, "low", False),
            ("Review HTTP status codes", "400 validation, 401 unauth, 404 isolation, 409 conflict", next_week, "low", False),
            ("Check XSS prevention measures", "Ensure strictly DOM textContent and zero raw innerHTML", None, "medium", False),
            ("Inspect PWA manifest and service worker", "Test offline caching behavior in Chrome DevTools", None, "low", True),
        ]

        # Check existing tasks count
        existing_tasks = models.get_tasks(user_id)
        if len(existing_tasks) < len(sample_tasks):
            for title, desc, due, prio, done in sample_tasks:
                task = models.create_task(user_id, title, desc, due, prio)
                if done:
                    models.update_task(user_id, task["id"], {"done": True})
            print(f"[Seed] Successfully added {len(sample_tasks)} realistic sample tasks!")
        else:
            print(f"[Seed] Database already has {len(existing_tasks)} tasks for {demo_email}.")

if __name__ == "__main__":
    seed_database()
