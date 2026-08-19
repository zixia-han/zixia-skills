#!/usr/bin/env python3
"""子夏八字离线排盘入口。输出稳定 JSON，供 Skill 解读。"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "vendor"))

from lunar_python import Solar  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="子夏八字：离线四柱、十神与大运计算")
    parser.add_argument("--date", required=True, help="公历日期 YYYY-MM-DD")
    parser.add_argument("--time", required=True, help="当地钟表时间 HH:MM 或 HH:MM:SS")
    parser.add_argument("--gender", required=True, choices=("female", "male"))
    parser.add_argument("--utc-offset", required=True, type=float, help="出生地 UTC 时差，例如中国为 8")
    parser.add_argument("--time-mode", choices=("clock", "true-solar"), default="clock")
    parser.add_argument("--longitude", type=float, help="真太阳时所需经度，东经为正、西经为负")
    parser.add_argument("--late-zi", choices=("same-day", "next-day"), default="same-day")
    parser.add_argument("--luck-sect", type=int, choices=(1, 2), default=1)
    parser.add_argument("--dayun-count", type=int, default=9)
    return parser.parse_args()


def parse_local_datetime(date_text: str, time_text: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(f"{date_text} {time_text}", fmt)
        except ValueError:
            pass
    raise ValueError("日期时间格式应为 YYYY-MM-DD 和 HH:MM（或 HH:MM:SS）")


def equation_of_time_minutes(dt: datetime) -> float:
    """NOAA 近似均时差；用于传统真太阳时校正，非天文测量用途。"""
    day = dt.timetuple().tm_yday
    gamma = 2 * math.pi / 365 * (day - 1 + (dt.hour - 12) / 24)
    return 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma)
        - 0.040849 * math.sin(2 * gamma)
    )


def adjusted_datetime(dt: datetime, mode: str, longitude: float | None, utc_offset: float) -> tuple[datetime, float]:
    if mode == "clock":
        return dt, 0.0
    if longitude is None:
        raise ValueError("time-mode=true-solar 时必须提供 --longitude")
    standard_meridian = utc_offset * 15.0
    correction = 4.0 * (longitude - standard_meridian) + equation_of_time_minutes(dt)
    return dt + timedelta(minutes=correction), correction


def pillar(ec, prefix: str) -> dict:
    get = lambda suffix: getattr(ec, f"get{prefix}{suffix}")()
    hidden = list(get("HideGan"))
    hidden_gods = list(get("ShiShenZhi"))
    return {
        "ganzhi": get(""),
        "stem": get("Gan"),
        "branch": get("Zhi"),
        "wuxing": get("WuXing"),
        "nayin": get("NaYin"),
        "stem_ten_god": get("ShiShenGan"),
        "hidden_stems": [
            {"stem": stem, "ten_god": god} for stem, god in zip(hidden, hidden_gods)
        ],
        "growth_stage": get("DiShi"),
    }


def main() -> int:
    args = parse_args()
    try:
        clock_dt = parse_local_datetime(args.date, args.time)
        used_dt, correction = adjusted_datetime(clock_dt, args.time_mode, args.longitude, args.utc_offset)
        solar = Solar.fromYmdHms(
            used_dt.year, used_dt.month, used_dt.day, used_dt.hour, used_dt.minute, used_dt.second
        )
        lunar = solar.getLunar()
        ec = lunar.getEightChar()
        ec.setSect(2 if args.late_zi == "same-day" else 1)
        gender_value = 0 if args.gender == "female" else 1
        yun = ec.getYun(gender_value, args.luck_sect)
        dayun = []
        for item in yun.getDaYun(args.dayun_count):
            if item.getIndex() == 0:
                continue
            dayun.append(
                {
                    "index": item.getIndex(),
                    "ganzhi": item.getGanZhi(),
                    "start_year": item.getStartYear(),
                    "end_year": item.getEndYear(),
                    "start_age_nominal": item.getStartAge(),
                    "end_age_nominal": item.getEndAge(),
                    "years": [
                        {"year": y.getYear(), "age_nominal": y.getAge(), "ganzhi": y.getGanZhi()}
                        for y in item.getLiuNian()
                    ],
                }
            )
        result = {
            "ok": True,
            "engine": {"name": "lunar_python", "version": "1.4.8", "license": "MIT"},
            "calculation": {
                "input_clock": clock_dt.isoformat(sep=" "),
                "input_used": used_dt.isoformat(sep=" "),
                "time_mode": args.time_mode,
                "true_solar_correction_minutes": round(correction, 3),
                "utc_offset_hours": args.utc_offset,
                "longitude": args.longitude,
                "late_zi_rule": args.late_zi,
                "luck_sect": args.luck_sect,
            },
            "calendar": {
                "solar": solar.toYmdHms(),
                "lunar": lunar.toString(),
                "year_shengxiao": lunar.getYearShengXiaoExact(),
            },
            "pillars": {
                "year": pillar(ec, "Year"),
                "month": pillar(ec, "Month"),
                "day": pillar(ec, "Day"),
                "time": pillar(ec, "Time"),
            },
            "day_master": {"stem": ec.getDayGan(), "wuxing": ec.getDayWuXing()[0]},
            "auxiliary": {
                "tai_yuan": ec.getTaiYuan(),
                "ming_gong": ec.getMingGong(),
                "shen_gong": ec.getShenGong(),
                "year_xunkong": ec.getYearXunKong(),
                "day_xunkong": ec.getDayXunKong(),
            },
            "luck": {
                "direction": "forward" if yun.isForward() else "backward",
                "start_after": {
                    "years": yun.getStartYear(),
                    "months": yun.getStartMonth(),
                    "days": yun.getStartDay(),
                    "hours": yun.getStartHour(),
                },
                "start_solar": yun.getStartSolar().toYmdHms(),
                "dayun": dayun,
            },
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
