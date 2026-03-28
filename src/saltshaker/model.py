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
        
        for dec in self.declinations:
            mask = data[:, 0] == dec
            dec_data = data[mask]
            
            if -62.75 <= dec < -1.75:
                east_mask = dec_data[:, 1] <= 0
                west_mask = dec_data[:, 1] > 0
                
                e_ha = dec_data[east_mask, 1]
                e_tl = dec_data[east_mask, 2]
                w_ha = dec_data[west_mask, 1]
                w_tl = dec_data[west_mask, 2]
                
                self.east_data[dec] = self._finalize_track_arrays(e_ha, e_tl)
                self.west_data[dec] = self._finalize_track_arrays(w_ha, w_tl)
            else:
                self.east_data[dec] = self._finalize_track_arrays(dec_data[:, 1], dec_data[:, 2])
                self.west_data[dec] = (np.array([]), np.array([]))

    def _finalize_track_arrays(self, ha, tl):
        """Helper to add the end-of-track point to NumPy arrays."""
        if len(ha) == 0:
            return np.array([]), np.array([])
            
        end_ha = ha[-1] + self.UT_TO_ST_FACTOR * tl[-1] / 3600.0
        ha_final = np.concatenate([ha, [end_ha]])
        tl_final = np.concatenate([tl, [0.0]])
        
        return ha_final, tl_final

    def _get_track_limits(self, dec):
        """Internal helper to get ha_start and ha_end for both tracks at a specific dec."""
        e_ha, _ = self.east_data[dec]
        w_ha, _ = self.west_data[dec]
        
        e_limits = (e_ha[0], e_ha[-1]) if len(e_ha) > 0 else (None, None)
        w_limits = (w_ha[0], w_ha[-1]) if len(w_ha) > 0 else (None, None)
        
        return e_limits, w_limits

    def get_east_track(self, declination):
        """Calculates the start and end hour angles for the eastern (rising) track."""
        if declination < self.declinations[0] or declination > self.declinations[-1]:
            raise ValueError(f"Declination {declination} out of range.")
            
        idx = np.searchsorted(self.declinations, declination)
        if idx == 0: idx = 1
        if idx == len(self.declinations): idx = len(self.declinations) - 1
            
        dec1, dec2 = self.declinations[idx-1], self.declinations[idx]
        lim1_e, lim1_w = self._get_track_limits(dec1)
        lim2_e, lim2_w = self._get_track_limits(dec2)
        
        if lim1_w[0] is not None and lim2_w[0] is not None:
            s1, e1 = lim1_e
            s2, e2 = lim2_e
        elif lim1_w[0] is None and lim2_w[0] is not None:
            s1, e1 = lim1_e[0], 0.0
            s2, e2 = lim2_e
        elif lim1_w[0] is not None and lim2_w[0] is None:
            s1, e1 = lim1_e
            s2, e2 = lim2_e[0], 0.0
        else:
            s1, e1 = lim1_e
            s2, e2 = lim2_e
            
        frac = (declination - dec1) / (dec2 - dec1)
        return s1 + (s2 - s1) * frac, e1 + (e2 - e1) * frac

    def get_west_track(self, declination):
        """Calculates the start and end hour angles for the western (setting) track."""
        if declination < self.declinations[0] or declination > self.declinations[-1]:
            raise ValueError(f"Declination {declination} out of range.")
            
        idx = np.searchsorted(self.declinations, declination)
        if idx == 0: idx = 1
        if idx == len(self.declinations): idx = len(self.declinations) - 1
                     
        lim1_e, lim1_w = self._get_track_limits(self.declinations[idx-1])
        lim2_e, lim2_w = self._get_track_limits(self.declinations[idx])
        
        if lim1_w[0] is not None and lim2_w[0] is not None:
            s1, e1 = lim1_w
            s2, e2 = lim2_w
        elif lim1_w[0] is None and lim2_w[0] is not None:
            s1, e1 = 0.0, lim1_e[1]
            s2, e2 = lim2_w
        elif lim1_w[0] is not None and lim2_w[0] is None:
            s1, e1 = lim1_w
            s2, e2 = 0.0, lim2_e[1]
        else:
            return None
            
        frac = (declination - self.declinations[idx-1]) / (self.declinations[idx] - self.declinations[idx-1])
        return s1 + (s2 - s1) * frac, e1 + (e2 - e1) * frac

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
            e_ha, e_tl = self.east_data[d]
            w_ha, w_tl = self.west_data[d]
            
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
        ha_peaks = np.concatenate([self.east_data[d1][0], self.west_data[d1][0],
                                   self.east_data[d2][0], self.west_data[d2][0]])
        
        if len(ha_peaks) == 0: return 0.0
        
        # Use vectorized track_length
        lengths = self.track_length(declination, ha_peaks)
        return np.max(lengths)

def get_model():
    """Returns the singleton instance of the SaltTrackingModel."""
    return SaltTrackingModel()
