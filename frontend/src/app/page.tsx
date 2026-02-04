"use client";

import { useState } from "react";
import styles from "./page.module.css";

export default function Home() {
  const [zona, setZona] = useState("");
  const [area, setArea] = useState("");
  const [rooms, setRooms] = useState("");
  const [yearBuilt, setYearBuilt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<{
    estimated_price_eur: number;
    price_range_eur: [number, number];
    overvalued: boolean;
  } | null>(null);

  const handleEstimate = async () => {
    setError("");
    setResult(null);

    if (!zona || !area) {
      setError("Indica zona y superficie.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/valuation/estimate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          zona,
          area_m2: Number(area),
          rooms: rooms ? Number(rooms) : undefined,
          year_built: yearBuilt ? Number(yearBuilt) : undefined,
        }),
      });

      if (!response.ok) {
        throw new Error("No se pudo calcular el estimado.");
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <header className={styles.header}>
          <div>
            <p className={styles.eyebrow}>Mercado inmobiliario · España</p>
            <h1>Inmo Analytics</h1>
            <p className={styles.subtitle}>
              Panel de análisis con estimación de precios por zona y detección de
              sobrevaloración usando datos abiertos oficiales.
            </p>
          </div>
          <div className={styles.status}>
            <span className={styles.badge}>MVP</span>
            <span className={styles.dot} />
            <span>Actualización diaria</span>
          </div>
        </header>

        <section className={styles.kpis}>
          <article className={styles.kpiCard}>
            <p className={styles.kpiLabel}>Precio medio €/m²</p>
            <h2>2.240</h2>
            <span className={styles.kpiDelta}>+1,8% trimestral</span>
          </article>
          <article className={styles.kpiCard}>
            <p className={styles.kpiLabel}>Rango medio zona</p>
            <h2>1.820 - 2.740</h2>
            <span className={styles.kpiDelta}>P25 - P75</span>
          </article>
          <article className={styles.kpiCard}>
            <p className={styles.kpiLabel}>Volumen transacciones</p>
            <h2>52.430</h2>
            <span className={styles.kpiDelta}>Último trimestre</span>
          </article>
          <article className={styles.kpiCard}>
            <p className={styles.kpiLabel}>Índice de esfuerzo</p>
            <h2>34,2%</h2>
            <span className={styles.kpiDelta}>Renta disponible</span>
          </article>
        </section>

        <section className={styles.charts}>
          <div className={styles.chartCard}>
            <h3>Evolución de precios</h3>
            <div className={styles.chartPlaceholder}>
              Serie temporal · INE / MITMA
            </div>
          </div>
          <div className={styles.chartCard}>
            <h3>Mapa de rangos por zona</h3>
            <div className={styles.chartPlaceholder}>Mapa · PostGIS / OSM</div>
          </div>
        </section>

        <section className={styles.tools}>
          <div className={styles.toolCard}>
            <h3>Estimador de precios</h3>
            <form className={styles.form}>
              <label>
                Zona
                <input
                  type="text"
                  placeholder="Madrid - Centro"
                  value={zona}
                  onChange={(event) => setZona(event.target.value)}
                />
              </label>
              <label>
                Superficie (m²)
                <input
                  type="number"
                  placeholder="85"
                  value={area}
                  onChange={(event) => setArea(event.target.value)}
                />
              </label>
              <label>
                Habitaciones
                <input
                  type="number"
                  placeholder="3"
                  value={rooms}
                  onChange={(event) => setRooms(event.target.value)}
                />
              </label>
              <label>
                Año construcción
                <input
                  type="number"
                  placeholder="2005"
                  value={yearBuilt}
                  onChange={(event) => setYearBuilt(event.target.value)}
                />
              </label>
              <button type="button" onClick={handleEstimate} disabled={loading}>
                {loading ? "Calculando..." : "Calcular rango"}
              </button>
            </form>
            {error ? <p className={styles.error}>{error}</p> : null}
          </div>
          <div className={styles.toolCard}>
            <h3>Detector de sobrevaloración</h3>
            <div className={styles.detector}>
              <p>
                Precio estimado:{" "}
                <strong>
                  {result ? result.estimated_price_eur.toLocaleString("es-ES") : "--"} €
                </strong>
              </p>
              <p>
                Rango zona:{" "}
                <strong>
                  {result
                    ? `${result.price_range_eur[0].toLocaleString("es-ES")} € - ${result.price_range_eur[1].toLocaleString("es-ES")} €`
                    : "--"}
                </strong>
              </p>
              <div className={styles.verdict}>
                <span className={styles.verdictLabel}>Valoración</span>
                <span className={styles.verdictState}>
                  {result ? (result.overvalued ? "Sobrevalorada" : "Correcta") : "--"}
                </span>
              </div>
              <p className={styles.verdictHint}>
                Se considera sobrevalorada si supera el P75 del rango zonal.
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
