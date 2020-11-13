import socket
import sys
import pygame
import random
import time
from PIL import Image
from threading import Thread
import threading
from util import *

WAIT_TIME = 0.025

def receiveFile(soc, path):
    req = -1 
    data = bytes([])
    while req < 0 or len(data) < req:
        data += soc.recv(8192)
        if req < 0 and len(data) >= HEADER_SIZE:
            req = int(data[:HEADER_SIZE].decode('utf8'))
            data = data[HEADER_SIZE:]
            
    out_file = open(path, 'wb') # open for [w]riting as [b]inary
    out_file.write(data)
    out_file.close()

def receiveImage(soc, screen):
    receiveFile(soc, 'screen.png')
    screen.blit(pygame.image.load('screen.png'), (0, 0))
    pygame.display.flip()
    print('DONE')    

# define a variable to control the main loop
running = True

rec = 1
def receive(soc, screen):
    global rec, running
    while running:
        while rec > 0:
            zz = []
            while True:
                zz.append(soc.recv(8192).decode("utf8").rstrip())
                if zz[-1][-1] == ']':
                    try:
                        t = eval(''.join(zz))
                        zz = []
                        for x in t:
                            color, pp, np, w = decEvent(x)
                            pygame.draw.line(screen, color, pp, np, w)
                            for i in range(-1, 2):
                                for j in range(-1, 2):
                                    pygame.draw.aaline(screen, color, (pp[0] + i, pp[1] + j), (np[0] + i, np[1] + j), w)
                        break
                    except:
                        pass
            rec -= 1
        time.sleep(0.04)

def main():
    global rec, running
    host, port = input("Input host and port: ").rstrip().split()
    port = int(port)
    
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        soc.connect((host, port))
    except:
        print("Connection Error")
        sys.exit()
        
    soc.sendall('__screen__'.encode('utf8'))

    ts = input('Input RGB (press enter for random): ')
    try:
        r, g, b = map(int, ts.split())
    except:
        r, g, b = random.randint(0, 160), random.randint(0, 160), random.randint(0, 160)    

    pygame.init()
    screen = pygame.display.set_mode((WIDTH,HEIGHT))
    receiveImage(soc, screen)



    px, py = 0, 0
    pPressed = False
    pPressed2 = False
    pPressed3 = False
    # main loop
    events = []
    timer = 15

    white = (255, 255, 255)


    print("RGB:", r, g, b, '\n')
    soc.sendall(str('__big__').encode('utf8'))

    Thread(target=receive, args=(soc, screen)).start()
    while running:

        # event handling, gets all event from the event queue
        for event in pygame.event.get():
            # only do something if the event is of type QUIT
            if event.type == pygame.QUIT:
                # change the value to False, to exit the main loop
                running = False
                
        pressed = pygame.mouse.get_pressed()[0]
        pressed2 = pygame.mouse.get_pressed()[2]
        pressed3 = pygame.mouse.get_pressed()[1]
        x, y = pygame.mouse.get_pos()
##        print(x, y)
        if (x, y) != (px, py):
            if pPressed and pressed:
                events.append(encEvent(r, g, b, px, py, x, y, 3))
                pygame.draw.line(screen, (r, g, b), (px, py), (x, y), 3)
            elif pPressed2 and pressed2:
                events.append(encEvent(255, 255, 255, px, py, x, y, 30))
                pygame.draw.line(screen, white, (px, py), (x, y), 30)
            elif pPressed3 and pressed3:
                events.append(encEvent(255, 255, 255, px, py, x, y, 100))
                pygame.draw.line(screen, white, (px, py), (x, y), 100)
            
        pPressed = pressed
        pPressed2 = pressed2
        pPressed3 = pressed3
        px = x
        py = y

        if timer <= 0 and rec == 0:
            timer = 15
            rec += 1
            if len(events):
                soc.sendall(str(events).replace(' ', '').encode('utf8'))
            else:
                soc.sendall(str('__idle__').encode('utf8'))
            events = []
##        receive(soc, screen)
        pygame.display.flip()
        timer -= 1
        time.sleep(0.001)
    soc.sendall(str('__exit__').encode('utf8'))
    soc.close()

if __name__ == "__main__":
   main()
