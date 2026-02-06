from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.append(str(ROOT))

from app.core.config import settings  # noqa: E402


REQUIRED_ZONES_COLUMNS = {"name", "source"}
REQUIRED_LISTINGS_COLUMNS = {"zone", "period", "p25_m2", "p50_m2", "p75_m2", "sample_size", "source"}
REQUIRED_PRICE_COLUMNS = {"zone", "period", "price_m2", "source"}


class IngestError(Exception):
    pass


def _require_columns(df: pd.DataFrame, required: set[str], label: str) -> None:
    missing = required - set(df.columns)
    if missing:
        raise IngestError(f"{label}: faltan columnas {sorted(missing)}")


def _normalize_zone(name: str) -> str:
    return " ".join(str(name).strip().split())


def _parse_period(df: pd.DataFrame, label: str) -> pd.Series:
    period = pd.to_datetime(df["period"], errors="coerce").dt.date
    if period.isna().any():
        raise IngestError(f"{label}: hay valores inválidos en 'period'")
    return period


def _to_numeric(df: pd.DataFrame, column: str, label: str) -> pd.Series:
    values = pd.to_numeric(df[column], errors="coerce")
    if values.isna().any():
        raise IngestError(f"{label}: hay valores inválidos en '{column}'")
    return values


def _ensure_zone(conn, name: str, source: str, geom_wkt: str | None = None) -> int:
    row = conn.execute(
        text("SELECT id FROM zones WHERE lower(name) = lower(:name) LIMIT 1"),
        {"name": name},
    ).first()
    if row:
        return int(row[0])

    if geom_wkt:
        row = conn.execute(
            text(
                "INSERT INTO zones (name, source, geom) VALUES (:name, :source, ST_GeomFromText(:wkt, 4326)) RETURNING id"
            ),
            {"name": name, "source": source, "wkt": geom_wkt},
        ).first()
    else:
        row = conn.execute(
            text("INSERT INTO zones (name, source) VALUES (:name, :source) RETURNING id"),
            {"name": name, "source": source},
        ).first()

    return int(row[0])


def _chunked(iterable: Iterable[dict], size: int) -> Iterable[list[dict]]:
    batch: list[dict] = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def ingest(zones_csv: Path | None, listings_csv: Path, price_csv: Path, dry_run: bool) -> None:
    zones_df: pd.DataFrame | None = None
    if zones_csv:
        zones_df = pd.read_csv(zones_csv)
        _require_columns(zones_df, REQUIRED_ZONES_COLUMNS, "zones")
        zones_df["name"] = zones_df["name"].map(_normalize_zone)

    listings_df = pd.read_csv(listings_csv)
    _require_columns(listings_df, REQUIRED_LISTINGS_COLUMNS, "listings_agg")
    listings_df["zone"] = listings_df["zone"].map(_normalize_zone)
    listings_df["period"] = _parse_period(listings_df, "listings_agg")
    listings_df["p25_m2"] = _to_numeric(listings_df, "p25_m2", "listings_agg")
    listings_df["p50_m2"] = _to_numeric(listings_df, "p50_m2", "listings_agg")
    listings_df["p75_m2"] = _to_numeric(listings_df, "p75_m2", "listings_agg")
    listings_df["sample_size"] = _to_numeric(listings_df, "sample_size", "listings_agg").astype(int)

    price_df = pd.read_csv(price_csv)
    _require_columns(price_df, REQUIRED_PRICE_COLUMNS, "price_index")
    price_df["zone"] = price_df["zone"].map(_normalize_zone)
    price_df["period"] = _parse_period(price_df, "price_index")
    price_df["price_m2"] = _to_numeric(price_df, "price_m2", "price_index")

    if dry_run:
        print("OK: validación completada")
        print(f"zones: {0 if zones_df is None else len(zones_df)}")
        print(f"listings_agg: {len(listings_df)}")
        print(f"price_index: {len(price_df)}")
        return

    engine = create_engine(settings.database_url, pool_pre_ping=True)

    with engine.begin() as conn:
        zone_ids: dict[str, int] = {}

        if zones_df is not None:
            geom_present = "geom_wkt" in zones_df.columns
            for _, row in zones_df.iterrows():
                zone_name = row["name"]
                source = row["source"]
                geom_wkt = row["geom_wkt"] if geom_present else None
                zone_ids[zone_name.lower()] = _ensure_zone(conn, zone_name, source, geom_wkt)

        for zone_name in pd.concat([listings_df["zone"], price_df["zone"]]).unique():
            key = zone_name.lower()
            if key not in zone_ids:
                zone_ids[key] = _ensure_zone(conn, zone_name, "ingest")

        listings_rows = (
            {
                "zone_id": zone_ids[row["zone"].lower()],
                "period": row["period"],
                "p25_m2": float(row["p25_m2"]),
                "p50_m2": float(row["p50_m2"]),
                "p75_m2": float(row["p75_m2"]),
                "sample_size": int(row["sample_size"]),
                "source": row["source"],
            }
            for _, row in listings_df.iterrows()
        )

        price_rows = (
            {
                "zone_id": zone_ids[row["zone"].lower()],
                "period": row["period"],
                "price_m2": float(row["price_m2"]),
                "source": row["source"],
            }
            for _, row in price_df.iterrows()
        )

        listings_sql = text(
            """
            INSERT INTO listings_agg (zone_id, period, p25_m2, p50_m2, p75_m2, sample_size, source)
            VALUES (:zone_id, :period, :p25_m2, :p50_m2, :p75_m2, :sample_size, :source)
            """
        )
        price_sql = text(
            """
            INSERT INTO price_index (zone_id, period, price_m2, source)
            VALUES (:zone_id, :period, :price_m2, :source)
            """
        )

        for batch in _chunked(listings_rows, 1000):
            conn.execute(listings_sql, batch)
        for batch in _chunked(price_rows, 1000):
            conn.execute(price_sql, batch)

    print("OK: datos cargados correctamente")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Carga datos reales de precios por zona")
    parser.add_argument("--zones-csv", type=Path, default=None, help="CSV de zonas (name, source, geom_wkt opcional)")
    parser.add_argument("--listings-csv", type=Path, required=True, help="CSV con percentiles por zona")
    parser.add_argument("--price-csv", type=Path, required=True, help="CSV con precio medio €/m2 por zona")
    parser.add_argument("--dry-run", action="store_true", help="Valida archivos sin insertar en BD")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    ingest(args.zones_csv, args.listings_csv, args.price_csv, args.dry_run)


if __name__ == "__main__":
    main()
