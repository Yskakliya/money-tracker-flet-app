"""
notifications.py — System notification helper for Money Tracker
Uses plyer for cross-platform OS notifications (Windows/Mac/Linux).
"""

import os


def _send(title: str, message: str, app_name: str = "Money Tracker"):
    """Send a system notification. Falls back to print if plyer unavailable."""
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name=app_name,
            timeout=6,
        )
    except ImportError:
        os.system("pip install plyer --break-system-packages -q")
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                app_name=app_name,
                timeout=6,
            )
        except Exception:
            print(f"[NOTIFY] {title}: {message}")
    except Exception as e:
        print(f"[NOTIFY] {title}: {message} (error: {e})")


def notify_budget_warning(category: str, pct: float, spent: float, limit: float):
    """Fire when a category reaches >= 85% of its budget."""
    if pct >= 1.0:
        _send(
            title=" Budget Exceeded!",
            message=f"{category}: ${spent:,.0f} spent — OVER limit of ${limit:,.0f}",
        )
    else:
        _send(
            title=" Budget Warning",
            message=f"{category}: {pct*100:.0f}% used (${spent:,.0f} / ${limit:,.0f})",
        )


def notify_transaction_saved(category: str, amount: float):
    """Fire after a transaction is saved successfully."""
    _send(
        title=" Transaction Saved",
        message=f"${amount:,.2f} added to {category}",
    )


def notify_export_done(file_path: str):
    """Fire after an export is completed."""
    filename = os.path.basename(file_path)
    _send(
        title=" Export Complete",
        message=f"Saved: {filename}",
    )


def check_and_notify_budgets(db_config: dict, user_name: str):
    """
    Connect to DB, check all budgets for the user, and fire
    a system notification for any category >= 85% used.
    Call this on app start-up or after saving a transaction.
    """
    try:
        import mysql.connector
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT category_name, limit_amount, spent_amount FROM user_budgets WHERE user_name=%s",
            (user_name,),
        )
        budgets = cursor.fetchall()
        db.close()

        for b in budgets:
            limit = float(b["limit_amount"])
            spent = float(b["spent_amount"])
            if limit <= 0:
                continue
            pct = spent / limit
            if pct >= 0.85:
                notify_budget_warning(b["category_name"], pct, spent, limit)

    except Exception as e:
        print(f"[NOTIFY] Budget check error: {e}")