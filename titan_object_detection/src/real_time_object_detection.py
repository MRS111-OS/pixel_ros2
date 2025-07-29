#!/usr/bin/env python3

import cv2
import imutils
import numpy as np
import argparse
import time
from imutils.video import VideoStream, FPS

def main():
    # Construct the argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--prototxt", required=True, help="Path to Caffe 'deploy' prototxt file")
    ap.add_argument("-m", "--model", required=True, help="Path to Caffe pre-trained model")
    ap.add_argument("-c", "--confidence", type=float, default=0.2, help="Minimum probability to filter weak detections")
    args = vars(ap.parse_args())

    # Initialize class labels and colors
    CLASSES = ["aeroplane", "background", "bicycle", "bird", "boat",
               "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
               "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
               "sofa", "train", "tvmonitor"]
    COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

    # Load model
    print("[INFO] Loading model...")
    net = cv2.dnn.readNetFromCaffe(args["prototxt"], args["model"])

    # Start video stream and FPS
    print("[INFO] Starting video stream...")
    vs = VideoStream(src=0).start()
    time.sleep(2.0)
    fps = FPS().start()

    while True:
        frame = vs.read()
        frame = imutils.resize(frame, width=400)
        (h, w) = frame.shape[:2]

        # Prepare input blob for the image
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)),
                                     scalefactor=1/127.5,
                                     size=(300, 300),
                                     mean=127.5,
                                     swapRB=True)
        net.setInput(blob)
        detections = net.forward()

        # Loop over the detections
        for i in np.arange(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > args["confidence"]:
                idx = int(detections[0, 0, i, 1])
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                label = "{}: {:.2f}%".format(CLASSES[idx], confidence * 100)
                print("Object detected:", label)

                cv2.rectangle(frame, (startX, startY), (endX, endY), COLORS[idx], 2)
                y = startY - 15 if startY - 15 > 15 else startY + 15
                cv2.putText(frame, label, (startX, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2)

        # Display the frame
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

        fps.update()

    # Stop FPS counter and video stream
    fps.stop()
    print("[INFO] Elapsed Time: {:.2f}".format(fps.elapsed()))
    print("[INFO] Approximate FPS: {:.2f}".format(fps.fps()))

    cv2.destroyAllWindows()
    vs.stop()

if __name__ == "__main__":
    main()

