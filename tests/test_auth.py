from datetime import datetime, timedelta, timezone

from modules import auth


class FakeUserRepo:
    def __init__(self, now=None):
        self.users = {}
        self.now = now  # lets lockout tests control the clock

    def create_user(self, name, email, password_hash, role="passenger"):
        if email in self.users:
            return None
        self.users[email] = {
            "id": len(self.users) + 1,
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "failed_attempts": 0,
            "locked_until": None,
        }
        return self.users[email]["id"]

    def get_by_email(self, email):
        return self.users.get(email)

    def record_failed_login(self, user_id, max_attempts, lock_minutes):
        user = next(u for u in self.users.values() if u["id"] == user_id)
        user["failed_attempts"] += 1
        if user["failed_attempts"] >= max_attempts:
            user["failed_attempts"] = 0
            user["locked_until"] = (self.now or datetime.now(timezone.utc)) + timedelta(minutes=lock_minutes)
        return {"failed_attempts": user["failed_attempts"], "locked_until": user["locked_until"]}

    def reset_failed_logins(self, user_id):
        user = next(u for u in self.users.values() if u["id"] == user_id)
        user["failed_attempts"] = 0
        user["locked_until"] = None


def test_valid_registration_creates_account():  # TC-Auth-01
    repo = FakeUserRepo()
    user_id, errors = auth.register_user("Asha", "asha@example.com", "longenough1", repo=repo)
    assert errors == []
    assert user_id == 1


def test_duplicate_email_rejected():  # TC-Auth-01
    repo = FakeUserRepo()
    auth.register_user("Asha", "asha@example.com", "longenough1", repo=repo)
    user_id, errors = auth.register_user("Asha 2", "ASHA@example.com", "longenough1", repo=repo)
    assert user_id is None
    assert "already exists" in errors[0]


def test_invalid_registration_fields_rejected():
    repo = FakeUserRepo()
    user_id, errors = auth.register_user("", "not-an-email", "short", repo=repo)
    assert user_id is None
    assert len(errors) == 3
    assert repo.users == {}


def test_password_is_hashed_not_plaintext():  # TC-Sec-03 (PRJ-SR-002)
    repo = FakeUserRepo()
    auth.register_user("Asha", "asha@example.com", "longenough1", repo=repo)
    stored = repo.users["asha@example.com"]["password_hash"]
    assert stored != "longenough1"
    assert "longenough1" not in stored


def test_login_with_correct_credentials():  # TC-Auth-02
    repo = FakeUserRepo()
    auth.register_user("Asha", "asha@example.com", "longenough1", repo=repo)
    user = auth.authenticate("asha@example.com", "longenough1", repo=repo)
    assert user is not None and user["name"] == "Asha"


def test_login_with_wrong_password_or_unknown_user():  # TC-Auth-02
    repo = FakeUserRepo()
    auth.register_user("Asha", "asha@example.com", "longenough1", repo=repo)
    assert auth.authenticate("asha@example.com", "wrongpass", repo=repo) is None
    assert auth.authenticate("nobody@example.com", "longenough1", repo=repo) is None
    assert auth.authenticate("", "", repo=repo) is None
