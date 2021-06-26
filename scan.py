import os 
import time
import io
import threading

from windowcapture import WindowCapture

import pytesseract
import cv2
import numpy as np
from playsound import playsound
import keyboard 
from lz.reversal import reverse
from win32com.shell import shell, shellcon

'''
Modify these to change settings
'''
debug = False
min_time = 119
max_time = 156
'''
'''

path = os.path.join(shell.SHGetFolderPath(0, shellcon.CSIDL_LOCAL_APPDATA, None, 0), 'Warframe\ee.log')
dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, 'Tesseract-OCR\\tesseract.exe')

pytesseract.pytesseract.tesseract_cmd = filename

state = 0
WHITE = [255, 255, 255]
count = 0
prev_ended_time = 0 
proc_list = []

acolyte_time = 0
acolyte_death_time = 0
last_acolyte_time = time.time()
last_acolyte_death = time.time()

prev_time = '0'
scan_time = '0'

threads = []
stop_threads = False
in_mission = False

# initialize the WindowCapture class
#window name, box size
wincap = WindowCapture('Warframe', ( 460 , 190 ) )

def save_mission_stats():
    global path
    global dirname
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
        f = open(os.path.join(dirname, 'mission_log.txt'), "w")
        f.write("Average Acolyte spawn time: " + get_time_str(avg_time) + "\n")
        for elem in acolyte_int:
            f.write(get_time_str(elem)+ "\n")
        f.close()


def check_acolyte():
    global prev_time
    global scan_time
    global last_acolyte_time
    global last_acolyte_death
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
                clear()
                prev_time = cur_time
                save_mission_stats()
                return time.time()
            #find last acolyte
            if "OnAgentCreated " in line and "Acolyte" in line:
                in_mission = True
                prev_time = cur_time
                return time.time() - (float(cur_time) - float(line.split(" ")[0]))
            
            if 'Script [Info]: LotusGameRules.lua: persistent enemy was killed!' in line :
                last_acolyte_death = time.time() - (float(cur_time) - float(line.split(" ")[0]))

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
    min_str = ''
    sec_str = ''
    mins = (int)(secs/60)
    sr = int(secs - mins*60)
    if mins < 10:
        min_str = '0'+str(mins)
    else:
        min_str = str(mins)
    if sr < 10:
        sec_str = '0'+str(sr)
    else:
        sec_str = str(sr)

    return "00:"+min_str+":"+sec_str

def clear():
    os.system( 'cls' )

def print_stats():
    global state
    global proc_list
    global acolyte_time
    global acolyte_death_time

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
                print(f"{UP}Time since last acolyte died: {get_time_str(acolyte_death_time)}{CLR}\n")
            elif state == 1:
                print(f"{UP}Time since last acolyte died: {get_time_str(acolyte_death_time)}{CLR}\nProc 1 Time remaining: {round(proc_list[0]-t,1)}{CLR}\n")
            elif state == 2:
                print(f"{UP}Time since last acolyte died: {get_time_str(acolyte_death_time)}{CLR}\nProc 1 Time remaining: {round(proc_list[0]-t,1)}{CLR}\nProc 2 Time remaining: {round(proc_list[1]-t,1)}{CLR}\n")
            elif state == 3:
                print(f"{UP}Time since last acolyte died: {get_time_str(acolyte_death_time)}{CLR}\nProc 1 Time remaining: {round(proc_list[0]-t,1)}{CLR}\nProc 2 Time remaining: {round(proc_list[1]-t,1)}{CLR}\nProc 3 Time remaining: {round(proc_list[2]-t,1)}{CLR}\n")
            elif state == 4:
                print(f"{UP}Time since last acolyte died: {get_time_str(acolyte_death_time)}{CLR}\nProc 1 Time remaining: {round(proc_list[0]-t,1)}{CLR}\nProc 2 Time remaining: {round(proc_list[1]-t,1)}{CLR}\nProc 3 Time remaining: {round(proc_list[2]-t,1)}{CLR}\nProc 4 Time remaining: {round(proc_list[3]-t,1)}{CLR}\n")
            elif state == 5:
                print(f"{UP}Time since last acolyte died: {get_time_str(acolyte_death_time)}{CLR}\nProc 1 Time remaining: {round(proc_list[0]-t,1)}{CLR}\nProc 2 Time remaining: {round(proc_list[1]-t,1)}{CLR}\nProc 3 Time remaining: {round(proc_list[2]-t,1)}{CLR}\nProc 4 Time remaining: {round(proc_list[3]-t,1)}{CLR}\nProc 5 Time remaining: {round(proc_list[4]-t,1)}{CLR}\n")
        else:
            UP = "\x1B[2A"
            print(f"{UP}Time since last acolyte: Not in a mission!{CLR}\n")
        time.sleep(0.5)

