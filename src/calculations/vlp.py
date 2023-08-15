import numpy as np
from calculations.well import calc_pwf


async def calc_vlp(inclinometry: dict, casing: dict, tubing: dict, pvt: dict,
             p_wh: float, geo_grad: float, h_res: float):

    q_liq = np.linspace(0.001, 400, 7)
    p_wf = np.empty_like(q_liq)

    for i, ql in enumerate(q_liq):

        p_wf[i] = calc_pwf(inclinometry, casing, tubing, pvt, p_wh, geo_grad,
                           h_res, ql)

    result = {"q_liq": q_liq.tolist(), "p_wf": p_wf.tolist()}

    return result
