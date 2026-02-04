from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from app.schemas.valuation import ValuationRequest, ValuationResult


@dataclass(frozen=True)
class ZoneStats:
    median_price_m2: float
    iqr_low_m2: float
    iqr_high_m2: float


DEFAULT_STATS = ZoneStats(median_price_m2=2200.0, iqr_low_m2=1800.0, iqr_high_m2=2600.0)


def _estimate_zone_stats(zona: str) -> ZoneStats:
    _ = zona
    return DEFAULT_STATS


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


def estimate_valuation(payload: ValuationRequest) -> ValuationResult:
    stats = _estimate_zone_stats(payload.zona)

    low_m2 = _apply_room_adjustment(stats.iqr_low_m2, payload.rooms)
    low_m2 = _apply_age_adjustment(low_m2, payload.year_built)

    high_m2 = _apply_room_adjustment(stats.iqr_high_m2, payload.rooms)
    high_m2 = _apply_age_adjustment(high_m2, payload.year_built)

    median_m2 = _apply_room_adjustment(stats.median_price_m2, payload.rooms)
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
