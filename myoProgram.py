from msvcrt import getch
import os
import time
import signal
import threading
import subprocess
import time
import myo as myolib
import math
import ast
import socket
import copy
import pygame

emgList = []
learnVal = False
learnCount = 0
limit = 50
thresh = 35
learnSpan = 5
channels = 8
archetypes = {
    #"left": [0 for i in range(0, channels)],
    #"right": [0 for i in range(0, channels)],
    "fist": [0 for i in range(0, channels)],
    "open": [0 for i in range(0, channels)]
}
ip = "localhost"
port = 4950
portIn = 4951
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sockOut = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mode = {}
lastTime = int(round(time.time() * 1000))
zero = {"x": 0, "y": 0, "z": 0, "w": 0}
getZero = False
programRunning = True
translate = ["0", "0", "0"]
gestFont = None
outputFont = None
background = None
out = ""
markers = ""
center = [0, 0, 0]
stopped = False
rot = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

class Listener(myolib.DeviceListener):
    def on_connect(self, myo, time, firmv):
        myo.set_stream_emg(myolib.StreamEmg.enabled)

    def on_emg_data(self, myo, t, data):
        global emgList
        global learnVal
        global learnCount
        global learnSpan
        global archetypes
        global c
        global sock
        global ip
        global port
        global lastTime
        global zero
        global out
        global markers
        global zeroPos
        global rot
        global center
        
        if len(emgList) < limit:
            emgList.append(data)
        else:
            emgList.pop(0)
            emgList.append(data)

        if learnVal:
            if learnCount < learnSpan:
                learnCount += 1
            else:
                archetypes[learnVal] = absAvg(emgList)
                learnVal = False
                save("main.txt", archetypes)

        gest = interpret(absAvg(emgList))
        #gest = str(markers)
        
        direction = "1"
        if gest == "left":
            direction = "2"
        elif gest == "right" or gest == "fist":
            direction = "1"
        elif gest == "rest":
            direction = "0"
        elif gest == "open":
            direction = "-1"

        zeroMode = zeroOut(zero, mode)
        if not stopped:
            res = ""
            for i in rot:
                for j in i:
                    res += (str(j) + ",")
            msg = direction + "," + res[:-1] + "," + ",".join(list(map(str, roundVec(center, 3))))
            #msg = direction + "," + zeroMode["x"] + "," + zeroMode["y"] + "," + zeroMode["z"] + "," + zeroMode["w"] + "," + ",".join(list(map(str, markers)))
        #markers = processPos("absAvg")
        if int(round(time.time() * 1000)) - lastTime >= 75:
            show(gest, "gest")
            sock.sendto(msg.encode('utf-8'), (ip, port))
            out = msg.replace(",", ",  ")
            lastTime = int(round(time.time() * 1000))

    def on_orientation_data(self, myo, time, data):
        global mode
        global getZero
        global zero
        
        mode["x"] = str(round(data.x, 3))
        mode["y"] = str(round(data.y, 3))
        mode["z"] = str(round(data.z, 3))
        mode["w"] = str(round(data.w, 3))

def readCmd(args):
    global emgList
    global limit
    global thresh
    global getZero
    global gestFont
    
    cmd = args[0]
    if len(args) > 1:
        val = args[1]

    if cmd == "learn":
        print("Learning ", val)
        if val !="file":
            learn(val)
        else:
            learnFile(args[2])
    elif cmd == "emg":
        print("Last emgs: ", emgList)
    elif cmd == "avg":
        print(absAvg(emgList))
    elif cmd == "limit":
        limit = int(val)
        print("Emg limit set to ", val)
    elif cmd == "thresh":
        thresh = int(val)
        print("Thresh set to ", val)
    elif cmd == "read":
        print(interpret(absAvg(emgList)))
    elif cmd == "zero":
        getZero = True
    elif cmd == "quit":
        sys.exit()
    elif cmd == "stopmat":
        msg = "3, 0, 0, 0, 0, 0, 0, 0"
        sock.sendto(msg.encode('utf-8'), (ip, port))
    elif cmd == "textpos":
        print(gestFont.render("test", 1, (10, 10, 10)).get_rect().y)
    elif cmd == "phase":
        print(markers)
        
def absAvg(sigs):
    res = [0 for i in range(0, len(sigs[0]))]
    
    for tup in range(0, len(sigs)):
        for chan in range(0, len(sigs[tup])):
            res[chan] += abs(sigs[tup][chan])
    for chan in range(0, len(res)):
        res[chan] /= len(sigs)

    return res

def avg(sigs):
    res = [0 for i in range(0, len(sigs[0]))]
    
    for tup in range(0, len(sigs)):
        for chan in range(0, len(sigs[tup])):
            res[chan] += sigs[tup][chan]
    for chan in range(0, len(res)):
        res[chan] /= len(sigs)

    return res
            
def distance(list1, list2):
    total = 0
    for i in range(0, len(list1)):
        total += (list1[i] - list2[i])**2
    return math.sqrt(total)

def interpret(sigs):
    global thresh
    global archetypes
    
    mins = [1 for num in sigs if num >= thresh]

    if len(mins) > 0:
        smallest = ["left", math.inf]
        
        for arch in archetypes:
            d = distance(sigs, archetypes[arch])
            if d < smallest[1]:
                smallest[0] = arch
                smallest[1] = d
        return smallest[0]
    else:
        return "rest"
    
def learn(arch):
    global learnCount
    global learnVal
    
    learnCount = 0
    learnVal = arch

def learnFile(path):
    global archetypes

    with open(path) as file:
        archetypes = ast.literal_eval(file.read())

