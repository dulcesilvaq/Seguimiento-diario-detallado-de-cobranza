"""Lectura y validación de la base."""
from __future__ import annotations

import pandas as pd

REQUERIDAS = [
    "PERIODO", "Fecha Vencimiento Actual", "Fecha Pago",
    "Real Pago Dolar", "Coordinadora Cobranza",
]


def cargar_base(ruta, hojas_posibles: list[str], advertencias: list[str]) -> pd.DataFrame:
    xl = pd.ExcelFile(ruta)
    hoja = next((h for h in hojas_posibles if h in xl.sheet_names), None)
    if hoja is None:
        raise ValueError(
            f"No encontré ninguna de las hojas {hojas_posibles} en el archivo. "
            f"Hojas disponibles: {xl.sheet_names}"
        )
    # Solo se leen las columnas necesarias: DNI, correos, teléfonos, etc. nunca se cargan.
    df = pd.read_excel(xl, sheet_name=hoja, usecols=lambda c: str(c).strip() in REQUERIDAS)
    df.columns = [str(c).strip() for c in df.columns]

    faltan = [c for c in REQUERIDAS if c not in df.columns]
    if faltan:
        raise ValueError(f"Faltan columnas obligatorias en la hoja '{hoja}': {faltan}")

    n0 = len(df)
    df["Real Pago Dolar"] = pd.to_numeric(df["Real Pago Dolar"], errors="coerce")
    for c in ("Fecha Pago", "Fecha Vencimiento Actual"):
        df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=True).dt.normalize()
    df["PERIODO"] = pd.to_numeric(df["PERIODO"], errors="coerce")
    df["Coordinadora Cobranza"] = df["Coordinadora Cobranza"].astype("string").str.strip()

    # Solo pagos reales (> 0)
    sin_pago = ~(df["Real Pago Dolar"] > 0)
    # Filas con datos clave vacíos (no se pueden ubicar en las tablas)
    incompletas = (~sin_pago) & (
        df[["Fecha Pago", "Fecha Vencimiento Actual", "PERIODO", "Coordinadora Cobranza"]]
        .isna().any(axis=1)
    )
    if incompletas.any():
        advertencias.append(
            f"{int(incompletas.sum())} fila(s) con pago > 0 pero sin Fecha Pago / Fecha Vencimiento / "
            f"PERIODO / Coordinadora: se excluyeron (revisa la base)."
        )
    df = df[~sin_pago & ~incompletas].copy()
    excl = n0 - len(df) - int(incompletas.sum())
    if excl:
        advertencias.append(f"{excl} fila(s) con Real Pago Dolar vacío o <= 0: no se cuentan.")

    df["PERIODO"] = df["PERIODO"].astype(int)
    df["Coordinadora Cobranza"] = df["Coordinadora Cobranza"].astype(str)
    return df.reset_index(drop=True)
