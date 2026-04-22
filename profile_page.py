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
            print(e)
            return {"salary": 0, "savings": 0, "deposit_percent": 0, "total_saved": 0}, []

    profile, state["goals"] = load_db_data()

    def get_goals_total():
        return sum(float(g.get("saved_amount") or 0) for g in state["goals"])

    def make_field(label, value):
        return ft.TextField(
            label=label, 
            value=str(value) if value is not None else "0",
            border_color=BORDER2, 
            focused_border_color=PRIMARY,
            color="white", 
            label_style=ft.TextStyle(color=TEXT_GREY),
            border_radius=12, 
            height=52,
            keyboard_type=ft.KeyboardType.NUMBER
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
            goals = get_goals_total()
            free  = total - goals
            s     = float(tf_savings.value or 0)
            p     = float(tf_percent.value or 0) / 100
            projection = (free + s * 12) * (1 + p)
            txt_projection.value = f"${projection:,.0f}"
            txt_free.value       = f"Free: ${free:,.0f}"
            txt_goals_val.value  = f"In Goals: ${goals:,.0f}"
            txt_balance.value    = f"${total:,.0f}"
            page.update()
        except:
            pass

    tf_total_saved.on_change = recalc
    tf_savings.on_change     = recalc
    tf_percent.on_change     = recalc

    def save_to_db(field, value):
        try:
            val = float(value or 0)
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor()
            sql = f"INSERT INTO user_profile (user_name, {field}) VALUES (%s, %s) ON DUPLICATE KEY UPDATE {field} = VALUES({field})"
            cursor.execute(sql, (user_name, val))
            db.commit()
            db.close()
        except Exception as e:
            print(e)

    tf_total_saved.on_blur = lambda e: save_to_db("total_saved", e.control.value)
    tf_salary.on_blur      = lambda e: save_to_db("salary", e.control.value)
    tf_savings.on_blur     = lambda e: save_to_db("savings", e.control.value)
    tf_percent.on_blur     = lambda e: save_to_db("deposit_percent", e.control.value)

    goals_list = ft.Column(spacing=10)

    def add_money(goal, field, bar, text_w, pct_text, width):
        try:
            amount = float(field.value or 0)
            if amount <= 0: return
            new_amount = float(goal["saved_amount"] or 0) + amount
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor()
            cursor.execute("UPDATE user_goals SET saved_amount=%s WHERE user_name=%s AND goal_name=%s", (new_amount, user_name, goal["goal_name"]))
            db.commit()
            db.close()
            goal["saved_amount"] = new_amount
            field.value = ""
            refresh_goals()
            recalc()
        except:
            pass

    def goal_card(g):
        price = float(g["goal_price"] or 1)
        saved = float(g["saved_amount"] or 0)
        pct = min(saved / price, 1.0)
        width = 260
        bar = ft.Container(width=max(4, int(width * pct)), height=6, bgcolor=PRIMARY, border_radius=5)
        text_w = ft.Text(f"${saved:,.0f} / ${price:,.0f}", size=12, color=TEXT_GREY)
        pct_text = ft.Text(f"{pct*100:.0f}%", color="#22c55e" if pct >= 1.0 else PRIMARY, size=12, weight="bold")
        field = ft.TextField(label="Add $", width=100, height=44, border_radius=10, border_color=BORDER2, color="white", text_size=12)
        btn = ft.Container(content=ft.Icon(ft.icons.ADD, color="white", size=18), bgcolor=PRIMARY, border_radius=10, width=44, height=44, alignment=ft.alignment.center, on_click=lambda e: add_money(g, field, bar, text_w, pct_text, width), ink=True)
        return ft.Container(content=ft.Column([ft.Row([ft.Text(g["goal_name"], color="white", weight="bold", size=14, expand=True), pct_text]), ft.Stack([ft.Container(width=width, height=6, bgcolor=BORDER2, border_radius=5), bar]), text_w, ft.Row([field, btn], spacing=8)], spacing=8), padding=16, bgcolor=DARK_CARD, border=ft.border.all(1, BORDER2), border_radius=14)

    def refresh_goals():
        goals_list.controls.clear()
        for g in state["goals"]:
            goals_list.controls.append(goal_card(g))
        page.update()

    def add_goal(e):
        if not name_f.value: return
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor(dictionary=True)
            cursor.execute("INSERT INTO user_goals (user_name, goal_name, goal_price, saved_amount) VALUES (%s,%s,%s,%s)", (user_name, name_f.value, float(price_f.value or 0), 0))
            db.commit()
            cursor.execute("SELECT * FROM user_goals ORDER BY id DESC LIMIT 1")
            state["goals"].append(cursor.fetchone())
            db.close()
            name_f.value, price_f.value = "", ""
            refresh_goals()
            recalc()
        except:
            pass

    name_f = ft.TextField(label="Goal Name", border_color=BORDER2, color="white", border_radius=12, height=52)
    price_f = ft.TextField(label="Target Price ($)", border_color=BORDER2, color="white", border_radius=12, height=52, keyboard_type=ft.KeyboardType.NUMBER)

    overview_tab = ft.Column([ft.Row([ft.Container(content=ft.Column([ft.Text("Total Balance", color=TEXT_GREY, size=11), txt_balance]), padding=16, bgcolor=DARK_CARD, border=ft.border.all(1, BORDER2), border_radius=14, expand=True), ft.Container(content=ft.Column([ft.Text("Free Money", color=TEXT_GREY, size=11), txt_free]), padding=16, bgcolor=DARK_CARD, border=ft.border.all(1, BORDER2), border_radius=14, expand=True), ft.Container(content=ft.Column([ft.Text("In Goals", color=TEXT_GREY, size=11), txt_goals_val]), padding=16, bgcolor=DARK_CARD, border=ft.border.all(1, BORDER2), border_radius=14, expand=True)], spacing=12), ft.Container(content=ft.Column([ft.Row([ft.Icon(ft.icons.TRENDING_UP, color=PRIMARY, size=16), ft.Text("Annual Projection", color=TEXT_GREY, size=12, weight="bold")]), txt_projection], spacing=10), padding=18, bgcolor=DARK_CARD, border=ft.border.all(1, BORDER2), border_radius=16), ft.Container(content=ft.Column([ft.Row([ft.Icon(ft.icons.TUNE, color=PRIMARY, size=16), ft.Text("Financial Details", color=TEXT_GREY, size=12, weight="bold")]), tf_total_saved, tf_salary, tf_savings, tf_percent], spacing=10), padding=18, bgcolor=DARK_CARD, border=ft.border.all(1, BORDER2), border_radius=16)], spacing=14, scroll=ft.ScrollMode.AUTO)

    goals_tab = ft.Column([ft.Container(content=ft.Column([ft.Row([ft.Icon(ft.icons.ADD_CIRCLE, color=PRIMARY, size=16), ft.Text("Add New Goal", color=TEXT_GREY, size=12, weight="bold")]), name_f, price_f, ft.Container(content=ft.Text("Add Goal", color="white", size=13, weight="bold"), alignment=ft.alignment.center, height=46, border_radius=12, bgcolor=PRIMARY, on_click=add_goal, ink=True)], spacing=10), padding=18, bgcolor=DARK_CARD, border=ft.border.all(1, BORDER2), border_radius=16), ft.Container(content=ft.Column([ft.Row([ft.Icon(ft.icons.FLAG, color=PRIMARY, size=16), ft.Text("My Goals", color=TEXT_GREY, size=12, weight="bold")]), goals_list], spacing=10), padding=18, bgcolor=DARK_CARD, border=ft.border.all(1, BORDER2), border_radius=16)], spacing=14, scroll=ft.ScrollMode.AUTO)

    content_container = ft.Container(content=overview_tab, expand=True)

    def switch_tab(idx, btns):
        tabs = [overview_tab, goals_tab, ft.Text("Guide Tab")]
        content_container.content = tabs[idx]
        for i, btn in enumerate(btns):
            btn.bgcolor = ft.colors.with_opacity(0.2, PRIMARY) if i == idx else DARK_CARD
        page.update()

    tab_labels = [("Overview", ft.icons.PERSON), ("Goals", ft.icons.FLAG), ("How to Use", ft.icons.MENU_BOOK)]
    tab_btns = []
    for idx, (label, icon) in enumerate(tab_labels):
        btn = ft.Container(content=ft.Row([ft.Icon(icon, size=15, color=PRIMARY), ft.Text(label, size=13, color="white")], spacing=8), bgcolor=ft.colors.with_opacity(0.2, PRIMARY) if idx == 0 else DARK_CARD, border=ft.border.all(1, BORDER2), padding=12, border_radius=12, on_click=lambda e, i=idx: switch_tab(i, tab_btns), expand=True)
        tab_btns.append(btn)

    refresh_goals()
    recalc()

    return ft.Container(content=ft.Column([ft.Row([ft.Container(ft.Text(user_name[0].upper(), size=22, weight="bold", color="white"), width=52, height=52, bgcolor=ft.colors.with_opacity(0.2, PRIMARY), border_radius=16, alignment=ft.alignment.center), ft.Column([ft.Text(user_name, size=20, weight="bold", color="white"), ft.Text("Personal Finance Profile", color=TEXT_GREY, size=12)], spacing=3, expand=True)], spacing=14), ft.Row(tab_btns, spacing=10), content_container], spacing=16), padding=24, bgcolor=BG_DARK, expand=True)