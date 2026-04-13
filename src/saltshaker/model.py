"""
Core tracking model for the Southern African Large Telescope (SALT).

This module provides the `SaltTrackingModel` class, which encapsulates the 
unique fixed-altitude tracking geometry of SALT. It handles data loading from 
empirical visibility files and provides high-performance interpolation for 
track limits and available track lengths using NumPy.

The model is designed as a singleton to ensure that the underlying data file 
is only loaded and parsed once per session.
"""

import os
import numpy as np

class SaltTrackingModel:
    """
    A mathematical model for SALT's fixed-altitude tracking geometry.
    
    SALT is a fixed-altitude telescope (37° from zenith) that tracks targets 
    using a moving payload (the tracker) at the focal plane. This class 
    models the available tracking time and hour angle limits based on a 
    target's declination.

    Attributes:
        declinations (np.ndarray): A sorted array of declinations (degrees) 
            available in the empirical data file.
        UT_TO_ST_FACTOR (float): The conversion factor from Universal Time 
            to Sidereal Time (approx 1.0027379).
    """
    
    _instance = None
    UT_TO_ST_FACTOR = 1.00273790935
    
    def __new__(cls):
        """Implements the singleton pattern for SaltTrackingModel."""
        if cls._instance is None:
            cls._instance = super(SaltTrackingModel, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        Initializes the model.
        
        Loads empirical visibility data from 'data/visDataOrdered.dat' if 
        the singleton instance hasn't been initialized yet.
        """
        if self._initialized:
            return
            
        self._load_data()
        self._initialized = True

    def _load_data(self):
        """
        Internal method to read and parse the tracking model data file using NumPy.
        """
        data_file = os.path.join(os.path.dirname(__file__), "data", "visDataOrdered.dat")
        
        # Load the data: Dec (0), HA (1), Track Length (2)
        data = np.loadtxt(data_file, usecols=(0, 1, 2))
        
        self.declinations = np.unique(data[:, 0])
        self.east_data = {}  # {dec: (ha_array, tl_array)}
        self.west_data = {}  # {dec: (ha_array, tl_array)}
        
        # Pre-allocate arrays for vectorized limit lookup
        self.e_start = np.zeros_like(self.declinations)
        self.e_end = np.zeros_like(self.declinations)
        self.w_start = np.full_like(self.declinations, np.nan)
        self.w_end = np.full_like(self.declinations, np.nan)

        for i, dec in enumerate(self.declinations):
            mask = data[:, 0] == dec
            dec_data = data[mask]
            dec_key = float(dec)
            
            if -62.75 <= dec < -1.75:
                east_mask = dec_data[:, 1] <= 0
                west_mask = dec_data[:, 1] > 0
                
                e_ha, e_tl = self._finalize_track_arrays(dec_data[east_mask, 1], dec_data[east_mask, 2])
                w_ha, w_tl = self._finalize_track_arrays(dec_data[west_mask, 1], dec_data[west_mask, 2])
                
                self.east_data[dec_key] = (e_ha, e_tl)
                self.west_data[dec_key] = (w_ha, w_tl)
                
                self.e_start[i], self.e_end[i] = e_ha[0], e_ha[-1]
                self.w_start[i], self.w_end[i] = w_ha[0], w_ha[-1]
            else:
                e_ha, e_tl = self._finalize_track_arrays(dec_data[:, 1], dec_data[:, 2])
                self.east_data[dec_key] = (e_ha, e_tl)
                self.west_data[dec_key] = (np.array([]), np.array([]))
                
                self.e_start[i], self.e_end[i] = e_ha[0], e_ha[-1]
                # w_start/end remain NaN

    def _finalize_track_arrays(self, ha, tl):
        """Helper to add the end-of-track point to NumPy arrays."""
        if len(ha) == 0:
            return np.array([]), np.array([])
            
        end_ha = ha[-1] + self.UT_TO_ST_FACTOR * tl[-1] / 3600.0
        ha_final = np.concatenate([ha, [end_ha]])
        tl_final = np.concatenate([tl, [0.0]])
        
        return ha_final, tl_final

    def get_east_track(self, declination):
        """Calculates the start and end hour angles for the eastern (rising) track."""
        dec = np.asarray(declination)
        if np.any(dec < self.declinations[0]) or np.any(dec > self.declinations[-1]):
            if np.isscalar(declination):
                raise ValueError(f"Declination {declination} out of range.")
            # For arrays, we could return NaNs or handle it, but following original logic:
            dec = np.clip(dec, self.declinations[0], self.declinations[-1])
            
        s = np.interp(dec, self.declinations, self.e_start)
        e = np.interp(dec, self.declinations, self.e_end)
        
        return (float(s), float(e)) if np.isscalar(declination) else (s, e)

    def get_west_track(self, declination):
        """Calculates the start and end hour angles for the western (setting) track."""
        dec = np.asarray(declination)
        
        # Mask for declinations that HAVE a west track (not NaN in our pre-calculated arrays)
        has_west = ~np.isnan(self.w_start)
        if not np.any(has_west):
            return None if np.isscalar(declination) else (np.zeros_like(dec)*np.nan, np.zeros_like(dec)*np.nan)

        valid_decs = self.declinations[has_west]
        valid_w_start = self.w_start[has_west]
        valid_w_end = self.w_end[has_west]
        
        # Check if requested decs are within the range that HAS a west track
        # Outside this range, they might still be valid declinations but only have an east track
        mask_in_range = (dec >= valid_decs[0]) & (dec <= valid_decs[-1])
        
        res_s = np.full_like(dec, np.nan, dtype=float)
        res_e = np.full_like(dec, np.nan, dtype=float)
        
        if np.any(mask_in_range):
            res_s[mask_in_range] = np.interp(dec[mask_in_range], valid_decs, valid_w_start)
            res_e[mask_in_range] = np.interp(dec[mask_in_range], valid_decs, valid_w_end)
            
        if np.isscalar(declination):
            return (float(res_s), float(res_e)) if not np.isnan(res_s) else None
        return res_s, res_e

    def track_length(self, declination, hour_angle):
        """
        Returns the available track length (in seconds) for a target.
        Supports scalar or NumPy array inputs for hour_angle.
        """
        ha = np.asarray(hour_angle)
        
        if declination < self.declinations[0] or declination > self.declinations[-1]:
            return np.zeros_like(ha, dtype=float) if not np.isscalar(hour_angle) else 0.0
            
        idx = np.searchsorted(self.declinations, declination)
        if idx == 0: idx = 1
        if idx == len(self.declinations): idx = len(self.declinations) - 1
        
        dec1, dec2 = self.declinations[idx-1], self.declinations[idx]
        
        def get_tl_at_dec(d, ha_in):
            # Ensure d is a hashable scalar
            d_key = float(d)
            e_ha, e_tl = self.east_data[d_key]
            w_ha, w_tl = self.west_data[d_key]
            
            # This handles both scalars and arrays
            res = np.zeros_like(ha_in, dtype=float)
            
            # Logic for East track
            east_mask = (ha_in <= 0) | (len(w_ha) == 0)
            if len(e_ha) > 0:
                valid_e = (ha_in >= e_ha[0]) & (ha_in <= e_ha[-1]) & east_mask
                if np.any(valid_e):
                    res[valid_e] = np.interp(ha_in[valid_e], e_ha, e_tl) if not np.isscalar(ha_in) else np.interp(ha_in, e_ha, e_tl)
            
            # Logic for West track
            if len(w_ha) > 0:
                west_mask = (ha_in > 0)
                valid_w = (ha_in >= w_ha[0]) & (ha_in <= w_ha[-1]) & west_mask
                if np.any(valid_w):
                    res[valid_w] = np.interp(ha_in[valid_w], w_ha, w_tl) if not np.isscalar(ha_in) else np.interp(ha_in, w_ha, w_tl)
            
            return res

        # Interpolate between decs
        tl1 = get_tl_at_dec(dec1, ha)
        tl2 = get_tl_at_dec(dec2, ha)
        
        # Clipping logic for Zenith hole transition
        if np.any(ha < 0):
            rem_time = 3600.0 * (0.0 - ha) / self.UT_TO_ST_FACTOR
            mask_neg = ha < 0
            if -62.75 <= dec1 < -1.75 and not (-62.75 <= dec2 < -1.75):
                tl2[mask_neg] = np.minimum(tl2[mask_neg], rem_time[mask_neg])
            elif not (-62.75 <= dec1 < -1.75) and -62.75 <= dec2 < -1.75:
                tl1[mask_neg] = np.minimum(tl1[mask_neg], rem_time[mask_neg])

        frac = (declination - dec1) / (dec2 - dec1)
        result = tl1 + (tl2 - tl1) * frac
        
        return result if not np.isscalar(hour_angle) else float(result)

    def get_max_track_length(self, declination):
        """Calculates the maximum possible track length for a given declination."""
        if declination < self.declinations[0] or declination > self.declinations[-1]:
            return 0.0
            
        idx = np.searchsorted(self.declinations, declination)
        if idx == 0: idx = 1
        if idx == len(self.declinations): idx = len(self.declinations) - 1
        
        d1, d2 = self.declinations[idx-1], self.declinations[idx]
        ha_peaks = np.concatenate([self.east_data[float(d1)][0], self.west_data[float(d1)][0],
                                   self.east_data[float(d2)][0], self.west_data[float(d2)][0]])
        
        if len(ha_peaks) == 0: return 0.0
        
        # Use vectorized track_length
        lengths = self.track_length(declination, ha_peaks)
        return np.max(lengths)

def get_model():
    """Returns the singleton instance of the SaltTrackingModel."""
    return SaltTrackingModel()
