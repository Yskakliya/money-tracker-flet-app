import flet as ft
import mysql.connector
import calendar
from datetime import datetime


def get_dashboard_view(page: ft.Page, user_name="User"):
    PRIMARY      = "#85bb65"
    PRIMARY_DIM  = "#5a8c43"
    RED          = "#ef4444"
    AMBER        = "#f59e0b"
    BLUE         = "#3b82f6"
    CARD_BG      = "#0f2d25"
    CARD_BG2     = "#132e27"
    BG_DARK      = "#091f1a"
    BORDER_COLOR = "#1e4035"
    TEXT_DIM     = "#6b9e7e"

    CAT_COLORS = {
        "Food":          "#f97316",
        "Transport":     "#3b82f6",
        "Shopping":      "#ec4899",
        "Bills":         "#ef4444",
        "Entertainment": "#a855f7",
        "Health":        "#22c55e",
        "Education":     "#06b6d4",
        "Travel":        "#84cc16",
    }

    db_config = {
        "host":     "mysql.railway.internal",
        "user":     "root",
        "password": "FVmxLAOaqcNqRodWzphRlFoRnmWrsdwq",
        "database": "railway",
        "port":     3306,
    }

    def load_db_data():
        try:
            db     = mysql.connector.connect(**db_config)
            cursor = db.cursor(dictionary=True)
            now    = datetime.now()

            cursor.execute(
                "SELECT * FROM user_budgets WHERE user_name=%s", (user_name,)
            )
            budgets = cursor.fetchall()

            cursor.execute(
                """
                SELECT DAY(date) AS day, category, SUM(amount) AS total
                FROM user_transactions
                WHERE user_name=%s AND MONTH(date)=%s AND YEAR(date)=%s
                GROUP BY day, category
                """,
                (user_name, now.month, now.year),
            )
            transactions = cursor.fetchall()

            prev_month = now.month - 1 if now.month > 1 else 12
            prev_year  = now.year     if now.month > 1 else now.year - 1
            cursor.execute(
                """
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM user_transactions
                WHERE user_name=%s AND MONTH(date)=%s AND YEAR(date)=%s
                """,
                (user_name, prev_month, prev_year),
            )
            prev_row   = cursor.fetchone()
            prev_total = float(prev_row["total"]) if prev_row else 0.0

            db.close()
            return budgets, transactions, prev_total
        except Exception as e:
            print(f"DB Error: {e}")
            return [], [], 0.0

    budgets_data, trans_data, prev_month_total = load_db_data()

    total_spent = sum(float(b["spent_amount"]) for b in budgets_data)
    total_limit = sum(float(b["limit_amount"]) for b in budgets_data)
    remaining   = total_limit - total_spent
    budget_pct  = (total_spent / total_limit * 100) if total_limit > 0 else 0

    trend_delta = total_spent - prev_month_total
    trend_sign  = "▲" if trend_delta >= 0 else "▼"
    trend_color = RED if trend_delta >= 0 else PRIMARY
    trend_label = f"{trend_sign} ${abs(trend_delta):,.0f} vs last month"

    cat_totals: dict[str, float] = {}
    for b in budgets_data:
        cat_totals[b["category_name"]] = float(b["spent_amount"])
    top_cat      = max(cat_totals, key=cat_totals.get) if cat_totals else "—"
    top_cat_amt  = cat_totals.get(top_cat, 0)
    top_cat_color = CAT_COLORS.get(top_cat, PRIMARY)

    alerts = [
        b for b in budgets_data
        if float(b["limit_amount"]) > 0
        and float(b["spent_amount"]) / float(b["limit_amount"]) >= 0.85
    ]

    now = datetime.now()

    def divider():
        return ft.Container(height=1, bgcolor=BORDER_COLOR, margin=ft.margin.symmetric(vertical=4))

    def section_title(text: str, subtitle: str = ""):
        return ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(text, size=16, weight="bold", color="white"),
                        *(
                            [ft.Text(subtitle, size=11, color=TEXT_DIM)]
                            if subtitle
                            else []
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
            ]
        )

    def stat_card(icon, label, value, sub, accent):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                ft.Icon(icon, color=accent, size=18),
                                bgcolor=ft.colors.with_opacity(0.15, accent),
                                border_radius=10,
                                padding=8,
                            ),
                        ]
                    ),
                    ft.Text(label, color=TEXT_DIM, size=12),
                    ft.Text(value, color="white", size=22, weight="bold"),
                    ft.Text(sub,   color=accent,  size=11),
                ],
                spacing=6,
            ),
            bgcolor=CARD_BG,
            border=ft.border.all(1, BORDER_COLOR),
            padding=ft.padding.all(18),
            border_radius=20,
            expand=True,
        )

    overview_row = ft.Row(
        [
            stat_card(
                ft.icons.ACCOUNT_BALANCE_WALLET_OUTLINED,
                "Total Spent",
                f"${total_spent:,.0f}",
                trend_label,
                trend_color,
            ),
            stat_card(
                ft.icons.FLAG_OUTLINED,
                "Budget Limit",
                f"${total_limit:,.0f}",
                f"{budget_pct:.0f}% used",
                AMBER if budget_pct >= 80 else PRIMARY,
            ),
            stat_card(
                ft.icons.SAVINGS_OUTLINED,
                "Remaining",
                f"${remaining:,.0f}",
                "available this month",
                PRIMARY if remaining >= 0 else RED,
            ),
        ],
        spacing=14,
    )

    top_cat_pct = (
        (top_cat_amt / total_spent * 100) if total_spent > 0 else 0
    )
    top_category_card = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    ft.Text(
                        top_cat[0] if top_cat != "—" else "?",
                        size=22, weight="bold", color="white",
                    ),
                    width=52, height=52,
                    bgcolor=ft.colors.with_opacity(0.22, top_cat_color),
                    border_radius=16,
                    alignment=ft.alignment.center,
                ),
                ft.Column(
                    [
                        ft.Text("Top Spending Category", color=TEXT_DIM, size=11),
                        ft.Row(
                            [
                                ft.Text(top_cat,     color="white",        size=16, weight="bold"),
                                ft.Text(f"${top_cat_amt:,.0f}", color=top_cat_color, size=16, weight="bold"),
                            ],
                            spacing=8,
                        ),
                        ft.ProgressBar(
                            value=top_cat_pct / 100,
                            color=top_cat_color,
                            bgcolor=BORDER_COLOR,
                            height=5,
                            border_radius=4,
                        ),
                        ft.Text(
                            f"{top_cat_pct:.0f}% of total spending",
                            color=TEXT_DIM, size=11,
                        ),
                    ],
                    spacing=4,
                    expand=True,
                ),
            ],
            spacing=16,
        ),
        bgcolor=CARD_BG,
        border=ft.border.all(1, BORDER_COLOR),
        padding=18,
        border_radius=20,
        expand=True,
    )

    def alert_chip(b):
        pct   = float(b["spent_amount"]) / float(b["limit_amount"]) * 100
        color = RED if pct >= 100 else AMBER
        label = "OVER LIMIT" if pct >= 100 else f"{pct:.0f}%"
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        ft.icons.WARNING_AMBER_ROUNDED if pct < 100 else ft.icons.ERROR_OUTLINE,
                        color=color, size=16,
                    ),
                    ft.Column(
                        [
                            ft.Text(b["category_name"], color="white", size=13, weight="bold"),
                            ft.Text(
                                f"${float(b['spent_amount']):,.0f} / ${float(b['limit_amount']):,.0f}",
                                color=TEXT_DIM, size=11,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Container(
                        ft.Text(label, color=color, size=11, weight="bold"),
                        bgcolor=ft.colors.with_opacity(0.15, color),
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        border_radius=20,
                    ),
                ],
                spacing=10,
            ),
            bgcolor=ft.colors.with_opacity(0.07, color),
            border=ft.border.all(1, ft.colors.with_opacity(0.3, color)),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            border_radius=14,
        )

    alerts_section = (
        ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                ft.Icon(ft.icons.NOTIFICATIONS_ACTIVE_OUTLINED, color=AMBER, size=16),
                                bgcolor=ft.colors.with_opacity(0.15, AMBER),
                                border_radius=8,
                                padding=6,
                            ),
                            ft.Text("Budget Alerts", size=15, weight="bold", color="white"),
                            ft.Container(
                                ft.Text(str(len(alerts)), color=AMBER, size=11, weight="bold"),
                                bgcolor=ft.colors.with_opacity(0.2, AMBER),
                                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                border_radius=20,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Column([alert_chip(b) for b in alerts], spacing=8),
                ],
                spacing=12,
            ),
            bgcolor=CARD_BG,
            border=ft.border.all(1, ft.colors.with_opacity(0.35, AMBER)),
            padding=18,
            border_radius=20,
        )
        if alerts
        else ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE, color=PRIMARY, size=18),
                    ft.Text("All budgets are on track!", color=TEXT_DIM, size=13),
                ],
                spacing=10,
            ),
            bgcolor=ft.colors.with_opacity(0.07, PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.25, PRIMARY)),
            padding=ft.padding.symmetric(horizontal=18, vertical=12),
            border_radius=14,
        )
    )

    def get_daily_chart():
        days_in_month = calendar.monthrange(now.year, now.month)[1]
        today         = now.day
        bar_groups    = []

        for day in range(1, days_in_month + 1):
            day_trans  = [t for t in trans_data if t["day"] == day]
            rods       = []
            current_y  = 0.0
            is_today   = day == today

            if day_trans:
                for item in day_trans:
                    amt       = float(item["total"])
                    cat_color = CAT_COLORS.get(item["category"], PRIMARY)
                    rods.append(
                        ft.BarChartRod(
                            from_y=current_y,
                            to_y=current_y + amt,
                            width=9,
                            color=cat_color if not is_today else ft.colors.with_opacity(1, cat_color),
                            border_radius=3,
                            tooltip=f"{item['category']}: ${amt:.0f}",
                        )
                    )
                    current_y += amt
            else:
                rods.append(
                    ft.BarChartRod(
                        from_y=0, to_y=0.5,
                        width=9,
                        color=ft.colors.with_opacity(0.12, "white"),
                        border_radius=3,
                    )
                )

            bar_groups.append(ft.BarChartGroup(x=day - 1, bar_rods=rods))

        labels = []
        for d in range(1, days_in_month + 1):
            if d == 1 or d % 5 == 0 or d == today:
                label_color = PRIMARY if d == today else "white38"
                labels.append(
                    ft.ChartAxisLabel(
                        value=d - 1,
                        label=ft.Text(str(d), size=9, color=label_color,
                                      weight="bold" if d == today else "normal"),
                    )
                )

        return ft.BarChart(
            bar_groups=bar_groups,
            border=ft.border.all(0, "transparent"),
            bottom_axis=ft.ChartAxis(labels=labels, labels_size=22),
            left_axis=ft.ChartAxis(labels_size=44, visible=True),
            horizontal_grid_lines=ft.ChartGridLines(
                color=ft.colors.with_opacity(0.06, "white"), width=1
            ),
            expand=True,
            interactive=True,
        )

    chart_section = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        section_title(
                            "Daily Spending",
                            f"{now.strftime('%B %Y')}  ·  today = day {now.day}",
                        ),
                    ]
                ),
                ft.Container(get_daily_chart(), height=240),
            ],
            spacing=14,
        ),
        bgcolor=CARD_BG,
        border=ft.border.all(1, BORDER_COLOR),
        padding=20,
        border_radius=22,
    )

    days_elapsed = now.day
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    daily_avg  = total_spent / days_elapsed if days_elapsed > 0 else 0
    projected  = daily_avg * days_in_month

    def summary_tile(label, value, color=TEXT_DIM):
        return ft.Column(
            [
                ft.Text(label, color=TEXT_DIM, size=11),
                ft.Text(value, color=color,    size=16, weight="bold"),
            ],
            spacing=3,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    monthly_summary = ft.Container(
        content=ft.Column(
            [
                section_title("Monthly Summary", f"Day {days_elapsed} of {days_in_month}"),
                ft.Row(
                    [
                        summary_tile("Spent so far",    f"${total_spent:,.0f}",    "white"),
                        ft.VerticalDivider(width=1, color=BORDER_COLOR),
                        summary_tile("Daily average",   f"${daily_avg:,.0f}",      BLUE),
                        ft.VerticalDivider(width=1, color=BORDER_COLOR),
                        summary_tile("Projected total", f"${projected:,.0f}",
                                     RED if projected > total_limit else PRIMARY),
                        ft.VerticalDivider(width=1, color=BORDER_COLOR),
                        summary_tile("Budget left",     f"${remaining:,.0f}",
                                     RED if remaining < 0 else PRIMARY),
                    ],
                    spacing=0,
                ),
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text("Month progress", color=TEXT_DIM, size=11),
                                ft.Text(
                                    f"{days_elapsed}/{days_in_month} days",
                                    color=TEXT_DIM, size=11,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.ProgressBar(
                            value=days_elapsed / days_in_month,
                            color=BLUE,
                            bgcolor=BORDER_COLOR,
                            height=5,
                            border_radius=4,
                        ),
                    ],
                    spacing=6,
                ),
            ],
            spacing=14,
        ),
        bgcolor=CARD_BG,
        border=ft.border.all(1, BORDER_COLOR),
        padding=20,
        border_radius=22,
    )

    def category_row(b):
        spent = float(b["spent_amount"])
        limit = float(b["limit_amount"])
        pct   = spent / limit if limit > 0 else 0
        over  = pct >= 1.0
        near  = pct >= 0.85
        bar_color = RED if over else (AMBER if near else PRIMARY)
        cat_color = CAT_COLORS.get(b["category_name"], PRIMARY)

        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        ft.Text(b["category_name"][0], size=13, weight="bold", color="white"),
                        width=36, height=36,
                        bgcolor=ft.colors.with_opacity(0.2, cat_color),
                        border_radius=10,
                        alignment=ft.alignment.center,
                    ),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(b["category_name"], color="white", size=13,
                                            weight="bold", expand=True),
                                    ft.Text(
                                        f"${spent:,.0f} / ${limit:,.0f}",
                                        color=TEXT_DIM, size=11,
                                    ),
                                ]
                            ),
                            ft.ProgressBar(
                                value=min(pct, 1.0),
                                color=bar_color,
                                bgcolor=BORDER_COLOR,
                                height=5,
                                border_radius=4,
                            ),
                        ],
                        spacing=6,
                        expand=True,
                    ),
                    ft.Container(
                        ft.Text(f"{pct*100:.0f}%", color=bar_color,
                                size=12, weight="bold"),
                        width=40,
                        alignment=ft.alignment.center_right,
                    ),
                ],
                spacing=12,
            ),
            bgcolor=CARD_BG,
            border=ft.border.all(1, ft.colors.with_opacity(0.4, RED) if over else BORDER_COLOR),
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            border_radius=16,
        )

    categories_section = ft.Container(
        content=ft.Column(
            [
                section_title("Category Budgets"),
                ft.Column(
                    [category_row(b) for b in budgets_data],
                    spacing=8,
                ),
            ],
            spacing=12,
        ),
        bgcolor=CARD_BG2,
        border=ft.border.all(1, BORDER_COLOR),
        padding=20,
        border_radius=22,
    )

    header = ft.Row(
        [
            ft.Column(
                [
                    ft.Text(f"Welcome back, {user_name}", color=TEXT_DIM, size=12),
                    ft.Text("Dashboard", size=26, weight="bold", color="white"),
                ],
                spacing=2,
            ),
            ft.Row(
                [
                    ft.Text(now.strftime("%b %Y"), color=TEXT_DIM, size=13),
                    ft.Container(
                        ft.IconButton(
                            ft.icons.REFRESH_ROUNDED,
                            icon_color=PRIMARY,
                            icon_size=20,
                            on_click=lambda _: page.update(),
                            tooltip="Refresh",
                        ),
                        bgcolor=CARD_BG,
                        border_radius=12,
                        border=ft.border.all(1, BORDER_COLOR),
                    ),
                ],
                spacing=10,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    return ft.Container(
        content=ft.ListView(
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            header,
                            divider(),
                            overview_row,
                            ft.Row([top_category_card], spacing=14),
                            alerts_section,
                            monthly_summary,
                            chart_section,
                            categories_section,
                        ],
                        spacing=16,
                    ),
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