# Reporte de cobranza

Lee la hoja **BASE FINAL** de un Excel y genera un Excel con:

- **`RES MES`**: suma de *Real Pago Dolar* por *Fecha Pago* (filas) y *Coordinadora Cobranza* (columnas).
- **Una hoja por asesora** (Katherin, Yamile, ...) con tres tablas listas para copiar y pegar:
  1. **Tabla 1**: por día, del 01 del mes actual al 09 del mes siguiente. Dos filas por día: `Monto` (suma) y `Numero de cuotas` (conteo). Sábados y domingos en rojo.
  2. **Tabla 2**: por PERIODO, Monto.
  3. **Tabla 3**: por PERIODO, Numero de cuotas.

  Las columnas de las tres tablas se agrupan por *Fecha Vencimiento Actual*:
  `Anteriores | 2022 | 2023 | 2024 | 2025 | ene-26 ... mes actual | Adelanto | Adelanto Cierre | Total general`

## Dos formas de usarlo

### A) App web con Streamlit (recomendada)

```bash
pip install -r requirements.txt
streamlit run app.py
```

En la pantalla: subes el Excel, eliges **mes actual**, **fecha de cierre** y el **orden / nombres de las asesoras**, pulsas *Generar reporte* y descargas el Excel. Nada de esto requiere tocar Git.

- Los ajustes hechos en pantalla valen para esa sesión. Cada vez que abras la app, parte de los valores de `config.yaml`.
- Si quieres que unos ajustes queden como los iniciales, usa el botón *Descargar config.yaml* y reemplaza el `config.yaml` del repositorio (el archivo descargado no trae los comentarios).

### B) Línea de comandos

```bash
python -m src.main --input data/base.xlsx
python -m src.main --input data/base.xlsx --solo Katherin     # una sola asesora (pruebas)
```

Toma los parámetros de `config.yaml` y deja el Excel en `output/Reporte_cobranza_AAAA-MM.xlsx`.

## Publicar la app (Streamlit Community Cloud)

1. Sube este repositorio a GitHub (la base **no** se sube; ver "Datos personales").
2. Entra a <https://share.streamlit.io>, inicia sesión con GitHub y elige **Create app**.
3. Selecciona el repositorio, la rama `main` y como archivo principal `app.py`. Pulsa **Deploy**.
4. Cada cambio que subas al repositorio actualiza la app.

## Parámetros (`config.yaml` y pantalla de la app)

| Campo | Qué hace |
|---|---|
| `mes_actual` | `"2026-10"`. En noviembre: `"2026-11"`. Define hasta qué mes hay columnas y desde cuándo empieza Adelanto (día 1 del mes siguiente). |
| `fecha_cierre` | Fecha de cierre de ATC, p. ej. `"2026-11-05"`. **Adelanto Cierre** = vencimientos *después* de esa fecha (cierre el 5 -> desde el 6). Cámbiala si el cierre es el 6, 7, etc. |
| `tabla1_hasta_dia` | La Tabla 1 llega hasta este día del mes siguiente (9 -> 01/10 a 09/11). Solo formato. |
| `asesoras` | **Orden** = orden de columnas en `RES MES` y de pestañas. `nombre` = exactamente como viene en la base; `hoja` = nombre corto de la pestaña. |
| `anio_inicio_columnas` | Vencimientos anteriores a este año -> columna *Anteriores* (2022 -> 2021 hacia atrás). |
| `periodo_anteriores` | `PERIODO` <= este valor -> fila *Anteriores* (2019 agrupa 2018, 2019, 2020, 2021...). |

## Reglas

- Solo se cuentan filas con `Real Pago Dolar` > 0.
- **Adelanto** = vencimiento desde el día 1 del mes siguiente al mes actual.
- **Adelanto Cierre** = parte de Adelanto con vencimiento posterior a `fecha_cierre`. Como es un subconjunto, **no se suma al Total general** (así coincide con `RES MES`).
- Los días sin pagos quedan vacíos. Las filas de PERIODO son las mismas en todas las hojas.
- Si en la base aparece una coordinadora que no está en la lista, se avisa y se agrega al final.

## Datos personales

La base trae DNI, correos y teléfonos. Este programa **solo lee 5 columnas**: `PERIODO`, `Fecha Vencimiento Actual`, `Fecha Pago`, `Real Pago Dolar` y `Coordinadora Cobranza`. El resto nunca se carga, así que puedes dejar la base completa o borrar esas columnas antes de subirla a la app.

`.gitignore` excluye `*.xlsx`, `*.csv`, `data/` y `output/`: **no subas la base a GitHub**.

## Pruebas

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

## Estructura

```
app.py               <- app web (Streamlit)
config.yaml          <- valores iniciales
src/pipeline.py      <- flujo completo (lo usan la app y la consola)
src/main.py          <- línea de comandos
src/loader.py        <- lee y valida la base (solo 5 columnas)
src/buckets.py       <- reglas de Anteriores / meses / Adelanto / Adelanto Cierre
src/tables.py        <- RES MES y tablas por asesora
src/excel_writer.py  <- formato del Excel
tests/               <- pruebas
```
