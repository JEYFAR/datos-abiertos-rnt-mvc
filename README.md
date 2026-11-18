# Sistema Web de Consulta y Análisis de Datos Abiertos de Colombia

Proyecto integrador para la asignatura **Desarrollo de Aplicaciones con Acceso a Datos** (Corporación Universitaria Americana).

**Equipo de desarrollo:**
- **Jesus David Ayala Noche**
- **Steven Manuel Yepez Navarro**

Aplicación web desarrollada en **Python + Flask** bajo el patrón **MVC (Modelo–Vista–Controlador)** que consume una API pública del portal oficial [datos.gov.co](https://www.datos.gov.co/), persiste los registros en **Microsoft SQL Server** evitando duplicados y permite consultarlos, filtrarlos y analizar un resumen numérico desde el navegador.

---

## 1. Objetivo del proyecto

Construir una aplicación web sencilla y modular que integre:
1. Consumo de datos abiertos gubernamentales en formato **JSON** mediante la API REST **SODA** (*Socrata Open Data API*).
2. Almacenamiento relacional en **SQL Server** usando `pyodbc`, configuración externalizada en `.env` y control de duplicados mediante clave única (`UNIQUE` + `IF NOT EXISTS`).
3. Visualización web con **Flask**, búsqueda/filtro dinámico y resumen numérico calculado directamente en SQL Server, respetando la separación de responsabilidades **MVC**.

---

## 2. Conjunto de datos (Dataset) seleccionado

- **Nombre:** Registro Nacional de Turismo - RNT
- **Entidad responsable:** Ministerio de Comercio, Industria y Turismo (MinCIT)
- **Propósito:** Permite consultar los prestadores de servicios turísticos registrados en Colombia (agencias de viajes, hoteles, alojamientos, guías, etc.), su ubicación territorial, estado de registro, empleados y capacidad instalada (habitaciones y camas).
- **Ficha oficial:** https://www.datos.gov.co/d/thwd-ivmp
- **ID del recurso (SODA):** `thwd-ivmp`
- **Endpoint de consulta JSON:** `https://www.datos.gov.co/resource/thwd-ivmp.json?$limit=100`

### Mapeo y explicación de campos

| Campo JSON (`datos.gov.co`) | Columna SQL (`dbo.RegistrosRNT`) | Tipo SQL | Descripción |
| :--- | :--- | :--- | :--- |
| `codigo_rnt` + `ano` + `periodo` | `id_api` | `NVARCHAR(120) UNIQUE` | Clave única compuesta (`codigo_rnt-ano-periodo`) que evita duplicar un mismo prestador dentro del mismo periodo de reporte. |
| `codigo_rnt` | `codigo_rnt` | `NVARCHAR(50)` | Código oficial asignado al prestador en el Registro Nacional de Turismo. |
| `razon_social_establecimiento` | `razon_social` | `NVARCHAR(250)` | Nombre o razón social del establecimiento turístico. |
| `departamento` | `departamento` | `NVARCHAR(120)` | Departamento de Colombia donde opera el prestador. |
| `municipio` | `municipio` | `NVARCHAR(120)` | Municipio o ciudad donde está registrado el establecimiento. |
| `categoria` | `categoria` | `NVARCHAR(150)` | Categoría principal del prestador (ej. Agencias de Viajes, Alojamiento). |
| `sub_categoria` | `sub_categoria` | `NVARCHAR(200)` | Subcategoría o especialidad del servicio turístico. |
| `estado_rnt` | `estado_rnt` | `NVARCHAR(50)` | Estado actual del registro en el RNT (ej. `ACTIVO`). |
| `habitaciones` | `habitaciones` | `INT` | Número de habitaciones reportadas (convertido a entero de forma segura). |
| `camas` | `camas` | `INT` | Número de camas reportadas (convertido a entero de forma segura). |
| `num_emp1` | `empleados` | `INT` | Número de empleados reportados por el establecimiento. |
| `ano` + `periodo` | `periodo_reporte` | `NVARCHAR(60)` | Año y mes del corte de información (ej. `2026 - OCTUBRE`). |
| *(registro completo)* | `json_original` | `NVARCHAR(MAX)` | Copia íntegra del objeto JSON recibido de la API para trazabilidad. |
| *(automático)* | `fecha_captura` | `DATETIME2` | Fecha y hora en que SQL Server almacenó el registro (`SYSDATETIME()`). |

---

## 3. Arquitectura y patrón MVC

El proyecto separa estrictamente cada responsabilidad para evitar que la Vista consulte SQL Server o que el Modelo genere HTML:

```text
DevAppDB/
├── app.py                   # CONTROLADOR: rutas Flask (/, /sincronizar) y coordinación del flujo
├── api/
│   ├── __init__.py
│   └── api_client.py        # SERVICIO API: peticiones HTTP GET con requests a datos.gov.co
├── models/
│   ├── __init__.py
│   └── datos_model.py       # MODELO: conexión pyodbc, guardado sin duplicados, SELECT y resumen SQL
├── templates/
│   └── index.html           # VISTA: plantilla HTML + Jinja2 (tabla, filtro, resumen y mensajes)
├── static/
│   └── estilos.css          # Estilos CSS de la interfaz
├── sql/
│   └── crear_bd.sql         # Script SQL para crear DatosAbiertosDB y dbo.RegistrosRNT
├── evidencias/
│   ├── respuesta_api.json   # Muestra real de la respuesta JSON de la API
│   └── consulta_sql.txt     # Evidencia de conteo, anti-duplicados y filas en SQL Server
├── .env                     # Configuración local (NO publicar en repositorios)
├── .env.example             # Plantilla segura de variables de entorno
├── .gitignore               # Excluye .env, venv/ y archivos temporales
├── LICENSE                  # Licencia MIT
├── requirements.txt         # Dependencias instaladas en el entorno virtual
└── README.md                # Documentación del proyecto
```

### Flujo de ejecución
1. **Navegador → Controlador (`app.py`):** el usuario entra a `/` (consulta) o pulsa *"Consultar API y guardar datos"* (`POST /sincronizar`).
2. **Controlador → Cliente API (`api/api_client.py`):** en `/sincronizar`, `APIClient.obtener_registros(100)` solicita el JSON a `datos.gov.co`.
3. **Controlador → Modelo (`models/datos_model.py`):**
   - `guardar_registros(datos)` inserta cada registro en `dbo.RegistrosRNT` validando con `IF NOT EXISTS` que `id_api` no exista previamente.
   - En `/`, `consultar_registros(filtro)` y `obtener_resumen(filtro)` ejecutan consultas `SELECT` parametrizadas (`?`) en SQL Server.
4. **Controlador → Vista (`templates/index.html`):** Flask renderiza la plantilla con los resultados y las tarjetas de resumen numérico.

---

## 4. Requisitos previos

- **Python 3.10 o superior** (probado con Python 3.13)
- **Microsoft SQL Server** (ej. SQL Server Express `localhost\SQLEXPRESS`) y **SSMS**
- **Microsoft ODBC Driver 18 for SQL Server** (o versión 17 compatible)
- Conexión a Internet para sincronizar con `datos.gov.co`

---

## 5. Instalación y ejecución paso a paso

### Paso 1: Crear la base de datos y la tabla en SQL Server
Abrir **SQL Server Management Studio (SSMS)**, conectarse a la instancia (ej. `localhost\SQLEXPRESS`) y ejecutar el script:

```text
sql/crear_bd.sql
```

También se puede ejecutar desde PowerShell con `sqlcmd`:

```powershell
sqlcmd -S localhost\SQLEXPRESS -E -C -i sql\crear_bd.sql
```

### Paso 2: Configurar el archivo `.env`
Copiar `.env.example` como `.env` y verificar los valores locales:

```env
DB_SERVER=localhost\SQLEXPRESS
DB_NAME=DatosAbiertosDB
DB_DRIVER=ODBC Driver 18 for SQL Server
DB_TRUSTED=yes
DB_USER=
DB_PASSWORD=
API_RESOURCE_ID=thwd-ivmp
FLASK_SECRET_KEY=clave-local-datos-abiertos-rnt-2026
```

- Con **Autenticación de Windows**, dejar `DB_TRUSTED=yes` y `DB_USER`/`DB_PASSWORD` vacíos.
- Con **Autenticación SQL**, cambiar a `DB_TRUSTED=no` y diligenciar `DB_USER` y `DB_PASSWORD`.
- **Importante:** nunca subir el archivo `.env` a GitHub ni compartir credenciales.

### Paso 3: Crear el entorno virtual e instalar dependencias

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Paso 4: Ejecutar la aplicación web

```powershell
python app.py
```

Abrir en el navegador: **http://127.0.0.1:5000**

---

## 6. Pruebas de verificación

1. Al abrir `http://127.0.0.1:5000`, pulsar **"Consultar API y guardar datos"**.
2. Confirmar el mensaje verde de éxito indicando la cantidad de registros nuevos guardados.
3. Usar el buscador (ej. `CARTAGENA`, `BOGOTA`, `HOTEL` o `AGENCIAS`) y comprobar que tanto la tabla como las tarjetas del resumen numérico se recalculan desde SQL Server.
4. Pulsar nuevamente **"Consultar API y guardar datos"** y confirmar que muestra `Nuevos guardados: 0` y `Ya existentes (omitidos): 100`, demostrando la prevención de duplicados.
5. Verificar en SSMS:
   ```sql
   USE DatosAbiertosDB;
   SELECT COUNT(*) AS TotalRegistros FROM dbo.RegistrosRNT;
   SELECT TOP 10 codigo_rnt, razon_social, municipio, categoria, empleados, habitaciones
   FROM dbo.RegistrosRNT
   ORDER BY id DESC;
   ```

---

## 7. Guía rápida de sustentación (Equipo)

- **Jesus David Ayala Noche — API, Datos y SQL Server (`api/api_client.py`, `sql/crear_bd.sql`, `models/datos_model.py`):** explica el dataset RNT (`thwd-ivmp`), el consumo HTTP con `requests` (`$limit=100`, `timeout` y `raise_for_status()`), el diseño de `dbo.RegistrosRNT`, la conexión sin credenciales quemadas (`.env` + `pyodbc`), la clave única `id_api` (`UNIQUE` + `IF NOT EXISTS`) contra duplicados y las consultas SQL parametrizadas (`?`).
- **Steven Manuel Yepez Navarro — Controlador, Vista y Pruebas (`app.py`, `templates/index.html`, `static/estilos.css`):** explica la arquitectura MVC, las rutas Flask `/` (GET) y `/sincronizar` (POST), el manejo de mensajes `flash`, el filtro dinámico, las tarjetas de resumen numérico calculadas desde SQL Server, las evidencias y por qué la Vista no accede directamente a la base de datos.

---

## 8. Alcance y seguridad básica

- **Dentro del alcance:** consumo de API pública, carga/sincronización sin duplicados en SQL Server, consulta web con filtro y resumen numérico bajo patrón MVC.
- **Fuera del alcance:** CRUD completo (crear/editar/eliminar desde la web), autenticación de usuarios y despliegue en producción.
- **Buenas prácticas aplicadas:** credenciales aisladas en `.env` (excluido en `.gitignore`), consultas SQL 100% parametrizadas, validación/conversión segura de tipos externos y `debug=True` únicamente para entorno local.

---

## 9. Licencia

Este proyecto se distribuye bajo la licencia **MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.
