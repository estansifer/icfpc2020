import ops

def read_galaxy(infile = '../input/galaxy.txt'):
    symbols = {}
    with open(infile, 'r') as f:
        for line in f:
            line = line.strip()
            if len(line) > 0:
                a, b, c = line.split(maxsplit = 2)

                assert b == '='
                symbols[a] = ops.readexpression(c)

    for s in symbols:
        symbols[s].assign_symbol_references(symbols)
    return symbols


def print_expression(e):
    text = e.tostring()
    if len(text) < 50:
        return text
    else:
        return text[:20] + ' ... ' + text[-20:]

def print_all_symbols(symbols):
    for s in symbols:
        print(s, print_expression(symbols[s]))

def reduce_all_symbols(symbols):
    count = 0

    for s in symbols:
        text = print_expression(symbols[s])
        if symbols[s].reduce():
            print(s, text)
            print('    = ', print_expression(symbols[s]))
            count += 1

    print("Number reductions:", count)

    return count

def repeatedly_reduce(symbols, limit = 20):
    valid = set(symbols.keys())

    for i in range(limit):
        count = 0

        for s in sorted(list(valid)):
            text = print_expression(symbols[s])
            if symbols[s].reduce():
                print(s, text)
                print('    = ', print_expression(symbols[s]))
                count += 1
            else:
                valid.remove(s)

        print("Number of reductions:", count)

        if count == 0:
            break


def test():
    symbols = read_galaxy()
    # reduce_all_symbols(symbols)
    repeatedly_reduce(symbols, 1000)

if __name__ == "__main__":
    test()
