from datetime import date


def year(request):
    date_today = date.today()
    return {'year': date_today.year}
