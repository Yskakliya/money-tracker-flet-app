import flet as ft
import mysql.connector
from datetime import datetime, date


def get_add_transaction_view(page: ft.Page, user_name="User", on_saved=None):
    PRIMARY      = "#85bb65"
    RED          = "#ef4444"
    CARD_BG      = "#0f2d25"
    BG_DARK      = "#091f1a"
    BORDER_COLOR = "#1e4035"
    TEXT_DIM     = "#6b9e7e"

    db_config = {
        "host": "localhost", "user": "root",
        "password": "venera123!@ZX", "database": "money_tracker_v2",
    }

    def load_categories():
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, category_name, limit_amount, spent_amount FROM user_budgets WHERE user_name=%s",
                (user_name,),
            )
            rows = cursor.fetchall()
            db.close()
            return rows
        except Exception as e:
            print(f"Load cats error: {e}")
            return []

    categories = load_categories()

    amount_field = ft.TextField(
        label="Amount ($)",
        border_color=BORDER_COLOR,
        focused_border_color=PRIMARY,
        color="white",
        label_style=ft.TextStyle(color=TEXT_DIM),
        prefix_icon=ft.icons.ATTACH_MONEY,
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=12,
        height=56,
    )

    note_field = ft.TextField(
        label="Note (optional)",
        border_color=BORDER_COLOR,
        focused_border_color=PRIMARY,
        color="white",
        label_style=ft.TextStyle(color=TEXT_DIM),
        prefix_icon=ft.icons.NOTES,
        border_radius=12,
        height=56,
    )

    cat_dropdown = ft.Dropdown(
        label="Category",
        options=[
            ft.dropdown.Option(key=str(c["id"]), text=c["category_name"])
            for c in categories
        ],
        border_color=BORDER_COLOR,
        focused_border_color=PRIMARY,
        color="white",
        label_style=ft.TextStyle(color=TEXT_DIM),
        border_radius=12,
        height=56,
    )

    selected_date = {"value": date.today()}
    date_text = ft.Text(
        date.today().strftime("%d %B %Y"),
        color="white", size=14, weight="bold",
    )

    def on_date_picked(e):
        if e.control.value:
            selected_date["value"] = e.control.value.date() if hasattr(e.control.value, "date") else e.control.value
            date_text.value = selected_date["value"].strftime("%d %B %Y")
            page.update()

    date_picker = ft.DatePicker(
        first_date=datetime(2020, 1, 1),
        last_date=datetime(2030, 12, 31),
        on_change=on_date_picked,
    )
    page.overlay.append(date_picker)

    # Error / success text
    error_text   = ft.Text("", color=RED,     size=12, visible=False)
    success_text = ft.Text("", color=PRIMARY, size=12, visible=False)

    # Budget preview
    budget_preview = ft.Container(visible=False)

    def on_cat_change(e):
        cat_id = cat_dropdown.value
        cat = next((c for c in categories if str(c["id"]) == cat_id), None)
        if cat:
            spent = float(cat["spent_amount"])
            limit = float(cat["limit_amount"])
            pct   = spent / limit if limit > 0 else 0
            color = RED if pct >= 1.0 else ("#f59e0b" if pct >= 0.85 else PRIMARY)
            budget_preview.visible = True
            budget_preview.content = ft.Column([
                ft.Row([
                    ft.Text(f"{cat['category_name']} budget:", color=TEXT_DIM, size=12),
                    ft.Text(f"${spent:,.0f} / ${limit:,.0f}", color=color, size=12, weight="bold"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.ProgressBar(
                    value=min(pct, 1.0), color=color,
                    bgcolor=BORDER_COLOR, height=4, border_radius=4,
                ),
            ], spacing=6)
        else:
            budget_preview.visible = False
        page.update()

    cat_dropdown.on_change = on_cat_change

    def save_transaction(e):
        # Validate
        if not amount_field.value:
            error_text.value   = "Please enter an amount"
            error_text.visible = True
            page.update()
            return
        try:
            amt = float(amount_field.value.replace(",", "."))
            if amt <= 0:
                raise ValueError
        except ValueError:
            error_text.value   = "Please enter a valid positive number"
            error_text.visible = True
            page.update()
            return

        if not cat_dropdown.value:
            error_text.value   = "Please select a category"
            error_text.visible = True
            page.update()
            return

        error_text.visible = False

        try:
            cat_id   = cat_dropdown.value
            cat      = next(c for c in categories if str(c["id"]) == cat_id)
            cat_name = cat["category_name"]
            tx_date  = selected_date["value"]

            db = mysql.connector.connect(**db_config)
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO user_transactions (user_name, date, amount, category, budget_id) VALUES (%s,%s,%s,%s,%s)",
                (user_name, tx_date, amt, cat_name, cat_id),
            )
            cursor.execute(
                "UPDATE user_budgets SET spent_amount = spent_amount + %s WHERE id=%s",
                (amt, cat_id),
            )
            db.commit()
            db.close()

            # Reset form
            amount_field.value  = ""
            note_field.value    = ""
            cat_dropdown.value  = None
            budget_preview.visible = False
            selected_date["value"] = date.today()
            date_text.value = date.today().strftime("%d %B %Y")

            success_text.value   = f"${amt:,.2f} added to {cat_name}!"
            success_text.visible = True

            page.snack_bar = ft.SnackBar(
                ft.Text(f"Transaction saved: ${amt:,.2f} — {cat_name}"),
                bgcolor=PRIMARY,
            )
            page.snack_bar.open = True

            if on_saved:
                on_saved()

            page.update()

        except Exception as ex:
            print(f"Save TX error: {ex}")
            error_text.value   = "Database error, please try again"
            error_text.visible = True
            page.update()

    def reset_form(e):
        amount_field.value  = ""
        note_field.value    = ""
        cat_dropdown.value  = None
        budget_preview.visible  = False
        error_text.visible   = False
        success_text.visible = False
        selected_date["value"] = date.today()
        date_text.value = date.today().strftime("%d %B %Y")
        page.update()

    return ft.Container(
        content=ft.ListView(
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Column([
                                ft.Text("Add Transaction", size=26, weight="bold", color="white"),
                                ft.Text("Record a new expense", color=TEXT_DIM, size=12),
                            ], spacing=2),
                        ]),
                        ft.Container(height=1, bgcolor=BORDER_COLOR),

                        ft.Container(
                            content=ft.Column([
                                ft.Text("Transaction Details", color=TEXT_DIM, size=13, weight="bold"),
                                amount_field,
                                cat_dropdown,
                                budget_preview,
                                note_field,

                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(ft.icons.CALENDAR_TODAY_OUTLINED, color=TEXT_DIM, size=18),
                                        ft.Text("Date:", color=TEXT_DIM, size=13),
                                        date_text,
                                        ft.Container(expand=True),
                                        ft.TextButton(
                                            "Change",
                                            style=ft.ButtonStyle(color=PRIMARY),
                                            on_click=lambda _: setattr(date_picker, "open", True) or page.update(),
                                        ),
                                    ], spacing=10),
                                    bgcolor=ft.colors.with_opacity(0.05, "white"),
                                    border=ft.border.all(1, BORDER_COLOR),
                                    border_radius=12,
                                    padding=ft.padding.symmetric(horizontal=14, vertical=10),
                                ),

                                error_text,
                                success_text,

                                ft.Row([
                                    ft.Container(
                                        content=ft.Text("Reset", color=TEXT_DIM, size=14, weight="bold"),
                                        alignment=ft.alignment.center,
                                        expand=True,
                                        height=48,
                                        border_radius=12,
                                        border=ft.border.all(1, BORDER_COLOR),
                                        on_click=reset_form,
                                        ink=True,
                                    ),
                                    ft.Container(
                                        content=ft.Text("Save Transaction", color="white", size=14, weight="bold"),
                                        alignment=ft.alignment.center,
                                        expand=True,
                                        height=48,
                                        border_radius=12,
                                        gradient=ft.LinearGradient(["#198754", "#143d33"]),
                                        on_click=save_transaction,
                                        ink=True,
                                    ),
                                ], spacing=12),
                            ], spacing=14),
                            bgcolor=CARD_BG,
                            border=ft.border.all(1, BORDER_COLOR),
                            padding=24,
                            border_radius=22,
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