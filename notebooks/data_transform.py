"""
Módulo central de transformaciones de datos, consultas a PostgreSQL
y generación de figuras interactivas para el punto de venta (Viz2026).
"""

from pathlib import Path
import unicodedata
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sqlalchemy import create_engine, inspect, text

# Mapeo de meses en español
MESES_ES = {
    1: "Ene",
    2: "Feb",
    3: "Mar",
    4: "Abr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dic",
}

DEFAULT_DB_URL = "postgresql+psycopg2://eli@localhost:5432/Viz2026"


# -----------------------------------------------------------------------------
# 1. Conexión a Base de Datos y resolución de tablas con Unicode
# -----------------------------------------------------------------------------
def obtener_engine(db_url: str = DEFAULT_DB_URL):
    """Crea y retorna una instancia del motor SQLAlchemy."""
    return create_engine(db_url)


def obtener_nombre_tabla(engine, keyword: str, exclude: str = None) -> str:
    """
    Busca el nombre exacto de la tabla en PostgreSQL resolviendo discrepancias
    de codificación Unicode (NFD vs NFC en macOS/PostgreSQL).
    """
    inspector = inspect(engine)
    tablas = inspector.get_table_names()
    keyword_norm = unicodedata.normalize("NFKD", keyword).lower()
    exclude_norm = unicodedata.normalize("NFKD", exclude).lower() if exclude else None

    for t in tablas:
        t_norm = unicodedata.normalize("NFKD", t).lower()
        if keyword_norm in t_norm:
            if exclude_norm and exclude_norm in t_norm:
                continue
            return t

    raise ValueError(f"No se encontró ninguna tabla en la BD que coincida con '{keyword}'")


