import flet as ft
import mysql.connector

def get_profile_view(page: ft.Page, user_name="User"):
    PRIMARY = "#85bb65"
    BORDER = "#1e5c45"
    TEXT_GREY = "#8a8f8e"
    DARK_CARD = "#1a2e26"

    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "venera123!@ZX",
        "database": "money_tracker_v2"
    }

    state = {"goals": [], "selected_img_path": ""}

    # ---------- DB ----------
    def load_db_data():
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor(dictionary=True)

            cursor.execute("SELECT * FROM user_profile WHERE user_name=%s", (user_name,))
            profile = cursor.fetchone() or {
                "salary": 0, "savings": 0,
                "deposit_percent": 0, "total_saved": 0
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

    # ---------- INPUTS ----------
    tf_total_saved = ft.TextField(label="Total Balance", value=str(profile["total_saved"]), border_color=PRIMARY)
    tf_salary = ft.TextField(label="Salary", value=str(profile["salary"]), border_color=BORDER)
    tf_savings = ft.TextField(label="Monthly Savings", value=str(profile["savings"]), border_color=BORDER)
    tf_percent = ft.TextField(label="Bank %", value=str(profile["deposit_percent"]), border_color=BORDER)

    txt_projection = ft.Text(size=32, weight="bold", color=PRIMARY)
    txt_free = ft.Text(color="lightgreen")
    txt_goals = ft.Text(color="orange")

    # ---------- CALC ----------
    def recalc(e=None):
        try:
            total = float(tf_total_saved.value or 0)
            goals = get_goals_total()
            free = total - goals

            s = float(tf_savings.value or 0)
            p = float(tf_percent.value or 0) / 100

            projection = (free + s * 12) * (1 + p)

            txt_projection.value = f"${projection:,.0f}"
            txt_free.value = f"Free: ${free:,.0f}"
            txt_goals.value = f"In Goals: ${goals:,.0f}"

            page.update()
        except:
            pass

    tf_total_saved.on_change = recalc
    tf_savings.on_change = recalc
    tf_percent.on_change = recalc

    # ---------- SAVE ----------
    def save(field, value):
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor()
            cursor.execute(f"UPDATE user_profile SET {field}=%s WHERE user_name=%s", (value, user_name))
            db.commit()
            db.close()
        except:
            pass

    tf_total_saved.on_blur = lambda e: save("total_saved", e.control.value)
    tf_salary.on_blur = lambda e: save("salary", e.control.value)
    tf_savings.on_blur = lambda e: save("savings", e.control.value)
    tf_percent.on_blur = lambda e: save("deposit_percent", e.control.value)

    # ---------- GOALS ----------
    goals_list = ft.Column()

    def add_money(goal, field, bar, text, width):
        try:
            amount = float(field.value or 0)
            if amount <= 0:
                return

            new = float(goal["saved_amount"] or 0) + amount

            db = mysql.connector.connect(**db_config)
            cursor = db.cursor()
            cursor.execute(
                "UPDATE user_goals SET saved_amount=%s WHERE user_name=%s AND goal_name=%s",
                (new, user_name, goal["goal_name"])
            )
            db.commit()
            db.close()

            goal["saved_amount"] = new
            field.value = ""

            price = float(goal["goal_price"] or 0)
            percent = min(new / price, 1.0) if price > 0 else 0

            bar.width = int(width * percent)
            text.value = f"${new:,.0f} / ${price:,.0f}"

            recalc()
            page.update()
        except Exception as e:
            print(e)

    def goal_card(g):
        price = float(g["goal_price"] or 0)
        saved = float(g["saved_amount"] or 0)
        percent = min(saved / price, 1.0) if price > 0 else 0

        width = 260

        bar = ft.Container(width=int(width * percent), height=8, bgcolor=PRIMARY, border_radius=5)
        text = ft.Text(f"${saved:,.0f} / ${price:,.0f}", size=12, color=TEXT_GREY)

        field = ft.TextField(label="Add $", width=100)
        btn = ft.IconButton(
            icon=ft.icons.ADD,
            bgcolor=PRIMARY,
            icon_color="white",
            on_click=lambda e: add_money(g, field, bar, text, width)
        )

        return ft.Container(
            content=ft.Column([
                ft.Text(g["goal_name"], color="white"),
                ft.Stack([
                    ft.Container(width=width, height=8, bgcolor="#2c4f44"),
                    bar
                ]),
                text,
                ft.Row([field, btn])
            ]),
            padding=15,
            bgcolor=DARK_CARD,
            border_radius=12
        )

    def refresh():
        goals_list.controls.clear()
        for g in state["goals"]:
            goals_list.controls.append(goal_card(g))
        page.update()

    refresh()

    # ---------- ADD GOAL ----------
    name = ft.TextField(label="Goal Name")
    price = ft.TextField(label="Price")

    def add_goal(e):
        if not name.value:
            return
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor(dictionary=True)

            cursor.execute(
                "INSERT INTO user_goals (user_name, goal_name, goal_price, saved_amount) VALUES (%s,%s,%s,%s)",
                (user_name, name.value, float(price.value or 0), 0)
            )
            db.commit()

            cursor.execute("SELECT * FROM user_goals ORDER BY id DESC LIMIT 1")
            state["goals"].append(cursor.fetchone())

            db.close()

            name.value = ""
            price.value = ""

            refresh()
            recalc()
        except Exception as e:
            print(e)

    # ---------- UI ----------
    def card(title, content):
        return ft.Container(
            content=ft.Column([ft.Text(title, color=TEXT_GREY), content]),
            padding=20,
            bgcolor=DARK_CARD,
            border_radius=15
        )

    left = ft.Column([
        ft.Row([
            card("Balance", ft.Text(tf_total_saved.value, size=20, color="white")),
            card("Free", txt_free),
            card("Goals", txt_goals)
        ]),
        card("Projection", txt_projection),
        tf_total_saved, tf_salary, tf_savings, tf_percent
    ], expand=True)

    right = ft.Column([
        ft.Text("Add Goal", color=PRIMARY),
        name, price,
        ft.ElevatedButton("Save", on_click=add_goal),
        ft.Text("Goals", color=PRIMARY),
        goals_list
    ], expand=True, scroll="auto")

    recalc()

    return ft.Container(
        content=ft.Row([left, right]),
        padding=20
    )