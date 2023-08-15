from fastapi import APIRouter
from schemas.base import VlpCalcResponse, VlpCalcRequest
from calculations.vlp import calc_vlp
from config import DEBUG
import json
from pathlib import Path

router = APIRouter(prefix="/vlp", tags=["VLP"])


@router.post("/calculator")
async def calculate_vlp(vlp_in: VlpCalcRequest) -> VlpCalcResponse:
    data = vlp_in.model_dump()

    if DEBUG == '0':
        return await calc_vlp(**data)

    with open(Path('test_data/test_response.json')) as f:
        ans = json.load(f)
    return ans
