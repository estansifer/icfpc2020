def mod_int(n):
    if n == 0:
        return '010'
    elif n > 0:
        sign = '01'
    else:
        sign = '10'
        n = -n

    digits = format(n, 'b')
    if (len(digits) % 4) > 0:
        digits = ('0' * (4 - (len(digits) % 4))) + digits
    return sign + ('1' * ((len(digits) + 3) // 4)) + '0' + digits

def mod(o):
    if type(o) is int:
        return mod_int(o)
    else:
        parts = ['11']
        for x in o:
            parts.append(mod(x))
        parts.append('00')
        return ''.join(parts)

def dem(s):
    i = [0]

    def dem_int():
        neg = (s[i[0]] == '1')
        i[0] += 2

        length = 0
        while s[i[0]] == '1':
            length += 4
            i[0] += 1

        i[0] += 1

        if length == 0:
            return 0

        x = int(s[i[0] : i[0] + length], base = 2)
        i[0] += length

        return x

    def dem_list():
        i[0] += 2

        xs = []
        while s[i[0] : i[0] + 2] != '00':
            xs.append(dem_obj())

        i[0] += 2

        return xs

    def dem_obj():
        if s[i[0] : i[0] + 2] == '11':
            return dem_list()
        else:
            return dem_int()

    return dem_obj()

def test(o):
    print(o, mod(o), dem(mod(o)))
