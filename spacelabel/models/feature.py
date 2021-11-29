from datetime import datetime
from numpy import ndarray, datetime64
from time import mktime


class Feature:
    """
    A 'feature' from the observational data, which is described by a polygon on the time-flux plane.
    """
    _name: str = None
    _time: ndarray = None
    _freq: ndarray = None
    _id: int = None

    def __init__(self, name:str, time: ndarray, freq: ndarray, id: int):
        self._name = name
        self._time = time
        self._freq = freq
        self._id = id

    def to_text_summary(self) -> str:
        """
        Writes a summary of the feature's extent to text.
        :return: A string containing the feature name, and its maximum and minimum bounds in the time-flux plane
        """
        return f"{self._name}, {min(self._time)}, {max(self._time)}, {min(self._freq)}, {max(self._freq)}"

    def to_tfcat_dict(self) -> dict:
        """
        Expresses the polygon in the form of a dictionary containing a TFCat feature.
        :return: A dictionary *without* ID (which will need to be set separately)
            Times are returned in Unix time, not calendar time, via the mktime function
        """
        return {
            "type": "Feature",
            "id": self._id,
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    (float(mktime(time.timetuple())), freq) for time, freq in zip(self._time, self._freq)
                ]
            },
            "properties": {
                "feature_type": self._name
            }
        }

    def is_in_time_range(self, time_start: datetime, time_end: datetime) -> bool:
        """
        Whether or not the feature is within this time range. Converts dates to numpy format internally.
        :param time_start: The start of the time range (inclusive)
        :param time_end: The end of the time range (inclusive)
        :return: Whether or not the time range contains this feature
        """
        return (self._time[0] <= datetime64(time_start)) & (datetime64(time_end) <= self._time[-1])
