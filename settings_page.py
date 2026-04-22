import flet as ft
import mysql.connector


def get_settings_view(page: ft.Page, user_name="User", on_logout=None):
    PRIMARY      = "#85bb65"
    RED          = "#ef4444"
    AMBER        = "#f59e0b"
    CARD_BG      = "#0f2d25"
    BG_DARK      = "#091f1a"
    BORDER_COLOR = "#1e4035"
    TEXT_DIM     = "#6b9e7e"

    db_config = {
        "host": "localhost", "user": "root",
        "password": "venera123!@ZX", "database": "money_tracker_v2",
    }

    def load_user():
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE name=%s", (user_name,))
            row = cursor.fetchone()
            db.close()
            return row or {}
        except:
            return {}

    user_data = load_user()
    email_val = user_data.get("email", "")

    status_text = ft.Text("", color=TEXT_DIM, size=12)

    # ── Change password ───────────────────────────────────────────────────────
    current_pw  = ft.TextField(label="Current Password", password=True, can_reveal_password=True,
                               border_color=BORDER_COLOR, focused_border_color=PRIMARY,
                               color="white", label_style=ft.TextStyle(color=TEXT_DIM),
                               border_radius=12, height=52)
    new_pw      = ft.TextField(label="New Password",     password=True, can_reveal_password=True,
                               border_color=BORDER_COLOR, focused_border_color=PRIMARY,
                               color="white", label_style=ft.TextStyle(color=TEXT_DIM),
                               border_radius=12, height=52)
    confirm_pw  = ft.TextField(label="Confirm Password", password=True, can_reveal_password=True,
                               border_color=BORDER_COLOR, focused_border_color=PRIMARY,
                               color="white", label_style=ft.TextStyle(color=TEXT_DIM),
                               border_radius=12, height=52)

    def change_password(e):
        if not all([current_pw.value, new_pw.value, confirm_pw.value]):
            status_text.value = "Please fill all password fields"
            status_text.color = AMBER
            page.update()
            return
        if new_pw.value != confirm_pw.value:
            status_text.value = "New passwords do not match"
            status_text.color = RED
            page.update()
            return
        if len(new_pw.value) < 6:
            status_text.value = "Password must be at least 6 characters"
            status_text.color = AMBER
            page.update()
            return
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE name=%s AND password=%s",
                           (user_name, current_pw.value))
            if not cursor.fetchone():
                db.close()
                status_text.value = "Current password is incorrect"
                status_text.color = RED
                page.update()
                return
            cursor.execute("UPDATE users SET password=%s WHERE name=%s",
                           (new_pw.value, user_name))
            db.commit()
            db.close()
            current_pw.value = ""
            new_pw.value     = ""
            confirm_pw.value = ""
            status_text.value = "Password updated successfully"
            status_text.color = PRIMARY
            page.snack_bar = ft.SnackBar(ft.Text("Password changed!"), bgcolor=PRIMARY)
            page.snack_bar.open = True
            page.update()
        except Exception as ex:
            print(f"PW change error: {ex}")
            status_text.value = "Database error"
            status_text.color = RED
            page.update()

    def confirm_delete_data(e):
        dlg = ft.AlertDialog(
            title=ft.Text("Delete All Data?", color=RED, weight="bold"),
            content=ft.Text(
                "This will permanently delete all your transactions and budgets.\nThis cannot be undone.",
                color=TEXT_DIM,
            ),
            actions=[
                ft.TextButton("Cancel",
                              style=ft.ButtonStyle(color=TEXT_DIM),
                              on_click=lambda _: setattr(dlg, "open", False) or page.update()),
                ft.TextButton("Delete Everything",
                              style=ft.ButtonStyle(color=RED),
                              on_click=lambda _: (setattr(dlg, "open", False), delete_all_data())),
            ],
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def delete_all_data():
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor()
            cursor.execute("DELETE FROM user_transactions WHERE user_name=%s", (user_name,))
            cursor.execute("UPDATE user_budgets SET spent_amount=0 WHERE user_name=%s", (user_name,))
            db.commit()
            db.close()
            status_text.value = "All transaction data cleared"
            status_text.color = PRIMARY
            page.snack_bar = ft.SnackBar(ft.Text("Data cleared"), bgcolor=PRIMARY)
            page.snack_bar.open = True
            page.update()
        except Exception as ex:
            print(f"Delete data error: {ex}")

    notif_switch = ft.Switch(
        value=True,
        active_color=PRIMARY,
        inactive_thumb_color=TEXT_DIM,
        label="Budget warnings",
        label_style=ft.TextStyle(color="white", size=13),
    )
    login_notif_switch = ft.Switch(
        value=False,
        active_color=PRIMARY,
        inactive_thumb_color=TEXT_DIM,
        label="Check on app start",
        label_style=ft.TextStyle(color="white", size=13),
    )

    def section_card(title, icon, content_controls):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, color=PRIMARY, size=18),
                    ft.Text(title, color="white", size=15, weight="bold"),
                ], spacing=10),
                ft.Container(height=1, bgcolor=BORDER_COLOR),
                *content_controls,
            ], spacing=14),
            bgcolor=CARD_BG,
            border=ft.border.all(1, BORDER_COLOR),
            padding=20,
            border_radius=20,
        )

    def setting_row(label, value):
        return ft.Row([
            ft.Text(label, color=TEXT_DIM, size=13, expand=True),
            ft.Text(value, color="white",  size=13, weight="bold"),
        ])

    return ft.Container(
        content=ft.ListView(
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Column([
                                ft.Text("Settings", size=26, weight="bold", color="white"),
                                ft.Text(f"Signed in as {user_name}", color=TEXT_DIM, size=12),
                            ], spacing=2),
                        ]),
                        ft.Container(height=1, bgcolor=BORDER_COLOR),

                        section_card("Account", ft.icons.PERSON_OUTLINE, [
                            setting_row("Username", user_name),
                            setting_row("Email",    email_val or "—"),
                        ]),

                        section_card("Change Password", ft.icons.LOCK_OUTLINE, [
                            current_pw, new_pw, confirm_pw,
                            ft.Container(
                                content=ft.Text("Update Password", color="white", size=13, weight="bold"),
                                alignment=ft.alignment.center,
                                height=46,
                                border_radius=12,
                                gradient=ft.LinearGradient(["#198754", "#143d33"]),
                                on_click=change_password,
                                ink=True,
                            ),
                            status_text,
                        ]),

                        section_card("Notifications", ft.icons.NOTIFICATIONS_OUTLINED, [
                            ft.Text("System notifications when budget is ≥85% used",
                                    color=TEXT_DIM, size=12),
                            notif_switch,
                            login_notif_switch,
                        ]),

                        section_card("Data Management", ft.icons.STORAGE_OUTLINED, [
                            ft.Text("Clear all transaction history and reset budgets to $0 spent.",
                                    color=TEXT_DIM, size=12),
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.icons.DELETE_FOREVER_OUTLINED, color=RED, size=18),
                                    ft.Text("Clear All Transactions", color=RED, size=13, weight="bold"),
                                ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                                alignment=ft.alignment.center,
                                height=46,
                                border_radius=12,
                                border=ft.border.all(1, ft.colors.with_opacity(0.5, RED)),
                                bgcolor=ft.colors.with_opacity(0.07, RED),
                                on_click=confirm_delete_data,
                                ink=True,
                            ),
                        ]),

                        section_card("About", ft.icons.INFO_OUTLINE, [
                            setting_row("App",     "Dollar Money Tracker"),
                            setting_row("Version", "2.0.0"),
                            setting_row("Built with", "Flet 0.23.2 + MySQL"),
                        ]),

                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.icons.LOGOUT_ROUNDED, color=RED, size=18),
                                ft.Text("Logout", color=RED, size=14, weight="bold"),
                            ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                            alignment=ft.alignment.center,
                            height=50,
                            border_radius=14,
                            border=ft.border.all(1, ft.colors.with_opacity(0.5, RED)),
                            bgcolor=ft.colors.with_opacity(0.07, RED),
                            on_click=lambda _: on_logout() if on_logout else None,
                            ink=True,
                        ),

                    ], spacing=16),
                    padding=ft.padding.symmetric(horizontal=24, vertical=20),
                )
            ],
            expand=True,
            spacing=0,
            padding=0,
        ),
        expand=True,
        bgcolor=BG_DARK,
    )