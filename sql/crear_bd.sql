-- ============================================================================
-- Script de creación de Base de Datos y Tabla
-- Proyecto: Sistema Web de Consulta y Análisis de Datos Abiertos de Colombia
-- Dataset: Registro Nacional de Turismo - RNT (datos.gov.co / ID: thwd-ivmp)
-- Motor: Microsoft SQL Server
-- ============================================================================

IF DB_ID(N'DatosAbiertosDB') IS NULL
BEGIN
    CREATE DATABASE DatosAbiertosDB;
END
GO

USE DatosAbiertosDB;
GO

IF OBJECT_ID(N'dbo.RegistrosRNT', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.RegistrosRNT (
        id INT IDENTITY(1,1) PRIMARY KEY,
        id_api NVARCHAR(120) NOT NULL UNIQUE,
        codigo_rnt NVARCHAR(50) NOT NULL,
        razon_social NVARCHAR(250) NULL,
        departamento NVARCHAR(120) NULL,
        municipio NVARCHAR(120) NULL,
        categoria NVARCHAR(150) NULL,
        sub_categoria NVARCHAR(200) NULL,
        estado_rnt NVARCHAR(50) NULL,
        habitaciones INT NOT NULL DEFAULT 0,
        camas INT NOT NULL DEFAULT 0,
        empleados INT NOT NULL DEFAULT 0,
        periodo_reporte NVARCHAR(60) NULL,
        json_original NVARCHAR(MAX) NULL,
        fecha_captura DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );
END
GO

-- Índice de apoyo para acelerar las búsquedas por municipio y categoría
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_RegistrosRNT_Municipio_Categoria'
      AND object_id = OBJECT_ID(N'dbo.RegistrosRNT')
)
BEGIN
    CREATE INDEX IX_RegistrosRNT_Municipio_Categoria
    ON dbo.RegistrosRNT (municipio, categoria);
END
GO
