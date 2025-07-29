# Titan Object Detection Package

Can use a laptop camera or webcam using OpenCV and MobileNetSSD. The idea is to loop over each frame of the video stream, detect objects like person, chair, dog, etc. and bound each detection in a box.

Install all the necessary libraries:

```
pip3 install opencv-python opencv-contrib-python opencv-python-headless opencv-contrib-python-headless matplotlib imutils
```


 To make sure you have your video devices connected (e.g. Webcam, FaceTime HD Camera, etc.):

```
system_profiler SPCameraDataType
system_profiler SPCameraDataType | grep "^    [^ ]" | sed "s/    //" | sed "s/://"
```

To start your object detection package:

```
ros2 launch titan_object_detection object_detection.launch.py
```
