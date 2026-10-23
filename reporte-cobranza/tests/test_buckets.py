from datetime import date

from src.buckets import ADEL, ANT, params_desde_config, clave_vencimiento, es_cierre, clave_periodo

CFG = {"mes_actual": "2026-10", "fecha_cierre": "2026-11-05", "anio_inicio_columnas": 2022, "periodo_anteriores": 2019}
P = params_desde_config(CFG)


def test_limites_adelanto():
    assert clave_vencimiento(date(2026, 10, 31), P) == "2026-10"
    assert clave_vencimiento(date(2026, 11, 1), P) == ADEL


def test_adelanto_cierre_es_desde_el_6():
    assert not es_cierre(date(2026, 11, 5), P)   # vence el día de cierre: Adelanto, no Cierre
    assert es_cierre(date(2026, 11, 6), P)


def test_anteriores_vencimiento():
    assert clave_vencimiento(date(2021, 12, 31), P) == ANT
    assert clave_vencimiento(date(2022, 1, 1), P) == "2022"
    assert clave_vencimiento(date(2025, 12, 31), P) == "2025"


def test_periodo_anteriores():
    assert clave_periodo(2018, P) == ANT and clave_periodo(2019, P) == ANT
    assert clave_periodo(2023, P) == 2023


def test_diciembre_pasa_a_enero():
    p = params_desde_config({**CFG, "mes_actual": "2026-12", "fecha_cierre": "05/01/2027"})
    assert p.adelanto_desde == date(2027, 1, 1) and p.cierre_desde == date(2027, 1, 6)


def test_fecha_cierre_editable_y_formatos():
    p = params_desde_config({**CFG, "fecha_cierre": "07/11/2026"})
    assert p.cierre_desde == date(2026, 11, 8)
    p2 = params_desde_config({**CFG, "mes_actual": "2026-11", "fecha_cierre": date(2026, 12, 5)})
    assert p2.adelanto_desde == date(2026, 12, 1) and p2.cierre_desde == date(2026, 12, 6)


def test_fecha_cierre_invalida():
    import pytest
    with pytest.raises(ValueError):
        params_desde_config({**CFG, "fecha_cierre": "2026-10-05"})  # no es del mes siguiente


def test_rango_tabla1():
    from src.tables import dias_tabla1
    d = dias_tabla1(P, 9)
    assert d[0].date() == date(2026, 10, 1) and d[-1].date() == date(2026, 11, 9) and len(d) == 40
    d = dias_tabla1(params_desde_config({**CFG, "mes_actual": "2026-12", "fecha_cierre": "2027-01-05"}), 9)
    assert d[0].date() == date(2026, 12, 1) and d[-1].date() == date(2027, 1, 9)
