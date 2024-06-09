def validate_time(time):
    time_len = len(time.split(':'))
    if not time_len == 2:
        return False
    
    hours, minutes = time.split(':')

    if not (
        len(hours) == 2
        and len(minutes) == 2
    ):
        return False
    
    return True