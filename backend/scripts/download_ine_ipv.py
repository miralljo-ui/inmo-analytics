from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.request import urlopen


API_BASE = "https://servicios.ine.es/wstempus/js/ES"


def _fetch_json(url: str):
    with urlopen(url, timeout=30) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def _parse_zone_and_measure(name: str) -> tuple[str, str]:
    parts = [part.strip() for part in name.split(".") if part.strip()]
    if not parts:
        return name.strip(), ""
    zone = parts[0]
    measure = ". ".join(parts[1:])
    return zone, measure


def _iter_rows(series: Iterable[dict], metric_filter: str | None, series_regex: str | None):
    pattern = re.compile(series_regex, flags=re.IGNORECASE) if series_regex else None

    for item in series:
        name = str(item.get("Nombre", "")).strip()
        if metric_filter and metric_filter.lower() not in name.lower():
            continue
        if pattern and not pattern.search(name):
            continue

        zone, measure = _parse_zone_and_measure(name)
        series_code = item.get("COD")

        for row in item.get("Data", []):
            if row.get("Secreto") is True:
                continue
            value = row.get("Valor")
            if value is None:
                continue
            fecha = row.get("Fecha")
            if fecha is None:
                continue
            period = datetime.fromtimestamp(fecha / 1000, tz=timezone.utc).date().isoformat()

            yield {
                "zone": zone,
                "period": period,
                "value": float(value),
                "measure": measure,
                "series_code": series_code,
            }


def download_ipv(table_id: int, out_csv: Path, metric_filter: str | None, series_regex: str | None) -> int:
    url = f"{API_BASE}/DATOS_TABLA/{table_id}"
    series = _fetch_json(url)
    rows = list(_iter_rows(series, metric_filter, series_regex))

    if not rows:
        raise ValueError("No se generaron filas. Revisa filtros y tabla.")

    import pandas as pd

    df = pd.DataFrame(rows)
    df.insert(0, "source", f"INE:tabla {table_id}")
    df.to_csv(out_csv, index=False)
    return len(df)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Descarga INE IPV (tabla JAXI) a CSV")
    parser.add_argument("--table-id", type=int, default=25171, help="ID de tabla INE (JAXI)")
    parser.add_argument("--out-csv", type=Path, required=True, help="Ruta de salida CSV")
    parser.add_argument(
        "--metric-filter",
        default="Índice",
        help="Filtro de texto para series (ej: 'Índice')",
    )
    parser.add_argument(
        "--series-regex",
        default=None,
        help="Regex opcional para filtrar series por nombre",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    count = download_ipv(args.table_id, args.out_csv, args.metric_filter, args.series_regex)
    print(f"OK: {count} filas guardadas en {args.out_csv}")


if __name__ == "__main__":
    main()