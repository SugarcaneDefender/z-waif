import time
import numpy
import cv2
import tkinter
from tkinter import filedialog
import os

import utils.settings
import utils.vtube_studio
import random

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



def loop_random_look():

    # give us a little bit of boot time...
    time.sleep(20)

    while True:
        time.sleep(4 + random.uniform(0.0, 6.0))

        rand_look_value = random.uniform(-0.47, 0.47) + random.uniform(-0.47, 0.47)

        utils.vtube_studio.change_look_level(rand_look_value)

def loop_follow_look():

    # give us a little bit of boot time...
    time.sleep(10)

    while True:
        time.sleep(2)

        capture_follow_pic()

def capture_follow_pic():

    # reading the input using the camera
    result, img = cam.read()

    # If image will detected without any error,
    # show result
    if result:

        img = cv2.resize(img, (800, 450))

        # Load the cascade
        face_cascade = cv2.CascadeClassifier('utils/resource/haarcascade_frontalface_default.xml')

        # Convert into grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 7)

        # Follow the faces accoring to the X-cooridnate
        # If there are multiple, go at random
        if len(faces) == 0:
            return

        face_spot = -1
        for (x, y, w, h) in faces:
            if face_spot == -1:
                face_spot = x
            elif random.uniform(0.0, 1.0) > 0.3:
                face_spot = x + (w/2)

        face_span = (face_spot - 290) / -300
        utils.vtube_studio.change_look_level(face_span)



    # If captured image is corrupted, moving to else part
    else:
        print("No camera to take pictures from!")


