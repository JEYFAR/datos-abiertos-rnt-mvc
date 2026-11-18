import os
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

from api.api_client import APIClient
from models.datos_model import (
    consultar_registros,
    guardar_registros,
    obtener_resumen,
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv(
    "FLASK_SECRET_KEY", "clave-local-datos-abiertos-rnt-2026"
)


@app.route("/", methods=["GET"])
def inicio():
    """Ruta principal (Controlador): lee el filtro, consulta el Modelo y entrega datos a la Vista."""
    filtro = request.args.get("q", "").strip()
    registros = []
    resumen = {
        "total_registros": 0,
        "municipios_distintos": 0,
        "departamentos_distintos": 0,
        "total_empleados": 0,
        "total_habitaciones": 0,
        "total_camas": 0,
        "promedio_empleados": 0.0,
    }

    try:
        registros = consultar_registros(filtro)
        resumen = obtener_resumen(filtro)
    except Exception as error:
        flash(
            f"No fue posible consultar SQL Server. Verifica el servicio y el archivo .env: {error}",
            "error",
        )

    return render_template(
        "index.html",
        registros=registros,
        resumen=resumen,
        filtro=filtro,
    )


@app.route("/sincronizar", methods=["POST"])
def sincronizar():
    """Ruta de sincronización (Controlador): consulta la API externa y guarda en SQL Server."""
    try:
        cliente = APIClient()
        datos = cliente.obtener_registros(limite=100)
        resultado = guardar_registros(datos)
        flash(
            (
                f"Sincronización finalizada. Recibidos de la API: {resultado['recibidos']} | "
                f"Nuevos guardados: {resultado['insertados']} | "
                f"Ya existentes (omitidos): {resultado['duplicados']}."
            ),
            "success",
        )
    except Exception as error:
        flash(
            f"No fue posible consultar o guardar los datos: {error}",
            "error",
        )

    return redirect(url_for("inicio"))


if __name__ == "__main__":
    app.run(debug=True)
