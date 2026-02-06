from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class ZonePriceStats:
    mean_price_m2: float
    p25_m2: float
    p50_m2: float
    p75_m2: float
    sample_size: int


class ZoneNotFoundError(Exception):
    def __init__(self, zone: str) -> None:
        super().__init__(f"Zone not found: {zone}")
        self.zone = zone


class ZoneDataNotFoundError(Exception):
    def __init__(self, zone: str, year: int) -> None:
        super().__init__(f"No data for zone '{zone}' in year {year}")
        self.zone = zone
        self.year = year


def get_zone_price_stats(db: Session, zone: str, year: int) -> ZonePriceStats:
    zone_row = (
        db.execute(
            text("SELECT id, name FROM zones WHERE lower(name) = lower(:zone) LIMIT 1"),
            {"zone": zone},
        )
        .mappings()
        .first()
    )
    if not zone_row:
        raise ZoneNotFoundError(zone)

    zone_id = zone_row["id"]

    agg_row = (
        db.execute(
            text(
                """
                SELECT
                    avg(p25_m2) AS p25_m2,
                    avg(p50_m2) AS p50_m2,
                    avg(p75_m2) AS p75_m2,
                    sum(sample_size) AS sample_size
                FROM listings_agg
                WHERE zone_id = :zone_id
                  AND extract(year FROM period) = :year
                """
            ),
            {"zone_id": zone_id, "year": year},
        )
        .mappings()
        .first()
    )

    if (
        not agg_row
        or agg_row["p25_m2"] is None
        or agg_row["p50_m2"] is None
        or agg_row["p75_m2"] is None
    ):
        raise ZoneDataNotFoundError(zone, year)

    mean_row = (
        db.execute(
            text(
                """
                SELECT avg(price_m2) AS mean_price_m2
                FROM price_index
                WHERE zone_id = :zone_id
                  AND extract(year FROM period) = :year
                """
            ),
            {"zone_id": zone_id, "year": year},
        )
        .mappings()
        .first()
    )

    if not mean_row or mean_row["mean_price_m2"] is None:
        raise ZoneDataNotFoundError(zone, year)

    return ZonePriceStats(
        mean_price_m2=float(mean_row["mean_price_m2"]),
        p25_m2=float(agg_row["p25_m2"]),
        p50_m2=float(agg_row["p50_m2"]),
        p75_m2=float(agg_row["p75_m2"]),
        sample_size=int(agg_row["sample_size"] or 0),
    )
