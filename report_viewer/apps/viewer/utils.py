"""Uitility functions for report viewer"""
from datetime import date

SHOW_WARNING_START_DATE: date = date(2023, 7, 3)
SHOW_WARNING_END_DATE: date = date(2023, 7, 21)


def show_warning() -> bool:
    today: date = date.today()
    return today >= SHOW_WARNING_START_DATE and today <= SHOW_WARNING_END_DATE
