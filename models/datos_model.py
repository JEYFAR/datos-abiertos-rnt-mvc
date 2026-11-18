import json
import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()


def obtener_conexion():
    """Establece y devuelve una conexión a SQL Server usando variables de .env."""
    servidor = os.getenv("DB_SERVER", r"localhost\SQLEXPRESS")
    base_datos = os.getenv("DB_NAME", "DatosAbiertosDB")
    driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
    trusted = os.getenv("DB_TRUSTED", "yes").strip().lower() == "yes"

    if trusted:
        cadena = (
            f"DRIVER={{{driver}}};"
            f"SERVER={servidor};"
            f"DATABASE={base_datos};"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )
    else:
        usuario = os.getenv("DB_USER", "")
        clave = os.getenv("DB_PASSWORD", "")
        cadena = (
            f"DRIVER={{{driver}}};"
            f"SERVER={servidor};"
            f"DATABASE={base_datos};"
            f"UID={usuario};PWD={clave};"
            "TrustServerCertificate=yes;"
        )

    return pyodbc.connect(cadena)


def _limpiar_texto(valor, longitud_maxima):
    """Limpia espacios y ajusta la longitud para prevenir truncamientos en SQL Server."""
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    return texto[:longitud_maxima]


def _a_entero(valor):
    """Convierte valores numéricos recibidos como texto en entero seguro."""
    if valor is None:
        return 0
    texto = str(valor).strip().replace(",", "")
    if not texto:
        return 0
    try:
        return int(float(texto))
    except (ValueError, TypeError):
        return 0


def _construir_id_api(registro):
    """
    Construye una clave única estable para cada registro del RNT.
    Se combina codigo_rnt + ano + periodo porque un mismo establecimiento puede
    aparecer en diferentes cortes/periodos del conjunto de datos.
    """
    codigo_rnt = _limpiar_texto(registro.get("codigo_rnt"), 50)
    if not codigo_rnt:
        return ""

    ano = _limpiar_texto(registro.get("ano"), 10)
    periodo = _limpiar_texto(registro.get("periodo"), 30)

    partes = [codigo_rnt]
    if ano:
        partes.append(ano)
    if periodo:
        partes.append(periodo)

    return "-".join(partes)[:120]


