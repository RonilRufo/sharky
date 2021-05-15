def month_difference(date1, date2):
    """
    Returns the month difference between two dates.
    """
    return ((date1.year - date2.year) * 12) + (date1.month - date2.month)
