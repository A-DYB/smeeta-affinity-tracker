
from ctypes import wintypes
import pytesseract
from pytesseract import Output
import cv2
import numpy as np
from playsound import playsound
import os 
import sys
import time
from threading import Timer
from threading import Thread
import string
from windowcapture import WindowCapture
import keyboard 
import pickle
from os import SEEK_END
import io
from lz.reversal import reverse
import threading
from win32com.shell import shell, shellcon

path = os.path.join(shell.SHGetFolderPath(0, shellcon.CSIDL_LOCAL_APPDATA, None, 0), 'Warframe\ee.log')
debug = False
min_time = 130
max_time = 156

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, 'Tesseract-OCR\\tesseract.exe')

pytesseract.pytesseract.tesseract_cmd = filename

state = 0
WHITE = [255, 255, 255]
count = 0
prev_ended_time = 0 
proc_list = []
proc_time = [0, 0, 0 ,0 ,0 ]
ui_scale = 1


mission_start=0
mission_end=0
mission_time=0
tot_mission_t=0
total_proc_time=[0,0,0,0,0]

start_time = time.time()
acolyte_time = 0
last_acolyte_time = time.time()

prev_time = '0'
scan_time = '0'

threads = []
stop_threads = False
in_mission = False

# initialize the WindowCapture class
#window name, coordinate (top right frame of ref), box size
wincap = WindowCapture('Warframe', (int(650+490*(ui_scale-1)), int(60+12*(ui_scale-1)) ) , (int(460 +340*(ui_scale-1)), int(85 +80*(ui_scale-1))) )

def save_mission_stats():
    global path
    start_time = 0
    acolyte = []
    with open(path) as file:
        for line in reverse(file, batch_size=io.DEFAULT_BUFFER_SIZE):
            #find mission state
            if "GameRulesImpl::StartRound()" in line:
                start_time = float(line.split(" ")[0])
                break
            #find last acolyte
            if "OnAgentCreated " in line and "Acolyte" in line:
                acolyte.append(line.split(" ")[0])

    if len(acolyte) > 0:
        acolyte.reverse()
        acolyte_int = []
        for i in range(len(acolyte)):
            if i == 0:
                acolyte_int.append(float(acolyte[i])-float(start_time))
            else:
                acolyte_int.append(float(acolyte[i])-float(acolyte[i-1]))
        avg_time = sum(acolyte_int)/len(acolyte_int)
        f = open("E:\Warframe stuff\Code\VisionProject_dist\mission_log.txt", "w")
        f.write("Average Acolyte spawn time: " + get_time_str(avg_time) + "\n")
        for elem in acolyte_int:
            f.write(get_time_str(elem)+ "\n")
        f.close()

def check_acolyte():
    global prev_time
    global scan_time
    global last_acolyte_time
    global path
    global in_mission
    i=0
    with open(path) as file:
        for line in reverse(file, batch_size=io.DEFAULT_BUFFER_SIZE):
            if i == 0:
                cur_time = line.split(" ")[0]
            scan_time = line.split(" ")[0]
            
            if scan_time == prev_time:
                prev_time = cur_time
                break
            #find mission state
            if "GameRulesImpl::StartRound()" in line:
                in_mission = True
                prev_time = cur_time
                return (time.time() - (float(cur_time) - float(line.split(" ")[0])))
            #EndOfMatch.lua: Initialize
            #LotusGameRules::EndSessionCallback
            elif 'Game [Info]: CommitInventoryChangesToDB' in line:
                in_mission = False
                prev_time = cur_time
                save_mission_stats()
                return time.time()
            #find last acolyte
            if "OnAgentCreated " in line and "Acolyte" in line:
                prev_time = cur_time
                return time.time() - (float(cur_time) - float(line.split(" ")[0]))

            i+=1
    prev_time = cur_time
    return last_acolyte_time

def scan_file():
    global last_acolyte_time
    global stop_threads
    while(True):
        if stop_threads:
            break
        #scan mission state
        last_acolyte_time = check_acolyte()
        time.sleep(10)

def get_time_str(secs):
    mins = (int)(secs/60)
    sr = int(secs - mins*60)
    return str(mins)+":"+str(sr)

def clear():
    os.system( 'cls' )

