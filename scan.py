import pytesseract
from pytesseract import Output
import cv2
import numpy as np
from playsound import playsound
import os 
import time
from threading import Timer
from threading import Thread
import string
from windowcapture import WindowCapture
import keyboard 
import pickle

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
min_time = 119
max_time = 156

mission_start=0
mission_end=0
mission_time=0
tot_mission_t=0
total_proc_time=[0,0,0,0,0]


# initialize the WindowCapture class
#window name, coordinate (top right frame of ref), box size

wincap = WindowCapture('Warframe', (int(650+490*(ui_scale-1)), int(60+12*(ui_scale-1)) ) , (int(460 +340*(ui_scale-1)), int(85 +80*(ui_scale-1))) )

def onkeypress(event):
    global state
    global proc_list
    
    if event.name == '`' :
        t= time.time()
        if state == 0:
            play_s( os.path.join(dirname, 'Sounds\\none.mp3') , bl=True)
        elif state ==1:
            play_s( os.path.join(dirname,'Sounds\\single.mp3') , bl=True)
            play_s( os.path.join(dirname,'Sounds\\Numbers\\'+ str(int(proc_list[0]-t)) + '.mp3') , bl=True)
            play_s(os.path.join(dirname,'Sounds\\seconds_remain.mp3'))
        elif state == 2:
            play_s(os.path.join(dirname,'Sounds\\double.mp3') , bl=True)
            play_s(os.path.join(dirname,'Sounds\\Numbers\\'+ str(int(proc_list[0]-t)) + '.mp3'), bl=True)
            play_s(os.path.join(dirname,'Sounds\\seconds_remain.mp3'))
        elif state ==3:
            play_s(os.path.join(dirname,'Sounds\\triple.mp3') , bl=True)
            play_s(os.path.join(dirname,'Sounds\\Numbers\\'+ str(int(proc_list[0]-t)) + '.mp3'), bl=True)
            play_s(os.path.join(dirname,'Sounds\\seconds_remain.mp3'))
        elif state ==4:
            play_s(os.path.join(dirname, 'Sounds\\quadruple.mp3') , bl=True)
            play_s(os.path.join(dirname, 'Sounds\\Numbers\\' + str(int(proc_list[0]-t)) + '.mp3'), bl=True)
            play_s(os.path.join(dirname, 'Sounds\\seconds_remain.mp3'))

def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

def clean_input(text_pic):
    return text_pic
    morph = cv2.morphologyEx(text_pic, cv2.MORPH_OPEN, np.ones((3,3), np.uint8), iterations=1)
    morph = cv2.morphologyEx(morph, cv2.MORPH_CLOSE, np.ones((3,1), np.uint8), iterations=1)
    return morph

def get_rot_hls_mask(image, sens, deg):

    HLS_low = np.array([0,255-sens,0], dtype=np.uint8)
    HLS_high = np.array([255,255,255], dtype=np.uint8)
    mask = cv2.inRange(hls, HLS_low, HLS_high)

    M = cv2.getRotationMatrix2D((cols/2, rows/2), deg, 1)
    rot = cv2.warpAffine(mask, M, (cols, rows))
    gray = cv2.bitwise_not(rot)

    return gray

def play_s(file_name, bl = False):
    try:
        playsound(file_name,bl)
    except:
        print("Sound not found! -> ",file_name)

def warn_timer():
    global state
    global proc_list
    global proc_time
    global prev_ended_time
    global max_time
    
    play_s( os.path.join(dirname, 'Sounds\\warn.mp3') )
    time.sleep(18)

    print('State b4 destroy: ',state)

    t = time.time()

    #compute times of active procs
    prev_start = t
    cur_start = 0
    #loop in reverse
    for index, e in reversed(list(enumerate(proc_list))):
        if prev_ended_time != 0:
            cur_start = prev_ended_time
        else:
            cur_start = e - max_time
            #print('Cur start: ',cur_start)
        #sub 1st proc's end and last elem's start

        proc_time[index] += (prev_start - cur_start)
        prev_start = cur_start
    prev_ended_time = t

    state -= 1
    if state < 0:
        state = 0
    if state == 0:
        prev_ended_time = 0
        print(proc_time)
    
    del proc_list[0]
 
    if state == 0:
        play_s( os.path.join(dirname, 'Sounds\\none.mp3') )
    elif state ==1:
        play_s( os.path.join(dirname,'Sounds\\single.mp3') , bl=True)
        play_s( os.path.join(dirname,'Sounds\\Numbers\\'+ str(int(proc_list[0]-t)) + '.mp3') , bl=True)
        play_s(os.path.join(dirname,'Sounds\\seconds_remain.mp3'))
    elif state == 2:
        play_s(os.path.join(dirname,'Sounds\\double.mp3') , bl=True)
        play_s(os.path.join(dirname,'Sounds\\Numbers\\'+ str(int(proc_list[0]-t)) + '.mp3'), bl=True)
        play_s(os.path.join(dirname,'Sounds\\seconds_remain.mp3'))
    elif state ==3:
        play_s(os.path.join(dirname,'Sounds\\triple.mp3') , bl=True)
        play_s(os.path.join(dirname,'Sounds\\Numbers\\'+ str(int(proc_list[0]-t)) + '.mp3'), bl=True)
        play_s(os.path.join(dirname,'Sounds\\seconds_remain.mp3'))
    elif state ==4:
        play_s(os.path.join(dirname, 'Sounds\\quadruple.mp3') , bl=True)
        play_s(os.path.join(dirname, 'Sounds\\Numbers\\' + str(int(proc_list[0]-t)) + '.mp3'), bl=True)
        play_s(os.path.join(dirname, 'Sounds\\seconds_remain.mp3'))

