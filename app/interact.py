import subprocess

import galaxy
import ops

def display_image_with_feh(imagefile):
    subprocess.run(["feh", "-F", imagefile])

def zoom(image, factor = 4):
    import numpy as np
    return np.kron(image, np.ones((factor, factor, 1), dtype = np.uint8))

def addgridlines(image, spacing, color = [64, 64, 64]):

    xM = image.shape[0] // 2
    yM = image.shape[1] // 2

    for x in range(0, xM, spacing):
        image[xM + x, :] = color
        if x > 0:
            image[xM - x, :] = color

    for y in range(0, yM, spacing):
        image[:, yM + y] = color
        if y > 0:
            image[:, yM - y] = color

def get_extent(xyss):
    xm = 0
    xM = 0
    ym = 0
    yM = 0

    for xys in xyss:
        for x, y in xys:
            xm = min(xm, x)
            xM = max(xM, x)
            ym = min(ym, y)
            yM = max(yM, y)

    xM = max(xM, -xm)
    yM = max(yM, -ym)
    return xm, xM, ym, yM

def make_canvas(xyss):
    xm, xM, ym, yM = get_extent(xyss)
    canvass = [None] * len(xyss)
    for i in range(len(xyss)):
        canvas = [[0] * (2 * yM + 1) for j in range(2 * xM + 1)]
        canvass[i] = canvas

    for i, xys in enumerate(xyss):
        canvas = canvass[i]
        for x, y in xys:
            canvas[x + xM][y + yM] = 1

    return canvass

def make_image(xyss):
    import numpy as np

    c = np.array(make_canvas(xyss), dtype = np.uint8)

    k, x, y = c.shape

    if k > 4:
        print("Too many color channels!", k, "channels")
        k = 4

    image = np.zeros((x, y, 3), dtype = np.uint8)

    if k == 1:
        image[:, :, :] = c[0, :, :, None] * 255
    elif k <= 3:
        for i in range(k):
            image[:, :, i] = c[i] * 255
    else:
        image[:, :, :] = c[0, :, :, None] * 194
        for i in range(3):
            image[:, :, i] = np.maximum(image[:, :, i], c[i + 1] * 255)

    image = image.transpose((1, 0, 2))
    return image

def save_with_imageio(xyss, outfile = '../images/out.png', factor = 8):
    import imageio

    image = make_image(xyss)
    image = zoom(image, factor)
    addgridlines(image, factor * 10)

    imageio.imwrite(outfile, image)

class GalaxyPadUI:
    def __init__(self, image=0):
        self.im = image
        self.cid = self.im.figure.canvas.mpl_connect('button_press_event', self)

    def __call__(self, event):
        coord = (int(event.xdata), int(event.ydata))
        print('click', coord)
        '''
        image = make_image(xyss)
        xm, xM, ym, yM = get_extent(xyss)
        self.im.set_data(image)
        self.im.set_extent([-xM-0.5, xM+0.5, -yM-0.5, yM+0.5])
        plt.draw()
        '''

def plot_with_matplotlib(xyss):
    import matplotlib.pyplot as plt

    image = make_image(xyss)
    fig, ax = plt.subplots()
    xm, xM, ym, yM = get_extent(xyss)
    im = ax.imshow(image, interpolation='none',
                   origin='lower',
                   extent=[-xM-0.5, xM+0.5, -yM-0.5, yM+0.5])
    galaxy_pad = GalaxyPadUI(im)
    plt.show()
    return galaxy_pad

def no_render(xyss):
    print("Cannot draw image!")
    print(ops.tostring(xyss))
    raise RuntimeError()

def no_send(data):
    print("Cannot send data to server!")
    print(ops.tostring(data))
    raise RuntimeError()

# Takes data in cons-cell format and makes a list of list of pairs of integers
def process_xyss(data):
    xyss = []
    while data != ():
        d = data[0]
        data = data[1]

        xys = []
        while d != ():
            xys.append(d[0])
            d = d[1]
        xyss.append(xys)
    return xyss

def process_xyss_expr(expr):
    data = expr[0]

    xyss = []
    while data != ():
        d = data[0][0]
        data = data[1][0]

        xys = []
        while d != ():
            xy = d[0][0]
            xys.append((xy[0][0], xy[1][0]))
            d = d[1][0]
        xyss.append(xys)
    return xyss

def interact(protocol, renderer = no_render, sender = no_send, state = None, xy = None):
    if state is None:
        state = ()
    if xy is None:
        xy = (0, 0)

    while True:
        state = ops.make_expression(state)
        xy = ops.make_expression(xy)

        expr = [[protocol, state], xy]
        ops.reducer.reduce(expr)
        # result = ops.unmake_expression(expr)

        data = list(expr[0][1][0][1][0][0])
        expr[0][1][0][1][0][0][:] = [()]

        result = ops.unmake_expression(expr)

        flag = result[0]
        newstate = result[1][0]
        # data = result[1][1][0]
        assert result[1][1][1] == ()
        assert flag in [0, 1]

        if flag == 0:
            xyss = process_xyss_expr(data)
            renderer(xyss)
            return (newstate, xyss)
        else:
            state = newstate
            data = ops.unmake_expression(data)
            xy = sender(data)

def test():
    g = galaxy.galaxy()
    def render(xyss):
        imagefile = '../images/out.png'
        save_with_imageio(xyss, imagefile)
        display_image_with_feh(imagefile)

    interact(g, render)

def read_saved_states(infile = '../input/states'):
    states = []
    with open(infile, 'r') as f:
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue

            name, value = line.split('|')
            states.append((name.strip(), value.strip()))
    return states

def run():
    g = galaxy.galaxy()
    imagefile = '../images/out.png'

    def render(xyss):
        save_with_imageio(xyss, imagefile)
        display_image_with_feh(imagefile)

    saved_states = read_saved_states()

    state = ()
    xyss = []

    while True:
        prompt = '"<x> <y>" or (q)uit or (r)eset or show (s)tate or (e)dit state or show (c)oordinates or (d)isplay image:  '
        try:
            result = input(prompt).strip().lower()
        except EOFError:
            print("bye")
            return

        if len(result) == 0:
            continue

        if result[0] == 'q':
            print("bye")
            return

        if result[0] == 'r':
            print("resetting state to nil")
            state = ()
            continue

        if result[0] == 'c':
            for xys in xyss:
                print(xys)
            continue

        if result[0] == 'd':
            display_image_with_feh(imagefile)
            continue

        if result[0] == 's':
            print("State:", ops.tostring(ops.make_expression(state)))
            continue

        if result[0] == 'e':
            print("Saved states:")
            for i in range(len(saved_states)):
                name, value = saved_states[i]
                print("    ({})    ".format(i), name, "    ", value)
            print("    (c)ustom")

            cmd = input("Select state, or (c)ustom:  ").strip().lower()
            if len(cmd) == 0:
                print("aborted")
                continue

            if cmd[0] == 'c':
                value = input("Enter new state:  ").strip().lower()
            else:
                try:
                    value = saved_states[int(cmd)][1]
                except:
                    print("Unknown input")
                    continue

            state = ops.parse_list_expr(value)
            continue

        x_, y_ = result.split()
        x = int(x_)
        y = int(y_)

        try:
            state, xyss = interact(g, render, no_send, state, (x, y))
        except:
            print("Encountered exception during interaction!")

        s = ops.tostring(ops.make_expression(state))
        if len(s) < 100:
            print("State:", s)
        else:
            print("State [", str(len(s)), "characters]:", s[:50], ' ... ', s[-50:])

if __name__ == "__main__":
    run()
