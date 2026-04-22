import flet as ft
import mysql.connector
from calendar_page import get_calendar_view
from budget_page import get_budget_view
from dashboard_page import get_dashboard_view
from profile_page import get_profile_view
from transactions_page import get_transactions_view
from add_transaction_page import get_add_transaction_view
from export_page import get_export_view
from settings_page import get_settings_view
from notifications import check_and_notify_budgets


DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "venera123!@ZX",
    "database": "money_tracker_v2",
}


def db_connect():
    return mysql.connector.connect(**DB_CONFIG)


def main(page: ft.Page):
    page.fonts = {
        "Inter": "https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bslnt%2Cwght%5D.ttf"
    }
    page.theme        = ft.Theme(font_family="Inter")
    page.title        = "Dollar Money Tracker"
    page.bgcolor      = "#0b2e26"
    page.window_width  = 1100
    page.window_height = 850
    page.padding      = 0

    content_area = ft.Container(expand=True)

    active_route = {"value": "dashboard"}

    nav_buttons: dict[str, ft.Container] = {}

    def nav_button(text, icon, route):
        def on_hover(e):
            is_active = active_route["value"] == route
            if not is_active:
                e.control.bgcolor = (
                    ft.colors.with_opacity(0.1, "white") if e.data == "true" else None
                )
                page.update()

        btn = ft.Container(
            content=ft.Row([
                ft.Icon(icon, color="#85bb65", size=20),
                ft.Text(text, color="white", size=14, weight="w500"),
            ], spacing=14),
            padding=ft.padding.symmetric(vertical=11, horizontal=14),
            border_radius=12,
            on_click=lambda _, r=route: change_route(r),
            on_hover=on_hover,
            animate=ft.animation.Animation(150, "decelerate"),
        )
        nav_buttons[route] = btn
        return btn

    def update_active_nav(route):
        for r, btn in nav_buttons.items():
            if r == route:
                btn.bgcolor = ft.colors.with_opacity(0.18, "#85bb65")
                btn.border  = ft.border.all(1, ft.colors.with_opacity(0.25, "#85bb65"))
            else:
                btn.bgcolor = None
                btn.border  = None
        page.update()

    _current_user: dict[str, str] = {"name": "User"}

    def change_route(route: str):
        active_route["value"] = route
        uname = _current_user["name"]

        if route == "dashboard":
            content_area.content = get_dashboard_view(page, user_name=uname)
        elif route == "calendar":
            content_area.content = get_calendar_view(page, user_name=uname)
        elif route == "budget":
            content_area.content = get_budget_view(page, user_name=uname)
        elif route == "profile":
            content_area.content = get_profile_view(page, user_name=uname)
        elif route == "transactions":
            content_area.content = get_transactions_view(page, user_name=uname)
        elif route == "add_transaction":
            content_area.content = get_add_transaction_view(
                page,
                user_name=uname,
                on_saved=lambda: change_route("transactions"),
            )
        elif route == "export":
            content_area.content = get_export_view(page, user_name=uname)
        elif route == "settings":
            content_area.content = get_settings_view(
                page,
                user_name=uname,
                on_logout=lambda: main(page),
            )

        update_active_nav(route)
        page.update()

    def show_main_layout(user_name="User"):
        _current_user["name"] = user_name
        page.clean()
        page.vertical_alignment   = ft.MainAxisAlignment.START
        page.horizontal_alignment = ft.CrossAxisAlignment.START

        try:
            check_and_notify_budgets(DB_CONFIG, user_name)
        except Exception as e:
            print(f"Startup notify error: {e}")

        sidebar = ft.Container(
            content=ft.Column([
                ft.Container(height=20),
                ft.Row([
                    ft.Icon(ft.icons.MONETIZATION_ON_OUTLINED, color="#85bb65", size=26),
                    ft.Text("Tracker", size=22, weight="bold", color="white"),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=8),
                ft.Divider(color=ft.colors.with_opacity(0.15, "white"), thickness=1),

                ft.Container(
                    ft.Text("MAIN", color=ft.colors.with_opacity(0.4, "white"), size=10, weight="bold"),
                    padding=ft.padding.only(left=14, top=8, bottom=4),
                ),
                nav_button("Dashboard",    ft.icons.DASHBOARD_OUTLINED,              "dashboard"),
                nav_button("Calendar",     ft.icons.CALENDAR_MONTH_OUTLINED,         "calendar"),
                nav_button("Budget",       ft.icons.ACCOUNT_BALANCE_WALLET_OUTLINED, "budget"),
                nav_button("Profile",      ft.icons.PERSON_OUTLINE,                  "profile"),

                ft.Container(height=4),
                ft.Divider(color=ft.colors.with_opacity(0.1, "white"), thickness=1),

                ft.Container(
                    ft.Text("TRANSACTIONS", color=ft.colors.with_opacity(0.4, "white"), size=10, weight="bold"),
                    padding=ft.padding.only(left=14, top=8, bottom=4),
                ),
                nav_button("History",      ft.icons.RECEIPT_LONG_OUTLINED,    "transactions"),
                nav_button("Add Expense",  ft.icons.ADD_CIRCLE_OUTLINE,       "add_transaction"),

                ft.Container(height=4),
                ft.Divider(color=ft.colors.with_opacity(0.1, "white"), thickness=1),

                ft.Container(
                    ft.Text("TOOLS", color=ft.colors.with_opacity(0.4, "white"), size=10, weight="bold"),
                    padding=ft.padding.only(left=14, top=8, bottom=4),
                ),
                nav_button("Export",   ft.icons.FILE_DOWNLOAD_OUTLINED, "export"),
                nav_button("Settings", ft.icons.SETTINGS_OUTLINED,      "settings"),

                ft.Container(expand=True),

                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.LOGOUT_ROUNDED, color="#ff5252", size=20),
                        ft.Text("Logout", color="#ff5252", size=14, weight="bold"),
                    ], spacing=14),
                    padding=ft.padding.symmetric(vertical=11, horizontal=14),
                    on_click=lambda _: main(page),
                    border_radius=12,
                    on_hover=lambda e: setattr(
                        e.control, "bgcolor",
                        ft.colors.with_opacity(0.07, "red") if e.data == "true" else None,
                    ),
                ),
                ft.Container(height=10),
            ], spacing=4),
            bgcolor=ft.colors.with_opacity(0.4, "#143d33"),
            blur=ft.Blur(15, 15),
            padding=ft.padding.symmetric(horizontal=10, vertical=0),
            width=230,
            border=ft.border.only(right=ft.BorderSide(0.5, ft.colors.with_opacity(0.15, "white"))),
        )

        page.add(ft.Row([sidebar, content_area], expand=True, spacing=0))
        change_route("profile")

    import re

    def validate_email(email: str) -> str | None:
        """Returns error message or None if valid."""
        if not email:
            return "Email is required"
        pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return "Enter a valid email (e.g. name@example.com)"
        return None

    def validate_password(password: str, is_signup: bool) -> str | None:
        """Returns error message or None if valid."""
        if not password:
            return "Password is required"
        if is_signup:
            if len(password) < 8:
                return "At least 8 characters required"
            if not re.search(r'[A-Z]', password):
                return "Must contain at least one uppercase letter"
            if not re.search(r'[0-9]', password):
                return "Must contain at least one number"
            if not re.search(r'[!@#$%^&*(),.?\":{}|<>_\-]', password):
                return "Must contain at least one special character (!@#$...)"
        return None

    def clear_errors():
        email_input.error_text  = None
        pass_input.error_text   = None
        name_input.error_text   = None
        page.update()

    def on_login(e):
        clear_errors()
        email_err = validate_email(email_input.value)
        pass_err  = validate_password(pass_input.value, is_signup=False)
        has_error = False

        if email_err:
            email_input.error_text = email_err
            has_error = True
        if pass_err:
            pass_input.error_text = pass_err
            has_error = True
        if has_error:
            page.update()
            return

        try:
            db = db_connect()
            cursor = db.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE email=%s AND password=%s",
                (email_input.value.strip().lower(), pass_input.value),
            )
            user = cursor.fetchone()
            db.close()
            if user:
                show_main_layout(user[1])
            else:
                email_input.error_text = "Wrong email or password"
                pass_input.error_text  = "Wrong email or password"
                page.update()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Database Error: {ex}"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    def on_signup(e):
        clear_errors()
        name_err  = None if name_input.value.strip() else "Name is required"
        email_err = validate_email(email_input.value)
        pass_err  = validate_password(pass_input.value, is_signup=True)
        has_error = False

        if name_err:
            name_input.error_text = name_err
            has_error = True
        if email_err:
            email_input.error_text = email_err
            has_error = True
        if pass_err:
            pass_input.error_text = pass_err
            has_error = True
        if has_error:
            page.update()
            return

        try:
            db = db_connect()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO users (email, password, name) VALUES (%s, %s, %s)",
                (email_input.value.strip().lower(), pass_input.value, name_input.value.strip()),
            )
            db.commit()
            db.close()
            page.snack_bar = ft.SnackBar(ft.Text("Account created! Please login."), bgcolor="#198754")
            page.snack_bar.open = True
            switch_view(None)
            page.update()
        except Exception:
            email_input.error_text = "This email is already registered"
            page.update()

    auth_mode    = "login"
    email_input  = ft.TextField(
        label="Email", hint_text="name@example.com",
        border_color="#85bb65", focused_border_color="#85bb65",
        color="white", label_style=ft.TextStyle(color="#6b9e7e"),
        hint_style=ft.TextStyle(color="#3d6b57"),
        prefix_icon=ft.icons.EMAIL_OUTLINED,
        border_radius=12, height=56,
        keyboard_type=ft.KeyboardType.EMAIL,
        on_change=lambda e: setattr(email_input, "error_text", None) or page.update(),
    )
    pass_input   = ft.TextField(
        label="Password",
        border_color="#85bb65", focused_border_color="#85bb65",
        color="white", label_style=ft.TextStyle(color="#6b9e7e"),
        prefix_icon=ft.icons.LOCK_OUTLINE,
        border_radius=12, height=56,
        password=True, can_reveal_password=True,
        on_change=lambda e: setattr(pass_input, "error_text", None) or page.update(),
    )
    name_input   = ft.TextField(
        label="Your Name",
        border_color="#85bb65", focused_border_color="#85bb65",
        color="white", label_style=ft.TextStyle(color="#6b9e7e"),
        prefix_icon=ft.icons.PERSON_OUTLINE,
        border_radius=12, height=56,
        visible=False,
        on_change=lambda e: setattr(name_input, "error_text", None) or page.update(),
    )

    pw_hint = ft.Text(
        "8+ chars · uppercase · number · special char (!@#$...)",
        color="#3d6b57", size=11, visible=False,
    )

    title_text    = ft.Text("Money Tracker",       size=32, weight="bold", color="#85bb65")
    subtitle_text = ft.Text("Sign in to continue", color="#8a9e90", size=13)

    def switch_view(e):
        nonlocal auth_mode
        if auth_mode == "login":
            auth_mode = "signup"
            title_text.value          = "Create Account"
            name_input.visible        = True
            pw_hint.visible           = True
            main_button.content.value = "CREATE ACCOUNT"
            main_button.on_click      = on_signup
            toggle_text.text          = "Already a member? Login now"
        else:
            auth_mode = "login"
            title_text.value          = "Money Tracker"
            name_input.visible        = False
            pw_hint.visible           = False
            main_button.content.value = "LOGIN"
            main_button.on_click      = on_login
            toggle_text.text          = "Not a member? Sign up now"
        clear_errors()
        page.update()

    main_button = ft.Container(
        content=ft.Text("LOGIN", color="white", weight="bold", size=15),
        alignment=ft.alignment.center,
        width=340, height=52,
        border_radius=13,
        gradient=ft.LinearGradient(["#198754", "#143d33"]),
        on_click=on_login,
        on_hover=lambda e: setattr(e.control, "scale", 1.02 if e.data == "true" else 1.0),
        animate_scale=200,
    )
    toggle_text = ft.TextButton(
        "Not a member? Sign up now",
        style=ft.ButtonStyle(color="#85bb65"),
        on_click=switch_view,
    )

    login_screen = ft.Container(
        content=ft.Column([
            ft.Icon(ft.icons.LOCK_PERSON_OUTLINED, size=48, color="#85bb65"),
            title_text, subtitle_text,
            ft.Container(height=8),
            name_input, email_input, pass_input,
            pw_hint,
            ft.Container(height=8),
            main_button, toggle_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=14),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#143d33", "#0b2e26"],
        ),
        padding=40, border_radius=28, width=440,
        shadow=ft.BoxShadow(
            blur_radius=32,
            color=ft.colors.with_opacity(0.45, "black"),
            offset=ft.Offset(0, 14),
        ),
    )

    page.clean()
    page.vertical_alignment   = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.add(login_screen)


ft.app(target=main)