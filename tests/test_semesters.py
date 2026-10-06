import pytest

from saltshaker import get_semester_end, get_semester_nights, get_semester_start


def test_semester_dates():
    """Tests the start and end dates of SALT semesters."""
    # Semester 1 runs May-October, semester 2 November-April.
    assert get_semester_start(2026, 1).iso == '2026-05-01 12:00:00.000'
    assert get_semester_end(2026, 1).iso == '2026-11-01 12:00:00.000'
    assert get_semester_start(2026, 2).iso == '2026-11-01 12:00:00.000'
    assert get_semester_end(2026, 2).iso == '2027-05-01 12:00:00.000'


def test_invalid_semester():
    with pytest.raises(ValueError):
        get_semester_start(2026, 3)
    with pytest.raises(ValueError):
        get_semester_end(2026, 0)

def test_semester_nights():
    """Tests that we can get a list of nights in a semester."""
    nights = get_semester_nights(2026, 1)
    # Semester 1 is May to October (184 days)
    assert 182 <= len(nights) <= 184
    
    # Each night should have a start and end
    for night in nights:
        assert len(night) == 2
        assert night[0] < night[1]
        # Duration should be around 10-14 hours
        duration = (night[1] - night[0]).to('hour').value
        assert 7 < duration < 15
