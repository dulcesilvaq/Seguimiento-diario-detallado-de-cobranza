"""Pipeline completo: base -> Excel. Lo usan la línea de comandos (main.py) y la app (app.py)."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from openpyxl import Workbook

from . import buckets, loader, tables
from .excel_writer import escribir_hoja_asesora, escribir_res_mes


def _ciclo_sugerido(df: pd.DataFrame) -> pd.Period:
    """Mes del ciclo al que parecen pertenecer los pagos (el ciclo va de ~6 a ~5 del mes siguiente).
    Se usan los pagos con día >= 8, que pertenecen sin duda a ese mes."""
    d = df["Fecha Pago"]
    base = d[d.dt.day >= 8]
    return (base if len(base) else d).dt.to_period("M").mode().iloc[0]


@dataclass
class Resultado:
    libro: Workbook
    advertencias: list[str]
    params: buckets.Params
    res_mes: pd.DataFrame
    dias_base: pd.DatetimeIndex
    dias_tabla1: pd.DatetimeIndex
    n_filas: int
    # hoja -> {"monto": DataFrame, "cuotas": DataFrame} (tablas por PERIODO, columnas con su etiqueta)
    vistas: dict = field(default_factory=dict)


def generar(entrada, cfg: dict, solo: list[str] | None = None) -> Resultado:
    """`entrada`: ruta o archivo subido. `cfg`: dict con la misma forma que config.yaml."""
    p = buckets.params_desde_config(cfg)
    adv: list[str] = []

    df = loader.cargar_base(entrada, cfg["hojas_base"], adv)
    df = buckets.clasificar(df, p)
    asesoras = tables.orden_asesoras(df, cfg, adv)
    cols = buckets.columnas(p)
    etiquetas = {c.key: c.label for c in cols}

    dias_base = tables.dias_del_rango(df)                        # RES MES
    dias = tables.dias_tabla1(p, int(cfg["tabla1_hasta_dia"]))   # Tabla 1 de cada asesora
    fuera = df[(df["Fecha Pago"] < dias[0]) | (df["Fecha Pago"] > dias[-1])]
    sug = _ciclo_sugerido(df)
    if (sug.year, sug.month) != (p.anio, p.mes):
        sig = sug + 1
        adv.insert(0, (
            f"REVISA EL CICLO: los pagos de la base van del {df['Fecha Pago'].min():%d/%m/%Y} al "
            f"{df['Fecha Pago'].max():%d/%m/%Y} y parecen del ciclo de {sug.year}-{sug.month:02d}, pero el mes "
            f"actual está en {p.anio}-{p.mes:02d}. Pon mes actual = {sug.year}-{sug.month:02d} y la fecha de "
            f"cierre en el mes siguiente (ej. 05/{sig.month:02d}/{sig.year})."))
    elif len(fuera):
        adv.append(f"{len(fuera)} pago(s) con Fecha Pago fuera de {dias[0]:%d/%m/%Y}-{dias[-1]:%d/%m/%Y}: "
                   f"no salen en la Tabla 1 (sí en RES MES y tablas 2 y 3). Revisa el mes actual.")
    if (p.fecha_cierre.year, p.fecha_cierre.month) != (p.adelanto_desde.year, p.adelanto_desde.month):
        adv.append(f"La fecha de cierre ({p.fecha_cierre:%d/%m/%Y}) no cae en el mes siguiente al mes actual; revisa.")
    periodos = tables.periodos_en_base(df)

    wb = Workbook()
    res = tables.res_mes(df, asesoras)
    escribir_res_mes(wb, res)

    vistas = {}
    for a in asesoras:
        if solo is not None and a["hoja"] not in solo:
            continue
        d = df[df["Coordinadora Cobranza"] == a["nombre"]]
        per_m = tables.matriz(d, "per_key", periodos, cols, "sum")
        per_c = tables.matriz(d, "per_key", periodos, cols, "count")
        escribir_hoja_asesora(
            wb, a["hoja"], a["hoja"], p, cols, dias,
            tables.matriz(d, "Fecha Pago", list(dias), cols, "sum"),
            tables.matriz(d, "Fecha Pago", list(dias), cols, "count"),
            per_m, per_c, periodos, cfg["etiqueta_tabla"],
        )
        vistas[a["hoja"]] = {
            k: v.rename(columns=etiquetas).rename(index=buckets.etiqueta_periodo)
            for k, v in (("monto", per_m), ("cuotas", per_c))
        }

    return Resultado(wb, adv, p, res, dias_base, dias, len(df), vistas)
