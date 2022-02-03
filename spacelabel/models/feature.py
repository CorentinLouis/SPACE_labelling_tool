import numpy

from astropy.time import Time
from matplotlib.dates import num2julian
from numpy import ndarray, datetime64
from typing import List, Tuple


class Feature:
    """
    A named 'feature' from the observational data, which is described by a polygon on the time-flux plane.
    """
    _name: str = None
    _time: Time = None
    _freq: ndarray = None
    _id: int = None

    def __init__(self, name: str, vertexes: List[Tuple[float, float]], id: int):
        """
        Initialise the feature.
        :param name: The name of the feature.
        :param vertexes: The time-flux pairs of the vertexes defining it.
        :param id: The internal ID number for the feature.
        """
        self._name = name
        self._id = id
        self._time = Time(
            num2julian(numpy.array([vertex[0] for vertex in vertexes])), format='jd'
        )
        self._freq = numpy.array([vertex[1] for vertex in vertexes])

    def to_text_summary(self) -> str:
        """
        Writes a summary of the feature's extent to text.
        :return: A string containing the feature name, and its maximum and minimum bounds in the time-flux plane
        """
        return f"{self._name}, {min(self._time)}, {max(self._time)}, {min(self._freq)}, {max(self._freq)}"

    def to_tfcat_dict(self) -> dict:
        """
        Expresses the polygon in the form of a dictionary containing a TFCat feature.
        :return: A dictionary. Times are returned as Unix time, not calendar time.
        """
        return {
            "type": "Feature",
            "id": self._id,
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    (time.unix, freq) for time, freq in zip(self._time, self._freq)
                ]
            },
            "properties": {
                "feature_type": self._name
            }
        }

    def is_in_time_range(self, time_start: Time, time_end: Time) -> bool:
        """
        Whether or not the feature is within this time range.

        :param time_start: The start of the time range (inclusive)
        :param time_end: The end of the time range (inclusive)
        :return: Whether or not the time range contains any part of this feature
        """
        return (time_start <= self._time.min() <= time_end) or (time_start <= self._time.max() <= time_end)

    def vertexes(self) -> List[Tuple[datetime64, float]]:
        """Returns the vertexes of the polygon as a list of tuples of time-frequency points."""
        return [
            (time.datetime64, freq) for time, freq in zip(self._time, self._freq)
        ]