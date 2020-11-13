WIDTH = 850
HEIGHT = 550
HEADER_SIZE = 20
EVENTS_PER_CLIENT = 80

p = [256, 256, 256, WIDTH, HEIGHT, WIDTH, HEIGHT, 1000]
tp = [p[0]]
for i in range(1, len(p) - 1):
    tp.append(p[i] * tp[i - 1])

def encEvent(r, g, b, px, py, x, y, w):
    return r + g * tp[0] + b * tp[1] + px * tp[2] + py * tp[3] + x * tp[4] + y * tp[5] + w * tp[6]

def decEvent(x):
    res = []
    for i in range(8):
        res.append(x % p[i])
        x //= p[i]
    return ((res[0], res[1], res[2]), (res[3], res[4]), (res[5], res[6]), res[7])
