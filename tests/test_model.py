import astropy.units as u
import numpy as np
import pytest
from astropy.coordinates import SkyCoord
from astropy.time import Time

from saltshaker import get_model, get_salt_observer, get_track_length, is_target_observable


def test_track_length_array_inputs_match_scalar():
    m = get_model()
    decs = np.array([-30.0, -40.0, -50.0])
    has = np.array([-2.5, 0.0, 1.5])
    arr = m.track_length(decs, has)
    assert arr.shape == (3,)
    for d, h, v in zip(decs, has, arr):
        assert m.track_length(float(d), float(h)) == pytest.approx(v)
    # ha array, scalar dec
    assert m.track_length(-30.0, np.array([-2.5, 1.5])).shape == (2,)


def test_track_length_zero_outside_range_and_in_zenith_hole():
    m = get_model()
    assert m.track_length(50.0, 0.0) == 0.0
    assert m.track_length(-30.0, -1.0) == 0.0


def test_east_track_scalar_error_mentions_range():
    with pytest.raises(ValueError, match="observable range"):
        get_model().get_east_track(50.0)


def test_east_track_array_is_nan_out_of_range():
    s, e = get_model().get_east_track(np.array([-30.0, 50.0]))
    assert np.isfinite(s[0]) and np.isnan(s[1]) and np.isnan(e[1])


@pytest.mark.parametrize("dec", [-76.0, 11.25])
def test_range_edges_observable(dec):
    assert is_target_observable(dec)
    assert get_model().get_max_track_length(dec) > 0


def test_is_target_observable_input_types(polaris):
    assert is_target_observable(-30) is True
    assert is_target_observable([-30, 50]).tolist() == [True, False]
    assert is_target_observable(np.array([-90.0, -76.0])).tolist() == [False, True]
    assert is_target_observable(-30 * u.deg)
    assert not is_target_observable(polaris)


def test_get_track_length_time_array(sirius):
    times = Time('2026-01-15 12:00:00') + np.arange(0, 24, 0.5) * u.hour
    lengths = get_track_length(sirius, times)
    assert lengths.shape == times.shape
    assert lengths.unit == u.second
    assert (lengths > 0).any() and (lengths == 0).any()
    # consistent with scalar call
    i = int(np.argmax(lengths.value))
    assert get_track_length(sirius, times[i]).value == pytest.approx(lengths[i].value)
    assert get_salt_observer().track_length(sirius, times[i]).value == pytest.approx(lengths[i].value)


def test_get_track_length_many_targets_one_time():
    targets = SkyCoord(ra=[0, 100, 200] * u.deg, dec=[-30, -40, 50] * u.deg)
    out = get_track_length(targets, Time('2026-01-15 20:00:00'))
    assert out.shape == (3,)
    assert out[2].value == 0
