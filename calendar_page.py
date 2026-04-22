import flet as ft
import datetime
import calendar
import mysql.connector


def get_calendar_view(page: ft.Page, user_name="User"):
    PRIMARY      = "#85bb65"
    BG           = "#0b2e26"
    CARD         = "#143d33"
    CARD_DARK    = "#0f2d25"
    TODAY_COLOR  = "#1e5c45"
    BORDER_COLOR = "#1e4035"
    TEXT_DIM     = "#6b9e7e"
    EXPENSE      = "#ef4444"

    PALETTE = [
        "#f97316", "#3b82f6", "#ec4899", "#ef4444",
        "#a855f7", "#22c55e", "#06b6d4", "#84cc16",
        "#f59e0b", "#e11d48", "#0ea5e9", "#10b981",
    ]
    _cat_color_cache: dict[str, str] = {}

    def cat_color(name: str) -> str:
        if name not in _cat_color_cache:
            idx = len(_cat_color_cache) % len(PALETTE)
            _cat_color_cache[name] = PALETTE[idx]
        return _cat_color_cache[name]

    db_config = {
        "host":     "mysql.railway.internal",
    "user":     "root",
    "password": "FVmxLAOaqcNqRodWzphRlFoRnmWrsdwq",
    "database": "railway",
    "port":     3306,
    }

    if not hasattr(page, "current_date"):
        page.current_date = datetime.datetime.now()

    calendar_container = ft.Column(expand=True)

    def load_db_transactions(year, month):
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor(dictionary=True)
            start_date = f"{year}-{month:02d}-01"
            last_day   = calendar.monthrange(year, month)[1]
            end_date   = f"{year}-{month:02d}-{last_day}"
            cursor.execute(
                """SELECT amount, date, category
                   FROM user_transactions
                   WHERE user_name=%s AND date BETWEEN %s AND %s""",
                (user_name, start_date, end_date),
            )
            rows = cursor.fetchall()
            db.close()
            return rows
        except Exception as e:
            print(f"DB Load Error: {e}")
            return []

    def get_user_categories():
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, category_name FROM user_budgets WHERE user_name=%s",
                (user_name,),
            )
            rows = cursor.fetchall()
            db.close()
            return rows
        except:
            return []

    def build_calendar():
        calendar_container.controls.clear()

        today        = datetime.datetime.now()
        year         = page.current_date.year
        month        = page.current_date.month
        days_in_month = calendar.monthrange(year, month)[1]
        all_trans    = load_db_transactions(year, month)

        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        weekday_header = ft.Row(
            [
                ft.Container(
                    ft.Text(d, size=11, color=TEXT_DIM, text_align="center", weight="bold"),
                    expand=True,
                    alignment=ft.alignment.center,
                )
                for d in day_names
            ],
            spacing=4,
        )

        first_weekday = datetime.date(year, month, 1).weekday()

        grid = ft.GridView(
            expand=True,
            runs_count=7,
            spacing=6,
            run_spacing=6,
            child_aspect_ratio=0.85,
        )

        for _ in range(first_weekday):
            grid.controls.append(ft.Container(bgcolor="transparent"))

        for i in range(1, days_in_month + 1):
            is_today = (today.day == i and today.month == month and today.year == year)

            day_trans = []
            for t in all_trans:
                t_date = t["date"]
                if isinstance(t_date, str):
                    t_date = datetime.datetime.strptime(t_date, "%Y-%m-%d").date()
                elif hasattr(t_date, "date"):
                    t_date = t_date.date()
                if t_date.day == i:
                    day_trans.append(t)

            cell_controls = [
                ft.Text(
                    str(i),
                    size=12,
                    weight="bold",
                    color="white" if not is_today else PRIMARY,
                    text_align="center",
                )
            ]

            for t in day_trans[:2]:  
                amt  = float(t["amount"])
                cat  = t.get("category") or "?"
                color = cat_color(cat)
                cell_controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"-${amt:.0f}", color=EXPENSE, size=9, weight="bold"),
                            ft.Container(
                                ft.Text(cat, size=8, color="white", weight="bold"),
                                bgcolor=ft.colors.with_opacity(0.35, color),
                                border_radius=4,
                                padding=ft.padding.symmetric(horizontal=3, vertical=1),
                            ),
                        ], spacing=1, tight=True),
                    )
                )

            if len(day_trans) > 2:
                cell_controls.append(
                    ft.Text(f"+{len(day_trans)-2} more", color=TEXT_DIM, size=8)
                )

            cell_content = ft.Column(cell_controls, spacing=2)

            grid.controls.append(
                ft.Container(
                    content=cell_content,
                    bgcolor=TODAY_COLOR if is_today else CARD_DARK,
                    border=ft.border.all(1.5, PRIMARY) if is_today else ft.border.all(1, BORDER_COLOR),
                    border_radius=10,
                    padding=6,
                    on_click=lambda e, d=i, c=cell_content: open_dialog(e, d, c),
                    ink=True,
                )
            )

        header = ft.Row([
            ft.IconButton(ft.icons.KEYBOARD_DOUBLE_ARROW_LEFT,
                          on_click=lambda _: change_year(-1), icon_color=PRIMARY),
            ft.IconButton(ft.icons.CHEVRON_LEFT,
                          on_click=lambda _: change_month(-1), icon_color=PRIMARY),
            ft.Text(
                f"{calendar.month_name[month]} {year}",
                size=20, weight="bold", expand=True,
                text_align="center", color="white",
            ),
            ft.IconButton(ft.icons.CHEVRON_RIGHT,
                          on_click=lambda _: change_month(1), icon_color=PRIMARY),
            ft.IconButton(ft.icons.KEYBOARD_DOUBLE_ARROW_RIGHT,
                          on_click=lambda _: change_year(1), icon_color=PRIMARY),
        ])

        month_total = sum(float(t["amount"]) for t in all_trans)
        summary_row = ft.Row([
            ft.Text(f"{len(all_trans)} transactions this month",
                    color=TEXT_DIM, size=12, expand=True),
            ft.Text(f"Total: -${month_total:,.0f}",
                    color=EXPENSE, size=13, weight="bold"),
        ])

        calendar_container.controls.extend([
            ft.Row([
                ft.Text("Calendar", size=26, weight="bold", color="white"),
            ]),
            ft.Container(height=1, bgcolor=BORDER_COLOR),
            header,
            summary_row,
            weekday_header,
            ft.Container(content=grid, expand=True),
        ])

        page.update()

    def change_month(delta):
        m = page.current_date.month + delta
        y = page.current_date.year
        if m > 12: m, y = 1, y + 1
        elif m < 1: m, y = 12, y - 1
        page.current_date = datetime.datetime(y, m, 1)
        build_calendar()

    def change_year(delta):
        page.current_date = datetime.datetime(
            page.current_date.year + delta, page.current_date.month, 1
        )
        build_calendar()

    def save_transaction(e, amount_field, cat_dropdown, day_val, cell):
        if not amount_field.value or not cat_dropdown.value:
            amount_field.error_text = "Fill in all fields"
            page.update()
            return
        try:
            val       = float(amount_field.value.replace(",", "."))
            budget_id = cat_dropdown.value
            cat_name  = next(
                opt.text for opt in cat_dropdown.options if opt.key == budget_id
            )
            trans_date = datetime.date(
                page.current_date.year, page.current_date.month, day_val
            )

            db = mysql.connector.connect(**db_config)
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO user_transactions (user_name, date, amount, category, budget_id) VALUES (%s,%s,%s,%s,%s)",
                (user_name, trans_date, val, cat_name, budget_id),
            )
            cursor.execute(
                "UPDATE user_budgets SET spent_amount = spent_amount + %s WHERE id=%s",
                (val, budget_id),
            )
            db.commit()
            db.close()

            dialog.open = False

            # Update cell live
            color = cat_color(cat_name)
            cell.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"-${val:.0f}", color=EXPENSE, size=9, weight="bold"),
                        ft.Container(
                            ft.Text(cat_name, size=8, color="white", weight="bold"),
                            bgcolor=ft.colors.with_opacity(0.35, color),
                            border_radius=4,
                            padding=ft.padding.symmetric(horizontal=3, vertical=1),
                        ),
                    ], spacing=1, tight=True),
                )
            )
            cell.update()

            page.snack_bar = ft.SnackBar(
                ft.Text(f"${val:.0f} added to {cat_name}"), bgcolor=PRIMARY
            )
            page.snack_bar.open = True
            page.update()

        except Exception as ex:
            print(f"Save Error: {ex}")

    def open_dialog(e, day, cell):
        amount = ft.TextField(
            label="Amount ($)", prefix_icon=ft.icons.ATTACH_MONEY,
            border_color=PRIMARY, color="white",
            label_style=ft.TextStyle(color=TEXT_DIM),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
        )
        categories = get_user_categories()
        cat_dropdown = ft.Dropdown(
            label="Category",
            options=[
                ft.dropdown.Option(key=str(c["id"]), text=c["category_name"])
                for c in categories
            ],
            border_color=PRIMARY,
            color="white",
            label_style=ft.TextStyle(color=TEXT_DIM),
            border_radius=10,
        )

        global dialog
        dialog = ft.AlertDialog(
            title=ft.Text(
                f"Add Expense — {day} {calendar.month_name[page.current_date.month]}",
                color="white", weight="bold",
            ),
            bgcolor=CARD_DARK,
            content=ft.Column([amount, cat_dropdown], tight=True, spacing=12),
            actions=[
                ft.TextButton(
                    "Cancel",
                    style=ft.ButtonStyle(color=TEXT_DIM),
                    on_click=lambda _: setattr(dialog, "open", False) or page.update(),
                ),
                ft.Container(
                    content=ft.Text("Save", color="white", weight="bold"),
                    bgcolor=PRIMARY,
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=20, vertical=8),
                    on_click=lambda ev: save_transaction(ev, amount, cat_dropdown, day, cell),
                    ink=True,
                ),
            ],
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    build_calendar()

    return ft.Container(
        content=calendar_container,
        padding=ft.padding.symmetric(horizontal=24, vertical=20),
        bgcolor=BG,
        expand=True,
    )