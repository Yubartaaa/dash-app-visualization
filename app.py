import sys
from pathlib import Path
from dash import Dash, Input, Output, dcc, html
import pandas as pd
from sqlalchemy import text

# Añadir directorio notebooks al path para importar el módulo de transformación
CARPETA_RAIZ = Path(__file__).resolve().parent
sys.path.append(str(CARPETA_RAIZ / "notebooks"))

from data_transform import (
    obtener_engine,
    obtener_nombre_tabla,
    limpiar_ordenes,
    obtener_resumen_mensual_semanal,
    crear_figura_ordenes,
    MESES_ES,
)

# -------------------------------------------------------------
# 0. Conexion con base de datos y extracción
# -------------------------------------------------------------
engine = obtener_engine("postgresql+psycopg2://eli@localhost:5432/Viz2026")
tabla_ordenes = obtener_nombre_tabla(engine, keyword="pos.order", exclude="report")

# Consulta SQL definida explícitamente como query_variable
query_variable = f'SELECT * FROM "{tabla_ordenes}";'
df_raw = pd.read_sql(text(query_variable), con=engine)

# -------------------------------------------------------------
# 1. preparación inicial de datos
# -------------------------------------------------------------
df_2026 = limpiar_ordenes(df_raw, anio=2026)

# Lista única de responsables ordenada con opción de "Todos"
lista_responsables = sorted(df_2026["Responsable"].dropna().unique().tolist())
opciones_dropdown = [{"label": "Todos los Responsables", "value": "TODOS"}] + [
    {"label": r, "value": r} for r in lista_responsables
]

# -------------------------------------------------------------
# 2. Inicialización de la App Dash
# -------------------------------------------------------------
app = Dash(__name__)

app.layout = html.Div(
    style={
        "maxWidth": "1100px",
        "margin": "0 auto",
        "fontFamily": "Segoe UI, Arial, sans-serif",
        "padding": "25px",
    },
    children=[
        html.H1(
            "Dashboard de Ventas 2026",
            style={
                "textAlign": "center",
                "color": "#2c3e50",
                "marginBottom": "5px",
            },
        ),
        html.P(
            "Ventas mensuales acumuladas por semana y filtradas por responsable",
            style={
                "textAlign": "center",
                "color": "#7f8c8d",
                "marginBottom": "30px",
            },
        ),
        # Selector (Dropdown) de Responsable
        html.Div(
            style={"width": "50%", "margin": "0 auto 25px auto"},
            children=[
                html.Label(
                    "Selecciona un Responsable:",
                    style={"fontWeight": "bold", "marginBottom": "8px"},
                ),
                dcc.Dropdown(
                    id="filtro-responsable",
                    options=opciones_dropdown,
                    value="TODOS",  # Valor inicial por defecto
                    clearable=False,
                    style={"fontSize": "15px"},
                ),
            ],
        ),
        # Componente que renderiza el gráfico
        dcc.Graph(id="grafica-ventas-responsable"),
    ],
)


# -------------------------------------------------------------
# 3. Callback interactivo
# -------------------------------------------------------------
@app.callback(
    Output("grafica-ventas-responsable", "figure"),
    Input("filtro-responsable", "value"),
)
def actualizar_grafica(responsable_seleccionado):
    if responsable_seleccionado == "TODOS":
        titulo = "Ventas Mensuales (Todos los Responsables)"
    else:
        titulo = f"Ventas Mensuales - Responsable: {responsable_seleccionado}"

    # Agrupar y resumir datos consumiendo la función de notebooks/data_transform.py
    df_resumen = obtener_resumen_mensual_semanal(
        df_2026, responsable=responsable_seleccionado
    )

    # Crear figura de barras apiladas consumiendo la función centralizada
    fig = crear_figura_ordenes(df_resumen, titulo=titulo)
    return fig


# -------------------------------------------------------------
# 4. Ejecución del servidor
# -------------------------------------------------------------
if __name__ == "__main__":
  app.run(debug=True)