def print_stats():
    global state
    global proc_list
    global acolyte_time
    global display_text

    if not debug:    
        clear()
    UP = "\x1B[6A"
    CLR = "\x1B[0K"

    while True:
        if stop_threads:
            break
        if in_mission:
            UP = "\x1B["+ str(state+2) + "A"
            t= time.time()
            if state == 0:
                print(f"{UP}Time since last acolyte: {get_time_str(acolyte_time)}{CLR}\n")
            elif state == 1:
                print(f"{UP}Time since last acolyte: {get_time_str(acolyte_time)}{CLR}\nProc 1 Time remaining: {round(proc_list[0]-t,1)}{CLR}\n")
            elif state == 2:
                print(f"{UP}Time since last acolyte: {get_time_str(acolyte_time)}{CLR}\nProc 1 Time remaining: {round(proc_list[0]-t,1)}{CLR}\nProc 2 Time remaining: {round(proc_list[1]-t,1)}{CLR}\n")
            elif state == 3:
                print(f"{UP}Time since last acolyte: {get_time_str(acolyte_time)}{CLR}\nProc 1 Time remaining: {round(proc_list[0]-t,1)}{CLR}\nProc 2 Time remaining: {round(proc_list[1]-t,1)}{CLR}\nProc 3 Time remaining: {round(proc_list[2]-t,1)}{CLR}\n")
            elif state == 4:
                print(f"{UP}Time since last acolyte: {get_time_str(acolyte_time)}{CLR}\nProc 1 Time remaining: {round(proc_list[0]-t,1)}{CLR}\nProc 2 Time remaining: {round(proc_list[1]-t,1)}{CLR}\nProc 3 Time remaining: {round(proc_list[2]-t,1)}{CLR}\nProc 4 Time remaining: {round(proc_list[3]-t,1)}{CLR}\n")
            elif state == 5:
                print(f"{UP}Time since last acolyte: {get_time_str(acolyte_time)}{CLR}\nProc 1 Time remaining: {round(proc_list[0]-t,1)}{CLR}\nProc 2 Time remaining: {round(proc_list[1]-t,1)}{CLR}\nProc 3 Time remaining: {round(proc_list[2]-t,1)}{CLR}\nProc 4 Time remaining: {round(proc_list[3]-t,1)}{CLR}\nProc 5 Time remaining: {round(proc_list[4]-t,1)}{CLR}\n")
        else:
            UP = "\x1B[2A"
            print(f"{UP}Time since last acolyte: Not in a mission!{CLR}\n")
        time.sleep(0.5)

def onkeypress(event):
    global state
    global proc_list
    
    if event.name == '`' :
        t= time.time()
        if state == 0:
            play_s( os.path.join(dirname, 'Sounds\\none.mp3') , bl=True)
        else:
            play_s(os.path.join(dirname, 'Sounds\\Numbers\\' + str(int(proc_list[0]-t)) + '.mp3'), bl=True)
            play_s(os.path.join(dirname, 'Sounds\\seconds_remain.mp3'), bl=True)
            if state == 1:
                play_s( os.path.join(dirname,'Sounds\\single.mp3') )
            elif state == 2:
                play_s(os.path.join(dirname,'Sounds\\double.mp3') )
            elif state == 3:
                play_s(os.path.join(dirname,'Sounds\\triple.mp3') )
            elif state == 4:
                play_s(os.path.join(dirname, 'Sounds\\quadruple.mp3') )
            elif state == 5:
                play_s(os.path.join(dirname, 'Sounds\\quadruple.mp3') )

def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

def get_rot_hls_mask(image, sens, deg):
    rows,cols,_ = image.shape
    HLS_low = np.array([0,255-sens,0], dtype=np.uint8)
    HLS_high = np.array([255,255,255], dtype=np.uint8)
    mask = cv2.inRange(image, HLS_low, HLS_high)

    M = cv2.getRotationMatrix2D((cols/2, rows/2), deg, 1)
    rot = cv2.warpAffine(mask, M, (cols, rows))
    gray = cv2.bitwise_not(rot)

    return gray

def play_s(file_name, bl = False):
    try:
        playsound(file_name,bl)
    except:
        print("Sound not found! -> ",file_name)

def proc_handler(tim, end_time):
    global proc_list
    global state
    global threads

    t= time.time()

    play_s( os.path.join(dirname,'Sounds\\Numbers\\'+ str(int(proc_list[0]-t)) + '.mp3') , bl=True)
    play_s(os.path.join(dirname,'Sounds\\seconds_remain.mp3'), bl=True)
    if state ==1:
        play_s( os.path.join(dirname,'Sounds\\single.mp3') )
    elif state == 2:   
        play_s(os.path.join(dirname,'Sounds\\double.mp3') )
    elif state ==3:
        play_s(os.path.join(dirname,'Sounds\\triple.mp3') )
    elif state ==4:
        play_s(os.path.join(dirname, 'Sounds\\quadruple.mp3') )
    elif state ==5:
        play_s(os.path.join(dirname, 'Sounds\\quintuple.mp3') )

    target_time = end_time - 18
    while time.time() < target_time:
        corr =  (target_time - time.time())/2
        if corr < 1:
            time.sleep(target_time - time.time())
        else:
            time.sleep(corr)
        if stop_threads:
            break

    play_s( os.path.join(dirname, 'Sounds\\warn.mp3') )
    time.sleep(18)

    t = time.time()

    del proc_list[0]

    state -= 1
    if state < 0:
        state = 0
 
    clear()

    if state == 0:
        play_s( os.path.join(dirname, 'Sounds\\none.mp3') )
    else:
        play_s( os.path.join(dirname,'Sounds\\Numbers\\'+ str(int(proc_list[0]-t)) + '.mp3') , bl=True)
        play_s(os.path.join(dirname,'Sounds\\seconds_remain.mp3'), bl=True)
        if state ==1:
            play_s( os.path.join(dirname,'Sounds\\single.mp3') )
        elif state == 2:
            play_s(os.path.join(dirname,'Sounds\\double.mp3') )
        elif state ==3:
            play_s(os.path.join(dirname,'Sounds\\triple.mp3') )
        elif state ==4:
            play_s(os.path.join(dirname, 'Sounds\\quadruple.mp3') )


    threads.pop(0)
    

