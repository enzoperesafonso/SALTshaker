"""
Core tracking model for the Southern African Large Telescope (SALT).

This module provides the `SaltTrackingModel` class, which encapsulates the 
unique fixed-altitude tracking geometry of SALT. It handles data loading from 
empirical visibility files and provides high-performance interpolation for 
track limits and available track lengths.

The model is designed as a singleton to ensure that the underlying data file 
is only loaded and parsed once per session.
"""

import os
import math

class SaltTrackingModel:
    """
    A mathematical model for SALT's fixed-altitude tracking geometry.
    
    SALT is a fixed-altitude telescope (37° from zenith) that tracks targets 
    using a moving payload (the tracker) at the focal plane. This class 
    models the available tracking time and hour angle limits based on a 
    target's declination.

    Attributes:
        declinations (list[float]): A sorted list of declinations (degrees) 
            available in the empirical data file.
        east_tracks (list[list[dict]]): A list of data points for the eastern 
            (rising) tracks, indexed by declination.
        west_tracks (list[list[dict]]): A list of data points for the western 
            (setting) tracks, indexed by declination.
        UT_TO_ST_FACTOR (float): The conversion factor from Universal Time 
            to Sidereal Time (approx 1.0027379).
    """
    
    _instance = None
    # Conversion factor from Universal Time to sidereal time
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
        self.declinations = []
        self.east_tracks = []
        self.west_tracks = []
        self._read_model()
        self._initialized = True

    def _read_model(self):
        """
        Internal method to read and parse the tracking model data file.
        
        The file 'visDataOrdered.dat' contains triplets of (declination, 
        hour angle, track length).
        """
        data_file = os.path.join(os.path.dirname(__file__), "data", "visDataOrdered.dat")
        
        current_declination = None
        east_track_info = []
        west_track_info = []
        
        with open(data_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                parts = line.split()
                if len(parts) < 3:
                    continue
                    
                declination = float(parts[0])
                hour_angle = float(parts[1])
                track_length = float(parts[2])
                
                if current_declination is None or declination != current_declination:
                    if current_declination is not None:
                        self._finalize_tracks(east_track_info, west_track_info)
                        self.declinations.append(current_declination)
                        self.east_tracks.append(east_track_info)
                        self.west_tracks.append(west_track_info)
                    
                    current_declination = declination
                    east_track_info = []
                    west_track_info = []
                
                tl_info = {'hour_angle': hour_angle, 'track_length': track_length}
                
                # Logic for splitting East/West tracks
                if -62.75 <= declination < -1.75 and hour_angle > 0:
                    west_track_info.append(tl_info)
                else:
                    east_track_info.append(tl_info)
            
            if current_declination is not None:
                self._finalize_tracks(east_track_info, west_track_info)
                self.declinations.append(current_declination)
                self.east_tracks.append(east_track_info)
                self.west_tracks.append(west_track_info)

    def _finalize_tracks(self, east_track_info, west_track_info):
        """
        Internal helper to add end-of-track markers.
        
        Args:
            east_track_info: List of tracking data for the eastern track.
            west_track_info: List of tracking data for the western track.
        """
        if east_track_info:
            last_info = east_track_info[-1]
            end_of_track = last_info['hour_angle'] + self.UT_TO_ST_FACTOR * last_info['track_length'] / 3600.0
            east_track_info.append({'hour_angle': end_of_track, 'track_length': 0.0})
            
        if west_track_info:
            last_info = west_track_info[-1]
            end_of_track = last_info['hour_angle'] + self.UT_TO_ST_FACTOR * last_info['track_length'] / 3600.0
            west_track_info.append({'hour_angle': end_of_track, 'track_length': 0.0})

    def _lower_index_for_value(self, value, values):
        """
        Binary search helper to find the lower interpolation index.

        Args:
            value (float): The value to search for.
            values (list[float]): The sorted list of reference values.

        Returns:
            int: The index `i` such that `values[i] <= value`.

        Raises:
            ValueError: If the value is outside the range of the model.
        """
        if value < values[0] or value > values[-1]:
            raise ValueError(f"The declination {value} lies outside the allowed range from {values[0]} to {values[-1]}")
            
        i = 0
        while i < len(values) and values[i] <= value:
            i += 1
        i -= 1
        if i == len(values) - 1:
            i -= 1
        return i

    def get_east_track(self, declination):
        """
        Calculates the start and end hour angles for the eastern (rising) track.
        
        This method performs linear interpolation between the pre-computed 
        declination points in the tracking model.

        Args:
            declination (float): The target declination in degrees.
            
        Returns:
            tuple[float, float]: A tuple of (start_hour_angle, end_hour_angle) 
                in decimal hours.
        """
        lower_index = self._lower_index_for_value(declination, self.declinations)
        
        east_track1 = self.east_tracks[lower_index]
        east_track2 = self.east_tracks[lower_index + 1]
        west_track1 = self.west_tracks[lower_index]
        west_track2 = self.west_tracks[lower_index + 1]
        
        declination1 = self.declinations[lower_index]
        declination2 = self.declinations[lower_index + 1]
        
        if west_track1 and west_track2:
            start1, end1 = east_track1[0]['hour_angle'], east_track1[-1]['hour_angle']
            start2, end2 = east_track2[0]['hour_angle'], east_track2[-1]['hour_angle']
        elif not west_track1 and west_track2:
            start1, end1 = east_track1[0]['hour_angle'], 0
            start2, end2 = east_track2[0]['hour_angle'], east_track2[-1]['hour_angle']
        elif west_track1 and not west_track2:
            start1, end1 = east_track1[0]['hour_angle'], east_track1[-1]['hour_angle']
            start2, end2 = east_track2[0]['hour_angle'], 0
        else:
            start1, end1 = east_track1[0]['hour_angle'], east_track1[-1]['hour_angle']
            start2, end2 = east_track2[0]['hour_angle'], east_track2[-1]['hour_angle']
            
        fraction = (declination - declination1) / (declination2 - declination1)
        start = start1 + (start2 - start1) * fraction
        end = end1 + (end2 - end1) * fraction
        
        return start, end

    def get_west_track(self, declination):
        """
        Calculates the start and end hour angles for the western (setting) track.
        
        Args:
            declination (float): The target declination in degrees.
            
        Returns:
            tuple[float, float] | None: A tuple of (start_ha, end_ha) in 
                decimal hours, or None if no western track exists for 
                this declination.
        """
        lower_index = self._lower_index_for_value(declination, self.declinations)
        
        east_track1 = self.east_tracks[lower_index]
        east_track2 = self.east_tracks[lower_index + 1]
        west_track1 = self.west_tracks[lower_index]
        west_track2 = self.west_tracks[lower_index + 1]
        
        declination1 = self.declinations[lower_index]
        declination2 = self.declinations[lower_index + 1]
        
        if west_track1 and west_track2:
            start1, end1 = west_track1[0]['hour_angle'], west_track1[-1]['hour_angle']
            start2, end2 = west_track2[0]['hour_angle'], west_track2[-1]['hour_angle']
        elif not west_track1 and west_track2:
            start1, end1 = 0, east_track1[-1]['hour_angle']
            start2, end2 = west_track2[0]['hour_angle'], west_track2[-1]['hour_angle']
        elif west_track1 and not west_track2:
            start1, end1 = west_track1[0]['hour_angle'], west_track1[-1]['hour_angle']
            start2, end2 = 0, east_track2[-1]['hour_angle']
        else:
            return None
            
        fraction = (declination - declination1) / (declination2 - declination1)
        start = start1 + (start2 - start1) * fraction
        end = end1 + (end2 - end1) * fraction
        
        return start, end

    def _track_length_for_hour_angle(self, hour_angle, tl_info_list):
        """
        Calculates the available track length for a specific hour angle.
        
        Internal helper for interpolation within a single declination's track.
        """
        if not tl_info_list: return 0
        if hour_angle < tl_info_list[0]['hour_angle'] or hour_angle >= tl_info_list[-1]['hour_angle']:
            return 0
            
        ha_index = 0
        while ha_index < len(tl_info_list) and tl_info_list[ha_index]['hour_angle'] <= hour_angle:
            ha_index += 1
        ha_index -= 1
        if ha_index == len(tl_info_list) - 1: ha_index -= 1
            
        ha1, tl1 = tl_info_list[ha_index]['hour_angle'], tl_info_list[ha_index]['track_length']
        ha2, tl2 = tl_info_list[ha_index + 1]['hour_angle'], tl_info_list[ha_index + 1]['track_length']
        
        return tl1 + ((tl2 - tl1) / (ha2 - ha1)) * (hour_angle - ha1)

    def track_length(self, declination, hour_angle):
        """
        Returns the available track length (in seconds) for a target.
        
        The result represents how many seconds the tracker can follow the 
        target starting from the given hour angle before reaching the edge 
        of its mechanical limit.

        Args:
            declination (float): The target declination in degrees.
            hour_angle (float): The current hour angle in decimal hours.
            
        Returns:
            float: Available track length in seconds. Returns 0 if the 
                target is currently outside the tracking zone.
        """
        try:
            declination_index = self._lower_index_for_value(declination, self.declinations)
        except ValueError:
            return 0
            
        east_track = self.get_east_track(declination)
        west_track = self.get_west_track(declination)
        
        if west_track:
            if (hour_angle < east_track[0] or 
                (hour_angle > east_track[1] and hour_angle < west_track[0]) or 
                hour_angle > west_track[1]):
                return 0
        else:
            if hour_angle < east_track[0] or hour_angle > east_track[1]:
                return 0
                
        if self.west_tracks[declination_index] and self.west_tracks[declination_index + 1]:
            tl_info_list1 = self.east_tracks[declination_index] if hour_angle < 0 else self.west_tracks[declination_index]
            tl_info_list2 = self.east_tracks[declination_index + 1] if hour_angle < 0 else self.west_tracks[declination_index + 1]
            track_length1 = self._track_length_for_hour_angle(hour_angle, tl_info_list1)
            track_length2 = self._track_length_for_hour_angle(hour_angle, tl_info_list2)
        elif not self.west_tracks[declination_index] and self.west_tracks[declination_index + 1]:
            track_length1 = self._track_length_for_hour_angle(hour_angle, self.east_tracks[declination_index])
            if hour_angle < 0:
                rem = 3600 * (0 - hour_angle) / self.UT_TO_ST_FACTOR
                if rem < track_length1: track_length1 = rem
            
            tl_info_list2 = self.east_tracks[declination_index + 1] if hour_angle < 0 else self.west_tracks[declination_index + 1]
            track_length2 = self._track_length_for_hour_angle(hour_angle, tl_info_list2)
        elif self.west_tracks[declination_index] and not self.west_tracks[declination_index + 1]:
            tl_info_list1 = self.east_tracks[declination_index] if hour_angle < 0 else self.west_tracks[declination_index]
            track_length1 = self._track_length_for_hour_angle(hour_angle, tl_info_list1)
            
            track_length2 = self._track_length_for_hour_angle(hour_angle, self.east_tracks[declination_index + 1])
            if hour_angle < 0:
                rem = 3600 * (0 - hour_angle) / self.UT_TO_ST_FACTOR
                if rem < track_length2: track_length2 = rem
        else:
            track_length1 = self._track_length_for_hour_angle(hour_angle, self.east_tracks[declination_index])
            track_length2 = self._track_length_for_hour_angle(hour_angle, self.east_tracks[declination_index + 1])
            
        d1, d2 = self.declinations[declination_index], self.declinations[declination_index + 1]
        fraction = (declination - d1) / (d2 - d1)
        
        return track_length1 + (track_length2 - track_length1) * fraction

    def get_max_track_length(self, declination):
        """
        Calculates the maximum possible track length for a given declination.
        
        Args:
            declination (float): The target declination in degrees.
            
        Returns:
            float: Maximum track length in seconds. Returns 0 if the 
                declination is never visible at SALT.
        """
        try:
            declination_index = self._lower_index_for_value(declination, self.declinations)
        except ValueError:
            return 0
            
        tl_info_list = []
        for i in [declination_index, declination_index + 1]:
            tl_info_list.extend(self.east_tracks[i])
            tl_info_list.extend(self.west_tracks[i])
        
        hour_angles = [info['hour_angle'] for info in tl_info_list]
        max_track_length = 0
        for ha in hour_angles:
            length = self.track_length(declination, ha)
            if length > max_track_length: max_track_length = length
                
        return max_track_length

def get_model():
    """
    Returns the singleton instance of the SaltTrackingModel.
    
    This is the preferred way to access the model to ensure efficient 
    resource usage.

    Returns:
        SaltTrackingModel: The global singleton instance.
    """
    return SaltTrackingModel()
