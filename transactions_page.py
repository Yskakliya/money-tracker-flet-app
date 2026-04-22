import flet as ft
import mysql.connector
from datetime import datetime


def get_transactions_view(page: ft.Page, user_name="User"):
    PRIMARY      = "#85bb65"
    RED          = "#ef4444"
    AMBER        = "#f59e0b"
    CARD_BG      = "#0f2d25"
    BG_DARK      = "#091f1a"
    BORDER_COLOR = "#1e4035"
    TEXT_DIM     = "#6b9e7e"

    CAT_COLORS = {
        "Food": "#f97316", "Transport": "#3b82f6", "Shopping": "#ec4899",
        "Bills": "#ef4444", "Entertainment": "#a855f7", "Health": "#22c55e",
        "Education": "#06b6d4", "Travel": "#84cc16",
    }

    db_config = {
        "host":     "mysql.railway.internal",
        "user":     "root",
        "password": "FVmxLAOaqcNqRodWzphRlFoRnmWrsdwq",
        "database": "railway",
        "port":     3306,
    }

    # State
    state = {
        "all": [],
        "filtered": [],
        "search": "",
        "category": "All",
        "sort": "newest",
    }

    list_col = ft.Column(spacing=8)
    total_text = ft.Text("", color=TEXT_DIM, size=12)
    sum_text   = ft.Text("", color="white", size=14, weight="bold")

    def load_data():
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                """SELECT id, date, amount, category, budget_id
                   FROM user_transactions
                   WHERE user_name=%s
                   ORDER BY date DESC, id DESC""",
                (user_name,),
            )
            rows = cursor.fetchall()
            db.close()
            state["all"] = rows
        except Exception as e:
            print(f"TX load error: {e}")
            state["all"] = []

    def delete_tx(tx_id, amount, budget_id):
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor()
            cursor.execute("DELETE FROM user_transactions WHERE id=%s", (tx_id,))
            if budget_id:
                cursor.execute(
                    "UPDATE user_budgets SET spent_amount = GREATEST(0, spent_amount - %s) WHERE id=%s",
                    (amount, budget_id),
                )
            db.commit()
            db.close()
            load_data()
            apply_filters()
        except Exception as e:
            print(f"Delete error: {e}")

    def apply_filters():
        rows = list(state["all"])

        q = state["search"].lower()
        if q:
            rows = [r for r in rows if q in str(r["category"]).lower()]

        if state["category"] != "All":
            rows = [r for r in rows if r["category"] == state["category"]]

        if state["sort"] == "newest":
            rows.sort(key=lambda r: (r["date"], r["id"]), reverse=True)
        elif state["sort"] == "oldest":
            rows.sort(key=lambda r: (r["date"], r["id"]))
        elif state["sort"] == "highest":
            rows.sort(key=lambda r: float(r["amount"]), reverse=True)
        elif state["sort"] == "lowest":
            rows.sort(key=lambda r: float(r["amount"]))

        state["filtered"] = rows
        render_list()

    def render_list():
        list_col.controls.clear()
        rows = state["filtered"]

        total = sum(float(r["amount"]) for r in rows)
        total_text.value = f"{len(rows)} transactions"
        sum_text.value   = f"Total: ${total:,.2f}"

        if not rows:
            list_col.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.RECEIPT_LONG_OUTLINED, size=48, color=TEXT_DIM),
                        ft.Text("No transactions found", color=TEXT_DIM, size=14),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    alignment=ft.alignment.center,
                    padding=40,
                )
            )
        else:
            for r in rows:
                d = r["date"]
                if hasattr(d, "strftime"):
                    date_str = d.strftime("%d %b %Y")
                else:
                    date_str = str(d)

                amt       = float(r["amount"])
                cat       = r["category"] or "Other"
                cat_color = CAT_COLORS.get(cat, PRIMARY)
                tx_id     = r["id"]
                budget_id = r.get("budget_id")

                list_col.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                ft.Text(cat[0], size=14, weight="bold", color="white"),
                                width=38, height=38,
                                bgcolor=ft.colors.with_opacity(0.22, cat_color),
                                border_radius=12,
                                alignment=ft.alignment.center,
                            ),
                            ft.Column([
                                ft.Text(cat, color="white", size=13, weight="bold"),
                                ft.Text(date_str, color=TEXT_DIM, size=11),
                            ], spacing=3, expand=True),
                            ft.Text(f"-${amt:,.2f}", color=RED, size=14, weight="bold"),
                            ft.IconButton(
                                ft.icons.DELETE_OUTLINE,
                                icon_color=ft.colors.with_opacity(0.4, RED),
                                icon_size=18,
                                on_click=lambda e, i=tx_id, a=amt, b=budget_id: delete_tx(i, a, b),
                                tooltip="Delete",
                            ),
                        ], spacing=10),
                        bgcolor=CARD_BG,
                        border=ft.border.all(1, BORDER_COLOR),
                        padding=ft.padding.symmetric(horizontal=14, vertical=10),
                        border_radius=14,
                    )
                )

        page.update()

    search_field = ft.TextField(
        hint_text="Search by category...",
        border_color=BORDER_COLOR,
        focused_border_color=PRIMARY,
        color="white",
        hint_style=ft.TextStyle(color=TEXT_DIM),
        prefix_icon=ft.icons.SEARCH,
        height=44,
        border_radius=12,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=8),
        on_change=lambda e: state.update({"search": e.control.value}) or apply_filters(),
        expand=True,
    )

    all_cats = ["All"] + list(CAT_COLORS.keys())
    cat_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(c) for c in all_cats],
        value="All",
        border_color=BORDER_COLOR,
        focused_border_color=PRIMARY,
        color="white",
        height=44,
        width=150,
        border_radius=12,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=4),
        on_change=lambda e: state.update({"category": e.control.value}) or apply_filters(),
    )

    sort_dropdown = ft.Dropdown(
        options=[
            ft.dropdown.Option("newest", "Newest first"),
            ft.dropdown.Option("oldest", "Oldest first"),
            ft.dropdown.Option("highest", "Highest $"),
            ft.dropdown.Option("lowest",  "Lowest $"),
        ],
        value="newest",
        border_color=BORDER_COLOR,
        focused_border_color=PRIMARY,
        color="white",
        height=44,
        width=160,
        border_radius=12,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=4),
        on_change=lambda e: state.update({"sort": e.control.value}) or apply_filters(),
    )

    # Init
    load_data()
    apply_filters()

    return ft.Container(
        content=ft.ListView(
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Column([
                                ft.Text("Transaction History", size=26, weight="bold", color="white"),
                                ft.Text(f"All expenses for {user_name}", color=TEXT_DIM, size=12),
                            ], spacing=2),
                            ft.IconButton(
                                ft.icons.REFRESH_ROUNDED, icon_color=PRIMARY,
                                on_click=lambda _: (load_data(), apply_filters()),
                                tooltip="Refresh",
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                        ft.Container(height=1, bgcolor=BORDER_COLOR),

                        ft.Row([search_field, cat_dropdown, sort_dropdown], spacing=10),

                        ft.Row([total_text, ft.Container(expand=True), sum_text], spacing=8),

                        list_col,
                    ], spacing=14),
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