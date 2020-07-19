import subprocess
import requests
import os
import os.path
import readline

import galaxy
import modem
import ops
import secret

def display_image_with_feh(imagefile):
    subprocess.run(["feh", "-F", imagefile])

def zoom(image, factor = 4):
    import numpy as np
    return np.kron(image, np.ones((factor, factor, 1), dtype = bool))

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

    c = np.array(make_canvas(xyss), dtype = bool)
    k, x, y = c.shape
    c = c[:, :, :, None]

    colors4  = np.array([[192, 0, 0], [63, 0, 0], [0, 255, 0], [0, 0, 255]], dtype = np.uint8)
    colors4  = colors4[:, None, None, :]
    colors6  = np.array([[192, 0, 0], [63, 0, 0], [0, 170, 0], [0, 0, 170], [0, 85, 0], [0, 0, 85]], dtype = np.uint8)
    colors6  = colors6[:, None, None, :]
    colors8  = np.array([[192, 0, 0], [63, 0, 0], [0, 144, 0], [0, 0, 144], [0, 72, 0], [0, 0, 72], [0, 36, 0], [0, 0, 36]], dtype = np.uint8)
    colors8  = colors8[:, None, None, :]
    colors10 = np.array([[192, 0, 0], [63, 0, 0], [0, 136, 0], [0, 0, 136], [0, 68, 0], [0, 0, 68], [0, 34, 0], [0, 0, 34], [0, 17, 0], [0, 0, 17]], dtype = np.uint8)
    colors10 = colors10[:, None, None, :]

    if k > 10:
        print("Too many color channels!", k, "channels")
        k = 10
        c = c[:k]

    if k <= 4:
        image = np.sum(np.where(c, colors4[:k], 0), axis = 0, dtype = np.uint8)
    elif k <= 6:
        image = np.sum(np.where(c, colors6[:k], 0), axis = 0, dtype = np.uint8)
    elif k <= 8:
        image = np.sum(np.where(c, colors8[:k], 0), axis = 0, dtype = np.uint8)
    elif k <= 10:
        image = np.sum(np.where(c, colors10[:k], 0), axis = 0, dtype = np.uint8)

    image = image.transpose((1, 0, 2))
    return image

def save_with_imageio(image, outfile = '../images/out.png', factor = 8):
    import imageio

    image = zoom(image, factor)
    addgridlines(image, factor * 10)

    imageio.imwrite(outfile, image)

class GalaxyPadUI:
    def __init__(self, image, on_click):
        self.im = image
        self.cid = self.im.figure.canvas.mpl_connect('button_press_event', self)
        self.on_click = on_click

    def __call__(self, event):
        coord = (int(event.xdata), int(event.ydata))
        self.on_click(*coord)
        print('click', coord)

def plot_with_matplotlib(image, xyss, on_click):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    xm, xM, ym, yM = get_extent(xyss)
    im = ax.imshow(image, interpolation='none',
                   origin='lower',
                   extent=[-xM-0.5, xM+0.5, -yM-0.5, yM+0.5])
    galaxy_pad = GalaxyPadUI(im, on_click)
    plt.show()
    return galaxy_pad

def no_render(xyss):
    print("Cannot draw image!")
    print(ops.tostring(xyss))
    raise RuntimeError()

def send_to_test_server(data):
    data = ops.unmake_expression(data)
    data = modem.mod(data)

    test_url = 'https://icfpc2020-api.testkontur.ru/aliens/send?apiKey=' + secret.apikey

    response = requests.post(test_url, data = data)
    code = response.status_code
    if code != 200:
        print("Response code", code)
    return modem.dem(response.text)

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

        flag = int(expr[0][0][0])
        newstate = ops.unmake_expression(expr[0][1][0][0])
        data = expr[0][1][0][1][0][0]
        assert expr[0][1][0][1][0][1][0] == ()
        assert flag in [0, 1]

        if flag == 0:
            xyss = process_xyss_expr(data)
            renderer(xyss)
            return newstate
        else:
            state = newstate
            print("Intermediate state:", trim_state(state))
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

