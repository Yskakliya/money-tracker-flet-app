import flet as ft
import mysql.connector

def get_budget_view(page: ft.Page, user_name="User"):
    DOLLAR_GREEN = "#85bb65"

    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "venera123!@ZX",
        "database": "money_tracker_v2"
    }

    def load_budgets():
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM user_budgets WHERE user_name=%s", (user_name,))
            rows = cursor.fetchall()
            db.close()
            return rows
        except Exception as e:
            print(f"Error loading: {e}")
            return []

    def delete_budget(budget_id):
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor()
            cursor.execute("DELETE FROM user_budgets WHERE id=%s", (budget_id,))
            db.commit()
            db.close()
            refresh_view()
        except Exception as ex:
            print(f"Error deleting: {ex}")

    def update_spent(budget_id, new_spent):
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor()
            cursor.execute("UPDATE user_budgets SET spent_amount=%s WHERE id=%s", (new_spent, budget_id))
            db.commit()
            db.close()
            refresh_view()
        except Exception as ex:
            print(f"Error updating: {ex}")

    def make_save_handler(bid, sinput):
        def save_spent(e):
            try:
                db = mysql.connector.connect(**db_config)
                cursor = db.cursor()
                cursor.execute("SELECT spent_amount FROM user_budgets WHERE id=%s", (bid,))
                row = cursor.fetchone()
                db.close()
                old_spent = float(row[0]) if row else 0.0
                add_val = float(sinput.value.replace(",", "."))
                new_total = old_spent + add_val
                update_spent(bid, new_total)
            except Exception as ex:
                print(f"Save error: {ex}")
        return save_spent

    def add_budget(e):
        if not cat_input.value or not limit_input.value:
            return
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor()
            limit_val = float(limit_input.value.replace(",", "."))
            cursor.execute(
                "INSERT INTO user_budgets (user_name, category_name, limit_amount, spent_amount) VALUES (%s, %s, %s, %s)",
                (user_name, cat_input.value, limit_val, 0.0)
            )
            db.commit()
            db.close()
            cat_input.value = ""
            limit_input.value = ""
            refresh_view()
        except Exception as ex:
            print(f"Error saving: {ex}")

    def get_progress_color(progress):
        if progress >= 1.0:
            return DOLLAR_GREEN   # 100% green
        elif progress >= 0.5:
            return "#f39c12"      # 50-99% yellow
        else:
            return "#e74c3c"      # 0-49% red

    def make_circle_progress(spent, limit):
        progress = min(spent / limit, 1.0) if limit > 0 else 0
        color = get_progress_color(progress)

        bar = ft.ProgressRing(
            value=progress,
            color=color,
            bgcolor="#0d2620",
            width=100,
            height=100,
            stroke_width=10
        )

        percent_text = ft.Text(
            f"{int(progress * 100)}%",
            size=16,
            weight="bold",
            color=color
        )

        return ft.Stack([
            ft.Container(content=bar, width=100, height=100),
            ft.Container(
                content=percent_text,
                width=100,
                height=100,
                alignment=ft.Alignment(0, 0)
            )
        ], width=100, height=100)

    cat_input = ft.TextField(
        label="Category",
        border_color=DOLLAR_GREEN,
        color="white",
        label_style=ft.TextStyle(color="grey"),
        width=200,
        border_radius=10
    )
    limit_input = ft.TextField(
        label="Limit ($)",
        border_color=DOLLAR_GREEN,
        color="white",
        label_style=ft.TextStyle(color="grey"),
        width=150,
        border_radius=10
    )
    add_btn = ft.ElevatedButton(
        "+ Add",
        bgcolor=DOLLAR_GREEN,
        color="white",
        on_click=add_budget,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )

    budget_grid = ft.ResponsiveRow(spacing=20, run_spacing=20)

    def refresh_view():
        budget_grid.controls.clear()
        data = load_budgets()

        for item in data:
            limit = float(item['limit_amount'])
            spent = float(item['spent_amount'])
            remaining = limit - spent
            over = remaining < 0

            spent_input = ft.TextField(
                hint_text="Add amount...",
                border_color=DOLLAR_GREEN,
                color="white",
                text_align="center",
                width=100,
                height=35,
                border_radius=8,
                text_size=13,
                content_padding=ft.Padding(5, 0, 5, 0)
            )

            save_btn = ft.ElevatedButton(
                "Save",
                bgcolor=DOLLAR_GREEN,
                color="white",
                height=35,
                on_click=make_save_handler(item['id'], spent_input),
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            )

            card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(
                            item['category_name'],
                            weight="bold",
                            size=16,
                            color="white",
                            expand=True
                        ),
                        ft.TextButton(
                            "✕",
                            on_click=lambda e, bid=item['id']: delete_budget(bid),
                            style=ft.ButtonStyle(color="#e74c3c")
                        )
                    ]),
                    ft.Container(
                        content=make_circle_progress(spent, limit),
                        alignment=ft.Alignment(0, 0)
                    ),
                    ft.Container(height=4),
                    ft.Row([
                        ft.Text("+ Spent:", color="grey", size=12),
                        spent_input,
                        save_btn
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                    ft.Container(height=4),
                    ft.Row([
                        ft.Column([
                            ft.Text("Spent", color="grey", size=11),
                            ft.Text(f"${spent:.0f}", color="white", weight="bold", size=14),
                        ], horizontal_alignment="center", spacing=2),
                        ft.VerticalDivider(color="#1e5c45", width=1),
                        ft.Column([
                            ft.Text("Limit", color="grey", size=11),
                            ft.Text(f"${limit:.0f}", color="white", weight="bold", size=14),
                        ], horizontal_alignment="center", spacing=2),
                        ft.VerticalDivider(color="#1e5c45", width=1),
                        ft.Column([
                            ft.Text("Left", color="grey", size=11),
                            ft.Text(
                                f"-${abs(remaining):.0f}" if over else f"${remaining:.0f}",
                                color="#e74c3c" if over else DOLLAR_GREEN,
                                weight="bold",
                                size=14
                            ),
                        ], horizontal_alignment="center", spacing=2),
                    ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
                ], horizontal_alignment="center", spacing=10),
                bgcolor="#143d33",
                padding=20,
                border_radius=20,
                col={"sm": 12, "md": 6, "lg": 4},
                shadow=ft.BoxShadow(
                    blur_radius=10,
                    color="#00000033",
                    offset=ft.Offset(0, 4)
                )
            )
            budget_grid.controls.append(card)

        if not data:
            budget_grid.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon("account_balance_wallet_outlined", size=60, color="grey"),
                        ft.Text("No budgets yet. Add your first one!", color="grey", size=16)
                    ], horizontal_alignment="center"),
                    alignment=ft.Alignment(0, 0),
                    padding=40
                )
            )

        page.update()

    refresh_view()

    return ft.Column([
        ft.Row([
            ft.Column([
                ft.Text("Budget", size=32, weight="bold", color=DOLLAR_GREEN),
                ft.Text(f"User: {user_name}", color="grey", size=13),
            ], spacing=2, expand=True),
        ]),
        ft.Container(height=10),
        ft.Row(
            [cat_input, limit_input, add_btn],
            alignment="start",
            vertical_alignment="center",
            spacing=10
        ),
        ft.Divider(height=20, color="#1e5c45"),
        budget_grid
    ], scroll="auto", expand=True)