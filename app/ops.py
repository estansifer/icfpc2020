import inspect

# Expression is either
#   [x] such that x :: Term
#   [y, z] such that y, z :: Expr, representing "ap y z"
# a Term either an Op or a Variable an integer or a tuple
# tuple is either (), i.e., nil, or a pair of expressions

# Accepts integers, (), and pairs thereof
def make_expression(x):
    if x == ():
        return [()]
    elif type(x) is int:
        return [x]
    else:
        assert len(x) == 2
        return [(make_expression(x[0]), make_expression(x[1]))]

def unmake_expression(x):
    assert (type(x) is list) and (len(x) == 1)
    x = x[0]
    if x == ():
        return ()
    elif type(x) is int:
        return x
    else:
        a, b = x
        return (unmake_expression(a), unmake_expression(b))

def __test(x):
    print('test:', x)
    e = make_expression(x)
    print(e)
    print(unmake_expression(e))

def ap(x, y):
    return [x, y]

def reduce1(expr):
    args = []
    parents = []

    while len(expr) == 2:
        args.append(expr[1])
        parents.append(expr)
        expr = expr[0]

    foo = expr[0]
    if type(foo) is int:
        return False

    # Now want to evaluate foo applied to args (reversed)
    if isinstance(foo, tuple):
        arity = 1
        if len(args) >= 1:
            if foo == ():
                result = [true]
            else:
                result = [[args[-1], foo[0]], foo[1]]
            parents[-arity][:] = result
            return True
    elif foo.can_apply():
        arity = foo.arity
        if arity == 0:
            expr[:] = foo.apply()
            return True
        elif len(args) >= arity:
            args = args[-arity:]

            if foo.strict:
                for e in args:
                    if reduce1(e):
                        return True

            parents[-arity][:] = foo.apply(*args)
            return True
    return False

class Reducer:
    def __init__(self, maxdepth=10000):
        self.reduce_targets = [None] * maxdepth
        self.numargs = [None] * maxdepth

    def reduce(self, expr):
        progress = False

        rt = self.reduce_targets
        numargs = self.numargs

        rt[0] = expr
        numargs[0] = 0
        idx = 0

        while idx >= 0:
            e = rt[idx]
            # print("Reducing index", idx, tostring(e))

            if len(e) == 2:
                idx += 1
                rt[idx] = e[0]
                numargs[idx] = numargs[idx - 1] + 1
            else:
                foo = e[0]
                if type(foo) is list:
                    print("Unexpected list?", idx)
                    tostring(foo)
                    print(numargs[:idx + 1])
                    print(e)

                if type(foo) is int:
                    assert numargs[idx] == 0
                    idx -= 1
                elif type(foo) is tuple:
                    # arity = 1
                    idx -= 1
                    if numargs[idx + 1] >= 1:
                        if foo == ():
                            result = [true]
                        else:
                            result = [[rt[idx][1], foo[0]], foo[1]]
                        rt[idx][:] = result
                        progress = True
                elif foo.can_apply():
                    arity = foo.arity
                    if arity == 0:
                        e[:] = foo.apply()
                        progress = True
                    elif numargs[idx] >= arity:
                        args = [e_[1] for e_ in rt[idx - arity : idx]]
                        idx -= arity
                        if foo.strict:
                            rt[idx][:] = [DelayedApplication(foo, args)]
                            for e_ in args:
                                idx += 1
                                rt[idx] = e_
                                numargs[idx] = 0
                        else:
                            rt[idx][:] = foo.apply(*args)
                            progress = True
                    else:
                        idx = idx - numargs[idx] - 1
                else:
                    # assert numargs[idx] == 0
                    idx = idx - numargs[idx] - 1

        return progress

reducer = Reducer()

class DelayedApplication:
    def __init__(self, foo, args):
        self.foo = foo
        self.args = args
        self.arity = 0
        self.strict = False

    def can_apply(self):
        return True

    def apply(self):
        return self.foo.apply(*self.args)

    def __str__(self):
        return '[' + str(self.foo) + ' ; ' + str(self.args) + ' ]'

    def __repr__(self):
        return '[' + str(self.foo) + ' ; ' + str(self.args) + ' ]'

def walk(expr, f0, f2):
    memo = set()

    stack = [expr]
    while len(stack) > 0:
        cur = stack.pop()
        if id(cur) in memo:
            f0([recursion])
            continue
        else:
            memo.add(id(cur))

        if len(cur) == 1:
            f0(cur)
        else:
            f2(cur)
            stack.append(cur[1])
            stack.append(cur[0])

def assign_symbol_references(expr, symbols):
    def f0(cur):
        if isinstance(cur[0], Variable) and (cur[0].name in symbols):
            cur[0].reference = symbols[cur[0].name]
    def f2(cur):
        pass
    walk(expr, f0, f2)

def serialize_strict_list(l, terms):
    if l == ():
        terms.append('()')
    else:
        terms.append('(')
        while l != ():
            head, tail = l
            if len(head) == 1:
                if type(head[0]) is tuple:
                    serialize_strict_list(head[0], terms)
                else:
                    terms.append(str(head[0]))
            else:
                terms.append(tostring(head))

            terms.append(',')
            if len(tail) == 1:
                if type(tail[0]) is tuple:
                    l = tail[0]
                else:
                    terms.append(str(tail[0]))
                    break
            else:
                terms.append(tostring(tail))
                break
        terms.append(')')

