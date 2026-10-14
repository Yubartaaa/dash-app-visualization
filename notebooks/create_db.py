import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Conexión al servidor local usando el usuario por defecto 'postgres'
# (Coloca tu contraseña si definiste una durante la instalación, si no dejaste contraseña, déjalo vacío "")
conn = psycopg2.connect(
    dbname="postgres",
    user="eli",
    password="",
    host="localhost",
    port="5432",
)

conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

# Crear la base de datos Viz2026
cur.execute('CREATE DATABASE "Viz2026";')

cur.close()
conn.close()
print("¡Base de datos Viz2026 creada con éxito!")