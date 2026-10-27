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
    # PERIODO: el texto "Anteriores" (como viene en algunas bases) equivale al grupo Anteriores (<= 2019)
    per_raw = df["PERIODO"].copy()
    es_ant = df["PERIODO"].astype("string").str.strip().str.lower().str.startswith("anterior", na=False)
    df["PERIODO"] = pd.to_numeric(df["PERIODO"], errors="coerce")
    df.loc[es_ant, "PERIODO"] = 0
    df["Coordinadora Cobranza"] = df["Coordinadora Cobranza"].astype("string").str.strip()

    # Solo pagos reales (> 0)
    sin_pago = ~(df["Real Pago Dolar"] > 0)
    # Filas con datos clave vacíos (no se pueden ubicar en las tablas)
    incompletas = (~sin_pago) & (
        df[["Fecha Pago", "Fecha Vencimiento Actual", "PERIODO", "Coordinadora Cobranza"]]
        .isna().any(axis=1)
    )
    if incompletas.any():
        cols = ["Fecha Pago", "Fecha Vencimiento Actual", "PERIODO", "Coordinadora Cobranza"]
        det = {c: int(df.loc[incompletas, c].isna().sum()) for c in cols if df.loc[incompletas, c].isna().any()}
        raros = per_raw[incompletas & df["PERIODO"].isna()].dropna().astype(str).unique()[:5]
        extra = f" Valores de PERIODO no reconocidos: {list(raros)}." if len(raros) else ""
        adv.append(f"{int(incompletas.sum())} fila(s) con pago > 0 pero con datos vacíos o no reconocidos "
                   f"{det}: se excluyeron (revisa la base).{extra}")
    df = df[~sin_pago & ~incompletas].copy()
    excl = n0 - len(df) - int(incompletas.sum())
    if excl:
        advertencias.append(f"{excl} fila(s) con Real Pago Dolar vacío o <= 0: no se cuentan.")

    if df.empty:
        raise ValueError("La base no tiene pagos con 'Real Pago Dolar' mayor a 0 (revisa la hoja y las columnas).")
    df["PERIODO"] = df["PERIODO"].astype(int)
    df["Coordinadora Cobranza"] = df["Coordinadora Cobranza"].astype(str)
    return df.reset_index(drop=True)
