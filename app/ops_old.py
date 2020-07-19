import inspect

# Representation of an expression
# An expression is either a *term* or a list of length n where:
#       [x1, ..., xn]
# represents
#       ap ap ... ap x1 x2 ... xn
# In an expression, x1 must be a term, and x2 ... xn are expressions.
#
# A term is either an operator, a list, a literal, a variable, or maybe something else.

class Expr:
    def __init__(self, fun, arg = None):
        self.set(fun, arg)

    def set(self, fun, arg):
        self.fun = fun
        self.arg = arg

        if (arg is None) and (type(fun) is int):
            self.reduce = self.noop
            self.set = self.error

    def noop(self):
        pass

    def error(self, *args, **kwargs):
        raise ValueError("internal error")

    def reduce(self):
        # Walk tree until we find a function that can be applied
        args = []
        trees = []

        while not (self.arg is None):
            args.append(self.arg)
            trees.append(self)
            self = self.fun

        fun = self.fun
        arity = fun.arity

        # If we ended up at a symbol, substitute

        if isinstance(fun, Literal):
            if fun.reference is None:
                return False
            else:
                if len(args) > 0:
                    trees[-1].fun = fun.reference
                else:
                    self.replace_with(fun.reference)
                return True
        elif arity <= len(args):
            result = fun.apply(*args[-arity:])
            if not (result is None):
                trees[-arity].replace_with(result)
            return True
        else:
            return False

    def replace_with(self, other):
        if isinstance(other, Expr):
            self.set(other.fun, other.arg)
        else:
            self.set(other, None)

    # Left-side first
    def walk(self, f0, f2, accum):
        stack = [self]
        while len(stack) > 0:
            cur = stack.pop()

            if cur.arg is None:
                f0(cur, accum)
            else:
                f2(cur, accum)
                stack.append(cur.arg)
                stack.append(cur.fun)

        return accum

    def assign_symbol_references(self, symbols):
        def f0(cur, accum):
            if isinstance(cur.fun, Literal) and (cur.fun.data in symbols):
                cur.fun.reference = symbols[cur.fun.data]
        def f2(cur, accum):
            pass

        self.walk(f0, f2, None)

    def tostring(self):
        ap = 'ap'
        terms = []
        def f0(cur, accum):
            if type(cur.fun) is int:
                terms.append(str(cur.fun))
            else:
                terms.append(cur.fun.name)

        def f2(cur, accum):
            terms.append(ap)

        self.walk(f0, f2, None)
        return ' '.join(terms)

    def size(self):
        count = [0]
        def f(cur, accum):
            count[0] += 1

        self.walk(f, f, None)
        return count[0]

def readname(name):
    if name in name2op:
        return name2op[name]
    else:
        try:
            return int(name)
        except:
            return Literal(name, name)

def readexpression(line):
    parts = reversed(line.split())
    stack = []
    for part in parts:
        if part == 'ap':
            x = stack.pop()
            y = stack.pop()
            stack.append(ap(x, y))
        else:
            stack.append(Expr(readname(part)))

    assert len(stack) == 1
    return stack[0]

def ap(a, b):
    return Expr(a, b)

def no_apply(*args, **kwargs):
    raise ValueError("Cannot 'apply' that")

class Op:
    def __init__(self, name, apply, arity = None):
        if arity is None:
            arity = len(inspect.getargspec(apply)[0])

        self.name = name
        self.apply = apply
        self.arity = arity

class Literal:
    def __init__(self, name, data):
        # self.name = name
        self.name = str(data)
        self.data = data
        self.arity = 999999
        self.apply = no_apply
        self.reference = None

#######
# In each function below, arguments are given in *reverse* order!
#######

def ap_inc(a):
    if not a.reduce():
        return a.fun + 1

def ap_dec(a):
    if not a.reduce():
        return a.fun - 1

def ap_add(b, a):
    if not (a.reduce() or b.reduce()):
        if isinstance(b.fun, Op):
            print('add op??')
            print(b.tostring())
            print(a.tostring())
        return a.fun + b.fun

def ap_mul(b, a):
    if not (a.reduce() or b.reduce()):
        return a.fun * b.fun

def ap_div(b, a):
    if not (a.reduce() or b.reduce()):
        a = a.fun
        b = b.fun
        if a == 0:
            return 0
        if (a > 0) == (b > 0):
            return a // b
        else:
            return -(abs(a) // abs(b))

def ap_eq(b, a):
    if not (a.reduce() or b.reduce()):
        a = a.fun
        b = b.fun
        if a is b:
            return true
        if a == b:
            return true
        if (type(a) == int) or (type(b) == int):
            return false
        raise ValueError("Don't know how to compute equality of {} and {}".format(a, b))

def ap_lt(b, a):
    if not (a.reduce() or b.reduce()):
        a = a.fun
        b = b.fun
        if a < b:
            return true
        else:
            return false

def ap_neg(a):
    if not a.reduce():
        return -a.fun

def ap_pwr2(a):
    if not a.reduce():
        return 2 ** a.fun

def ap_true(b, a):
    return a

def ap_false(b, a):
    return b

class Modulated:
    def __init__(self, data):
        self.data = data
        self.name = 'modulated_data'
        self.arity = 0
        self.apply = no_apply

def ap_mod(x):
    return Modulated(x)

def ap_dem(x):
    if not x.reduce():
        assert isinstance(x.fun, Modulated)
        return x.fun.data

def ap_S(z, y, x):
    return ap(ap(x, z), ap(y, z))

def ap_C(z, y, x):
    return ap(ap(x, z), y)

def ap_B(z, y, x):
    return ap(x, ap(y, z))

def ap_I(x):
    return x

def ap_cons(z, y, x):
    return ap(ap(z, x), y)

def ap_nil(x):
    return true

def ap_car(x):
    return ap(x, Expr(true))

def ap_cdr(x):
    return ap(x, Expr(false))

def ap_isnil(x):
    if not x.reduce():
        if x.fun is nil:
            return true
        else:
            return false

true = Op('t', ap_true)
false = Op('f', ap_false)
nil = Op('nil', ap_nil)
cons = Op('cons', ap_cons)

all_ops = [
        true,
        false,
        nil,
        cons,
        Op('inc', ap_inc),
        Op('dev', ap_dec),
        Op('add', ap_add),
        Op('mul', ap_mul),
        Op('div', ap_div),
        Op('eq', ap_eq),
        Op('lt', ap_lt),
        Op('neg', ap_neg),
        Op('pwr2', ap_pwr2),
        Op('mod', ap_mod),
        Op('dem', ap_dem),
        Op('s', ap_S),
        Op('c', ap_C),
        Op('b', ap_B),
        Op('i', ap_I),
        Op('car', ap_car),
        Op('cdr', ap_cdr),
        Op('isnil', ap_isnil)
    ]

name2op = {}
for op in all_ops:
    name2op[op.name] = op
