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
        ops.assign_symbol_references(symbols[s], symbols)
    return symbols


def print_expression(e, M = 185):
    text = ops.tostring(e)
    if len(text) < M:
        return text
    else:
        return text[:(M // 2)] + ' ... ' + text[-(M // 2):] + ' [' + str(len(text)) + ']'

def print_all_symbols(symbols):
    for s in symbols:
        print(s, print_expression(symbols[s]))

def reduce_all_symbols(symbols):
    count = 0

    for s in symbols:
        text = print_expression(symbols[s])
        print(s, text)
        if ops.reducer.reduce(symbols[s]):
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
            if ops.reducer.reduce(symbols[s]):
                print(s, text)
                print('    = ', print_expression(symbols[s]))
                count += 1
            else:
                valid.remove(s)

        print("Number of reductions:", count)

        if count == 0:
            break

def evaluate_galaxy():
    symbols = read_galaxy('../input/ap_galaxy.txt')

    # result0 = ap ap galaxy nil ap ap cons 0 0
    s = symbols['result0']
    print(print_expression(s, 5000))
    while ops.reducer.reduce(s):
        print(print_expression(s, 5000))

def test():
    symbols = read_galaxy() #'../input/test.txt')
    d = {
            ':1096' : symbols[':1096'],
            ':1199' : symbols[':1199'],
            ':1201' : symbols[':1201'],
            ':1202' : symbols[':1202']
            }
    print_all_symbols(symbols)
    repeatedly_reduce(symbols, 1000)

if __name__ == "__main__":
    # test()
    evaluate_galaxy()