def parse_list_expr(s):
    s = s.strip()
    i = [0]

    def parse_int():
        j = i[0]
        while not (s[j] in [',', ')']):
            j += 1
        val = int(s[i[0] : j].strip())
        i[0] = j
        return val

    def parse_tail():
        while s[i[0]] == ' ':
            i[0] += 1

        if s[i[0]] == ')':
            i[0] += 1
            return ()

        o = parse_obj()

        while s[i[0]] == ' ':
            i[0] += 1

        if s[i[0]] == ',':
            i[0] += 1
            return (o, parse_tail())
        else:
            i[0] += 1
            return o


    def parse_list():
        i[0] += 1
        return parse_tail()

    def parse_obj():
        i0 = i[0]
        if s[i[0]] == '(':
            return parse_list()
        else:
            return parse_int()

    return parse_obj()

def tostring(expr):
    ap = 'ap'
    terms = []
    def f0(cur):
        if type(cur[0]) is tuple:
            serialize_strict_list(cur[0], terms)
        else:
            terms.append(str(cur[0]))
    def f2(cur):
        terms.append(ap)

    walk(expr, f0, f2)
    return ' '.join(terms)

class RecursionSymbol:
    def __init__(self):
        self.name = '(recursed)'

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

recursion = RecursionSymbol()

class Variable:
    def __init__(self, name):
        self.name = name
        self.reference = None
        self.arity = 0
        self.strict = False

    def can_apply(self):
        return not (self.reference is None)

    def apply(self):
        return self.reference

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class Op:
    def __init__(self, name, apply, strict = True):
        self.name = name
        self.apply = apply
        self.arity = len(inspect.getargspec(apply)[0])
        self.strict = strict

    def can_apply(self):
        return True

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

def _inc(a):
    return [a[0] + 1]
def _dec(a):
    return [a[0] - 1]
def _add(b, a):
    return [a[0] + b[0]]
def _mul(b, a):
    return [a[0] * b[0]]
def _div(b, a):
    a = a[0]
    b = b[0]
    if a == 0:
        return [0]
    if (a > 0) == (b > 0):
        return [a // b]
    else:
        return [-(abs(a) // abs(b))]
def _eq(b, a):
    if a[0] == b[0]:
        return [true]
    if (type(a[0]) == int) or (type(b[0]) == int):
        return [false]
    raise ValueError("Don't know how to compute equality of {} and {}".format(a, b))

def _lt(b, a):
    if a[0] < b[0]:
        return [true]
    else:
        return [false]

def _neg(a):
    return [-a[0]]

def _pwr2(a):
    return [2 ** a[0]]

def _true(b, a):
    return a

def _false(b, a):
    return b

def _S(z, y, x):
    return [[x, z], [y, z]]

def _C(z, y, x):
    return [[x, z], y]

def _B(z, y, x):
    return [x, [y, z]]

def _I(x):
    return x

def _cons_strict(y, x):
    return [(x, y)]
    # if type(y[0]) is tuple:
        # return [(x, y)]
    # return [[[cons_lazy], x], y]

def _cons(z, y, x):
    return [[z, x], y]

def _nil(x):
    return [true]

def _nil_strict():
    return [()]

def _car_strict(x):
    if type(x[0]) is tuple:
        if x[0] == ():
            return [true]
        else:
            return x[0][0]
    else:
        return [x, [true]]

def _car(x):
    return [x, [true]]

def _cdr_strict(x):
    if type(x[0]) is tuple:
        if x[0] == ():
            return [true]
        else:
            return x[0][1]
    else:
        return [x, [false]]

def _cdr(x):
    return [x, [false]]

def _isnil(x):
    # Because isnil is strict, if the argument is "nil" it will have been
    # reduced to () already
    if x[0] == ():
        return [true]
    else:
        return [false]

true = Op('t', _true, strict = False)
false = Op('f', _false, strict = False)
identity = Op('i', _I, strict = False)
nil = Op('nil', _nil_strict, strict = False)
cons = Op('cons', _cons_strict)
cons_lazy = Op('cons_lazy', _cons, strict = False)
car = Op('car', _car_strict)
car_lazy = Op('car_lazy', _car, strict = False)
cdr = Op('cdr', _cdr_strict)
cdr_lazy = Op('cdr_lazy', _cdr, strict = False)

all_ops = [
        true,
        false,
        nil,
        cons,
        identity,
        car,
        cdr,
        Op('inc', _inc),
        Op('dev', _dec),
        Op('add', _add),
        Op('mul', _mul),
        Op('div', _div),
        Op('eq', _eq),
        Op('lt', _lt),
        Op('neg', _neg),
        Op('pwr2', _pwr2),
        Op('s', _S, strict = False),
        Op('c', _C, strict = False),
        Op('b', _B, strict = False),
        Op('isnil', _isnil)
    ]

name2op = {}
for op in all_ops:
    name2op[op.name] = op

def readname(name):
    if name in name2op:
        return name2op[name]
    else:
        try:
            return int(name)
        except:
            return Variable(name)

def readexpression(text):
    ap = 'ap'
    terms = reversed(text.split())
    stack = []
    for term in terms:
        if term == ap:
            x = stack.pop()
            y = stack.pop()
            stack.append([x, y])
        else:
            stack.append([readname(term)])
    assert len(stack) == 1
    return stack[0]