def guardar_registros(registros):
    """
    Guarda los registros recibidos de la API en dbo.RegistrosRNT evitando duplicados.
    Retorna un diccionario con el conteo de insertados y duplicados omitidos.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    insertados = 0
    duplicados = 0

    try:
        for registro in registros:
            if not isinstance(registro, dict):
                continue

            identificador = _construir_id_api(registro)
            if not identificador:
                continue

            codigo_rnt = _limpiar_texto(registro.get("codigo_rnt"), 50)
            razon_social = _limpiar_texto(
                registro.get("razon_social_establecimiento"), 250
            )
            departamento = _limpiar_texto(registro.get("departamento"), 120)
            municipio = _limpiar_texto(registro.get("municipio"), 120)
            categoria = _limpiar_texto(registro.get("categoria"), 150)
            sub_categoria = _limpiar_texto(registro.get("sub_categoria"), 200)
            estado_rnt = _limpiar_texto(registro.get("estado_rnt"), 50)
            habitaciones = _a_entero(registro.get("habitaciones"))
            camas = _a_entero(registro.get("camas"))
            empleados = _a_entero(registro.get("num_emp1"))

            ano = _limpiar_texto(registro.get("ano"), 10) or ""
            periodo = _limpiar_texto(registro.get("periodo"), 40) or ""
            periodo_reporte = _limpiar_texto(
                f"{ano} - {periodo}".strip(" -"), 60
            )

            json_original = json.dumps(registro, ensure_ascii=False)

            cursor.execute(
                """
                IF NOT EXISTS (
                    SELECT 1 FROM dbo.RegistrosRNT WHERE id_api = ?
                )
                INSERT INTO dbo.RegistrosRNT (
                    id_api,
                    codigo_rnt,
                    razon_social,
                    departamento,
                    municipio,
                    categoria,
                    sub_categoria,
                    estado_rnt,
                    habitaciones,
                    camas,
                    empleados,
                    periodo_reporte,
                    json_original
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                identificador,
                identificador,
                codigo_rnt,
                razon_social,
                departamento,
                municipio,
                categoria,
                sub_categoria,
                estado_rnt,
                habitaciones,
                camas,
                empleados,
                periodo_reporte,
                json_original,
            )

            if cursor.rowcount > 0:
                insertados += 1
            else:
                duplicados += 1

        conexion.commit()
        return {
            "insertados": insertados,
            "duplicados": duplicados,
            "recibidos": len(registros),
        }
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def consultar_registros(filtro=""):
    """
    Consulta hasta 100 registros almacenados en SQL Server.
    Permite filtrar por municipio, departamento, categoría, razón social o código RNT.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        if filtro:
            patron = f"%{filtro}%"
            cursor.execute(
                """
                SELECT TOP 100
                    id_api,
                    codigo_rnt,
                    razon_social,
                    departamento,
                    municipio,
                    categoria,
                    sub_categoria,
                    estado_rnt,
                    habitaciones,
                    camas,
                    empleados,
                    periodo_reporte
                FROM dbo.RegistrosRNT
                WHERE municipio LIKE ?
                   OR departamento LIKE ?
                   OR categoria LIKE ?
                   OR razon_social LIKE ?
                   OR codigo_rnt LIKE ?
                ORDER BY id DESC
                """,
                patron,
                patron,
                patron,
                patron,
                patron,
            )
        else:
            cursor.execute(
                """
                SELECT TOP 100
                    id_api,
                    codigo_rnt,
                    razon_social,
                    departamento,
                    municipio,
                    categoria,
                    sub_categoria,
                    estado_rnt,
                    habitaciones,
                    camas,
                    empleados,
                    periodo_reporte
                FROM dbo.RegistrosRNT
                ORDER BY id DESC
                """
            )

        columnas = [columna[0] for columna in cursor.description]
        return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
    finally:
        cursor.close()
        conexion.close()


def obtener_resumen(filtro=""):
    """
    Calcula el resumen numérico básico directamente en SQL Server.
    Se adapta automáticamente al filtro activo.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        if filtro:
            patron = f"%{filtro}%"
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_registros,
                    COUNT(DISTINCT municipio) AS municipios_distintos,
                    COUNT(DISTINCT departamento) AS departamentos_distintos,
                    COALESCE(SUM(empleados), 0) AS total_empleados,
                    COALESCE(SUM(habitaciones), 0) AS total_habitaciones,
                    COALESCE(SUM(camas), 0) AS total_camas,
                    ROUND(COALESCE(AVG(CAST(empleados AS FLOAT)), 0), 1) AS promedio_empleados
                FROM dbo.RegistrosRNT
                WHERE municipio LIKE ?
                   OR departamento LIKE ?
                   OR categoria LIKE ?
                   OR razon_social LIKE ?
                   OR codigo_rnt LIKE ?
                """,
                patron,
                patron,
                patron,
                patron,
                patron,
            )
        else:
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_registros,
                    COUNT(DISTINCT municipio) AS municipios_distintos,
                    COUNT(DISTINCT departamento) AS departamentos_distintos,
                    COALESCE(SUM(empleados), 0) AS total_empleados,
                    COALESCE(SUM(habitaciones), 0) AS total_habitaciones,
                    COALESCE(SUM(camas), 0) AS total_camas,
                    ROUND(COALESCE(AVG(CAST(empleados AS FLOAT)), 0), 1) AS promedio_empleados
                FROM dbo.RegistrosRNT
                """
            )

        fila = cursor.fetchone()
        columnas = [columna[0] for columna in cursor.description]
        return dict(zip(columnas, fila))
    finally:
        cursor.close()
        conexion.close()
