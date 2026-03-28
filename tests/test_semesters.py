import pytest
from saltshaker import get_semester_start, get_semester_end, get_semester_nights
from astropy.time import Time

def test_semester_dates():
    """Tests the start and end dates of SALT semesters."""
    # Semester 1, 2026
    s1_start = get_semester_start(2026, 1)
    s1_end = get_semester_end(2026, 1)
    assert s1_start.iso == '2026-03-01 12:00:00.000'
    assert s1_end.iso == '2026-10-01 12:00:00.000'
    
    # Semester 2, 2026
    s2_start = get_semester_start(2026, 2)
    s2_end = get_semester_end(2026, 2)
    assert s2_start.iso == '2026-10-01 12:00:00.000'
    assert s2_end.iso == '2027-03-01 12:00:00.000'

def test_semester_nights():
    """Tests that we can get a list of nights in a semester."""
    nights = get_semester_nights(2026, 1)
    # Semester 1 is March to September (approx 214 days)
    assert 210 <= len(nights) <= 220
    
    # Each night should have a start and end
    for night in nights:
        assert len(night) == 2
        assert night[0] < night[1]
        # Duration should be around 10-14 hours
        duration = (night[1] - night[0]).to('hour').value
        assert 8 < duration < 15