keyboard.on_release(onkeypress)

cur_time = 0

try:
    while True:  
        #print("scanning...")
        cur_time = time.time()
    
        image = wincap.get_screenshot() 
        rows, cols, _ = image.shape       

        #snapshot time screenie was taken
        cur_t = time.time()

        #HLS 50
        hls = cv2.cvtColor(image, cv2.COLOR_BGR2HLS)
        line1_mask = get_rot_hls_mask(hls,50,-3.6/ui_scale)

        scale = 5/ui_scale

        #controversial
        line1 = cv2.resize( line1_mask,None,  fx = scale, fy = scale)
        

        close = clean_input(line1)
        #15
        filt = 5
        close = cv2.GaussianBlur(line1,(filt,filt),0)

        #ret,img = cv2.threshold(close,170,255,cv2.THRESH_BINARY)  
        img = cv2.threshold(close, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
        d = pytesseract.image_to_data(img, lang='eng',config='-c tessedit_do_invert=0 -c tessedit_char_whitelist="0123456789x.%m " --psm 11', output_type=Output.DICT)

        #img = image
        '''
        if img.shape[1] >1080:
            cv2.imshow('Computer Vision', cv2.resize( img,None,  fx = 1080/img.shape[1], fy = 1080/img.shape[1]))
        else:
            cv2.imshow('Computer Vision', img)
        '''

        n_boxes = len(d['level'])
        for i in range(n_boxes):
            if d['text'][i] is not '':
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
                            
                            #no procs active
                            if not proc_list:
                                state +=1
                                proc_list.append(cur_time + float(result))
                                print('Proc 1')

                                t = Timer(float(result)-18.0, warn_timer)
                                t.start()

                                play_s(os.path.join(dirname,'Sounds\\Numbers\\'+ str(int(result)) +'.mp3'))

                            else:
                                if result > ( proc_list[state - 1] - cur_time + 25 ):

                                    #New proc, append end time
                                    proc_list.append(cur_time + result)
                                    state +=1
                                    print('Proc ',len(proc_list))

                                    t = Timer(float(result)-18.0, warn_timer)
                                    t.start()

                                    # of procs
                                    play_s(os.path.join(dirname,'Sounds\\Numbers\\'+ str(len(proc_list)) +'.mp3'), bl=True)
                                    play_s(os.path.join(dirname,'Sounds\\procs_active.mp3'), bl=True)
                                    # seconds
                                    play_s(os.path.join(dirname,'Sounds\\Numbers\\'+ str(int(proc_list[0]-time.time())) +'.mp3'), bl=True)
                                    play_s(os.path.join(dirname,'Sounds\\seconds_remain.mp3'))
                                else:
                                    print("Failed ability cooldown test (ability occured too soon after previous ability)")
                        else:
                            print("Failed text width test: ", wid, "    Required a range of ",int(29*scale),int(38*scale))
                    else:
                        print("Failed valid time range test. Got: ", result, 'Expected: ('+str(min_time)+', '+str(max_time)+')')
                else:
                    print("Failed OCR confidence level test")
        count += 1
        #print('\n')
        
        
        if cv2.waitKey(1) == ord('q'):
            cv2.destroyAllWindows()
            os._exit(1)
            break
        
        #run once a second
        time.sleep(1)
except KeyboardInterrupt:
    #ctrl C
    print("Quit")
    os._exit(1)