# -----------------------------------------------------------------------------
# 2. Transformaciones para Órdenes de Venta
# -----------------------------------------------------------------------------
def limpiar_ordenes(df: pd.DataFrame, anio: int = 2026) -> pd.DataFrame:
    """
    Limpia el DataFrame de órdenes, parsea fechas y genera variables temporales:
    - Mes_num y Mes (nombre corto en español)
    - Semana_num y Semana (Semana 1 a 5 dentro del mes)
    Filtra los registros para el año especificado (por defecto 2026).
    """
    df_clean = df.copy()

    # Convertir a datetime y filtrar por año
    df_clean["Fecha"] = pd.to_datetime(df_clean["Fecha"], errors="coerce")
    if anio is not None:
        df_clean = df_clean[df_clean["Fecha"].dt.year == anio].copy()

    # Asegurar que el total sea numérico
    df_clean["Total"] = pd.to_numeric(df_clean["Total"], errors="coerce").fillna(0)

    # Extraer mes y mapeo a español
    df_clean["Mes_num"] = df_clean["Fecha"].dt.month
    df_clean["Mes"] = df_clean["Mes_num"].map(MESES_ES)

    # Extraer semana relativa del mes (Semana 1 a Semana 5)
    df_clean["Semana_num"] = ((df_clean["Fecha"].dt.day - 1) // 7) + 1
    df_clean["Semana"] = "Semana " + df_clean["Semana_num"].astype(str)

    # Limpiar strings de responsable
    if "Responsable" in df_clean.columns:
        df_clean["Responsable"] = df_clean["Responsable"].astype(str).str.strip()

    return df_clean


def obtener_resumen_mensual_semanal(
    df_ordenes_clean: pd.DataFrame, responsable: str = None
) -> pd.DataFrame:
    """
    Genera el resumen de ventas agrupado por mes y semana, con opción de
    filtro por responsable (o 'TODOS' para el consolidado global).
    """
    if responsable and responsable != "TODOS":
        df_filtrado = df_ordenes_clean[df_ordenes_clean["Responsable"] == responsable]
    else:
        df_filtrado = df_ordenes_clean

    resumen = (
        df_filtrado.groupby(["Mes_num", "Mes", "Semana"])["Total"]
        .sum()
        .reset_index()
    )
    return resumen.sort_values(by=["Mes_num", "Semana"])


def crear_figura_ordenes(
    df_resumen: pd.DataFrame, titulo: str = "Ventas Mensuales"
) -> go.Figure:
    """
    Crea la figura interactiva de barras apiladas por Mes y Semana para Dash app.py,
    incluyendo las etiquetas de totales acumulados por mes sobre las barras.
    """
    fig = px.bar(
        df_resumen,
        x="Mes",
        y="Total",
        color="Semana",
        barmode="stack",
        title=titulo,
        color_discrete_sequence=px.colors.sequential.Viridis,
        labels={"Total": "Importe Total ($)", "Mes": "Mes", "Semana": "Semana"},
        hover_data={"Total": ":$,.2f", "Mes_num": False},
    )

    # Etiquetas de totales por mes encima de cada barra apilada
    if not df_resumen.empty:
        totales_mes = df_resumen.groupby("Mes")["Total"].sum().to_dict()
        meses_orden = [MESES_ES[m] for m in sorted(df_resumen["Mes_num"].unique())]

        for mes in meses_orden:
            total_val = totales_mes.get(mes, 0)
            if total_val > 0:
                fig.add_annotation(
                    x=mes,
                    y=total_val,
                    text=f"${total_val:,.0f}",
                    showarrow=False,
                    yshift=10,
                    font=dict(size=11, color="#2c3e50", family="Segoe UI, Arial, sans-serif"),
                )

    fig.update_layout(
        template="plotly_white",
        title=dict(x=0.5, font=dict(size=18, color="#2c3e50")),
        xaxis=dict(title="Mes", showgrid=False),
        yaxis=dict(
            title="Ventas Totales ($)",
            tickprefix="$",
            tickformat=",.0f",
            showgrid=True,
            gridcolor="#f0f0f0",
        ),
        legend=dict(
            title=dict(text="<b>Semana</b>"),
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="center",
            x=0.5,
        ),
        margin=dict(l=60, r=40, t=70, b=90),
    )
    return fig


def crear_figura_ordenes_interactiva(df_ordenes_clean: pd.DataFrame) -> go.Figure:
    """
    Crea la visualización estática completa e interactiva con selector dropdown
    de responsables vía Plotly updatemenus para ser exportada a 'ordenes.html'.
    """
    responsables = sorted(df_ordenes_clean["Responsable"].dropna().unique().tolist())
    opciones_resp = ["TODOS"] + responsables

    # Semanas posibles y meses presentes
    semanas = sorted(df_ordenes_clean["Semana"].unique().tolist())
    meses_num = sorted(df_ordenes_clean["Mes_num"].unique().tolist())
    meses_nombres = [MESES_ES[m] for m in meses_num]

    palette = px.colors.sequential.Viridis
    color_step = (len(palette) - 1) / max(1, len(semanas) - 1)
    semana_colors = {
        sem: palette[int(i * color_step)] for i, sem in enumerate(semanas)
    }

    fig = go.Figure()

    traces_per_resp = len(semanas)
    annotations_by_resp = {}

    for r_idx, r in enumerate(opciones_resp):
        if r == "TODOS":
            df_r = df_ordenes_clean
            label_resp = "Todos los Responsables"
        else:
            df_r = df_ordenes_clean[df_ordenes_clean["Responsable"] == r]
            label_resp = r

        # Calcular totales mensuales para anotaciones
        totales_mes = df_r.groupby("Mes")["Total"].sum().to_dict()
        ann_list = []
        for m in meses_nombres:
            tot = totales_mes.get(m, 0)
            if tot > 0:
                ann_list.append(
                    dict(
                        x=m,
                        y=tot,
                        text=f"${tot:,.0f}",
                        showarrow=False,
                        yshift=10,
                        font=dict(size=11, color="#2c3e50", family="Segoe UI, Arial, sans-serif"),
                    )
                )
        annotations_by_resp[r] = ann_list

        # Agregar trazas por semana para esta opción de responsable
        is_default = (r == "TODOS")
        for s_idx, sem in enumerate(semanas):
            df_sem = df_r[df_r["Semana"] == sem]
            sem_totals = df_sem.groupby("Mes")["Total"].sum().to_dict()
            y_vals = [sem_totals.get(m, 0) for m in meses_nombres]

            fig.add_trace(
                go.Bar(
                    name=sem,
                    x=meses_nombres,
                    y=y_vals,
                    legendgroup=sem,
                    showlegend=is_default,
                    visible=is_default,
                    marker_color=semana_colors[sem],
                    hovertemplate=f"<b>Responsable:</b> {label_resp}<br><b>Mes:</b> %{{x}}<br><b>{sem}:</b> $%{{y:,.2f}}<extra></extra>",
                )
            )

    # Construir menú desplegable interactivo (updatemenus)
    total_traces = len(fig.data)
    buttons = []
    for r_idx, r in enumerate(opciones_resp):
        vis = [False] * total_traces
        showleg = [False] * total_traces
        for j in range(traces_per_resp):
            idx = r_idx * traces_per_resp + j
            vis[idx] = True
            showleg[idx] = True

        label_resp = "Todos los Responsables" if r == "TODOS" else r
        title_text = f"Ventas Mensuales 2026 ({label_resp})"

        buttons.append(
            dict(
                method="update",
                label=label_resp,
                args=[
                    {"visible": vis, "showlegend": showleg},
                    {
                        "title.text": title_text,
                        "annotations": annotations_by_resp[r],
                    },
                ],
            )
        )

    fig.update_layout(
        barmode="stack",
        template="plotly_white",
        title=dict(
            text="Ventas Mensuales 2026 (Todos los Responsables)",
            x=0.5,
            font=dict(size=18, color="#2c3e50"),
        ),
        xaxis=dict(title="Mes", showgrid=False),
        yaxis=dict(
            title="Ventas Totales ($)",
            tickprefix="$",
            tickformat=",.0f",
            showgrid=True,
            gridcolor="#f0f0f0",
        ),
        legend=dict(
            title=dict(text="<b>Semana</b>"),
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="center",
            x=0.5,
        ),
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                x=0.5,
                y=1.16,
                xanchor="center",
                yanchor="top",
                active=0,
                buttons=buttons,
                pad={"r": 10, "t": 10},
                showactive=True,
                bgcolor="#ffffff",
                bordercolor="#cbd5e1",
                font=dict(size=12, color="#1e293b"),
            )
        ],
        margin=dict(l=60, r=40, t=110, b=90),
        annotations=annotations_by_resp["TODOS"],
    )

    return fig


