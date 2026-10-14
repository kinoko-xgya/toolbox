#!/usr/bin/env python3
"""
kaoyan_countdown.py - 考研倒计时

用法:
    python kaoyan_countdown.py                          # 默认 12月19日开考
    python kaoyan_countdown.py 12-21                    # 自定义日期 MM-DD
    python kaoyan_countdown.py 12-21 2026               # 指定年份
    python kaoyan_countdown.py --weeks                  # 额外显示周数
    python kaoyan_countdown.py --no-banner              # 只输出天数

纯标准库，无第三方依赖。
"""

import argparse
import sys
from datetime import datetime


DEFAULT_DATE = "12-19"  # 历年多在 12 月中下旬，可自行改
EXAM_DAYS = 2


def parse_target(date_str, year=None):
    """从 'MM-DD' 解析目标日期，year 为 None 时自动推算"""
    today = datetime.now().date()
    if year is None:
        y = today.year
        target = datetime.strptime(f"{y}-{date_str}", "%Y-%m-%d").date()
        if target < today:
            y += 1
            target = datetime.strptime(f"{y}-{date_str}", "%Y-%m-%d").date()
    else:
        target = datetime.strptime(f"{year}-{date_str}", "%Y-%m-%d").date()
    return today, target


def progress_bar(pct, width=30):
    filled = int(width * pct)
    return "[" + "#" * filled + "." * (width - filled) + "]"


def main():
    ap = argparse.ArgumentParser(description="考研倒计时")
    ap.add_argument("target", nargs="?", default=DEFAULT_DATE,
                    help="目标日期 MM-DD 或 'MM-DD YYYY'，默认 12-19")
    ap.add_argument("year", nargs="?", type=int, default=None,
                    help="年份，默认自动推算")
    ap.add_argument("--weeks", action="store_true", help="额外显示周数")
    ap.add_argument("--no-banner", action="store_true", help="只输出天数")
    args = ap.parse_args()

    parts = args.target.split()
    date_str = parts[0]
    year = args.year
    if len(parts) > 1 and year is None:
        year = int(parts[1])

    today, target = parse_target(date_str, year)
    days = (target - today).days

    if days < 0:
        print(f"考完了 {abs(days)} 天")
        return

    if not args.no_banner:
        months_left = (target.year - today.year) * 12 + target.month - today.month
        print()
        print("=" * 42)
        print(f"  距考研还有  {target.month}月{target.day}日")
        print(f"  当前日期    {today.strftime('%Y-%m-%d')}")
        print(f"  月份跨度    {months_left} 个月")
        print("=" * 42)
        print()

    # 冲刺期用进度条
    ref_days = 200
    if days <= ref_days:
        pct = days / ref_days
        print(f"  倒计时     {progress_bar(pct)}  {days} 天")
    else:
        print(f"  倒计时     {days} 天  (距离冲刺阶段还很远)")
    print(f"  考试天数   {EXAM_DAYS} 天")

    if args.weeks:
        weeks, rem = divmod(days, 7)
        print(f"  折合       {weeks} 周 {rem} 天")

    if days > 150:
        stage = "早鸟阶段 · 打基础"
    elif days > 90:
        stage = "中期攻坚 · 专业课重点"
    elif days > 45:
        stage = "冲刺阶段 · 政治 + 模拟"
    elif days > 15:
        stage = "最后关头 · 别慌"
    else:
        stage = "上了就完事了"
    print()
    print(f"  阶段提示   {stage}")
    print()


if __name__ == "__main__":
    main()
