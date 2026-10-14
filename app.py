import os
from dotenv import load_dotenv
load_dotenv()

from dash import Dash, html, dcc, Input, Output
from sqlalchemy import create_engine, text
import pandas as pd
import plotly.express as px

# Connect to PostgreSQL
engine = create_engine(
    os.environ["DB_URL"]
)

# Get data directly from the database
query = text("""
    SELECT
        EXTRACT(MONTH FROM "Fecha") AS mes,
        FLOOR((EXTRACT(DAY FROM "Fecha") - 1) / 7) + 1 AS semana,
        "Responsable",
        SUM("Total") AS importe_total
    FROM ordenes_punto_venta
    WHERE EXTRACT(YEAR FROM "Fecha") = 2026
    GROUP BY mes, semana, "Responsable"
    ORDER BY mes, semana, "Responsable";
""")

with engine.connect() as connection:
    df = pd.read_sql(query, connection)

df["mes"] = df["mes"].astype(int)
df["semana"] = df["semana"].astype(int)

months = {
    1: "January", 2: "February", 3: "March",
    4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September",
    10: "October", 11: "November", 12: "December"
}

# Paleta coral (el CSS está en assets/kawaii.css, Dash lo carga solo)
KAWAII_COLORS = [
    "#F4776A", "#7D1E2C", "#F7A9A0", "#C2185B", "#FFB38A", "#E85D75",
    "#9C6B6B", "#F48FB1", "#D4A373", "#B5838D", "#FF8C69", "#6D2E46",
    "#FFCDB2", "#E5989B", "#A26769", "#FFB4A2", "#CB997E", "#F28482"
]

app = Dash(
    __name__,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Anton&family=Lora:wght@500;700"
        "&family=Nunito:wght@400;600;700;800&family=Pacifico&display=swap"
    ]
)

app.layout = html.Div(
    children=[
        # Portada tipo collage
        html.Div(className="banner", children=[
            html.Div(html.Span("🎀", className="big-emoji"), className="tile t-dots"),
            html.Div(html.Span("💄", className="big-emoji"), className="tile t-stripes"),
            html.Div(html.Span("¡KA-CHING!", className="burst"), className="tile t-wine"),
            html.Div(html.Div("SWEETHEART", className="news-word"), className="tile t-news"),
            html.Div(html.Span("🍓", className="big-emoji"), className="tile t-checker"),
            html.Div(html.Span("Sales ♡", className="script"), className="tile t-coral"),
        ]),

        html.Main(className="page", children=[
            html.Div("🐰", className="avatar"),
            html.H1("Sales by Month, Week and Responsible Person"),
            html.Div(
                [html.B("Point of sale · 2026"), "Weekly sales by responsible person"],
                className="title-bar"
            ),

            html.Div(className="grid2", children=[
                # Columna izquierda: frase, filtro y notas
                html.Div(className="col", children=[
                    html.Div("“Every sale counts ♡”", className="callout"),

                    html.Div(className="filter-box", children=[
                        html.Label("Select month:", htmlFor="month-dropdown"),

                        dcc.Dropdown(
                            id="month-dropdown",
                            options=[
                                {"label": months[m], "value": m}
                                for m in sorted(df["mes"].unique())
                            ],
                            value=int(df["mes"].min()) if not df.empty else None,
                            clearable=True
                        ),
                    ]),

                    html.Div(className="notes", children=[
                        html.H3("📝 Notes"),
                        html.Ul([
                            html.Li("Weeks are 7-day blocks of the month (1–5)."),
                            html.Li("Click a name in the legend to hide it."),
                            html.Li("Clear the month to see the whole year."),
                        ]),
                    ]),
                ]),

                # Columna derecha: gráfica
                html.Section(className="chart-block", children=[
                    html.H2("Sales chart", className="block-title"),
                    html.Div(dcc.Graph(id="sales-chart"), className="chart-frame"),
                ]),
            ]),

            html.Footer("PostgreSQL + Dash + Plotly · made with 💖",
                        className="footer"),
        ]),
    ]
)


@app.callback(
    Output("sales-chart", "figure"),
    Input("month-dropdown", "value")
)
def update_chart(selected_month):
    filtered_df = df.copy()

    if selected_month is not None:
        filtered_df = filtered_df[
            filtered_df["mes"] == selected_month
        ]

    if filtered_df.empty:
        empty_fig = px.bar(title="No data available for this month 🥺")
        empty_fig.update_layout(
            template="plotly_white",
            font=dict(family="Nunito, Arial, sans-serif", color="#8C6F73")
        )
        return empty_fig

    fig = px.bar(
        filtered_df,
        x="semana",
        y="importe_total",
        color="Responsable",
        barmode="group",
        title="Total Sales by Week and Responsible Person",
        labels={
            "semana": "Week of the Month",
            "importe_total": "Total Amount",
            "Responsable": "Responsible Person"
        },
        category_orders={
            "semana": [1, 2, 3, 4, 5]
        },
        color_discrete_sequence=KAWAII_COLORS
    )

    fig.update_layout(
        template="plotly_white",
        xaxis=dict(type="category", linecolor="#F3D6D9"),
        yaxis=dict(gridcolor="#F8E1E3", zerolinecolor="#F3D6D9"),
        legend_title="Responsible Person",
        barcornerradius=6,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Nunito, Arial, sans-serif", color="#8C6F73"),
        title_font=dict(size=21, color="#3D2A2E",
                        family="Lora, Georgia, serif"),
        hoverlabel=dict(
            bgcolor="#FDE7E9",
            bordercolor="#F4776A",
            font=dict(color="#3D2A2E", family="Nunito, Arial, sans-serif")
        )
    )

    return fig


if __name__ == "__main__":
    app.run(debug=True)
