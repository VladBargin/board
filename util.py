WIDTH = 800
HEIGHT = 550
HEADER_SIZE = 20

def encRgb(r, g, b):
    return r + g*256 + b * 256 * 256

def decRgb(x):
    b = x // 256 // 256
    g = (x - 256 * 256 * b) // 256
    r = x % 256
    return (r, g, b)

def encPos(x, y):
    return y * WIDTH + x

def decPos(p):
    return (p % WIDTH, p // WIDTH) 
