# Visualización y Modelado de Datos de Punto de Venta (POS) - Viz2026

Proyecto de ingeniería y visualización interactiva de datos transaccionales de punto de venta (POS) implementado en **Python**, **PostgreSQL**, **SQLAlchemy**, **Plotly** y **Dash**.

---

## 📋 Características Principales

1. **Gráfica de Órdenes (`ordenes.html` y `app.py`)**:
   - Extracción directa desde PostgreSQL `Viz2026`.
   - Consulta SQL definida explícitamente como `query_variable`.
   - Filtrado exclusivo para el año **2026**.
   - Gráfica de barras apiladas de ventas acumuladas por **Mes** y **Semana** (Semana 1 a 5 dentro del mes).
   - Etiquetas numéricas con totales por mes sobre cada barra apilada.
   - Selector interactivo (*dropdown*) para filtrar por **Responsable** (incluyendo opción "Todos").
   - Exportación a archivo HTML autónomo e interactivo: `ordenes.html`.

2. **Gráfica de Pagos (`pagos.html`)**:
   - Extracción de la tabla `Pagos en Punto de venta (pos.payment)(1)`.
   - Consulta SQL definida explícitamente como `query_variable`.
   - Limpieza de subtotales/filas no transaccionales y filtrado para el período **2025-2026**.
   - Agrupación por **Método de pago**.
   - Control interactivo con botones (`updatemenus`) para alternar la granularidad temporal entre:
     - **Día**
     - **Semana**
     - **Mes**
     - **Trimestre**
   - Exportación a archivo HTML autónomo e interactivo: `pagos.html`.

3. **Dashboard Web Interactivo en Dash (`app.py`)**:
   - Servidor web reactivo con diseño responsivo.
   - Consulta dinámica mediante SQLAlchemy utilizando la variable explícita `query_variable`.
   - Consumo centralizado de funciones desde `notebooks/data_transform.py`.
   - Selector `dcc.Dropdown` interactivo por Responsable (con opción "Todos") y callback reactivo.

---

## 🗂️ Estructura del Proyecto

```text
├── app.py                      # Aplicación interactiva Dash (servidor web local)
├── generar_reportes.py         # Script para generar y exportar ordenes.html y pagos.html
├── ordenes.html                # Visualización estática interactiva de órdenes 2026
├── pagos.html                  # Visualización estática interactiva de pagos 2025-2026
├── requirements.txt            # Dependencias del proyecto
├── .gitignore                  # Configuración de exclusión para Git (Python, macOS, venv)
├── README.md                   # Documentación general y guía de uso
├── notebooks/
│   ├── data_transform.py       # Módulo central de transformación, BD y figuras Plotly
│   ├── create_db.py            # Utilidad de creación de base de datos
│   ├── load_to_db.py           # Utilidad de carga de archivos Excel a PostgreSQL
│   └── try_table.py            # Script de prueba rápida de consulta
└── data/                       # Archivos fuente (.xlsx y .csv)
```

---

## ⚙️ Requisitos Previos

- **Python**: 3.10 o superior (compatible con Python 3.14).
- **PostgreSQL**: Servidor PostgreSQL activo en `localhost:5432`.
  - Base de datos: `Viz2026`
  - Usuario: `eli` (sin contraseña o según configuración local)
  - Cadena de conexión: `postgresql+psycopg2://eli@localhost:5432/Viz2026`

---

## 🚀 Instalación y Configuración

1. **Clonar el directorio del proyecto**:
   ```bash
   git clone https://github.com/Yubartaaa/dash-app-visualization.git
   ```

2. **Crear y activar un entorno virtual**:
   ```bash
   python3 -m venv class
   source class/bin/activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Instrucciones de Uso

### 1. Generar los Reportes HTML Estáticos (`ordenes.html` y `pagos.html`)

Para extraer los datos de PostgreSQL y exportar las dos visualizaciones interactivas:

```bash
python generar_reportes.py
```

Esto generará:
- `ordenes.html`: Ábrelo en cualquier navegador web. Incluye el menú desplegable para alternar responsables y visualizar las ventas semanales y mensuales de 2026 con etiquetas de totales.
- `pagos.html`: Ábrelo en cualquier navegador web. Incluye los botones de control para alternar la visualización por **Día**, **Semana**, **Mes** y **Trimestre** con desglose por método de pago.

### 2. Ejecutar la Aplicación Web Dash (`app.py`)

Para iniciar el servidor interactivo de Dash:

```bash
python app.py
```

Una vez iniciado, abre tu navegador en:
```
http://127.0.0.1:8050/
```
Podrás interactuar en tiempo real con el selector de responsable y visualizar la gráfica reactiva de ventas 2026.