def trim_state(state, full = False):
    s = ops.tostring(ops.make_expression(state))
    if full or (len(s) < 100):
        return s
    else:
        return "[" + str(len(s)) +  " characters]" + s[:50] + ' ... ' + s[-50:]

class Runner:
    def __init__(self):
        self.g = galaxy.galaxy()
        self.imagefile = '../images/out.png'
        self.moviefile = None
        self.movieframe = None
        self.lastimagefile = self.imagefile
        self.lastimage = None
        self.inmovie = False
        self.state = [()]
        self.xyss = []

    def renderer(self, xyss):
        self.xyss = xyss
        image = make_image(xyss)
        self.lastimage = image
        if self.inmovie:
            f = self.moviefile.format(self.movieframe)
            self.lastimagefile = f
            self.movieframe += 1
        else:
            self.lastimagefile = self.imagefile

        save_with_imageio(image, self.lastimagefile)
        self.display()

    def sender(self, data):
        print("Sending data to server:", ops.tostring(data))
        response = send_to_test_server(data)
        print("Server response:", ops.tostring(ops.make_expression(response)))
        return response

    def mainloop(self):
        prompt = '(q)uit (d)isplay (c)oordinates (s)tate (e)dit state (m)ovie (u)ndo  '
        while True:
            try:
                result = input(prompt).strip().lower()
            except EOFError:
                self.quit()
                return

            if len(result) == 0:
                continue

            c = result[0]

            if c == 'q':
                self.quit()
                return

            if c == 'd':
                self.display()
            elif c == 'c':
                for xys in self.xyss:
                    print(xys)
            elif c == 's':
                self.show_state(True)
            elif c == 'e':
                self.edit_state()
            elif c == 'm':
                self.movie()
            elif c == 'u':
                self.undo()
            elif result == '0':
                self.click(0, 0)
            elif c in '-0123456789':
                try:
                    x_, y_ = result.split()
                    x = int(x_)
                    y = int(y_)
                except:
                    print("Invalid coordinates")
                    continue
                self.click(x, y)
            else:
                print("Unrecognized command")

    def quit(self):
        print('bye')

    def display(self):
        plot_with_matplotlib(self.lastimage, self.xyss, self.click)
        # display_image_with_feh(self.lastimagefile)

    def show_state(self, full = False):
        print("State:", trim_state(self.state[-1], full))

    def edit_state(self):
        saved_states = read_saved_states()

        print("Saved states:")
        for i in range(len(saved_states)):
            name, value = saved_states[i]
            print("    ({})    ".format(i), name, "    ", value)
        print("    (c)ustom")

        cmd = input("Select state, or (c)ustom:  ").strip().lower()
        if len(cmd) == 0:
            print("canceled")
            return

        if cmd[0] == 'c':
            value = input("Enter new state:  ").strip().lower()
        else:
            try:
                value = saved_states[int(cmd)][1]
            except:
                print("canceled")
                return

        try:
            self.state.append(ops.parse_list_expr(value))
        except:
            print("invalid")

    def movie(self):
        if self.inmovie:
            self.moviefile = None
            self.movieframe = None
            self.inmovie = False
        else:
            cmd = input("Choose movie name:  ").strip()
            if len(cmd) == 0:
                print('canceled')
                return
            d = os.path.join('..', 'movies', cmd)
            os.mkdir(d)
            self.moviefile = str(os.path.join(d, 'f{:04d}.png'))
            self.movieframe = 0
            self.inmovie = True

    def undo(self):
        print("State history:")
        for i in range(min(30, len(self.state))):
            print("    ({})    ".format(i), trim_state(self.state[-i - 1]))
        cmd = input("Select number of steps to rewind (0 does nothing):  ").strip().lower()
        try:
            idx = int(cmd)
            if idx > 0 and idx < len(self.state):
                self.state = self.state[:len(self.state) - idx]
        except:
            print("canceled")

    def click(self, x, y):
        newstate = interact(self.g, self.renderer, self.sender, self.state[-1], (x, y))
        self.state.append(newstate)
        self.show_state()

def run():
    Runner().mainloop()

if __name__ == "__main__":
    run()
