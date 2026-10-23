import io
from datetime import date

import pandas as pd

from src.pipeline import generar

CFG = {
    "hojas_base": ["BASE FINAL", "BASE"], "mes_actual": "2026-10", "fecha_cierre": "2026-11-05",
    "tabla1_hasta_dia": 9, "anio_inicio_columnas": 2022, "periodo_anteriores": 2019,
    "etiqueta_tabla": "x", "asesoras": [{"nombre": "Ana, A", "hoja": "Ana"}, {"nombre": "Beto, B", "hoja": "Beto"}],
}


def _excel(filas):
    df = pd.DataFrame(filas, columns=["PERIODO", "Fecha Vencimiento Actual", "Fecha Pago",
                                      "Real Pago Dolar", "Coordinadora Cobranza"])
    df["DNI"] = "12345678"            # dato personal: el programa no debe cargarlo
    df["Email"] = "alguien@correo.com"
    buf = io.BytesIO()
    with pd.ExcelWriter(buf) as xw:
        df.to_excel(xw, sheet_name="BASE FINAL", index=False)
    buf.seek(0)
    return buf


def test_totales_y_adelanto_cierre():
    d = pd.Timestamp
    base = _excel([
        (2026, d("2026-10-20"), d("2026-10-06"), 100.0, "Ana, A"),   # oct-26
        (2026, d("2026-11-05"), d("2026-10-06"), 50.0, "Ana, A"),    # Adelanto (no cierre)
        (2026, d("2026-11-06"), d("2026-10-07"), 30.0, "Ana, A"),    # Adelanto + Adelanto Cierre
        (2019, d("2021-12-31"), d("2026-10-07"), 10.0, "Beto, B"),   # Anteriores
        (2026, d("2026-10-20"), d("2026-10-07"), 0.0, "Beto, B"),    # pago 0: no cuenta
    ])
    r = generar(base, CFG)
    assert r.n_filas == 4
    assert r.res_mes.loc["Total general", "Total general"] == 190.0
    m = r.vistas["Ana"]["monto"]
    assert m.loc["2026", "Adelanto"] == 80.0 and m.loc["2026", "Adelanto Cierre"] == 30.0
    assert m.loc["2026", "Total general"] == 180.0          # sin duplicar Adelanto Cierre
    assert r.vistas["Beto"]["cuotas"].loc["Anteriores", "Anteriores"] == 1


def test_coordinadora_nueva_avisa():
    d = pd.Timestamp
    r = generar(_excel([(2026, d("2026-10-20"), d("2026-10-06"), 5.0, "Perez, Nora")]), CFG)
    assert any("Perez, Nora" in a for a in r.advertencias)
    assert "Nora" in r.libro.sheetnames
