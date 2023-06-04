import os
import sys
import glob
import cv2
import dlib

import numpy as np

# Now let's use the detector as you would in a normal application.  First we
# will load it from disk.
detector = dlib.simple_object_detector("detector.svm")
	
img = dlib.load_rgb_image("./imgs/standing_1.png")
win1 = dlib.image_window(detector, "My image")
dlib.hit_enter_to_continue()

# Now let's run the detector over the images in the faces folder and display the
# results.
print("Showing detections on the images in the faces folder...")
win2 = dlib.image_window(detector,"Test")
for f in glob.glob(os.path.join('./imgs', "*.png")):
    print("Processing file: {}".format(f))
    img = dlib.load_rgb_image(f)
    dets = detector(img)
    print("Number of faces detected: {}".format(len(dets)))
    for k, d in enumerate(dets):
        print("Detection {}: Left: {} Top: {} Right: {} Bottom: {}".format(
            k, d.left(), d.top(), d.right(), d.bottom()))

    win2.clear_overlay()
    win2.set_image(img)
    win2.add_overlay(dets)
    win2.get_next_keypress()
