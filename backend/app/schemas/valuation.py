from pydantic import BaseModel, Field
from typing import Optional, Tuple


class ValuationRequest(BaseModel):
    zona: str = Field(..., description="Nombre de zona o municipio")
    area_m2: float = Field(..., gt=0)
    rooms: Optional[int] = Field(default=None, ge=0)
    year_built: Optional[int] = Field(default=None, ge=1800)
    lat: Optional[float] = Field(default=None)
    lon: Optional[float] = Field(default=None)


class ValuationResult(BaseModel):
    zona: str
    price_range_eur: Tuple[float, float]
    estimated_price_eur: float
    overvalued: bool
    score: float
    model_version: str = "baseline-0.2"
