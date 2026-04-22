import flet as ft
import mysql.connector
import os

def get_profile_view(page: ft.Page, user_name="User"):
    PRIMARY   = "#85bb65"
    BORDER2   = "#1e4035"
    TEXT_GREY = "#6b9e7e"
    DARK_CARD = "#0f2d25"
    BG_DARK   = "#091f1a"
    AMBER     = "#f59e0b"
    BLUE      = "#3b82f6"
    RED       = "#ef4444"

    db_config = {
        "host":     "mysql.railway.internal",
        "user":     "root",
        "password": "FVmxLAOaqcNqRodWzphRlFoRnmWrsdwq",
        "database": "railway",
        "port":     3306,
    }

    state = {"goals": [], "selected_tab": 0}

    def load_db_data():
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM user_profile WHERE user_name=%s", (user_name,))
            profile = cursor.fetchone() or {
                "salary": 0, "savings": 0,
                "deposit_percent": 0, "total_saved": 0,
            }
            cursor.execute("SELECT * FROM user_goals WHERE user_name=%s", (user_name,))
            goals = cursor.fetchall()
            db.close()
            return profile, goals
        except Exception as e:
            return {"salary": 0, "savings": 0, "deposit_percent": 0, "total_saved": 0}, []

    profile, state["goals"] = load_db_data()

    def save_to_db(field, value):
        try:
            val = float(value or 0)
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor()
            sql = f"INSERT INTO user_profile (user_name, {field}) VALUES (%s, %s) ON DUPLICATE KEY UPDATE {field} = VALUES({field})"
            cursor.execute(sql, (user_name, val))
            db.commit()
            db.close()
        except:
            pass

    def make_field(label, value):
        return ft.TextField(
            label=label, 
            value=str(value) if value is not None else "0",
            border_color=BORDER2, 
            focused_border_color=PRIMARY,
            color="white", 
            label_style=ft.TextStyle(color=TEXT_GREY),
            border_radius=12, height=52,
            keyboard_type=ft.KeyboardType.NUMBER
        )

    def guide_step(num, title, desc, icon, color=PRIMARY):
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    ft.Text(str(num), size=16, weight="bold", color="white"),
                    width=40, height=40, bgcolor=ft.colors.with_opacity(0.25, color),
                    border_radius=12, alignment=ft.alignment.center,
                ),
                ft.Column([
                    ft.Row([ft.Icon(icon, color=color, size=16), ft.Text(title, color="white", size=14, weight="bold")], spacing=8),
                    ft.Text(desc, color=TEXT_GREY, size=12),
                ], spacing=4, expand=True),
            ], spacing=14),
            bgcolor=DARK_CARD, border=ft.border.all(1, BORDER2), padding=16, border_radius=14,
        )

    def tip_card(text, icon=ft.icons.LIGHTBULB_OUTLINE, color=AMBER):
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=color, size=18),
                ft.Text(text, color=TEXT_GREY, size=12, expand=True),
            ], spacing=12),
            bgcolor=ft.colors.with_opacity(0.06, color),
            border=ft.border.all(1, ft.colors.with_opacity(0.25, color)),
            padding=ft.padding.symmetric(horizontal=16, vertical=12), border_radius=12,
        )

    tf_total_saved = make_field("Total Balance ($)", profile.get("total_saved", 0))
    tf_salary      = make_field("Monthly Salary ($)", profile.get("salary", 0))
    tf_savings     = make_field("Monthly Savings ($)", profile.get("savings", 0))
    tf_percent     = make_field("Bank Interest %", profile.get("deposit_percent", 0))

    txt_projection = ft.Text("$0", size=30, weight="bold", color=PRIMARY)
    txt_free       = ft.Text("Free: $0", color="lightgreen", size=13)
    txt_goals_val  = ft.Text("In Goals: $0", color=AMBER, size=13)
    txt_balance    = ft.Text(f"${float(profile.get('total_saved', 0)):,.0f}", size=20, color="white", weight="bold")

    def recalc(e=None):
        try:
            total = float(tf_total_saved.value or 0)
            goals_total = sum(float(g.get("saved_amount") or 0) for g in state["goals"])
            free = total - goals_total
            s = float(tf_savings.value or 0)
            p = float(tf_percent.value or 0) / 100
            projection = (free + s * 12) * (1 + p)
            txt_projection.value = f"${projection:,.0f}"
            txt_free.value = f"Free: ${free:,.0f}"
            txt_goals_val.value = f"In Goals: ${goals_total:,.0f}"
            txt_balance.value = f"${total:,.0f}"
            page.update()
        except:
            pass

    tf_total_saved.on_change = recalc
    tf_savings.on_change     = recalc
    tf_percent.on_change     = recalc
    tf_total_saved.on_blur = lambda e: save_to_db("total_saved", e.control.value)
    tf_salary.on_blur      = lambda e: save_to_db("salary", e.control.value)
    tf_savings.on_blur     = lambda e: save_to_db("savings", e.control.value)
    tf_percent.on_blur     = lambda e: save_to_db("deposit_percent", e.control.value)

    overview_tab = ft.Column([
        ft.Row([
            ft.Container(content=ft.Column([ft.Text("Balance", color=TEXT_GREY, size=11), txt_balance]), padding=16, bgcolor=DARK_CARD, border=ft.border.all(1, BORDER2), border_radius=14, expand=True),
            ft.Container(content=ft.Column([ft.Text("Free", color=TEXT_GREY, size=11), txt_free]), padding=16, bgcolor=DARK_CARD, border=ft.border.all(1, BORDER2), border_radius=14, expand=True),
        ], spacing=12),
        ft.Container(content=ft.Column([ft.Row([ft.Icon(ft.icons.TRENDING_UP, color=PRIMARY, size=16), ft.Text("Annual Projection", color=TEXT_GREY, size=12, weight="bold")]), txt_projection], spacing=10), padding=18, bgcolor=DARK_CARD, border=ft.border.all(1, BORDER2), border_radius=16),
        ft.Container(content=ft.Column([ft.Row([ft.Icon(ft.icons.TUNE, color=PRIMARY, size=16), ft.Text("Financial Details", color=TEXT_GREY, size=12, weight="bold")]), tf_total_saved, tf_salary, tf_savings, tf_percent], spacing=10), padding=18, bgcolor=DARK_CARD, border=ft.border.all(1, BORDER2), border_radius=16)
    ], spacing=14)

    guide_tab = ft.Column([
        ft.Container(content=ft.Column([ft.Row([ft.Icon(ft.icons.MENU_BOOK_OUTLINED, color=PRIMARY, size=22), ft.Text("How to Use", color="white", size=16, weight="bold")]), ft.Text("Follow these steps to get the most out of the app", color=TEXT_GREY, size=12)], spacing=6), bgcolor=DARK_CARD, border=ft.border.all(1, BORDER2), padding=18, border_radius=16),
        guide_step(1, "Create Budgets", 'Go to Budget and set spending limits.', ft.icons.ACCOUNT_BALANCE_WALLET_OUTLINED),
        guide_step(2, "Log Expenses", 'Click any day in the Calendar to add transactions.', ft.icons.ADD_CIRCLE_OUTLINE, BLUE),
        guide_step(3, "Track Goals", 'Add a goal in Goals tab and track your savings.', ft.icons.FLAG_OUTLINED, AMBER),
        tip_card("Budget alerts fire automatically at 85% limit."),
    ], spacing=10)

    goals_tab = ft.Column([ft.Text("Goals feature active", color="white")], spacing=10)

    tab_contents = [overview_tab, goals_tab, guide_tab]
    content_container = ft.Container(content=overview_tab, expand=True)

    tab_labels = [("Overview", ft.icons.PERSON_OUTLINE), ("Goals", ft.icons.FLAG_OUTLINED), ("How to Use", ft.icons.MENU_BOOK_OUTLINED)]
    tab_btns = []

    def switch_tab(idx):
        content_container.content = tab_contents[idx]
        for i, btn in enumerate(tab_btns):
            is_sel = (i == idx)
            btn.bgcolor = ft.colors.with_opacity(0.2, PRIMARY) if is_sel else DARK_CARD
            btn.border = ft.border.all(1, ft.colors.with_opacity(0.4, PRIMARY) if is_sel else BORDER2)
            btn.content.controls[0].color = PRIMARY if is_sel else TEXT_GREY
            btn.content.controls[1].color = "white" if is_sel else TEXT_GREY
        page.update()

    for idx, (label, icon) in enumerate(tab_labels):
        btn = ft.Container(
            content=ft.Row([ft.Icon(icon, size=15, color=PRIMARY if idx==0 else TEXT_GREY), ft.Text(label, size=13, weight="bold", color="white" if idx==0 else TEXT_GREY)], spacing=8),
            bgcolor=ft.colors.with_opacity(0.2, PRIMARY) if idx==0 else DARK_CARD,
            border=ft.border.all(1, BORDER2), padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border_radius=12, on_click=lambda e, i=idx: switch_tab(i), ink=True, expand=True
        )
        tab_btns.append(btn)

    recalc()

    return ft.Container(
        content=ft.ListView(
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(ft.Text(user_name[0].upper(), size=22, weight="bold", color="white"), width=52, height=52, bgcolor=ft.colors.with_opacity(0.2, PRIMARY), border_radius=16, alignment=ft.alignment.center),
                            ft.Column([ft.Text(user_name, size=20, weight="bold", color="white"), ft.Text("Personal Finance Profile", color=TEXT_GREY, size=12)], spacing=3, expand=True),
                        ], spacing=14),
                        ft.Container(height=1, bgcolor=BORDER2),
                        ft.Row(tab_btns, spacing=10),
                        content_container,
                    ], spacing=16),
                    padding=24,
                )
            ], expand=True
        ),
        expand=True, bgcolor=BG_DARK
    )