import flet as ft
import mysql.connector

def get_dashboard_view(page: ft.Page, user_name="User"):
    DOLLAR_GREEN = "#85bb65"
    YELLOW = "#f39c12"
    RED = "#e74c3c"

    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "venera123!@ZX",
        "database": "money_tracker_v2"
    }

    def load_data():
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM user_budgets WHERE user_name=%s", (user_name,))
            rows = cursor.fetchall()
            db.close()
            return rows
        except Exception as e:
            print(f"Error: {e}")
            return []

    data = load_data()

    total_limit = sum(float(r['limit_amount']) for r in data)
    total_spent = sum(float(r['spent_amount']) for r in data)
    total_left = total_limit - total_spent
    overall_progress = min(total_spent / total_limit, 1.0) if total_limit > 0 else 0
    over_budget_count = sum(1 for r in data if float(r['spent_amount']) >= float(r['limit_amount']))

    def get_color(progress):
        if progress >= 1.0:
            return DOLLAR_GREEN
        elif progress >= 0.5:
            return YELLOW
        else:
            return RED

    def summary_ring():
        color = get_color(overall_progress)
        ring = ft.ProgressRing(
            value=overall_progress,
            color=color,
            bgcolor="#0d2620",
            width=130,
            height=130,
            stroke_width=14
        )
        return ft.Stack([
            ft.Container(content=ring, width=130, height=130),
            ft.Container(
                content=ft.Column([
                    ft.Text(f"{int(overall_progress*100)}%", size=22, weight="bold", color=color),
                    ft.Text("used", size=11, color="grey"),
                ], horizontal_alignment="center", spacing=0),
                width=130, height=130,
                alignment=ft.Alignment(0, 0)
            )
        ], width=130, height=130)

    def stat_card(title, value, subtitle, color):
        return ft.Container(
            content=ft.Column([
                ft.Text(title, color="grey", size=12),
                ft.Text(value, color=color, size=22, weight="bold"),
                ft.Text(subtitle, color="grey", size=11),
            ], spacing=4, horizontal_alignment="center"),
            bgcolor="#143d33",
            padding=20,
            border_radius=16,
            expand=True,
            alignment=ft.Alignment(0, 0),
            shadow=ft.BoxShadow(blur_radius=8, color="#00000033", offset=ft.Offset(0, 3))
        )

    def top_spender_card():
        if not data:
            return ft.Container(
                content=ft.Text("No data yet", color="grey", size=14),
                bgcolor="#143d33",
                padding=20,
                border_radius=16,
            )
        top = max(data, key=lambda r: float(r['spent_amount']))
        spent = float(top['spent_amount'])
        limit = float(top['limit_amount'])
        progress = min(spent / limit, 1.0) if limit > 0 else 0
        color = get_color(progress)

        return ft.Container(
            content=ft.Column([
                ft.Text("🏆 Top Spending Category", color="grey", size=12),
                ft.Text(top['category_name'], color="white", size=18, weight="bold"),
                ft.Text(f"${spent:.0f} spent of ${limit:.0f}", color=color, size=13),
                ft.Container(height=6),
                ft.ProgressBar(
                    value=progress,
                    color=color,
                    bgcolor="#0d2620",
                    height=8,
                    border_radius=4
                ),
            ], spacing=6),
            bgcolor="#143d33",
            padding=20,
            border_radius=16,
            shadow=ft.BoxShadow(blur_radius=8, color="#00000033", offset=ft.Offset(0, 3))
        )

    def category_bars():
        if not data:
            return [ft.Text("No categories yet", color="grey")]
        bars = []
        for item in sorted(data, key=lambda r: float(r['spent_amount']), reverse=True):
            limit = float(item['limit_amount'])
            spent = float(item['spent_amount'])
            progress = min(spent / limit, 1.0) if limit > 0 else 0
            color = get_color(progress)

            bars.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(item['category_name'], color="white", size=13, expand=True),
                            ft.Text(f"${spent:.0f} / ${limit:.0f}", color="grey", size=12),
                            ft.Text(f"{int(progress*100)}%", color=color, size=12, weight="bold"),
                        ]),
                        ft.ProgressBar(
                            value=progress,
                            color=color,
                            bgcolor="#0d2620",
                            height=8,
                            border_radius=4
                        ),
                    ], spacing=6),
                    bgcolor="#143d33",
                    padding=ft.Padding(16, 12, 16, 12),
                    border_radius=12,
                    shadow=ft.BoxShadow(blur_radius=6, color="#00000022", offset=ft.Offset(0, 2))
                )
            )
        return bars

    summary_section = ft.Container(
        content=ft.Row([
            ft.Column([
                summary_ring(),
                ft.Container(height=6),
                ft.Text("Overall Budget", color="grey", size=12),
            ], horizontal_alignment="center", spacing=4),
            ft.Container(width=24),
            ft.Column([
                ft.Text(f"${total_spent:.0f}", color="white", size=28, weight="bold"),
                ft.Text("Total Spent", color="grey", size=12),
                ft.Container(height=10),
                ft.Text(
                    f"${total_left:.0f}" if total_left >= 0 else f"-${abs(total_left):.0f}",
                    color=DOLLAR_GREEN if total_left >= 0 else RED,
                    size=22, weight="bold"
                ),
                ft.Text("Remaining", color="grey", size=12),
            ], spacing=2),
        ], alignment="start"),
        bgcolor="#143d33",
        padding=24,
        border_radius=20,
        shadow=ft.BoxShadow(blur_radius=10, color="#00000033", offset=ft.Offset(0, 4))
    )

    return ft.Column([
        ft.Row([
            ft.Column([
                ft.Text("Dashboard", size=32, weight="bold", color=DOLLAR_GREEN),
                ft.Text(f"User: {user_name}", color="grey", size=13),
            ], spacing=2)
        ]),
        ft.Container(height=10),
        summary_section,
        ft.Container(height=16),
        ft.Row([
            stat_card("Total Budget", f"${total_limit:.0f}", f"{len(data)} categories", "white"),
            stat_card("Total Spent", f"${total_spent:.0f}", "this period", YELLOW if overall_progress < 1 else DOLLAR_GREEN),
            stat_card("Over Budget", str(over_budget_count), "categories", RED if over_budget_count > 0 else DOLLAR_GREEN),
        ], spacing=12),
        ft.Container(height=16),
        top_spender_card(),
        ft.Container(height=16),
        ft.Text("Category Breakdown", color="white", size=16, weight="bold"),
        ft.Container(height=8),
        ft.Column(category_bars(), spacing=10),
    ], scroll="auto", expand=True)