def save(name, contents):
    with open(name, "w") as file:
        file.write(str(contents))

def zeroOut(zero, pos):
    return {key: str(round(float(pos[key]) - float(zero[key]), 3)) for key in pos.keys()}

def vibrate(feed, val):
    feed.get_connected_devices()[0].vibrate(val)

def crossP(vec1, vec2):
	vec1 = unitVec(vec1)
	vec2 = unitVec(vec2)
	return [vec1[1] * vec2[2] - vec1[2] * vec2[1], -1 * vec1[0] * vec2[2] + vec1[2] * vec2[0], vec1[0] * vec2[1] - vec1[1] * vec2[0]]

def roundVec(vec, amt):
	return [round(num, amt) for num in vec]

def unitVec(vec):
	mag = 0
	for i in vec:
		mag += i ** 2
	mag = math.sqrt(mag)
	return [i / mag for i in vec]

def secondThread():
    global out
    global stopped

    myolib.init("myo-sdk-win-0.9.0/bin")
    feed = myolib.device_listener.Feed()
    hub = myolib.Hub()
    hub.run(1000, Listener())
    hub2 = myolib.Hub()
    hub2.run(1000, feed)
    vibrate(feed, 3)
    haptix = subprocess.Popen(["C:\\Users\\qiushifu\\Desktop\\MyoPythonProgram\\mjhaptix140\\program\\mjhaptix.exe"])
    #matlab = subprocess.Popen(["C:\\Program Files\\MATLAB\\R2016a\\bin\\matlab.exe"])
    learnFile("main.txt")
    
    try:
        while hub.running:
            args = input("\nEnter command: ")
            readCmd(args.split())
    except KeyboardInterrupt:
        print("\nQuitting")
        stopped = True
        msg = "3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0"
        sock.sendto(msg.encode('utf-8'), (ip, port))
        sock.close()
        hub.shutdown()
        pygame.quit()
        haptix.kill()
        os.kill(pid, 9)
    finally:
        stopped = True
        msg = "3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0"
        sock.sendto(msg.encode('utf-8'), (ip, port))
        sock.close()
        hub.shutdown()
        pygame.quit()
        haptix.kill()
        os.kill(pid, 9)

def pygameThread():
    global translate
    global gestFont
    global outputFont
    global background
    global markers
    global zeroPos
    global rot
    global center

    pygame.init()
    sock.bind(("localhost", portIn))

    pwidth = 700
    pheight = 200
    pscreen = pygame.display.set_mode((pwidth, pheight))
    
    background = pygame.Surface(pscreen.get_size()).convert()
    background.fill((250, 250, 250))

    gestFont = pygame.font.Font(None, 40)
    outputFont = pygame.font.Font(None, 18)

    show("test2", "out")
    
    while True:
        try:
            data = sock.recvfrom(1024)[0].decode("utf-8")[:-1].split(",")
            markers = []
            for i in [x for x in range(0, 9) if x % 3 == 0]:
                if float(data[0 + i]) != 0.0 and float(data[1 + i]) != 0.0 and float(data[2 + i]) != 0.0:
                    markers.append([float(data[2 + i]), float(data[0 + i]), float(data[1 + i])])

            center = [(markers[0][0] + markers[1][0]) / 2, (markers[0][1] + markers[1][1]) / 2, (markers[0][2] + markers[1][2]) / 2]
            vec1 = [markers[2][0] - center[0], markers[2][1] - center[1], markers[2][2] - center[2]]
            vec2 = [markers[0][0] - markers[1][0], markers[0][1] - markers[1][1], markers[0][2] - markers[1][2]]
            vec3 = crossP(vec1, vec2)
            vec1 = crossP(vec3, vec2)
            rot = [roundVec(unitVec(vec3), 3), roundVec(unitVec(vec2), 3), roundVec(unitVec(vec1), 3)]
        except:
            pass
        
        pscreen.blit(background, (0, 0))
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    translate[1] = "1"
                elif event.key == pygame.K_s:
                    translate[1] = "-1"
                elif event.key == pygame.K_a:
                    translate[0] = "-1"
                elif event.key == pygame.K_d:
                    translate[0] = "1"
                elif event.key == pygame.K_SPACE:
                    translate[2] = "1"
                elif event.key == pygame.K_LSHIFT:
                    translate[2] = "-1"
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_w or event.key == pygame.K_s:
                    translate[1] = "0"
                elif event.key == pygame.K_a or event.key == pygame.K_d:
                    translate[0] = "0"
                elif event.key == pygame.K_SPACE or event.key == pygame.K_LSHIFT:
                    translate[2] = "0"

def processPos(method, sigs):
    if method == "avg":
        if len(sigs) == 9:
            sensors = []
            for i in [x for x in range(0, 9) if x % 3 == 0]:
                sensors.append([sigs[0 + i], sigs[1 + i], sigs[2 + i]])
            return [round(val, 3) for val in avg(sensors)]

def show(text, fontType):
    global gestFont
    global outputFont
    global background
    global out

    if gestFont is not None:
        if fontType == "gest":
            text = gestFont.render(text, 1, (10, 10, 10))
            
            textPos = text.get_rect()
            textPos.centerx = background.get_rect().centerx
            textPos.y = 50

            outText = outputFont.render(out, 1, (10, 10, 10))
            outPos = outText.get_rect()
            outPos.centerx = background.get_rect().centerx
            outPos.y = 80
            
            background.fill((250, 250, 250))
            background.blit(text, textPos)
            background.blit(outText, outPos)
        else:
            out = text

pid = os.getpid()
threading.Thread(target=secondThread).start()
pygameThread()