def main():
    global state
    global debug
    global proc_list
    global acolyte_time
    global stop_threads
    global threads
    global min_time
    global max_time
    

    keyboard.on_release(onkeypress)
    x = threading.Thread(target=scan_file)
    x.start()

    x2 = threading.Thread(target=print_stats)
    x2.start()

    cur_time = 0

    try: 
        while True:  
            
            if stop_threads:
                break
            if in_mission:
                cur_time = time.time()
            
                image = wincap.get_screenshot() 
                rows, cols, _ = image.shape       

                
                #snapshot time screenie was taken
                cur_t = time.time()

                #HLS 50
                hls = cv2.cvtColor(image, cv2.COLOR_BGR2HLS)
                line1_mask = get_rot_hls_mask(hls,50,-3.6/ui_scale)

                scale = 5/ui_scale
                line1 = cv2.resize( line1_mask,None,  fx = scale, fy = scale)
                #15
                filt = 5
                close = cv2.GaussianBlur(line1,(filt,filt),0)

                #ret,img = cv2.threshold(close,170,255,cv2.THRESH_BINARY)  
                img = cv2.threshold(close, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                d = pytesseract.image_to_data(img, lang='eng',config='-c tessedit_do_invert=0 -c tessedit_char_whitelist="0123456789x.%m " --psm 11', output_type=Output.DICT)

                '''
                if img.shape[1] >1080:
                    cv2.imshow('Computer Vision', cv2.resize( img,None,  fx = 1080/img.shape[1], fy = 1080/img.shape[1]))
                else:
                    cv2.imshow('Computer Vision', img)
                '''

                n_boxes = len(d['level'])
                for i in range(n_boxes):
                    if d['text'][i] is not '' and debug:
                        print("OUTPUT " + str(count)+": " + d['text'][i] + "    Conf: " ,d['conf'][i],"     Is float:",isfloat(d['text'][i]))

                    if isfloat(d['text'][i]):
                        result = float(d['text'][i])

                        if '.' in d['text'][i]:
                            result = float(d['text'][i])
                        else:
                            result = float(d['text'][i].replace('.',''))/10

                        if d['conf'][i] >= 50:
                            #129 and result < 156
                            if (result > min_time and result <= max_time) :

                                wid = d['width'][i]

                                if wid >= 29*scale*ui_scale and wid <= 38*scale*ui_scale:

                                    if not proc_list:
                                        state +=1
                                        proc_list.append(cur_time + float(result))

                                        t1 = threading.Thread(target=proc_handler, args=(float(result), cur_time + float(result), ))
                                        t1.start()
                                        threads.append(t1)

                                    else:
                                        if result > ( proc_list[state - 1] - cur_time + 25 ):

                                            #New proc, append end time
                                            proc_list.append(cur_time + result)
                                            state +=1

                                            t1 = threading.Thread(target=proc_handler, args=(float(result), cur_time + float(result), ))
                                            t1.start()
                                            threads.append(t1)

                                        else:
                                            if debug:
                                                print("Failed ability cooldown test (ability occured too soon after previous ability)")
                                else:
                                    if debug:
                                        print("Failed text width test: ", wid, "    Required a range of ",int(29*scale),int(38*scale))
                            else:
                                if debug:
                                    print("Failed valid time range test. Got: ", result, 'Expected: ('+str(min_time)+', '+str(max_time)+')')
                        else:
                            if debug:
                                print("Failed OCR confidence level test")

                acolyte_time = (int)(cur_time - last_acolyte_time)
                
                if cv2.waitKey(1) == ord('q'):
                    cv2.destroyAllWindows()
                    stop_threads = True
                    os._exit(1)
            #run once a second
            time.sleep(1)
    except KeyboardInterrupt:
        clear()
        stop_threads = True
        x.join()
        os._exit(1)

if __name__ == '__main__':
    main()

