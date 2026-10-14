import os
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from pathlib import Path
import json
import html


# ─────────────────────────────────────
# 1. CONEXIÓN A LA BASE DE DATOS
# ─────────────────────────────────────

engine = create_engine(
    os.environ["DB_URL"]
)


# ─────────────────────────────────────
# 2. CONSULTA DE SESIONES
# ─────────────────────────────────────

query = text("""
    SELECT
        "ID de sesión" AS id_sesion,
        "Abierta por" AS usuario,
        DATE_TRUNC('week', "Fecha de apertura")::date AS semana,
        EXTRACT(
            EPOCH FROM ("Fecha de cierre" - "Fecha de apertura")
        ) / 3600.0 AS duracion_horas
    FROM sesion_punto_venta
    WHERE "Fecha de apertura" IS NOT NULL
      AND "Fecha de cierre" IS NOT NULL
      AND "Fecha de cierre" >= "Fecha de apertura"
      AND "Abierta por" IS NOT NULL
      AND TRIM("Abierta por") <> ''
    ORDER BY semana, usuario;
""")

with engine.connect() as connection:
    df = pd.read_sql(query, connection)

if df.empty:
    raise ValueError("No se encontraron sesiones cerradas válidas.")


# ─────────────────────────────────────
# 3. PREPARAR LOS DATOS
# ─────────────────────────────────────

df["semana"] = pd.to_datetime(df["semana"])

resumen = (
    df.groupby(["semana", "usuario"], as_index=False)
    .agg(duracion_promedio=("duracion_horas", "mean"))
)

resumen["semana_label"] = resumen["semana"].dt.strftime("%d/%m/%Y")

promedio_general = df["duracion_horas"].mean()
total_sesiones = len(df)
total_usuarios = df["usuario"].nunique()

horas = int(promedio_general)
minutos = round((promedio_general - horas) * 60)

if minutos == 60:
    horas += 1
    minutos = 0

promedio_texto = f"{horas} h {minutos:02d} min"

usuarios = sorted(df["usuario"].unique().tolist())

# Resumen semanal para todos los usuarios
# Paleta kawaii
KAWAII_COLORS = [
    "#F4776A", "#7D1E2C", "#F7A9A0", "#C2185B", "#FFB38A", "#E85D75",
    "#9C6B6B", "#F48FB1", "#D4A373", "#B5838D", "#FF8C69", "#6D2E46",
    "#FFCDB2", "#E5989B", "#A26769", "#FFB4A2", "#CB997E", "#F28482",
    "#84A59D", "#F5CAC3", "#B56576", "#EAAC8B", "#6B705C"
]

fig = px.line(
    resumen,
    x="semana",
    y="duracion_promedio",
    color="usuario",
    markers=True,
    custom_data=["semana_label"],
    color_discrete_sequence=KAWAII_COLORS,
    labels={
        "semana": "Semana",
        "duracion_promedio": "Duración promedio (horas)",
        "usuario": "Usuario",
    },
)

fig.update_traces(
    line=dict(width=3),
    marker=dict(size=8, line=dict(width=2, color="#FFFFFF")),
    hovertemplate=(
        "<b>%{fullData.name}</b><br>"
        "Semana del %{customdata[0]}<br>"
        "Promedio: %{y:.2f} horas"
        "<extra></extra>"
    ),
)

fig.update_layout(
    template="plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Nunito, Arial, sans-serif", color="#8C6F73", size=12),
    hoverlabel=dict(
        bgcolor="#FDE7E9",
        bordercolor="#F4776A",
        font=dict(color="#3D2A2E", family="Nunito, Arial, sans-serif"),
    ),
    hovermode="closest",
    margin=dict(l=15, r=20, t=25, b=15),
    height=430,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
        title_text="",
    ),
    xaxis=dict(
        title="Semana (inicio en lunes)",
        showgrid=False,
        tickformat="%d %b %Y",
        automargin=True,
        linecolor="#F3D6D9",
    ),
    yaxis=dict(
        title="Horas promedio",
        rangemode="tozero",
        gridcolor="#F8E1E3",
        zeroline=False,
    ),
)

