import numpy as np
import win32gui, win32ui, win32con
from win32api import GetSystemMetrics

class WindowCapture:

    # properties
    w = 450
    h = 100
    hwnd = None
    window_name = None
    cropped_x = 0
    cropped_y = 0
    offset_x = 0
    offset_y = 0
    x_coord=y_coord=0

    # constructor
    def __init__(self, window_name, coord, dim):

        # find the handle for the window we want to capture
        self.x_coord,self.y_coord = coord
        self.cropped_x, self.cropped_y  = (GetSystemMetrics(0)-self.x_coord,self.y_coord)
        self.w, self.h = dim
        self.window_name = window_name
        
        self.hwnd = win32gui.FindWindow(None, self.window_name)

        if not self.hwnd:
            raise Exception('Window not found: {}'.format(window_name))
        

    def get_screenshot(self):

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