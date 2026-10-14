"""
Script de exportación de visualizaciones estáticas interactivas:
- ordenes.html: Ventas 2026 agrupadas por mes y semana con selector dropdown interactivo por responsable.
- pagos.html: Pagos 2025-2026 por método de pago con control interactivo de granularidad (Día, Semana, Mes, Trimestre).
"""

import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import text

# Agregar notebooks al path para consumir data_transform.py
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / 'notebooks'))

from data_transform import (
    obtener_engine,
    obtener_nombre_tabla,
    limpiar_ordenes,
    crear_figura_ordenes_interactiva,
    limpiar_pagos,
    crear_figura_pagos_interactiva,
)


def exportar_ordenes(engine, salida_html: str = 'ordenes.html'):
    print("\n--- Exportando Visualización de Órdenes ---")
    # 1. Obtener nombre de la tabla de forma segura
    tabla_ordenes = obtener_nombre_tabla(engine, keyword='pos.order', exclude='report')
    print(f'Tabla de órdenes identificada: "{tabla_ordenes}"')

    # 2. Definición explícita de query_variable
    query_variable = f'SELECT * FROM "{tabla_ordenes}";'
    print(f'Ejecutando consulta SQL: {query_variable}')
    df_raw = pd.read_sql(text(query_variable), con=engine)

    # 3. Limpieza y filtrado para el año 2026
    df_clean = limpiar_ordenes(df_raw, anio=2026)
    print(f'Registros limpios para 2026: {len(df_clean)}')

    # 4. Generación de figura con dropdown interactivo de responsables y etiquetas numéricas
    fig = crear_figura_ordenes_interactiva(df_clean)

    # 5. Exportar a HTML estático
    fig.write_html(salida_html)
    print(f'✓ Visualización exportada exitosamente a: {salida_html}')


def exportar_pagos(engine, salida_html: str = 'pagos.html'):
    print("\n--- Exportando Visualización de Pagos ---")
    # 1. Obtener nombre de la tabla de pagos
    tabla_pagos = obtener_nombre_tabla(engine, keyword='pos.payment')
    print(f'Tabla de pagos identificada: "{tabla_pagos}"')

    # 2. Definición explícita de query_variable
    query_variable = f'SELECT * FROM "{tabla_pagos}";'
    print(f'Ejecutando consulta SQL: {query_variable}')
    df_raw = pd.read_sql(text(query_variable), con=engine)

    # 3. Limpieza y filtrado para 2025-2026
    df_clean = limpiar_pagos(df_raw, anios=[2025, 2026])
    print(f'Registros limpios para 2025-2026: {len(df_clean)}')

    # 4. Generación de figura con selector interactivo de granularidad (Día, Semana, Mes, Trimestre)
    fig = crear_figura_pagos_interactiva(df_clean)

    # 5. Exportar a HTML estático
    fig.write_html(salida_html)
    print(f'✓ Visualización exportada exitosamente a: {salida_html}')


if __name__ == '__main__':
    engine = obtener_engine('postgresql+psycopg2://eli@localhost:5432/Viz2026')
    exportar_ordenes(engine, salida_html=str(BASE_DIR / 'ordenes.html'))
    exportar_pagos(engine, salida_html=str(BASE_DIR / 'pagos.html'))
