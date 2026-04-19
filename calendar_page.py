import flet as ft
import datetime
import calendar

def get_calendar_view(page: ft.Page, user_name="User"):
    # COLORS
    PRIMARY = "#85bb65"
    BG = "#0b2e26"
    CARD = "#143d33"
    INCOME = "#ffeb3b"
    EXPENSE = "#ff5252"

    # STATE
    if not hasattr(page, "current_date"):
        page.current_date = datetime.datetime.now()

    # ---------- MONTH SWITCH ----------
    def change_month(delta):
        month = page.current_date.month + delta
        year = page.current_date.year

        if month > 12:
            month = 1
            year += 1
        elif month < 1:
            month = 12
            year -= 1

        page.current_date = datetime.datetime(year, month, 1)

        page.controls.clear()
        page.add(get_calendar_view(page, user_name))
        page.update()

    # ---------- SAVE TRANSACTION ----------
    def save_transaction(e, amount, category, cell):
        if not amount.value:
            amount.error_text = "Enter amount"
            page.update()
            return

        is_income = "Income" in category.value
        color = INCOME if is_income else EXPENSE
        sign = "+" if is_income else "-"

        cell.controls.append(
            ft.Text(
                f"{sign}${amount.value}",
                color=color,
                size=14,
                weight="bold"
            )
        )

        dialog.open = False
        page.update()

    # ---------- OPEN DIALOG ----------
    def open_dialog(e, day, cell):
        amount = ft.TextField(label="Amount", prefix=ft.Text("$"), border_color=PRIMARY)

        category = ft.Dropdown(
            label="Category",
            options=[
                ft.dropdown.Option("Food 🍔"),
                ft.dropdown.Option("Income 💰"),
                ft.dropdown.Option("Transport 🚗"),
            ],
            value="Food 🍔"
        )

        global dialog
        dialog = ft.AlertDialog(
            title=ft.Text(f"Day {day}"),
            content=ft.Column([amount, category], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: close_dialog()),
                ft.TextButton("Save", on_click=lambda e: save_transaction(e, amount, category, cell)),
            ]
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def close_dialog():
        dialog.open = False
        page.update()

    # ---------- BUILD CALENDAR ----------
    year = page.current_date.year
    month = page.current_date.month
    month_name = calendar.month_name[month]

    days = calendar.monthrange(year, month)[1]

    grid = ft.GridView(
        expand=True,
        runs_count=7,
        spacing=10,
        child_aspect_ratio=1
    )

    for i in range(1, days + 1):
        cell = ft.Column(
            [ft.Text(str(i), size=12, weight="bold", color="white")],
            spacing=2
        )

        grid.controls.append(
            ft.Container(
                content=cell,
                bgcolor=CARD,
                border_radius=12,
                padding=8,
                alignment=ft.alignment.top_left,
                on_click=lambda e, d=i, c=cell: open_dialog(e, d, c)
            )
        )

    # ---------- HEADER ----------
    header = ft.Row([
        ft.IconButton(
            icon=ft.icons.CHEVRON_LEFT,
            on_click=lambda _: change_month(-1),
            icon_color=PRIMARY
        ),
        ft.Text(
            f"{month_name} {year}",
            size=22,
            weight="bold",
            expand=True,
            text_align="center",
            color="white"
        ),
        ft.IconButton(
            icon=ft.icons.CHEVRON_RIGHT,
            on_click=lambda _: change_month(1),
            icon_color=PRIMARY
        ),
    ])

    # ---------- FINAL UI ----------
    return ft.Container(
        content=ft.Column([
            ft.Text(f"Welcome, {user_name}", size=24, color=PRIMARY, weight="bold"),
            header,
            grid
        ], expand=True),
        padding=20,
        bgcolor=BG,
        expand=True
    )