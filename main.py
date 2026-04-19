import flet as ft
import mysql.connector
from calendar_page import get_calendar_view 
from budget_page import get_budget_view
from dashboard_page import get_dashboard_view
from profile_page import get_profile_view

def db_connect():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="venera123!@ZX",
        database="money_tracker_v2"
    )

def main(page: ft.Page):
    page.title = "Dollar Money Tracker"
    page.bgcolor = "#0b2e26"
    page.window_width = 1100 
    page.window_height = 850
    page.padding = 0  
    
    # This is the key: a single container for the right side
    content_area = ft.Container(expand=True, padding=20)

    def change_route(page_name, user_name):
        """Updates content WITHOUT clearing the whole page (No black flash)"""
        if page_name == "calendar":
            content_area.content = get_calendar_view(page, user_name=user_name)
        elif page_name == "budget":
            content_area.content = get_budget_view(page, user_name=user_name)
        elif page_name == "dashboard":
            content_area.content = get_dashboard_view(page, user_name=user_name)
        elif page_name == "profile":
            content_area.content = get_profile_view(page, user_name=user_name)
        
        page.update()

    def show_main_layout(user_name="User"):
        """Builds the sidebar structure once and never cleans it again"""
        page.clean()
        page.vertical_alignment = "start"
        page.horizontal_alignment = "start"

        nav_sidebar = ft.Container(
            content=ft.Column([
                ft.Container(height=20),
                ft.Text("  Menu", size=22, weight="bold", color="#85bb65"),
                ft.Divider(color="#198754", thickness=1),
                ft.TextButton("Dashboard", icon=ft.icons.DASHBOARD, 
                              on_click=lambda _: change_route("dashboard", user_name), 
                              style=ft.ButtonStyle(color="white")),
                ft.TextButton("Calendar", icon=ft.icons.CALENDAR_MONTH, 
                              on_click=lambda _: change_route("calendar", user_name), 
                              style=ft.ButtonStyle(color="white")),
                ft.TextButton("Budget", icon=ft.icons.ACCOUNT_BALANCE_WALLET, 
                              on_click=lambda _: change_route("budget", user_name), 
                              style=ft.ButtonStyle(color="white")),
                ft.TextButton("Profile", icon=ft.icons.PERSON, 
                              on_click=lambda _: change_route("profile", user_name), 
                              style=ft.ButtonStyle(color="white")),
                ft.Container(expand=True), # Spacer
                ft.TextButton("Logout", icon=ft.icons.LOGOUT, 
                              on_click=lambda _: main(page), 
                              style=ft.ButtonStyle(color="red")),
                ft.Container(height=10),
            ], spacing=15),
            bgcolor="#143d33",
            padding=15,
            width=220,
        )

        # Main layout assembly
        main_layout = ft.Row(
            [
                nav_sidebar,
                ft.VerticalDivider(width=1, color="#198754"),
                content_area  # This is where views will be swapped
            ],
            expand=True,
            spacing=0,
        )

        page.add(main_layout)
        # Load the first page immediately
        change_route("dashboard", user_name)

    # --- Authentication Logic ---

    def on_login(e):
        try:
            db = db_connect()
            cursor = db.cursor()
            cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", 
                         (email_input.value, pass_input.value))
            user = cursor.fetchone()
            if user:
                show_main_layout(user[1])
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Wrong credentials"), bgcolor="red")
                page.snack_bar.open = True
            db.close()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Database Error! {ex}"), bgcolor="red")
            page.snack_bar.open = True
        page.update()

    def on_signup(e):
        try:
            db = db_connect()
            cursor = db.cursor()
            cursor.execute("INSERT INTO users (email, password, name) VALUES (%s, %s, %s)", 
                         (email_input.value, pass_input.value, name_input.value))
            db.commit()
            page.snack_bar = ft.SnackBar(ft.Text("Success! Please login."), bgcolor="#198754")
            page.snack_bar.open = True
            switch_view(None) 
            db.close()
        except Exception:
            page.snack_bar = ft.SnackBar(ft.Text("User already exists"), bgcolor="red")
            page.snack_bar.open = True
        page.update()

    auth_mode = "login"
    email_input = ft.TextField(label="Email Address", border_color="#85bb65", color="white", border_radius=10)
    pass_input = ft.TextField(label="Password", password=True, can_reveal_password=True, border_color="#85bb65", color="white", border_radius=10)
    name_input = ft.TextField(label="Your Name", border_color="#85bb65", color="white", border_radius=10, visible=False)
    title_text = ft.Text("Money Tracker", size=32, weight="bold", color="#85bb65")
    subtitle_text = ft.Text("Sign in to your account", color="#dee2e6", size=14)

    def switch_view(e):
        nonlocal auth_mode
        if auth_mode == "login":
            auth_mode = "signup"; title_text.value = "Create Account"; name_input.visible = True
            main_button.text = "CREATE ACCOUNT"; main_button.on_click = on_signup
            toggle_text.value = "Already a member? Login now"
        else:
            auth_mode = "login"; title_text.value = "Money Tracker"; name_input.visible = False
            main_button.text = "LOGIN"; main_button.on_click = on_login
            toggle_text.value = "Not a member? Signup now"
        page.update()

    main_button = ft.ElevatedButton("LOGIN", bgcolor="#198754", color="white", width=350, height=55, on_click=on_login)
    toggle_text = ft.TextButton("Not a member? Signup now", style=ft.ButtonStyle(color="#85bb65"), on_click=switch_view)

    # Login UI setup
    login_screen = ft.Container(
        content=ft.Column([
            title_text, subtitle_text, ft.Container(height=10),
            name_input, email_input, pass_input, main_button, toggle_text
        ], horizontal_alignment="center", spacing=15),
        bgcolor="#143d33", padding=40, border_radius=30, width=400
    )

    # Initial page settings for login
    page.clean()
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"
    page.add(login_screen)

ft.app(target=main)