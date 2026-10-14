import os
from dotenv import load_dotenv
load_dotenv()
"""
Carga los Excel de la carpeta data/ en tu PostgreSQL.
Córrelo UNA sola vez, después de crear la base Viz2026:

    python cargar_datos.py

Crea (o reemplaza) estas tablas:
    ordenes_punto_venta, pagos_punto_venta, sesion_punto_venta
"""
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

# ── CAMBIA ESTO por tu usuario y contraseña de PostgreSQL ──
USUARIO = "postgres"
CONTRASENA = "(se toma del archivo .env)"
# ───────────────────────────────────────────────────────────

engine = create_engine(
    os.environ["DB_URL"]
)

carpeta = Path(__file__).resolve().parent / "data"


def buscar(texto):
    archivos = [f for f in carpeta.glob("*.xlsx") if texto in f.name]
    if not archivos:
        raise FileNotFoundError(f"No encontré el Excel que contiene '{texto}' en {carpeta}")
    return archivos[0]


ordenes = pd.read_excel(buscar("(pos.order)"))
ordenes.to_sql("ordenes_punto_venta", engine, if_exists="replace", index=False)

# La columna Fecha de pagos se guarda como texto (así la espera pagos.py)
pagos = pd.read_excel(buscar("(pos.payment)"), dtype={"Fecha": str})
pagos.to_sql("pagos_punto_venta", engine, if_exists="replace", index=False)

sesiones = pd.read_excel(buscar("(pos.session)"))
sesiones.to_sql("sesion_punto_venta", engine, if_exists="replace", index=False)

print("¡Listo! Tablas cargadas:")
print(f"  ordenes_punto_venta: {len(ordenes):,} filas")
print(f"  pagos_punto_venta:   {len(pagos):,} filas")
print(f"  sesion_punto_venta:  {len(sesiones):,} filas")
