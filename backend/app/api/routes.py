from fastapi import APIRouter
from app.schemas.valuation import ValuationRequest, ValuationResult
from app.services.valuation import estimate_valuation


router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/valuation/estimate", response_model=ValuationResult)
def valuation_estimate(payload: ValuationRequest) -> ValuationResult:
    return estimate_valuation(payload)