chart_html = fig.to_html(
    full_html=False,
    include_plotlyjs=True,
    config={
        "responsive": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    },
)

# Escapar los nombres para usarlos de forma segura en HTML
opciones_usuarios = "".join(
    f'<option value="{html.escape(usuario, quote=True)}">'
    f'{html.escape(usuario)}</option>'
    for usuario in usuarios
)

# ─────────────────────────────────────
# 4. DISEÑO DEL DASHBOARD
# ─────────────────────────────────────

documento = f"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sesiones | Punto de venta</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Lora:wght@500;700&family=Nunito:wght@400;600;700;800&family=Pacifico&display=swap" rel="stylesheet">
<style>
:root {{
    --coral: #F4776A;
    --coral-soft: #FBC4BB;
    --blush: #FDE7E9;
    --blush-2: #FCF1F2;
    --peach: #FBD3C4;
    --wine: #7D1E2C;
    --ink: #3D2A2E;
    --muted: #8C6F73;
    --line: #F3D6D9;
}}
* {{ box-sizing: border-box; }}
body {{
    margin: 0;
    background: #FFFFFF;
    color: var(--ink);
    font-family: "Nunito", "Segoe UI", Arial, sans-serif;
}}
.serif {{ font-family: "Lora", Georgia, serif; }}

