from django import template

register = template.Library()


@register.filter
def hc_duration(td):
    total = int(td.total_seconds() / 60)
    total, m = divmod(total, 60)
    total, h = divmod(total, 24)
    o, rem = divmod(total, 30)
    w, d = divmod(rem, 7)

    result = ""
    if o:
        result += "1 month " if w == 0 else "%d months " % w

    if w:
        result += "1 week " if w == 1 else "%d weeks " % w

    if d:
        result += "1 day " if d == 1 else "%d days " % d

    if h:
        result += "1 hour " if h == 1 else "%d hours " % h

    if m:
        result += "1 minute " if m == 1 else "%d minutes " % m

    return result
