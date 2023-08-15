from typing import List

from pydantic import BaseModel, Field, confloat, conlist, field_validator


class Inclinometry(BaseModel):
    MD: conlist(item_type=confloat(ge=0)) = Field(
        title="Измеренная по стволу глубина, м")
    TVD: List[confloat(ge=0)] = Field(title="Вертикальная глубина, м")


class Pipeline(BaseModel):
    d: confloat(gt=0) = Field(title="Диаметр трубы, м")


class Tubing(Pipeline):
    h_mes: confloat(gt=0) = Field(title="Глубина спуска НКТ, м")


class PVT(BaseModel):
    wct: confloat(ge=0, le=100) = Field(title="Обводненность, %")
    rp: confloat(ge=0) = Field(title="Газовый фактор, м3/т")
    gamma_oil: confloat(ge=0.6, le=1) = Field(title="Отн. плотность нефти")
    gamma_gas: confloat(ge=0.5, le=1) = Field(title="Отн. плотность газа")
    gamma_wat: confloat(ge=0.98, le=1.2) = Field(title="Отн. плотность воды")
    t_res: confloat(ge=10, le=500) = Field(title="Пластовая температура, C")


class VlpCalcRequest(BaseModel):
    inclinometry: Inclinometry = Field(title="Инклинометрия")
    casing: Pipeline = Field(title="Данные по ЭК")
    tubing: Tubing = Field(title="Данные по НКТ")
    pvt: PVT = Field(title="PVT")
    p_wh: confloat(ge=0) = Field(title="Буферное давление, атм")
    geo_grad: confloat(ge=0) = Field(title="Градиент температуры, C/100 м")
    h_res: confloat(ge=0) = Field(title="Глубина Верхних Дыр Перфорации, м")

    model_config = {
        "json_schema_extra": {
            "example": {
                "inclinometry": {
                    "MD": [0, 1000, 1500],
                    "TVD": [0, 1000, 1100]
                },
                "casing": {
                    "d": 0.1
                },
                "tubing": {
                    "d": 0.062,
                    "h_mes": 1000
                },
                "pvt": {
                    "wct": 50,
                    "rp": 100,
                    "gamma_oil": 0.8,
                    "gamma_gas": 0.7,
                    "gamma_wat": 1,
                    "t_res": 90
                },
                "p_wh": 10,
                "geo_grad": 3,
                "h_res": 1500
            }
        }
    }


class VlpCalcResponse(BaseModel):
    q_liq: List[confloat(ge=0)] = Field(title="Дебиты жидкости, м3/сут")
    p_wf: List[confloat(gt=0)] = Field(title="Забойное давление, атм")

    @field_validator("q_liq", "p_wf")
    @classmethod
    def round_result(cls, v):
        return [round(val, 2) for val in v]

    model_config = {
        "json_schema_extra": {
            "example": {
                "q_liq": [
                    0, 21.05, 42.11, 63.16, 84.21, 105.26, 126.32, 147.37,
                    168.42, 189.47, 210.53, 231.58, 252.63, 273.68, 294.74,
                    315.79, 336.84, 357.89, 378.95, 400
                ],
                "p_wf": [
                    34.94, 15.27, 14.36, 15.18, 17.23, 20.23, 24, 28.41, 33.38,
                    38.86, 44.81, 51.23, 58.1, 65.42, 73.2, 81.44, 90.15,
                    99.33, 109, 119.18
                ]
            }
        }
    }
