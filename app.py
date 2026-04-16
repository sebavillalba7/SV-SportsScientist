
from flask import Flask, render_template, request, session
import pandas as pd
import plotly.express as px
import json
import plotly
from pathlib import Path
import uuid
import re

app = Flask(__name__)
app.secret_key = "sv_demo_secret_key_change_me"

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

BRAND = {
    "nombre": "Sebastián Villalba",
    "titulo": "Sports Scientist | Performance Consultant | Data Applied to Football",
    "headline": "Transformo datos deportivos en decisiones prácticas de rendimiento",
    "subheadline": "Monitoreo de cargas, análisis de rendimiento, implementación de procesos y visualización de datos para fútbol profesional.",
    "primary": "#00C2FF",
    "secondary": "#7C3AED",
    "accent": "#22C55E",
    "bg": "#07111F",
    "bg_soft": "#0D1728",
    "text": "#E5EEF8",
    "text_soft": "#9FB3C8",
    "whatsapp_url": "https://wa.me/5493424391972",
    "email": "sebastiangvillalba@gmail.com",
    "instagram": "https://www.instagram.com/sebagvillalba/",
    "linkedin": "https://www.linkedin.com/in/sebastianvillalba/"
}


def clean_columns(columns):
    cleaned = []
    for c in columns:
        c = str(c).strip()
        c = re.sub(r"\s+", " ", c)
        cleaned.append(c)
    return cleaned


def load_uploaded_file(file_storage):
    suffix = Path(file_storage.filename).suffix.lower()
    temp_name = f"{uuid.uuid4().hex}{suffix}"
    temp_path = UPLOAD_DIR / temp_name
    file_storage.save(temp_path)

    if suffix in [".csv", ".txt"]:
        # intenta separadores comunes
        last_error = None
        for sep in [None, ";", ",", "\t"]:
            try:
                if sep is None:
                    df = pd.read_csv(temp_path, sep=None, engine="python")
                else:
                    df = pd.read_csv(temp_path, sep=sep)
                break
            except Exception as e:
                last_error = e
                df = None
        if df is None:
            raise last_error
    elif suffix in [".xlsx", ".xls"]:
        df = pd.read_excel(temp_path)
    else:
        raise ValueError("Formato no soportado. Subí CSV o Excel.")

    df.columns = clean_columns(df.columns)
    return df, temp_path


def normalize_dataframe(df):
    df = df.copy()
    df.columns = clean_columns(df.columns)

    # limpia strings
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()

    # intenta convertir columnas numéricas
    for col in df.columns:
        if df[col].dtype == "object":
            s = df[col].astype(str).str.replace(".", "", regex=False)
            s = s.str.replace(",", ".", regex=False)
            converted = pd.to_numeric(s, errors="coerce")
            if converted.notna().sum() >= max(5, int(len(df) * 0.4)):
                df[col] = converted

    return df


def guess_column(columns, keywords):
    cols_upper = {c: c.upper() for c in columns}
    for keyword in keywords:
        for c, cu in cols_upper.items():
            if keyword in cu:
                return c
    return ""


def build_mapping_suggestions(columns):
    return {
        "player_col": guess_column(columns, ["JUGADOR", "PLAYER", "ATHLETE", "NAME"]),
        "micro_col": guess_column(columns, ["MICROCICLO", "MICRO", "WEEK", "SEMANA"]),
        "pos_col": guess_column(columns, ["POS", "POSITION", "PUESTO"]),
        "minutes_col": guess_column(columns, ["MIN", "MINUTOS", "MINUTES"]),
        "totdist_col": guess_column(columns, ["TOT DIST", "DISTANCIA TOTAL", "TOTAL DIST", "DIST"]),
        "hsd_col": guess_column(columns, ["MTS>19", "HSD", ">19", "HIGH SPEED"]),
        "decel_col": guess_column(columns, ["DES", "DECEL", "DEACC", "DESAC"]),
        "mtsmin_col": guess_column(columns, ["MTS/MIN", "DIST/MIN", "M/MIN"])
    }


def build_fixed_demo_chart():
    demo_df = pd.DataFrame({
        "Microciclo": ["MD-4", "MD-3", "MD-2", "MD-1", "MD"],
        "Carga": [420, 560, 390, 210, 95]
    })

    fig = px.line(
        demo_df,
        x="Microciclo",
        y="Carga",
        markers=True,
        title="Ejemplo de distribución de carga semanal"
    )

    fig.update_layout(
        paper_bgcolor=BRAND["bg_soft"],
        plot_bgcolor=BRAND["bg_soft"],
        font=dict(color=BRAND["text"]),
        margin=dict(l=30, r=30, t=60, b=30)
    )
    return fig.to_json()


def classify_status(value, mean, std):
    if pd.isna(value) or pd.isna(mean):
        return "gris"
    if std == 0 or pd.isna(std):
        return "verde"
    z = (value - mean) / std
    if abs(z) <= 0.75:
        return "verde"
    elif abs(z) <= 1.5:
        return "amarillo"
    return "rojo"


