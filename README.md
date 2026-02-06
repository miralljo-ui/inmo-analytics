Inmo Analytics

Aplicación web para analizar el mercado inmobiliario en España usando datos abiertos oficiales.

Estructura
- frontend: Next.js (dashboard, estimador, detector)
- backend: FastAPI (API de valoración y servicios)
- db: SQL y documentación de PostGIS

Objetivos MVP
- Dashboard con KPIs y series temporales
- Estimador de precios por zona
- Detector de sobrevaloración basado en percentiles

Ejecución rápida (local)
- Backend: FastAPI con PostgreSQL/PostGIS (ver db/schema.sql)
- Frontend: Next.js

Variables de entorno (backend)
- DATABASE_URL: cadena de conexión a PostgreSQL
- ALLOWED_ORIGINS: orígenes permitidos para CORS

Ingesta de datos reales (CSV)
- Script: backend/scripts/ingest_stats.py
- Requiere tres CSV:
	- zonas: columnas name, source, (opcional geom_wkt)
	- listings_agg: columnas zone, period, p25_m2, p50_m2, p75_m2, sample_size, source
	- price_index: columnas zone, period, price_m2, source

Descarga INE (IPV) desde API TEMPUS
- Script: backend/scripts/download_ine_ipv.py
- Tabla ejemplo: 25171 (Índice de Precios de Vivienda por CCAA)
- Salida CSV con columnas: source, zone, period, value, measure, series_code
