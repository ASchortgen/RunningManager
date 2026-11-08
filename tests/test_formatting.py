"""Copyright (C) 2025 Pierre Marrec
SPDX-License-Identifier: GPL-3.0-or-later
"""

from utils.formatting import (
    fmt_decimal,
    fmt_km,
    fmt_m,
    fmt_speed_kmh,
    pace_min_km_to_speed_kmh,
    set_locale,
    speed_kmh_to_pace_min_km,
    to_str_storage,
)


def test_fr_formatting():
    set_locale("fr_FR")
    s = fmt_decimal(1234.5)
    # Normalize NBSP (\u00A0) and NNBSP (\u202F) to regular space for assertion
    normalized = s.replace("\u00a0", " ").replace("\u202f", " ")
    assert normalized == "1 234,5"
    assert fmt_km(12.3).endswith("km")
    assert "," in fmt_km(12.3)
    assert fmt_m(350).endswith("m")
    assert fmt_speed_kmh(9.4).endswith("km/h")
    assert to_str_storage(12.3) == "12.3"


def test_speed_and_pace_conversions():
    assert speed_kmh_to_pace_min_km(12.0) == 5.0
    assert pace_min_km_to_speed_kmh(5.0) == 12.0
    assert speed_kmh_to_pace_min_km(0.0) is None
    assert pace_min_km_to_speed_kmh(0.0) == 0.0
    assert speed_kmh_to_pace_min_km(float("nan")) is None
    assert pace_min_km_to_speed_kmh(float("nan")) == 0.0


def test_threshold_pace_range_round_trips_without_swapping_meaning():
    speed_min_kmh = 8.0
    speed_max_kmh = 12.0

    pace_min = speed_kmh_to_pace_min_km(speed_max_kmh)
    pace_max = speed_kmh_to_pace_min_km(speed_min_kmh)

    assert pace_min == 5.0
    assert pace_max == 7.5
    assert pace_min_km_to_speed_kmh(pace_max) == speed_min_kmh
    assert pace_min_km_to_speed_kmh(pace_min) == speed_max_kmh