# -----------------------------------------------------------------------------
# 3. Transformaciones para Pagos en Punto de Venta
# -----------------------------------------------------------------------------
def limpiar_pagos(df: pd.DataFrame, anios: list = [2025, 2026]) -> pd.DataFrame:
    """
    Limpia el DataFrame de pagos eliminando subtotales/filas no transaccionales,
    parsea la columna Fecha y filtra exclusivamente para el período indicado (2025-2026).
    """
    df_clean = df.dropna(subset=["Método de pago", "Empleado"]).copy()
    df_clean["Fecha"] = pd.to_datetime(df_clean["Fecha"], errors="coerce")
    df_clean = df_clean.dropna(subset=["Fecha"]).copy()

    if anios is not None:
        df_clean = df_clean[df_clean["Fecha"].dt.year.isin(anios)].copy()

    df_clean["Importe"] = pd.to_numeric(df_clean["Importe"], errors="coerce").fillna(0)
    df_clean["Método de pago"] = df_clean["Método de pago"].astype(str).str.strip()

    # Precalcular dimensiones temporales
    df_clean["Dia"] = df_clean["Fecha"].dt.date.astype(str)
    df_clean["Semana"] = df_clean["Fecha"].dt.to_period("W").apply(
        lambda p: p.start_time.strftime("%Y-%m-%d")
    )
    df_clean["Mes"] = df_clean["Fecha"].dt.strftime("%Y-%m")
    df_clean["Trimestre"] = df_clean["Fecha"].dt.to_period("Q").apply(
        lambda q: f"{q.year}-T{q.quarter}"
    )

    return df_clean


def obtener_resumen_pagos(
    df_pagos_clean: pd.DataFrame, granularidad: str = "mes"
) -> pd.DataFrame:
    """
    Agrupa los importes de pagos por la columna temporal solicitada
    ('Dia', 'Semana', 'Mes', 'Trimestre') y por 'Método de pago'.
    """
    mapeo_cols = {
        "dia": "Dia",
        "día": "Dia",
        "semana": "Semana",
        "mes": "Mes",
        "trimestre": "Trimestre",
    }
    col_temp = mapeo_cols.get(granularidad.lower(), "Mes")

    resumen = (
        df_pagos_clean.groupby([col_temp, "Método de pago"])["Importe"]
        .sum()
        .reset_index()
    )
    return resumen.sort_values(by=[col_temp, "Importe"], ascending=[True, False])


