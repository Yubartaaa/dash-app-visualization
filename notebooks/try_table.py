import pandas as pd
from sqlalchemy import create_engine, inspect, text

# crear la conexión con SQLAlchemy
connection_url = "postgresql+psycopg2://eli@localhost:5432/Viz2026"
engine = create_engine(connection_url)

inspector = inspect(engine)
tablas = inspector.get_table_names()

# Obtiene la cadena exacta con los bytes exactos guardados en PostgreSQL
tabla_ordenes = next(t for t in tablas if "pos.order" in t)

query = text(f'SELECT * FROM "{tabla_ordenes}" LIMIT 5;')
df_test = pd.read_sql(query, con=engine)
print(df_test.head())