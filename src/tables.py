"""Construcción de las tablas (sin formato): RES MES y tablas por asesora."""
from __future__ import annotations

import pandas as pd

from .buckets import ADEL, ANT, CIERRE, TOTAL, Columna, Params, columnas

VAL = "Real Pago Dolar"


def dias_del_rango(df: pd.DataFrame) -> pd.DatetimeIndex:
    """Todos los días entre la primera y la última Fecha Pago de la base."""
    return pd.date_range(df["Fecha Pago"].min(), df["Fecha Pago"].max(), freq="D")


def dias_tabla1(p: Params, hasta_dia: int) -> pd.DatetimeIndex:
    """Tabla 1 de cada asesora: del 01 del mes actual al día `hasta_dia` del mes siguiente.

    Ej.: mes actual 2026-10, hasta_dia 9  ->  01/10/2026 a 09/11/2026.
    (Solo por formato; las tablas 2 y 3 usan todos los pagos de la base.)
    """
    inicio = pd.Timestamp(p.anio, p.mes, 1)
    fin = pd.Timestamp(p.adelanto_desde.year, p.adelanto_desde.month, hasta_dia)
    return pd.date_range(inicio, fin, freq="D")


def orden_asesoras(df: pd.DataFrame, cfg: dict, advertencias: list[str]) -> list[dict]:
    """Asesoras en el orden de la config; las que no estén se agregan al final."""
    lista = [dict(a) for a in cfg["asesoras"]]
    conocidas = {a["nombre"] for a in lista}
    nuevas = sorted(set(df["Coordinadora Cobranza"]) - conocidas)
    for n in nuevas:
        corto = n.split(",")[-1].strip().split(" ")[0] if "," in n else n.split(" ")[0]
        advertencias.append(
            f"Coordinadora NO está en config.yaml: '{n}'. Se agregó al final (hoja '{corto}'). "
            f"Agrégala a 'asesoras' para controlar su posición."
        )
        lista.append({"nombre": n, "hoja": corto})
    return lista


def res_mes(df: pd.DataFrame, asesoras: list[dict]) -> pd.DataFrame:
    """Filas = Fecha Pago (todos los días), columnas = coordinadoras, valor = suma."""
    dias = dias_del_rango(df)
    nombres = [a["nombre"] for a in asesoras]
    t = (df.groupby(["Fecha Pago", "Coordinadora Cobranza"])[VAL].sum()
           .unstack("Coordinadora Cobranza")
           .reindex(index=dias, columns=nombres))
    t["Total general"] = t.sum(axis=1, min_count=1)
    t.loc["Total general"] = t.sum(axis=0, min_count=1)
    return t


def matriz(df: pd.DataFrame, fila_col: str, filas: list, cols: list[Columna], agg: str) -> pd.DataFrame:
    """Tabla con columnas = Columna.key (incl. CIERRE y TOTAL) y filas = `filas`.

    TOTAL = suma de columnas de vencimiento (SIN Adelanto Cierre, que es subconjunto de Adelanto).
    """
    keys = [c.key for c in cols if c.key not in (CIERRE, TOTAL)]
    desconocidas = set(df["col_venc"]) - set(keys)
    if desconocidas:
        raise ValueError(f"Fechas de vencimiento fuera de las columnas definidas: {desconocidas}")

    base = (df.groupby([fila_col, "col_venc"])[VAL].agg(agg)
              .unstack("col_venc")
              .reindex(index=filas, columns=keys)
              .fillna(0))
    cierre = (df[df["es_cierre"]].groupby(fila_col)[VAL].agg(agg)
              .reindex(filas).fillna(0))
    out = base.copy()
    out[CIERRE] = cierre
    out[TOTAL] = base.sum(axis=1)
    return out[[c.key for c in cols]]


def fila_total(m: pd.DataFrame) -> pd.Series:
    return m.sum(axis=0)


def periodos_en_base(df_global: pd.DataFrame) -> list:
    """Filas de PERIODO comunes a todas las hojas: Anteriores + cada PERIODO presente."""
    presentes = sorted(k for k in df_global["per_key"].unique() if k != ANT)
    return [ANT] + presentes