def crear_figura_pagos_interactiva(df_pagos_clean: pd.DataFrame) -> go.Figure:
    """
    Genera la figura interactiva de pagos por Método de pago con botones de control
    (updatemenus) para alternar dinámicamente la granularidad temporal entre
    Día, Semana, Mes y Trimestre. Exportable a 'pagos.html'.
    """
    granularidades = [
        ("Mes", "Mes", "Importe Mensual por Método de Pago (2025-2026)"),
        ("Trimestre", "Trimestre", "Importe Trimestral por Método de Pago (2025-2026)"),
        ("Semana", "Semana", "Importe Semanal por Método de Pago (2025-2026)"),
        ("Dia", "Día", "Importe Diario por Método de Pago (2025-2026)"),
    ]

    # Lista única y ordenada de métodos de pago por volumen global
    totales_por_metodo = (
        df_pagos_clean.groupby("Método de pago")["Importe"].sum().sort_values(ascending=False)
    )
    metodos = totales_por_metodo.index.tolist()

    # Paleta de colores atractiva
    colores_disponibles = (
        px.colors.qualitative.Dark24
        + px.colors.qualitative.Alphabet
        + px.colors.qualitative.Plotly
    )
    color_map = {
        metodo: colores_disponibles[i % len(colores_disponibles)]
        for i, metodo in enumerate(metodos)
    }

    fig = go.Figure()
    gran_trace_indices = {}
    current_trace_idx = 0

    # Construir trazas para cada granularidad
    for col_key, etiqueta, _ in granularidades:
        periodos = sorted(df_pagos_clean[col_key].unique().tolist())
        indices_esta_gran = []

        is_default = (col_key == "Mes")

        for metodo in metodos:
            df_sub = df_pagos_clean[df_pagos_clean["Método de pago"] == metodo]
            totales = df_sub.groupby(col_key)["Importe"].sum().to_dict()
            y_vals = [totales.get(p, 0) for p in periodos]

            # Omitir traza si este método nunca tuvo pagos en este nivel
            if sum(y_vals) == 0:
                continue

            fig.add_trace(
                go.Bar(
                    name=metodo,
                    x=periodos,
                    y=y_vals,
                    legendgroup=metodo,
                    showlegend=is_default,
                    visible=is_default,
                    marker_color=color_map[metodo],
                    hovertemplate=(
                        f"<b>Método:</b> {metodo}<br>"
                        f"<b>{etiqueta}:</b> %{{x}}<br>"
                        f"<b>Importe:</b> $%{{y:,.2f}}<extra></extra>"
                    ),
                )
            )
            indices_esta_gran.append(current_trace_idx)
            current_trace_idx += 1

        gran_trace_indices[col_key] = indices_esta_gran

    total_traces = len(fig.data)

    # Construir botones updatemenus para alternar granularidades
    buttons = []
    for col_key, etiqueta, titulo in granularidades:
        vis = [False] * total_traces
        showleg = [False] * total_traces
        for idx in gran_trace_indices[col_key]:
            vis[idx] = True
            showleg[idx] = True

        buttons.append(
            dict(
                method="update",
                label=etiqueta,
                args=[
                    {"visible": vis, "showlegend": showleg},
                    {
                        "title.text": titulo,
                        "xaxis.title.text": etiqueta,
                    },
                ],
            )
        )

    fig.update_layout(
        barmode="stack",
        template="plotly_white",
        title=dict(
            text="Importe Mensual por Método de Pago (2025-2026)",
            x=0.5,
            font=dict(size=18, color="#2c3e50"),
        ),
        xaxis=dict(
            title="Mes",
            showgrid=False,
            rangeslider=dict(visible=False),
        ),
        yaxis=dict(
            title="Importe Total ($)",
            tickprefix="$",
            tickformat=",.0f",
            showgrid=True,
            gridcolor="#f0f0f0",
        ),
        legend=dict(
            title=dict(text="<b>Método de Pago</b>"),
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            font=dict(size=10),
        ),
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                x=0.0,
                y=1.14,
                xanchor="left",
                yanchor="top",
                active=0,
                buttons=buttons,
                pad={"r": 10, "t": 10},
                showactive=True,
                bgcolor="#f8fafc",
                bordercolor="#cbd5e1",
                font=dict(size=12, color="#1e293b"),
            )
        ],
        margin=dict(l=60, r=180, t=100, b=80),
    )

    return fig