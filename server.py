import socket
import sys
import traceback
import time
from threading import Thread
import threading
import random
import pygame
from PIL import Image
from queue import Queue
from util import *

def main():
    start_server()

MAX_CLIENTS = 100
idUsed = [(False, None)] * MAX_CLIENTS
# We will store the last EVENTS_STORED events with their time values and with priorities.
# And so ensure that everyone has the same board, I will send an image to all new clients and send to all clients the same events to draw localy.
# But in this version new clients will just start with a blank slate
# So I will just send them this queue, each event will be given some ID. The local client will check, if he has this ID.
# In this way, I will not care about dispatching all the events at one time. 
events = Queue()
events_to_send = []
str_to_send_big = ''
str_to_send_small = ''
screen = None
MAX_EVENTS = 512
CNT_EVENTS = 10
WAIT_TIME = 0.015 # This is aproximate, because I may randomize a bit to avoid some data races.

# And this is a flag. I don't want to use the queue system because it won't allow me to do what I want.
qUsed = False
sData = 0

def update(ID, status):
    global idUsed
    idUsed[ID] = status

def addEvent(event):
    global events, qUsed
    qUsed = True
    events.put_nowait(event)
    qUsed = False

def draw():
    global sData
    sData += 1
##    print("draw start")
    le = len(events_to_send)
    for x in events_to_send:
        color, pp, np, w = decEvent(x)
        pygame.draw.line(screen, color, pp, np, w)
        for i in range(-1, 2):
            for j in range(-1, 2):
                pygame.draw.aaline(screen, color, (pp[0] + i, pp[1] + j), (np[0] + i, np[1] + j), w)
    pygame.display.flip()
##    print("draw end")
    sData -= 1
    
def updateETS():
    global events_to_send, events, str_to_send_big, str_to_send_small, qUsed
    events_to_send = []
    
    qUsed = True
    while not events.empty():
        events_to_send.append(events.get_nowait())

    le = len(events_to_send)
    for q in events_to_send[max(0, le - MAX_EVENTS):le]:
        events.put_nowait(q)

    str_to_send_big = str(events_to_send[max(0, le - MAX_EVENTS):le]).replace(' ', ' ')
    str_to_send_small = str(events_to_send[max(0, le - CNT_EVENTS):le]).replace(' ', ' ')
    qUsed = False
    

def sendEvents(connection, ip, port, big=False):
    global events_to_send, sData, str_to_send_big, str_to_send_small
    sData += 1
##    connection.sendto(str(events_to_send).encode(), (ip, port))
    le = len(events_to_send)
    if big:
        connection.sendall(str_to_send_big.encode('utf8'))
    else:
        connection.sendall(str_to_send_small.encode('utf8'))
    sData -= 1

def sendFile(connection, path):
    in_file = open('screenshot.png', 'rb') # opening for [r]eading as [b]inary
    data = in_file.read() # if you only wanted to read 512 bytes, do .read(512)
    in_file.close()
    le = len(data)
    le = str(le).zfill(HEADER_SIZE)
    connection.sendall(le.encode('utf8') + data)
    

def sendScreen(connection):
    pygame.image.save(screen, 'screenshot.png')
    sendFile(connection, 'screenshot.png')
    #im = Image.open("screenshot.png").convert('RGB').load()
    #ta = [tuple([im[i, j][0] + im[i, j][1]*256 + im[i, j][2]*256*256 for j in range(HEIGHT)]) for i in range(WIDTH)]
    #connection.sendall(str(ta).encode('utf8'))
    
def start_server():
    global screen
##    host = input("Input host: ")
    host = ''
    port = 8000 # arbitrary non-privileged port
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Socket created")
    try:
        soc.bind((host, port))
    except:
        print("Bind failed. Error : " + str(sys.exc_info()))
        sys.exit()
    soc.listen(6) # queue up to 6 requests
    print("Socket now listening")

    pygame.init()
    screen = pygame.display.set_mode((WIDTH,HEIGHT))
    screen.fill((255,255,255))

    Thread(target=regularThread).start()
    Thread(target=regularThread2, args=(soc, 0)).start()
    while True:
        for event in pygame.event.get():
            pass
        while sData > 0:
            time.sleep(0.01)
        draw()
        time.sleep(0.04)
        
    soc.close()

def regularThread2(soc, _):
    # infinite loop- do not reset for every requests
    while True:
        connection, address = soc.accept()
        ip, port = str(address[0]), str(address[1])
        print("Connected with " + ip + ":" + port)
      
        try:
            c_ID = 0
            while c_ID < MAX_CLIENTS and idUsed[c_ID][0]:
                c_ID += 1

            if c_ID >= MAX_CLIENTS:
                print("Oops!")
            else:
                print("New thread!")
                Thread(target=clientThread, args=(connection, ip, port, c_ID)).start()
        except:
            print("Thread did not start.")
            traceback.print_exc()
        
def regularThread():
    global idUsed
    i = 0
    while True:
        while qUsed or sData > 0:
            time.sleep(random.uniform(0.0005, 0.001))
        updateETS()
        if i % 100 == 0:
            sz = sys.getsizeof(str_to_send_big.encode('utf8')) / 1024
            print(len(events_to_send), 'events stored, takes up', "{:.2f}".format(sz), 'KB ', 'C_E:', CNT_EVENTS)            
        i += 1
        time.sleep(WAIT_TIME)


def clientThread(connection, ip, port, ID, max_buffer_size = 8192):
    global idUsed, CNT_EVENTS
    
    idUsed[ID] = (True, connection)
    ci = 1000
    CNT_EVENTS += EVENTS_PER_CLIENT
    while ci > 0:
        try:
            inp = receive_input(connection, max_buffer_size)
            if inp == '__exit__':
                print("Closed connection with " + ip + ":" + port)
                connection.close()
                break
            elif inp == '__big__':
                sendEvents(connection, ip, port, True)
                time.sleep(WAIT_TIME)
                continue
            elif inp == '__screen__':
                sendScreen(connection)
                time.sleep(0.5)
                continue
            elif inp != '__idle__':
                cinst = ''
                while True:
                    cinst += inp
                    if cinst[-1] != ']':
                        inp = receive_input(connection, max_buffer_size)
                        continue
                    events_list = eval(cinst)
                    for ev in events_list:
                        while True:
                            if not qUsed:
                                addEvent(ev)
                                break
                            time.sleep(random.uniform(0.00001, 0.00005))
                    break

            sendEvents(connection, ip, port)
            ci = 1000
        except:
            ci -= 1
            time.sleep(0.01)

    
    CNT_EVENTS -= EVENTS_PER_CLIENT
                
    idUsed[ID] = (False, None)

def receive_input(connection, max_buffer_size):
    client_input = connection.recv(max_buffer_size)
    client_input_size = sys.getsizeof(client_input)
##    if client_input_size > max_buffer_size:
##      print("The input size is greater than expected {}".format(client_input_size))
    decoded_input = client_input.decode("utf8").rstrip()
    return decoded_input
    
if __name__ == "__main__":
   main()
