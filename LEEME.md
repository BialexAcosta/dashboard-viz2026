# Dashboards Viz2026 · versión kawaii 🌸

Solo cambió el **estilo** (colores, tipografía, tarjetas, gráficas).
Las consultas SQL, los cálculos y los datos son exactamente los mismos.

## Programas que necesitas

1. **Python 3.10 o más nuevo**: https://www.python.org/downloads/
   (en Windows marca la casilla "Add Python to PATH" al instalar)
2. **PostgreSQL**: https://www.postgresql.org/download/
   El instalador te pide una contraseña para el usuario `postgres`: **anótala**.
   También instala **pgAdmin** (viene incluido).
3. **Un navegador** (Chrome, Edge, Firefox).

> Solo quieres ver cómo se ve? Abre los archivos de `vista_previa/` con doble clic.

## Paso a paso (en tu computadora)

### 1. Crea la base de datos
Abre **pgAdmin** → conecta con tu contraseña → clic derecho en *Databases* →
*Create* → *Database…* → nombre: `Viz2026` → *Save*.

### 2. Instala las librerías de Python
Abre una terminal dentro de esta carpeta:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Pon tu usuario y contraseña
- En `cargar_datos.py`, cambia `USUARIO` y `CONTRASENA` (arriba del archivo).
- En `app.py`, `pagos.py`, `sesiones.py` y `ordenes.py`, cambia la línea

  `postgresql+psycopg2://karen@localhost:5432/Viz2026`

  por

  `postgresql+psycopg2://postgres:TU_CONTRASEÑA@localhost:5432/Viz2026`

### 4. Carga los Excel a tu base (solo una vez)
```bash
python cargar_datos.py
```
Debe decir: 37,973 órdenes · 45,125 pagos · 3,039 sesiones.

### 5. Genera los dashboards
```bash
python pagos.py      # crea pagos.html
python sesiones.py   # crea sesiones.html
python ordenes.py    # crea ordenes.html
```
Ábrelos con doble clic (déjalos juntos en la misma carpeta para que funcione la navegación).

### 6. App interactiva de Dash
```bash
python app.py
```
Entra a http://127.0.0.1:8050 (Ctrl + C para detenerla).

### Totales que deberías ver
- Pagos: **$5,430,792.71** · 21 métodos
- Sesiones: **3,038** sesiones · 9 h 11 min promedio
- Órdenes: **$1,673,175.00** · 6,559 órdenes · 10 responsables

## Qué cambió

- **Diseño nuevo estilo Notion / scrapbook**: portada tipo collage, avatar de conejito,
  títulos con letra serif y paleta coral, rosa y vino.
- **Organización nueva** en 3 columnas:
  - izquierda: frase, indicador principal en tarjeta coral y barras de progreso (año/mes/día);
  - centro: galería de navegación entre los 3 dashboards y resumen con los otros indicadores;
  - derecha: reloj grande, calendario y notas de cómo leer la gráfica;
  - abajo: la gráfica a todo lo ancho, con su filtro arriba como pestaña.
- Los 3 HTML se enlazan entre sí: déjalos en la misma carpeta.
- `app.py` + **nuevo** `assets/kawaii.css`: mismo estilo para la app de Dash.
- El reloj, el calendario y las barras de progreso son decoración en vivo
  (usan la hora de tu computadora, no la base de datos).
- **Nuevo** `cargar_datos.py`: sube los Excel de `data/` a tu PostgreSQL.
- `requirements.txt`: se agregaron `dash` (faltaba), `openpyxl` (para leer Excel) y `plotly>=5.19`.
- `pagos.py`: se corrigió que la gráfica desaparecía al cambiar "Agrupar por".
- Las consultas SQL y los cálculos **no cambiaron**.