/* ---------- Portada tipo collage ---------- */
.banner {{
    display: grid;
    grid-template-columns: 1.1fr .8fr 1fr 1.2fr .8fr 1.3fr;
    height: 190px;
    overflow: hidden;
    background: #F7D9DC;
}}
.tile {{ position: relative; overflow: hidden; display: grid; place-items: center; }}
.t-dots {{ background: #F9C9CF radial-gradient(#FFFFFF 2px, transparent 2.5px) 0 0 / 16px 16px; }}
.t-stripes {{ background: repeating-linear-gradient(135deg, #2B1B1E 0 14px, #FFFFFF 14px 28px); }}
.t-wine {{ background: var(--wine); }}
.t-news {{
    background: #FFF8F3 repeating-linear-gradient(180deg, transparent 0 9px, #E9D3CE 9px 10px);
    color: #2B1B1E; font-family: "Lora", Georgia, serif; text-align: center;
}}
.t-checker {{
    background-color: #FDE7E9;
    background-image:
        linear-gradient(45deg, #F4A7A0 25%, transparent 25%, transparent 75%, #F4A7A0 75%),
        linear-gradient(45deg, #F4A7A0 25%, transparent 25%, transparent 75%, #F4A7A0 75%);
    background-size: 30px 30px; background-position: 0 0, 15px 15px;
}}
.t-coral {{ background: var(--coral); }}
.big-emoji {{ font-size: 64px; filter: drop-shadow(0 6px 0 rgba(0,0,0,.12)); transform: rotate(-8deg); }}
.burst {{
    display: grid; place-items: center; width: 150px; height: 150px;
    background: #FFE45C; color: var(--wine);
    font-family: "Anton", Impact, sans-serif; font-size: 17px; letter-spacing: 1px; text-align: center;
    clip-path: polygon(50% 0, 61% 18%, 82% 7%, 79% 30%, 100% 33%, 85% 50%, 100% 67%, 79% 70%, 82% 93%, 61% 82%, 50% 100%, 39% 82%, 18% 93%, 21% 70%, 0 67%, 15% 50%, 0 33%, 21% 30%, 18% 7%, 39% 18%);
    transform: rotate(-10deg);
}}
.news-word {{ font-size: 21px; font-weight: 700; letter-spacing: 3px; background: #FFF8F3; padding: 2px 10px; }}
.news-sub {{ font-size: 11px; letter-spacing: 2px; margin-top: 4px; }}
.script {{
    font-family: "Pacifico", cursive; color: #FFFFFF; font-size: 34px; line-height: 1;
    transform: rotate(-9deg); text-shadow: 3px 3px 0 var(--wine);
}}
.sticker {{
    position: absolute; background: #FFFFFF; color: var(--wine);
    font-weight: 800; font-size: 12px; padding: 4px 10px; border-radius: 4px;
    box-shadow: 0 3px 0 rgba(0,0,0,.12);
}}

/* ---------- Encabezado ---------- */
.page {{ max-width: 1240px; margin: 0 auto; padding: 0 28px 48px; }}
.avatar {{
    width: 104px; height: 104px; margin-top: -52px; position: relative;
    border-radius: 50%; background: var(--coral); border: 4px solid #FFFFFF;
    box-shadow: 0 4px 0 #F3B3AA; display: grid; place-items: center;
}}
.avatar svg {{ width: 76px; height: 76px; }}
.title-row {{ display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-top: 18px; }}
h1 {{ font-family: "Lora", Georgia, serif; font-weight: 700; font-size: clamp(28px, 3.4vw, 38px); margin: 0; }}
.status {{
    display: inline-flex; align-items: center; gap: 8px;
    font-size: 12px; font-weight: 800; color: var(--wine);
    background: var(--blush); border: 1px solid var(--line); border-radius: 6px; padding: 6px 12px;
}}
.status-dot {{ width: 8px; height: 8px; border-radius: 50%; background: var(--coral); }}
.title-bar {{
    margin: 14px 0 26px; padding: 10px 14px;
    background: var(--blush); border-bottom: 2px solid var(--line);
    font-size: 14px; color: var(--muted); font-weight: 600;
}}
.title-bar b {{ color: var(--wine); text-transform: uppercase; font-size: 11px; letter-spacing: 1.4px; margin-right: 8px; }}

/* ---------- Cuadrícula de 3 columnas ---------- */
.grid3 {{ display: grid; grid-template-columns: 250px minmax(0, 1fr) 250px; gap: 28px; align-items: start; }}
.col {{ display: flex; flex-direction: column; gap: 22px; min-width: 0; }}

.callout {{
    border-left: 3px solid var(--ink); background: #F6EEEF;
    padding: 12px 14px; font-family: "Lora", Georgia, serif; font-size: 14px; line-height: 1.5;
}}

.block-title {{
    font-family: "Lora", Georgia, serif; font-size: 20px; font-weight: 700;
    background: var(--blush); padding: 10px 14px; margin: 0 0 12px;
}}
.view-tabs {{
    display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
    font-size: 12px; color: var(--muted); font-weight: 700;
    border-bottom: 1px solid var(--line); padding: 0 4px 8px; margin-bottom: 10px;
}}
.view-tabs .on {{ color: var(--ink); border-bottom: 2px solid var(--ink); padding-bottom: 6px; margin-bottom: -9px; }}

/* KPI principal: tarjeta coral grande */
.kpi-hero {{
    background: var(--coral); color: #FFFFFF; text-align: center;
    border-radius: 6px; padding: 22px 16px; box-shadow: 0 6px 0 #E0594C;
}}
.kpi-hero .k-label {{ font-weight: 800; font-size: 13px; opacity: .9; }}
.kpi-hero .k-icon {{ font-size: 38px; margin: 6px 0 2px; }}
.kpi-hero .k-value {{ font-family: "Anton", Impact, sans-serif; font-size: 27px; letter-spacing: .5px; white-space: nowrap; line-height: 1.2; }}
.kpi-hero .k-note {{ font-size: 12px; font-weight: 700; opacity: .9; margin-top: 4px; }}

/* Barras de progreso */
.progress {{ display: flex; flex-direction: column; gap: 12px; }}
.prog-row {{ display: flex; align-items: center; gap: 10px; }}
.prog-track {{ flex: 1; height: 30px; border: 2px solid var(--coral); border-radius: 3px; padding: 3px; }}
.prog-fill {{ height: 100%; background: var(--coral); border-radius: 1px; width: 0; transition: width 1s ease; }}
.prog-label {{ width: 72px; font-size: 11px; color: var(--coral); font-weight: 800; }}
.mini-head {{ font-size: 11px; font-weight: 800; letter-spacing: 1.2px; text-transform: uppercase; color: var(--muted); margin-bottom: -2px; }}

/* Galería de navegación */
.gallery {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }}
.g-card {{
    display: block; text-decoration: none; color: var(--ink);
    border: 1px solid var(--line); border-radius: 4px; overflow: hidden; background: #FFFFFF;
    transition: transform .2s ease, box-shadow .2s ease;
}}
.g-card:hover {{ transform: translateY(-3px); box-shadow: 0 6px 14px rgba(125, 30, 44, .12); }}
.g-img {{ height: 132px; display: grid; place-items: center; font-size: 46px; }}
.g-img.pink {{ background: #F9C9CF; }} .g-img.peach {{ background: #FBC2A8; }} .g-img.rose {{ background: #F7B0B6; }}
.g-cap {{ display: flex; align-items: center; gap: 6px; padding: 8px 10px; font-size: 12px; font-weight: 700; }}
.g-card.active {{ outline: 2px solid var(--coral); outline-offset: -2px; }}
.g-card.active .g-cap::after {{ content: "♡ aquí"; margin-left: auto; color: var(--coral); font-size: 11px; }}

/* KPIs secundarios */
.kpi-pair {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
.kpi-card {{ border: 1px solid var(--line); border-radius: 4px; background: var(--blush-2); padding: 14px 16px; }}
.kpi-card .k-top {{ display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 800; color: var(--muted); }}
.kpi-card .k-value {{ font-family: "Lora", Georgia, serif; font-size: clamp(24px, 2.4vw, 30px); font-weight: 700; margin-top: 6px; overflow-wrap: anywhere; }}
.kpi-card .k-note {{ font-size: 12px; color: var(--muted); font-weight: 600; margin-top: 2px; }}

/* Reloj */
.clock {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }}
.flip {{
    position: relative; background: #F9B4BC; border-radius: 10px; height: 128px;
    display: grid; place-items: center; overflow: hidden;
    font-family: "Anton", Impact, sans-serif; font-size: 70px; color: var(--wine);
}}
.flip::after {{ content: ""; position: absolute; left: 0; right: 0; top: 50%; height: 2px; background: #FDE7E9; }}
.flip small {{ position: absolute; bottom: 8px; font-family: "Nunito", sans-serif; font-size: 10px; font-weight: 800; letter-spacing: .5px; }}
.flip.left small {{ left: 10px; }} .flip.right small {{ right: 10px; }}

/* Calendario */
.cal-head {{
    display: flex; justify-content: space-between; align-items: center;
    background: var(--wine); color: #FFFFFF; border-radius: 3px 3px 0 0;
    padding: 9px 12px; font-size: 12px; font-weight: 800;
}}
.cal-grid {{ display: grid; grid-template-columns: repeat(7, 1fr); text-align: center; font-size: 11px; font-weight: 700; padding-top: 8px; row-gap: 6px; }}
.cal-grid .dow {{ color: var(--ink); font-weight: 800; }}
.cal-grid span {{ padding: 4px 0; }}
.cal-grid .out {{ color: #D7C3C5; }}
.cal-grid .today {{ background: var(--wine); color: #FFFFFF; border-radius: 3px; }}

/* Notas */
.notes {{ background: var(--blush); padding: 14px 16px 16px; }}
.notes h3 {{ font-family: "Lora", Georgia, serif; margin: 0 0 8px; font-size: 19px; }}
.notes ul {{ margin: 0; padding-left: 18px; }}
.notes li {{ font-size: 13px; line-height: 1.5; padding: 7px 0; border-bottom: 1px solid #F5C9CE; }}
.notes li:last-child {{ border-bottom: none; }}

/* Sección de la gráfica */
.divider {{ border: none; border-top: 1px solid var(--line); margin: 34px 0 26px; }}
.chart-block {{ min-width: 0; }}
.chart-block .view-tabs label {{ color: var(--ink); }}
select {{
    appearance: none; -webkit-appearance: none;
    border: 1px solid var(--line); border-radius: 4px; background-color: var(--blush-2);
    padding: 6px 30px 6px 10px; color: var(--ink);
    font-family: inherit; font-size: 13px; font-weight: 700; cursor: pointer;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%237D1E2C' stroke-width='1.8' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
    background-repeat: no-repeat; background-position: right 10px center;
}}
select:focus {{ outline: 2px solid var(--coral-soft); }}
.chart-frame {{ border: 1px solid var(--line); border-radius: 4px; padding: 10px 6px 4px; }}
.footer {{ text-align: center; color: var(--muted); font-size: 12px; font-weight: 700; margin-top: 26px; }}

/* ---------- Responsivo ---------- */
@media (max-width: 1050px) {{
    .grid3 {{ grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }}
    .grid3 .col.mid {{ grid-column: 1 / -1; order: -1; }}
}}
@media (max-width: 680px) {{
    .banner {{ height: 120px; grid-template-columns: 1fr 1fr 1fr; }}
    .banner .tile:nth-child(n+4) {{ display: none; }}
    .burst {{ width: 100px; height: 100px; font-size: 12px; }}
    .big-emoji {{ font-size: 44px; }}
    .page {{ padding: 0 14px 32px; }}
    .grid3 {{ grid-template-columns: 1fr; }}
    .gallery {{ grid-template-columns: 1fr 1fr 1fr; gap: 8px; }}
    .g-img {{ height: 70px; font-size: 34px; }}
    .kpi-pair {{ grid-template-columns: 1fr; }}
}}

.chart-wrap {{ width: 100%; min-width: 0; }}
</style>
</head>
<body>
<div class="banner" aria-hidden="true">
    <div class="tile t-dots"><span class="big-emoji">🎀</span><span class="sticker" style="left:14px;bottom:14px">xoxo</span></div>
    <div class="tile t-stripes"><span class="big-emoji">💄</span></div>
    <div class="tile t-wine"><span class="burst">¡KA-CHING!</span></div>
    <div class="tile t-news"><div><div class="news-word">SWEETHEART</div><div class="news-sub">EDICIÓN · PUNTO DE VENTA</div></div></div>
    <div class="tile t-checker"><span class="big-emoji">🍓</span></div>
    <div class="tile t-coral"><span class="script">Datos<br>&amp; ventas ♡</span><span class="sticker" style="right:16px;top:14px">✦ 2026</span></div>
</div>

<main class="page">
    <div class="avatar">
            <svg viewBox="0 0 100 100" aria-hidden="true">
                <ellipse cx="37" cy="27" rx="9" ry="22" fill="#FFFFFF" transform="rotate(-12 37 27)"/>
                <ellipse cx="63" cy="27" rx="9" ry="22" fill="#FFFFFF" transform="rotate(12 63 27)"/>
                <ellipse cx="37" cy="29" rx="4" ry="14" fill="#F9B4BC" transform="rotate(-12 37 29)"/>
                <ellipse cx="63" cy="29" rx="4" ry="14" fill="#F9B4BC" transform="rotate(12 63 29)"/>
                <circle cx="50" cy="63" r="27" fill="#FFFFFF"/>
                <circle cx="40" cy="61" r="3.6" fill="#3D2A2E"/>
                <circle cx="60" cy="61" r="3.6" fill="#3D2A2E"/>
                <ellipse cx="33" cy="70" rx="5" ry="3" fill="#F9B4BC"/>
                <ellipse cx="67" cy="70" rx="5" ry="3" fill="#F9B4BC"/>
                <path d="M45 69 q5 5 10 0" stroke="#3D2A2E" stroke-width="2.2" fill="none" stroke-linecap="round"/>
            </svg>
    </div>

    <div class="title-row">
        <h1>Análisis de sesiones</h1>
        <div class="status"><span class="status-dot"></span>Datos procesados</div>
    </div>
    <div class="title-bar"><b>Punto de venta · Analítica</b>Duración promedio de las sesiones de trabajo y su evolución semanal por usuario.</div>

    <div class="grid3">
        <!-- Columna izquierda -->
        <div class="col">
            <div class="callout">“Tómate tu tiempo… pero que quede registrado.” ♡</div>

            <div class="kpi-hero">
                <div class="k-label">Duración promedio</div>
                <div class="k-icon">⏰</div>
                <div class="k-value">{promedio_texto}</div>
                <div class="k-note">Por sesión cerrada</div>
            </div>

            <div class="progress">
                <div class="mini-head">Progreso del tiempo</div>
                <div class="prog-row"><div class="prog-track"><div class="prog-fill" id="p-year"></div></div><span class="prog-label" id="pl-year">Año</span></div>
                <div class="prog-row"><div class="prog-track"><div class="prog-fill" id="p-month"></div></div><span class="prog-label" id="pl-month">Mes</span></div>
                <div class="prog-row"><div class="prog-track"><div class="prog-fill" id="p-day"></div></div><span class="prog-label" id="pl-day">Día</span></div>
            </div>
        </div>

        <!-- Columna central -->
        <div class="col mid">
            <section>
                <h2 class="block-title">Navegación</h2>
                <div class="view-tabs"><span class="on">▦ Galería</span><span>Dashboards</span></div>
                <div class="gallery">
                <a class="g-card" href="pagos.html">
                    <div class="g-img pink">💳</div>
                    <div class="g-cap">💳 Pagos</div>
                </a>
                <a class="g-card active" href="sesiones.html">
                    <div class="g-img peach">⏰</div>
                    <div class="g-cap">⏰ Sesiones</div>
                </a>
                <a class="g-card" href="ordenes.html">
                    <div class="g-img rose">🧾</div>
                    <div class="g-cap">🧾 Órdenes</div>
                </a>
                </div>
            </section>

            <section>
                <h2 class="block-title">Resumen</h2>
                <div class="kpi-pair">
                <div class="kpi-card">
                    <div class="k-top">📒 Sesiones analizadas</div>
                    <div class="k-value">{total_sesiones:,}</div>
                    <div class="k-note">Registros con duración válida</div>
                </div>
                <div class="kpi-card">
                    <div class="k-top">🧸 Usuarios registrados</div>
                    <div class="k-value">{total_usuarios:,}</div>
                    <div class="k-note">Con sesiones válidas</div>
                </div>
                </div>
            </section>
        </div>

        <!-- Columna derecha -->
        <div class="col">
            <div class="clock">
                <div class="flip left"><span id="clock-h">--</span><small id="clock-ampm"></small></div>
                <div class="flip right"><span id="clock-m">--</span><small id="clock-day"></small></div>
            </div>

            <div>
                <div class="cal-head"><span>‹</span><span id="cal-title"></span><span>›</span></div>
                <div class="cal-grid" id="cal-grid"></div>
            </div>

            <div class="notes">
                <h3>📝 Notas</h3>
                <ul>
                    <li>Cada punto es el promedio de un usuario en esa semana.</li>
                    <li>Las semanas se agrupan de lunes a domingo.</li>
                    <li>Las sesiones abiertas se excluyen del análisis.</li>
                </ul>
            </div>
        </div>
    </div>

    <hr class="divider">

    <section class="chart-block">
        <h2 class="block-title">Evolución semanal</h2>
        <div class="view-tabs"><span class="on">▤ Gráfica</span><label for="userFilter">Filtrar por usuario:</label>
            <select id="userFilter">
                <option value="__all__">Todos los usuarios</option>
                {opciones_usuarios}
            </select></div>
        <div class="chart-frame">
            <div class="chart-wrap">
                {chart_html}
            </div>
        </div>
    </section>

    <footer class="footer">Viz2026 · PostgreSQL + SQLAlchemy + Plotly · hecho con 💖</footer>
</main>

<script>
/* Reloj, calendario y barras de progreso (solo decoración, no usan los datos) */
(function () {{
    const DIAS = ["DOMINGO", "LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO"];
    const MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
                   "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];
    const pad = n => String(n).padStart(2, "0");
    const $ = id => document.getElementById(id);

    function tick() {{
        const now = new Date();
        const h = now.getHours();
        $("clock-h").textContent = pad(h % 12 || 12);
        $("clock-m").textContent = pad(now.getMinutes());
        $("clock-ampm").textContent = h >= 12 ? "PM" : "AM";
        $("clock-day").textContent = DIAS[now.getDay()];

        const y0 = new Date(now.getFullYear(), 0, 1), y1 = new Date(now.getFullYear() + 1, 0, 1);
        const m0 = new Date(now.getFullYear(), now.getMonth(), 1), m1 = new Date(now.getFullYear(), now.getMonth() + 1, 1);
        const d0 = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const pct = [
            (now - y0) / (y1 - y0),
            (now - m0) / (m1 - m0),
            (now - d0) / 86400000
        ];
        ["year", "month", "day"].forEach((k, i) => {{
            const v = Math.round(pct[i] * 100);
            $("p-" + k).style.width = v + "%";
            $("pl-" + k).textContent = ["Año", "Mes", "Día"][i] + ": " + v + "%";
        }});
    }}

    function calendar() {{
        const now = new Date();
        const y = now.getFullYear(), m = now.getMonth();
        $("cal-title").textContent = MESES[m] + " " + y;
        const first = (new Date(y, m, 1).getDay() + 6) % 7;   // lunes = 0
        const days = new Date(y, m + 1, 0).getDate();
        const prev = new Date(y, m, 0).getDate();
        let html = ["L", "M", "M", "J", "V", "S", "D"].map(d => '<span class="dow">' + d + '</span>').join("");
        for (let i = first - 1; i >= 0; i--) html += '<span class="out">' + (prev - i) + '</span>';
        for (let d = 1; d <= days; d++) html += '<span' + (d === now.getDate() ? ' class="today"' : '') + '>' + d + '</span>';
        const rest = (7 - (first + days) % 7) % 7;
        for (let d = 1; d <= rest; d++) html += '<span class="out">' + d + '</span>';
        $("cal-grid").innerHTML = html;
    }}

    tick(); calendar();
    setInterval(tick, 15000);
}})();
</script>

<script>
const userFilter = document.getElementById("userFilter");
const chart = document.querySelector(".chart-wrap .plotly-graph-div");

userFilter.addEventListener("change", function () {{
    const selected = this.value;

    if (!chart) return;

    const visibility = chart.data.map(trace => {{
        return selected === "__all__" || trace.name === selected;
    }});

    Plotly.restyle(chart, {{ visible: visibility }});
}});
</script>

</body>
</html>
"""

# ─────────────────────────────────────
# 5. GUARDAR EL HTML
# ─────────────────────────────────────

salida = Path(__file__).resolve().parent / "sesiones.html"
salida.write_text(documento, encoding="utf-8")

print(f"Dashboard generado: {salida}")
print(f"Sesiones analizadas: {total_sesiones:,}")
print(f"Usuarios: {total_usuarios:,}")
print(f"Duración promedio: {promedio_texto}")