def onkeypress(event):
    global state
    global proc_list
    global dirname
    
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
    global dirname

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

def moving_average(window_size, data_list, sample):
    if len(data_list)<window_size:
        data_list.append(sample)
    else:
        data_list.pop(0)
        data_list.append(sample)
    if debug:
        print(data_list)

    return (sum(data_list)/len(data_list), data_list)

def main():
    global state
    global debug
    global proc_list
    global acolyte_time
    global acolyte_death_time
    global stop_threads
    global threads
    global min_time
    global max_time


    width_sample_list = []
    wid_avg = 36
    wid_sample_count = 1

    keyboard.on_release(onkeypress)

    x1 = threading.Thread(target=scan_file)
    x1.start()

    x2 = threading.Thread(target=print_stats)
    x2.start()


    cur_time = 0

    try: 
        while True:  
            
            if stop_threads:
                break
            if in_mission:
                cur_time = time.time()
            
                #wincap.set_window_size()
                image = wincap.get_screenshot(wid_avg) 
                x,y,w,h = wincap.get_window_size()

                rows, cols, _ = image.shape     
                #cv2.imshow("test",image) 

                #HLS 50
                hls = cv2.cvtColor(image, cv2.COLOR_BGR2HLS)
                line1_mask = get_rot_hls_mask(hls,50,-3.6)

                scale = 5
                #scale = (2300/(wid_avg * 12.75))
                line1 = cv2.resize(line1_mask,None,  fx = scale, fy = scale)
                #15
                filt = 5
                close = cv2.GaussianBlur(line1,(filt,filt),0)

                #ret,img = cv2.threshold(close,170,255,cv2.THRESH_BINARY)  
                img = cv2.threshold(close, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                d = pytesseract.image_to_data(img, lang='eng',config='-c tessedit_do_invert=0 -c tessedit_char_whitelist="0123456789x.%m " --psm 11', output_type=pytesseract.Output.DICT)

                '''
                if img.shape[1] >1080:
                    cv2.imshow('Computer Vision', cv2.resize( img,None,  fx = 1080/img.shape[1], fy = 1080/img.shape[1]))
                else:
                    cv2.imshow('Computer Vision', img)
                '''
                
                
                n_boxes = len(d['level'])
                for i in range(n_boxes):
                    if d['text'][i] is not '' and debug:
                        print("\nOUTPUT " + str(count)+": " + d['text'][i] + "    Conf: " ,d['conf'][i],"     Is float:",isfloat(d['text'][i]))
                        print( d['width'][i])

                    if isfloat(d['text'][i]):
                        result = float(d['text'][i])

                        if '.' in d['text'][i]:
                            result = float(d['text'][i])
                            if d['conf'][i] >= 50:
                                s_len = len(d['text'][i])

                                wid_avg, width_sample_list = moving_average(5, width_sample_list, d['width'][i]/s_len)
                                #wid_avg = (wid_avg * (wid_sample_count) + d['width'][i]/s_len)/(wid_sample_count+1)
                                #wid_sample_count+=1
                                if debug:
                                    print("AVERAGE WIDTH: ",wid_avg, d['width'][i], s_len, d['width'][i]/s_len, scale)
                        else:
                            result = float(d['text'][i])/10

                        if d['conf'][i] >= 50:
                            #129 and result < 156
                            
                            if (result > min_time and result <= max_time) :

                                wid = d['width'][i]

                                if wid >= (wid_avg - 0.15 * wid_avg)*scale and wid <= (wid_avg + 0.15 * wid_avg)*scale:
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
                                        print("Failed text width test: ", wid, "    Required a range of ",(wid_avg - 0.15 * wid_avg)*scale,(wid_avg + 0.15 * wid_avg)*scale)
                            else:
                                if debug:
                                    print("Failed valid time range test. Got: ", result, 'Expected: ('+str(min_time)+', '+str(max_time)+')')
                        else:
                            if debug:
                                print("Failed OCR confidence level test")

                acolyte_time = (int)(cur_time - last_acolyte_time)
                acolyte_death_time = (int)(cur_time - last_acolyte_death)
                
                if cv2.waitKey(1) == ord('q'):
                    cv2.destroyAllWindows()
                    stop_threads = True
                    os._exit(1)
            #run once a second
            time.sleep(1)
    except KeyboardInterrupt:
        clear()
        stop_threads = True
        #x1.join()
        os._exit(1)

if __name__ == '__main__':
    main()

