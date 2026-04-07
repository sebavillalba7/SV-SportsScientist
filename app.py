
from flask import Flask, render_template
import pandas as pd
import plotly.express as px
import json
import plotly

app = Flask(__name__)

@app.route("/")
def home():
    # Datos DEMO: después los podés reemplazar por tus datos reales
    df = pd.DataFrame({
        "Microciclo": ["MD-4", "MD-3", "MD-2", "MD-1", "MD"],
        "Carga": [420, 560, 390, 210, 95]
    })

    fig = px.line(
        df,
        x="Microciclo",
        y="Carga",
        markers=True,
        title="Ejemplo de distribución de carga semanal"
    )

    fig.update_layout(
        paper_bgcolor="#0D1728",
        plot_bgcolor="#0D1728",
        font=dict(color="#E5EEF8"),
        margin=dict(l=30, r=30, t=60, b=30)
    )

    fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder) if False else fig.to_json()

    servicios = [
        "Monitoreo de cargas y microciclos",
        "Implementación y lectura de GPS",
        "Dashboards deportivos personalizados",
        "Análisis de rendimiento y toma de decisiones"
    ]

    proyectos = [
        {
            "titulo": "Dashboard de cargas",
            "descripcion": "Visualización interactiva para interpretar carga externa por jugador, posición y microciclo."
        },
        {
            "titulo": "Riesgo y disponibilidad",
            "descripcion": "Integración de carga, wellness, lesiones y evaluaciones para mejorar el seguimiento del plantel."
        },
        {
            "titulo": "Consultoría aplicada",
            "descripcion": "Procesos, reportes y flujos de trabajo para cuerpos técnicos y áreas de rendimiento."
        }
    ]

    return render_template(
        "index.html",
        brand={'site_folder': 'SV-SportsScientist', 'nombre': 'Mag. Sebastián Villalba', 'titulo': 'Sports Scientist | Performance Consultant | Data Applied to Football', 'headline': 'Transformo datos deportivos en decisiones prácticas de rendimiento', 'subheadline': 'Monitoreo de cargas, análisis de rendimiento, implementación de procesos y visualización de datos para fútbol profesional.', 'primary': '#00C2FF', 'secondary': '#7C3AED', 'accent': '#22C55E', 'bg': '#07111F', 'bg_soft': '#0D1728', 'text': '#E5EEF8', 'text_soft': '#9FB3C8', 'whatsapp_url': 'https://wa.me/5493424391972', 'email': 'sebastiangvillalba@gmail.com', 'instagram': 'https://www.instagram.com/sebagvillalba/', 'linkedin': 'https://www.linkedin.com/in/sebastianvillalba/'},
        fig_json=fig_json,
        servicios=servicios,
        proyectos=proyectos
    )

if __name__ == "__main__":
    app.run(debug=True)