def build_demo_payload(df, mapping):
    player_col = mapping["player_col"]
    micro_col = mapping["micro_col"]
    pos_col = mapping["pos_col"]

    semaforo_options = [
        mapping["totdist_col"],
        mapping["hsd_col"],
        mapping["decel_col"]
    ]
    semaforo_options = [c for c in semaforo_options if c]

    scatter_defaults = {
        "x": mapping["hsd_col"],
        "y": mapping["mtsmin_col"],
        "size": mapping["minutes_col"]
    }

    needed = [player_col, micro_col, pos_col] + semaforo_options + [scatter_defaults["x"], scatter_defaults["y"], scatter_defaults["size"]]
    needed = [c for c in needed if c and c in df.columns]
    demo_df = df[needed].copy()

    # agrupamos por microciclo, posición y jugador
    agg_map = {}
    for c in demo_df.columns:
        if c == player_col:
            continue
        if pd.api.types.is_numeric_dtype(demo_df[c]):
            agg_map[c] = "mean"
        else:
            agg_map[c] = "first"

    grouped = demo_df.groupby(player_col, as_index=False).agg(agg_map)

    # para cada combinación de filtro, usamos el df base sin agrupar y la agrupación la hace JS
    records = df.to_dict(orient="records")

    return {
        "records": records,
        "columns": list(df.columns),
        "mapping": mapping,
        "filters": {
            "micro_values": sorted([str(v) for v in df[micro_col].dropna().unique().tolist()]) if micro_col in df.columns else [],
            "pos_values": sorted([str(v) for v in df[pos_col].dropna().unique().tolist()]) if pos_col in df.columns else []
        },
        "defaults": {
            "semaforo": semaforo_options[:3],
            "scatter_x": scatter_defaults["x"],
            "scatter_y": scatter_defaults["y"],
            "scatter_size": scatter_defaults["size"]
        }
    }
def clear_uploaded_session():
    csv_path = session.get("uploaded_csv_path")
    if csv_path:
        try:
            Path(csv_path).unlink(missing_ok=True)
        except Exception:
            pass

    session.pop("uploaded_csv_path", None)
    session["upload_stage"] = "upload"


@app.route("/", methods=["GET", "POST"])
def home():
    fig_json = build_fixed_demo_chart()

    servicios = [
        "Mentoría 1:1",
        "Monitoreo y gestión de cargas",
        "Implementación de tecnologías",
        "Dashboards deportivos",
        "Análisis de rendimiento"
    ]

    proyectos = [
        {"titulo": "Dashboard de cargas", "descripcion": "Visualización interactiva para interpretar carga externa por jugador, posición y microciclo."},
        {"titulo": "Riesgo y disponibilidad", "descripcion": "Integración de carga, wellness, lesiones y evaluaciones para mejorar el seguimiento del plantel."},
        {"titulo": "Consultoría aplicada", "descripcion": "Procesos, reportes y flujos de trabajo para cuerpos técnicos y áreas de rendimiento."}
    ]

    upload_error = None
    upload_stage = session.get("upload_stage", "upload")
    columns = []
    suggestions = {}
    demo_payload = None

    if request.method == "GET":
        clear_uploaded_session()
        upload_stage = "upload"
        columns = []
        suggestions = {}
        demo_payload = None

    if request.method == "POST":
        action = request.form.get("action", "")


        elif action == "upload_file":
            file = request.files.get("demo_file")
            if not file or file.filename == "":
                upload_error = "Subí un CSV o Excel para continuar."
                upload_stage = "upload"
            else:
                try:
                    df, temp_path = load_uploaded_file(file)
                    df = normalize_dataframe(df)
                    saved_path = UPLOAD_DIR / f"{uuid.uuid4().hex}.csv"
                    df.to_csv(saved_path, index=False)
                    try:
                        temp_path.unlink(missing_ok=True)
                    except Exception:
                        pass

                    session["uploaded_csv_path"] = str(saved_path)
                    session["upload_stage"] = "mapping"
                    upload_stage = "mapping"
                    columns = list(df.columns)
                    suggestions = build_mapping_suggestions(columns)
                except Exception as e:
                    upload_error = f"No pude leer el archivo: {e}"
                    upload_stage = "upload"

        elif action == "build_demo":
            csv_path = session.get("uploaded_csv_path")
            if not csv_path or not Path(csv_path).exists():
                upload_error = "No encontré el archivo cargado. Volvé a subirlo."
                upload_stage = "upload"
            else:
                df = pd.read_csv(csv_path)
                df = normalize_dataframe(df)

                mapping = {
                    "player_col": request.form.get("player_col", ""),
                    "micro_col": request.form.get("micro_col", ""),
                    "pos_col": request.form.get("pos_col", ""),
                    "minutes_col": request.form.get("minutes_col", ""),
                    "totdist_col": request.form.get("totdist_col", ""),
                    "hsd_col": request.form.get("hsd_col", ""),
                    "decel_col": request.form.get("decel_col", ""),
                    "mtsmin_col": request.form.get("mtsmin_col", "")
                }

                required = ["player_col", "micro_col", "pos_col", "totdist_col", "hsd_col", "decel_col", "mtsmin_col", "minutes_col"]
                missing = [k for k in required if not mapping.get(k)]
                if missing:
                    upload_error = "Completá todos los mapeos de columnas para construir el demo."
                    upload_stage = "mapping"
                    columns = list(df.columns)
                    suggestions = mapping
                else:
                    demo_payload = build_demo_payload(df, mapping)
                    session["upload_stage"] = "dashboard"
                    upload_stage = "dashboard"
                    columns = list(df.columns)
                    suggestions = mapping

    if upload_stage in ["mapping", "dashboard"] and not columns:
        csv_path = session.get("uploaded_csv_path")
        if csv_path and Path(csv_path).exists():
            df = pd.read_csv(csv_path)
            df = normalize_dataframe(df)
            columns = list(df.columns)
            suggestions = build_mapping_suggestions(columns)

    return render_template(
        "index.html",
        brand=BRAND,
        fig_json=fig_json,
        servicios=servicios,
        proyectos=proyectos,
        upload_error=upload_error,
        upload_stage=upload_stage,
        upload_columns=columns,
        mapping_suggestions=suggestions,
        demo_payload=json.dumps(demo_payload) if demo_payload else None
    )


if __name__ == "__main__":
    app.run(debug=True)
