import ops

def read_galaxy_txt(infile = '../input/galaxy.txt'):
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

def galaxy():
    symbols = read_galaxy_txt()
    return symbols['galaxy']


#### Various testing stuff


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

def evaluate_galaxy():
    symbols = read_galaxy_txt('../input/ap_galaxy.txt')

    # result0 = ap ap galaxy nil ap ap cons 0 0
    s = symbols['result0']
    print(ops.tostring(s))
    ops.reducer.reduce(s)
    print(ops.tostring(s))

def test():
    symbols = read_galaxy_txt() #'../input/test.txt')
    d = {
            ':1096' : symbols[':1096'],
            ':1199' : symbols[':1199'],
            ':1201' : symbols[':1201'],
            ':1202' : symbols[':1202']
            }
    print_all_symbols(symbols)
    reduce_all_symbols(symbols, 1000)

if __name__ == "__main__":
    # test()
    evaluate_galaxy()
