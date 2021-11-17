from datetime import timedelta, datetime


def float_to_string(val: float) -> str:
    """
    Routine for converting ISO-format floats to strings.

    Arguments:
        val (float): A float in the format YYYYMMDD.HHMMSS[...]
            e.g. 20041231.125959 for one second to midnight, new year's eve 2004

    Returns:
        str: The ISO-format date as a string e.g. "2004-12-31 12:59:59"
    """
    output = f"{val:.6f}"
    return f"{output[0:4]}-{output[4:6]}-{output[6:8]} " \
           f"{output[9:11]}:{output[11:13]}:{output[13:15]}"


def fix_iso_format(val: bytes) -> str:
    """
    Routine for fixing malformed ISO-format date strings.

    Arguments:
        val (bytes): A bytestring in the format YYYY-MM-DD HH:MM:SS.dddd, where HH may be 24, MM and SS may be 60.

    Returns:
        str: The corrected ISO-format date
    """
    date, time = val.decode('utf-8').split(' ')
    hours, minutes, seconds = time.split(':')

    return str(datetime.fromisoformat(date) + timedelta(
        hours=int(hours), minutes=int(minutes), seconds=float(seconds)
    ))
