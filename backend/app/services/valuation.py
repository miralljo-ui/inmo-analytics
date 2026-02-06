from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.repository import (
    ZoneDataNotFoundError,
    ZoneNotFoundError,
    get_zone_price_stats,
)
from app.schemas.valuation import ValuationRequest, ValuationResult


@dataclass(frozen=True)
class ZoneStats:
    mean_price_m2: float
    p25_m2: float
    p50_m2: float
    p75_m2: float


def _estimate_zone_stats(db: Session, zona: str, year: int) -> ZoneStats:
    stats = get_zone_price_stats(db, zona, year)
    return ZoneStats(
        mean_price_m2=stats.mean_price_m2,
        p25_m2=stats.p25_m2,
        p50_m2=stats.p50_m2,
        p75_m2=stats.p75_m2,
    )


def _apply_room_adjustment(base_m2: float, rooms: int | None) -> float:
    if rooms is None:
        return base_m2
    if rooms <= 1:
        return base_m2 * 1.05
    if rooms >= 4:
        return base_m2 * 0.97
    return base_m2


def _apply_age_adjustment(base_m2: float, year_built: int | None) -> float:
    if year_built is None:
        return base_m2
    if year_built < 1970:
        return base_m2 * 0.94
    if year_built >= 2010:
        return base_m2 * 1.03
    return base_m2


def estimate_valuation(payload: ValuationRequest, db: Session) -> ValuationResult:
    year = date.today().year
    try:
        stats = _estimate_zone_stats(db, payload.zona, year)
    except ZoneNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zona no encontrada: {exc.zone}",
        ) from exc
    except ZoneDataNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No hay datos para la zona '{exc.zone}' en el año {exc.year}",
        ) from exc

    low_m2 = _apply_room_adjustment(stats.p25_m2, payload.rooms)
    low_m2 = _apply_age_adjustment(low_m2, payload.year_built)

    high_m2 = _apply_room_adjustment(stats.p75_m2, payload.rooms)
    high_m2 = _apply_age_adjustment(high_m2, payload.year_built)

    median_m2 = _apply_room_adjustment(stats.p50_m2, payload.rooms)
    median_m2 = _apply_age_adjustment(median_m2, payload.year_built)

    low = low_m2 * payload.area_m2
    high = high_m2 * payload.area_m2
    estimated = median_m2 * payload.area_m2

    score = max(0.0, min(1.0, (estimated - low) / (high - low) if high > low else 0.5))
    overvalued = estimated > high

    return ValuationResult(
        zona=payload.zona,
        price_range_eur=(round(low, 2), round(high, 2)),
        estimated_price_eur=round(estimated, 2),
        overvalued=overvalued,
        score=round(score, 3),
    )
