from dataclasses import dataclass, field

@dataclass
class ExpectedIssue:
    file: str
    line_range: tuple[int, int]
    keywords: list[str]


@dataclass
class EvalCase:
    name: str
    diff: str
    expected_issues: list[ExpectedIssue] = field(default_factory=list)


GOLDEN_DATASET: list[EvalCase] = [
    EvalCase(
        name="sql_injection_via_string_interpolation",
        diff="""### src/auth.py

@@ -10,6 +10,15 @@ def login(username, password):
+def reset_password(user_id, new_password):
+    db.execute(
+        f"UPDATE users SET password='{new_password}' WHERE id={user_id}"
+    )
+    return True""",
        expected_issues=[
            ExpectedIssue(file="src/auth.py", line_range=(11, 14), keywords=["sql injection", "parameteriz"]),
        ],
    ),
    EvalCase(
        name="plaintext_password_storage",
        diff="""### src/auth.py

@@ -25,4 +25,9 @@ def login(username, password):
+def create_user(username, password):
+    user = User(username=username, password=password)
+    db.session.add(user)
+    db.session.commit()
+    return user""",
        expected_issues=[
            ExpectedIssue(file="src/auth.py", line_range=(25, 29), keywords=["plaintext", "hash"]),
        ],
    ),
    EvalCase(
        name="missing_none_check",
        diff="""### src/orders.py

@@ -40,4 +40,8 @@ def process_order(order_id):
+def get_shipping_city(order_id):
+    order = orders.find(order_id)
+    city = order.address.city
+    return city""",
        expected_issues=[
            ExpectedIssue(file="src/orders.py", line_range=(40, 43), keywords=["none", "attributeerror", "null"]),
        ],
    ),
    EvalCase(
        name="off_by_one_loop",
        diff="""### src/inventory.py

@@ -15,3 +15,8 @@ def restock(items):
+def apply_discount_to_last_n(items, n):
+    result = []
+    for i in range(len(items) - n, len(items) + 1):
+        result.append(items[i])
+    return result""",
        expected_issues=[
            ExpectedIssue(file="src/inventory.py", line_range=(17, 18), keywords=["off-by-one", "index", "range"]),
        ],
    ),
    EvalCase(
        name="resource_leak",
        diff="""### src/reports.py

@@ -30,2 +30,6 @@ def load_config():
+def export_report(path, data):
+    f = open(path, "w")
+    f.write(data)
+    return True""",
        expected_issues=[
            ExpectedIssue(file="src/reports.py", line_range=(30, 33), keywords=["resource leak", "not closed", "context manager", "with statement"]),
        ],
    ),
    EvalCase(
        name="hardcoded_credential",
        diff="""### src/integrations/payment.py

@@ -1,3 +1,8 @@
+import requests
+
+STRIPE_API_KEY = "hardcoded-secret-do-not-commit-1234567890"
+
+def charge_customer(amount, customer_id):
+    return requests.post("https://api.stripe.com/v1/charges", auth=(STRIPE_API_KEY, ""), data={"amount": amount, "customer": customer_id})""",
        expected_issues=[
            ExpectedIssue(file="src/integrations/payment.py", line_range=(3, 3), keywords=["hardcoded", "secret", "credential", "api key"]),
        ],
    ),
    EvalCase(
        name="broad_exception_swallow",
        diff="""### src/sync.py

@@ -12,3 +12,9 @@ def run_sync():
+def sync_user_records(records):
+    for record in records:
+        try:
+            save(record)
+        except Exception:
+            pass
+    return True""",
        expected_issues=[
            ExpectedIssue(file="src/sync.py", line_range=(14, 17), keywords=["swallow", "except exception", "silently", "bare except"]),
        ],
    ),
    EvalCase(
        name="clean_refactor",
        diff="""### src/utils.py

@@ -8,5 +8,5 @@ def format_name(first, last):
-    full = first + " " + last
-    return full.strip()
+    full_name = f"{first} {last}"
+    return full_name.strip()""",
        expected_issues=[],
    ),
    EvalCase(
        name="clean_feature_addition",
        diff="""### src/notifications.py

@@ -18,3 +18,10 @@ class NotificationService:
+    def send_welcome_email(self, user):
+        if not user.email:
+            return False
+        subject = "Welcome!"
+        body = f"Hi {user.name}, welcome aboard."
+        self.mailer.send(to=user.email, subject=subject, body=body)
+        return True""",
        expected_issues=[],
    ),
    EvalCase(
        name="clean_defensive_fix",
        diff="""### src/api/validators.py

@@ -3,4 +3,11 @@ def validate_age(age):
+def validate_email(email):
+    if not email or "@" not in email:
+        raise ValueError("Invalid email address")
+    return email.strip().lower()""",
        expected_issues=[],
    ),
]

