# import the necessary packages
import numpy as np
import cv2


face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

cv2.startWindowThread()
cv2.namedWindow("frame", cv2.WND_PROP_AUTOSIZE)
cap = cv2.VideoCapture(0)


initBB = None
tracker = cv2.TrackerCSRT_create()


def onMouse(event, x, y, flags, param):
    global initBB
    if event == cv2.EVENT_LBUTTONDOWN and initBB is None:
        for (x1, y1, w, h) in faces:
            if ((x > x1 and x < x1 + w) and (y > y1 and y < y1 + h)):
                print(x1, y1)
                initBB = (x1, y1, w, h)
                tracker.init(frame, initBB)
    elif event == cv2.EVENT_RBUTTONDOWN and initBB is not None:
        initBB = None


while (True):
    ret, frame = cap.read()
    cv2.setMouseCallback("frame", onMouse)
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    if initBB is None:
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
    if initBB is not None:
        (success, box) = tracker.update(frame)
        if success:
            (x, y, w, h) = [int(v) for v in box]
            cv2.rectangle(frame, (x, y), (x + w, y + h),
                          (0, 255, 0), 2)
        else:
            initBB = None
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
cv2.waitKey(1)
