import time
import numpy
import cv2

# initialize the camera
# If you have multiple camera connected with
# current device, assign a value in cam_port
# variable according to that

# cam_port = 0
# cam = cv2.VideoCapture(cam_port)
#
#
# def capture_pic():
#
#     # reading the input using the camera
#     result, image = cam.read()
#
#     # If image will detected without any error,
#     # show result
#     if result:
#
#         image = cv2.resize(image,(320, 240))
#         # saving image in local storage
#         cv2.imwrite("LiveImage.png", image)
#
#     # If captured image is corrupted, moving to else part
#     else:
#         print("No camera to take pictures from!")
