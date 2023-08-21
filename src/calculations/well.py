from calculations.pipe import calc_pipe, incl_func
from copy import deepcopy

def _convert_temperature(t, current, aim):
    if current == "C":
        t = t + 273.15

    if aim == "C":
        t = t - 273.15

    return t


def _convert_pressure(p, current, aim):
    if current == "atm":
        p *= 101325

    if aim == "atm":
        p /= 101325

    return p


def calc_pwf(inclinometry: dict, casing: dict, tubing: dict, pvt: dict,
             p_wh: float, geo_grad: float, h_res: float,
             q_liq: float) -> float:
    """
    Расчёт забойного давления в скважине

    :param inclinometry: словарь с инклинометрией
    :param casing: словарь с данными по ЭК
    :param tubing: словарь с данными по НКТ
    :param pvt: словарь с свойствами флюидов
    :param p_wh: буферное давление, атм
    :param geo_grad: геотермический градиент, C/100 м
    :param h_res: глубина верхних дыр перфорации
    :return: забойное давление, атм
    """
    copy_pvt = deepcopy(pvt)
    copy_pvt["t_res"] = _convert_temperature(copy_pvt["t_res"], "C", "K")
    p_wh = _convert_pressure(p_wh, "atm", "pa")
    copy_pvt["wct"] = copy_pvt["wct"] / 100

    # Интерполяционный полином инклинометрии
    incl = incl_func(tuple(inclinometry["MD"]), tuple(inclinometry["TVD"]))

    # Расчёт давления на приеме (конце НКТ)
    p_in = calc_pipe(tubing["d"], 0, tubing["h_mes"], incl, geo_grad, copy_pvt,
                     p_wh,
                     incl(h_res).item(), q_liq)

    # Расчёт забойного давления
    p_wf = calc_pipe(casing["d"], tubing["h_mes"], h_res, incl, geo_grad, copy_pvt,
                     p_in,
                     incl(h_res).item(), q_liq)
    return _convert_pressure(p_wf, 'pa', 'atm')
