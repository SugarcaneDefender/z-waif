import time
import numpy
import cv2
import tkinter
from tkinter import filedialog
import os

import utils.settings

# initialize the camera
# If you have multiple camera connected with
# current device, assign a value in cam_port
# variable according to that

vision_enabled_string = os.environ.get("MODULE_VISUAL")
if vision_enabled_string == "ON":
    utils.settings.vision_enabled = True
else:
    utils.settings.vision_enabled = False

if utils.settings.vision_enabled:
    cam_port = 0
    cam = cv2.VideoCapture(cam_port)

root = tkinter.Tk()
root.withdraw() #use to hide tkinter window


def capture_pic():

    # reading the input using the camera
    result, image = cam.read()

    # If image will detected without any error,
    # show result
    if result:

        image = cv2.resize(image,(320, 240))
        # saving image in local storage
        cv2.imwrite("LiveImage.png", image)

        # Show it to us, if we are previewing!
        if utils.settings.cam_image_preview:
            cv2.imshow("Z-Waif Image Preview", image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()


    # If captured image is corrupted, moving to else part
    else:
        print("No camera to take pictures from!")


def use_image_feed():

    # Read the feed, Sneed
    image = cv2.imread(browse_feed_image())

    # Resize it accoring to max width/height
    maxwidth = 360
    maxheight = 360

    f1 = maxwidth / image.shape[1]
    f2 = maxheight / image.shape[0]
    f = min(f1, f2)  # resizing factor
    dim = (int(image.shape[1] * f), int(image.shape[0] * f))
    image = cv2.resize(image, dim)

    # saving image in local storage
    cv2.imwrite("LiveImage.png", image)



def browse_feed_image():
    currdir = os.getcwd()
    browsed_image_path = filedialog.askopenfilename(parent=root, initialdir=currdir, title='Please select the image', filetypes=[("JPG", '*.jpg'), ("PNG", '*.png'), ("JPEG", '*.jpeg')])
    return browsed_image_path

