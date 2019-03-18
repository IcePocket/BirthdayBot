from datetime import datetime
from re import search

# Validation functions

# Checks if a year is a leap year
def leap_year(year):
    if year % 4 == 0:
        if year % 100 == 0:
            if year % 400 == 0:
                return True
            else:
                return False
        else:
            return True
    else:
        return False

# Checks if the string is a Discord channel mention
def channel_mention(s):
	return bool(search(r'<#\d{18}>', s))

# Checks if the parameters form a valid date
def valid_date(year, month, day):
    if (not 1940 <= year <= datetime.now().year - 5) or (not 1 <= month <= 12) or (not 1 <= day <= 31):
        return False
    elif month in [4, 6, 9, 11] and day > 30:
        return False
    elif month == 2 and (day > 29 or (day == 29 and not leap_year(year))):
        return False
    return True

def upcoming_birthday(date):
    now = datetime.now(tz=date.tzinfo)

    if date < now:
        return False

    return (date - now).days <= 30

def recent_birthday(date):
    now = datetime.now(tz=date.tzinfo)

    if date > now:
        return False

    return (now - date).days <= 30

def all_are_integers(args):
    for arg in args:
        if not arg.isdigit():
            return False
    return True