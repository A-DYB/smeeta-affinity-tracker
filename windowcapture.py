import numpy as np
import win32gui, win32ui, win32con
from win32api import GetSystemMetrics

class WindowCapture:

    # properties
    w = 450
    h = 100
    base_h = h
    offset_x = 180
    hwnd = None
    window_name = None
    cropped_x = cropped_y = 0

    # constructor
    def __init__(self, window_name, dim):
        self.window_name = window_name
        # find the handle for the window we want to capture
        self.hwnd = win32gui.FindWindow(None, self.window_name)
        if not self.hwnd:
            raise Exception('Window not found: {}'.format(window_name))

        #get window properties
        rect = win32gui.GetWindowRect(self.hwnd)
        win_w = rect[2] - rect[0]
        y_border_thickness = GetSystemMetrics(33) + 2 * GetSystemMetrics(4)
        
        #width and height of detection box
        self.w, self.h = dim
        self.base_h = self.h
        #Upper left corner of detection box, given top left of screen is 0,0
        self.cropped_x, self.cropped_y  = ( int(win_w - self.w - self.offset_x) , int(y_border_thickness) )

    def get_screenshot(self, avg_width):
        self.w = int(avg_width * 14)
        #get window properties
        rect = win32gui.GetWindowRect(self.hwnd)
        win_w = rect[2] - rect[0]
        y_border_thickness = GetSystemMetrics(33) + GetSystemMetrics(4)
        ui_scale = avg_width/(36)
        if ui_scale<1:
            ui_scale=1
        self.h = int(ui_scale * self.base_h)

        #Upper left corner of detection box, given top left of screen is 0,0
        self.cropped_x, self.cropped_y  = ( int(win_w - self.w - self.offset_x * ui_scale) , int(y_border_thickness) )

        # get the window image data
        try:
            wDC = win32gui.GetWindowDC(self.hwnd)
        except:
            raise Exception('Window not found: {}'.format(self.window_name))

        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, self.w, self.h)
        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0, 0), (self.w, self.h), dcObj, (self.cropped_x, self.cropped_y), win32con.SRCCOPY)

        # convert the raw data into a format opencv can read
        #dataBitMap.SaveBitmapFile(cDC, 'debug.bmp')
        signedIntsArray = dataBitMap.GetBitmapBits(True)
        img = np.fromstring(signedIntsArray, dtype='uint8')
        img.shape = (self.h, self.w, 4)

        # free resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        # drop the alpha channel, or cv.matchTemplate() will throw an error like:
        #   error: (-215:Assertion failed) (depth == CV_8U || depth == CV_32F) && type == _templ.type() 
        #   && _img.dims() <= 2 in function 'cv::matchTemplate'
        img = img[...,:3]

        # make image C_CONTIGUOUS to avoid errors that look like:
        #   File ... in draw_rectangles
        #   TypeError: an integer is required (got type tuple)
        # see the discussion here:
        # https://github.com/opencv/opencv/issues/14866#issuecomment-580207109
        img = np.ascontiguousarray(img)

        return img
    def get_window_size(self):
        rect = win32gui.GetWindowRect(self.hwnd)
        win_x = rect[0]
        win_y = rect[1]
        win_w = rect[2] - win_x
        win_h = rect[3] - win_y

        return (win_x, win_y, win_w, win_h)