import json
import math as mt
from functools import lru_cache

import numpy as np
from scipy.integrate import solve_ivp
from config import PVT_HOST
from scipy.interpolate import interp1d
import httpx


def calc_pipe(d, h0, h1, incl, temp_grad, pvt, p_in, tvd_res, qliq):
    """
    Расчёт давления на участке трубы

    :param d: диаметр трубы, м
    :param h0: начальная глубина, м
    :param h1: граничная глубина, м
    :param incl: интерполяционный полином инклинометрии
    :param temp_grad:
    :param pvt: словарь с свойствами флюидов
    :param p_in: входное давление в трубу, атм
    :param tvd_res:
    :return: выходное давление из трубы, атм
    """
    tvd_cur = incl(h0).item()

    with httpx.Client() as client:
        result = solve_ivp(
            _calc_grad,
            t_span=(h0, h1),
            y0=[p_in, temp_func(temp_grad, pvt["t_res"], tvd_res, tvd_cur)],
            method="RK23",
            args=(d, temp_grad, pvt, incl, qliq, client))

    return result.y[0][-1]


def _calc_sin_angle(incl, md1: float, md2: float) -> float:
    """
    Расчет синуса угла с горизонталью по интерполяционной функции скважины
    Parameters
    ----------
    :param md1: measured depth 1, м
    :param md2: measured depth 2, м
    :return: синус угла к горизонтали
    """
    return (0 if md2 == md1 else min(
        (incl(md2).item() - incl(md1).item()) / (md2 - md1), 1))


def _calc_angle(incl, md1: float, md2: float) -> float:
    """
    Расчет угла по интерполяционной функции траектории по MD
    Parameters
    ----------
    :param md1: measured depth 1, м
    :param md2: measured depth 2, м
    :return: угол к горизонтали, град
    """
    return (np.degrees(np.arcsin(_calc_sin_angle(incl, md1, md1 + 0.001)))
            if md2 == md1 else np.degrees(np.arcsin(_calc_sin_angle(incl, md1, md2))))


def _grav_gradient(rho_mix, theta_deg):
    return rho_mix * 9.81 * mt.sin(theta_deg / 180 * mt.pi)


def _fric_gradient(ff, rho_mix, vsm, d):
    return ff * rho_mix * vsm ** 2 / (2 * d)


def _calc_vm(qm, d):
    return qm / (mt.pi * d ** 2 / 4)


def _calc_grad(h, pt, d, geotemp_grad, pvt, incl, qliq, client):
    angle = _calc_angle(incl, h, h - 0.0001)

    prms = {
        "P": pt[0],
        "T": pt[1],
        "GammaOil": pvt["gamma_oil"],
        "GammaGas": pvt["gamma_gas"],
        "GammaWat": pvt["gamma_wat"],
        "Wct": pvt["wct"],
        "Rp": pvt["rp"],
        "QLiq": qliq,
    }

    r = client.post(f"http://{PVT_HOST}:8001/calculator", json=prms)
    r = json.loads(r.text)
    qm, rhom, mum = r["QMix"], r['RhoMix'], r['MuMix']
    vsm = _calc_vm(qm, d)
    n_re = _calc_n_re(d, rhom, vsm, mum)

    ff = _calc_ff(n_re, 0.0001)

    dp_dl_fric = _fric_gradient(ff, rhom, vsm, d)

    dp_dl_grav = _grav_gradient(rhom, angle)

    return dp_dl_fric + dp_dl_grav, geotemp_grad / 100


def _calc_n_re(d_m, rho_n_kgm3, vsm_msec, mu_n_cp):
    """
    Вычисление числа Рейнольдса
    Parameters
    ----------
    :param d_m: диаметр трубы, м
    :param rho_n_kgm3: плотность смеси, кг/м3
    :param vsm_msec: скорость смеси, м/с
    :param mu_n_cp: вязкость смеси, сПз
    :return: число Рейнольдса, безразмерн.
    """
    return 1000 * rho_n_kgm3 * vsm_msec * d_m / max(mu_n_cp, 0.000001)


def _calc_ff(n_re, eps):
    if n_re == 0:
        f_n = 0
    elif n_re < 2000:  # ламинарный поток
        f_n = 64 / n_re
    else:

        n_re_save = -1  # флаг для расчета переходного режима
        if n_re <= 4000:
            n_re_save = n_re
            n_re = 4000

        # расcчитываем турбулентный режим
        f_n = (2 *
               mt.log10(0.5405405405405405 * eps - 5.02 / n_re *
                        mt.log10(0.5405405405405405 * eps + 13 / n_re))) ** -2
        i = 0
        while True:
            f_n_new = (1.74 - 2 * mt.log10(2 * eps + 18.7 /
                                           (n_re * f_n ** 0.5))) ** -2
            i = i + 1
            error = abs(f_n_new - f_n) / f_n_new
            f_n = f_n_new
            # stop when error is sufficiently small or max number of iterations exceeded
            if error <= 0.0001 or i > 19:
                break

        if n_re_save > 0:  # переходный режим
            min_re = 2000
            max_re = 4000
            f_turb = f_n
            f_lam = 0.032
            f_n = f_lam + (n_re_save - min_re) * (f_turb - f_lam) / (max_re -
                                                                     min_re)

    return f_n


@lru_cache(maxsize=1024)
def incl_func(inclinometry_md: tuple, inclinometry_tvd: tuple):
    """
    Функция интерполяции инклинометрии
    """
    return interp1d(inclinometry_md,
                    inclinometry_tvd,
                    fill_value='extrapolate')


@lru_cache(maxsize=1024)
def temp_func(temp_grad, t_res, tvd_res, tvd_cur):
    return t_res - temp_grad * (tvd_res - tvd_cur) / 100
