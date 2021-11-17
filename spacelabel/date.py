from datetime import timedelta, datetime


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

    return str(
        datetime.fromisoformat(date) + timedelta(
            hours=int(hours), minutes=int(minutes), seconds=float(seconds)
        )
    )
