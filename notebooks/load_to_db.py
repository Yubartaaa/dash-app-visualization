from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

# -----------------------------------------------------------------
# 1. Configuración de conexión con SQLAlchemy
# -----------------------------------------------------------------

DB_USER = "eli"
DB_PASS = ""
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "Viz2026"

connection_url = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
engine = create_engine(connection_url)

# -----------------------------------------------------------------
# 2. Guardar archivos xlsx en sus respectivas tablas
# -----------------------------------------------------------------
carpeta_data = Path("data")

# Buscar todos los archivos .xlsx
archivos_excel = list(carpeta_data.glob("*.xlsx"))

print(f"Se encontraron {len(archivos_excel)} archivos para cargar...")

for archivo in archivos_excel:
  nombre_tabla = (
      archivo.stem
  )  # El nombre de la tabla será igual al nombre del archivo
  print(f"\nLeyendo: {archivo.name}")

  # Leer Excel
  df = pd.read_excel(archivo)

  print(
      f"Guardando {len(df)} registros en la tabla '{nombre_tabla}' de"
      f" {DB_NAME}..."
  )
  
  df.to_sql(
      name=nombre_tabla,
      con=engine,
      if_exists="replace",
      index=False,
      chunksize=1000,  # Inserta en bloques para optimizar velocidad
  )
  print(f"✓ Tabla '{nombre_tabla}' creada y cargada exitosamente.")

print("\n¡Todos los archivos han sido cargados a la Base de Datos Viz2026!")