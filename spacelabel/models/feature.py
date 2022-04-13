import logging

import numpy

from astropy.time import Time
from numpy import ndarray
from shapely.geometry import LinearRing
from typing import List, Tuple, Optional

log = logging.getLogger(__name__)


class Feature:
    """
    A named 'feature' from the observational data, which is described by a polygon on the time-flux plane.
    """
    _name: str = None
    _time: Time = None
    _freq: ndarray = None
    _id: int = None

    def __init__(
            self, name: str,
            vertexes: List[Tuple[Time, float]],
            feature_id: int,
            log_level: Optional[int] = None
    ):
        """
        Initialize the feature.

        :param name: The name of the feature
        :param vertexes: The time-flux pairs of the vertexes defining it
        :param feature_id: The internal ID number for the feature
        :param log_level: The level of logging to show. Inherited from DataSet
        """
        self._name = name
        self._id = feature_id
        self._time = Time([vertex[0] for vertex in vertexes])
        self._freq = numpy.array([vertex[1] for vertex in vertexes])

        if log_level:
            log.setLevel(log_level)

    def to_text_summary(self) -> str:
        """
        Writes a summary of the feature's extent to text.

        :return: A string containing the feature name, and its maximum and minimum bounds in the time-flux plane
        """
        return f"{self._name}, {min(self._time)}, {max(self._time)}, {min(self._freq)}, {max(self._freq)}"

    def to_tfcat_dict(self) -> dict:
        """
        Expresses the polygon in the form of a dictionary containing a TFCat feature.

        :return: A dictionary. Times are returned as Unix time, not calendar time
        """
        coordinates = [
            (time.unix, freq) for time, freq in zip(self._time, self._freq)
        ]


        # TFcat format is counter-clockwise, so invert if our co-ordinates are not
        if not LinearRing(coordinates).is_ccw:
            coordinates = coordinates[::-1]

        return {
            "type": "Feature",
            "id": self._id,
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    coordinates
                ]
            },
            "properties": {
                "feature_type": self._name
            }
        }

    def is_in_time_range(self, time_start: Time, time_end: Time) -> bool:
        """
        Whether the feature is within this time range.

        :param time_start: The start of the time range (inclusive)
        :param time_end: The end of the time range (inclusive)
        :return: Whether the time range contains any part of this feature
        """
        return (time_start <= self._time.min() <= time_end) or (time_start <= self._time.max() <= time_end)

    def vertexes(self) -> List[Tuple[Time, float]]:
        """
        Returns the vertexes of the polygon as a list of tuples of time-frequency points.

        :return: List of vertexes as (time, frequency)
        """
        return [
            (time, freq) for time, freq in zip(self._time, self._freq)
        ]

    def arrays(self) -> Tuple[Time, ndarray]:
        """
        Returns the arrays of the poly co-ordinates

        :return: The co-ordinates in seperated arrays
        """
        return (
            self._time, self._freq
        )
