from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.uic import loadUi
from PyQt5.QtCore import QThread, QMutex, Qt, pyqtSignal, pyqtSlot
import arduino_communication
import cv2
import sys

initBB = None
tracker = cv2.TrackerKCF_create()
mutex = QMutex(QMutex.Recursive)


class Thread(QThread):
    changePixmap = pyqtSignal(QImage)
    setVars = pyqtSignal(object, object, object, object)
    send_pos = pyqtSignal(object)

    def run(self):
        global initBB, tracker
        face_cascade = cv2.CascadeClassifier(
            'haarcascade_frontalface_default.xml')
        cap = cv2.VideoCapture(0)
        while (True):
            mutex.lock()
            ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            if initBB is None:
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            else:
                (success, box) = tracker.update(frame)
                if success:
                    self.send_pos.emit(box)
                    (x, y, w, h) = [int(v) for v in box]
                    cv2.rectangle(frame, (x, y), (x + w, y + h),
                                  (0, 255, 0), 2)

                else:
                    tracker = cv2.TrackerKCF_create()
                    initBB = None
            if ret:
                # https://stackoverflow.com/a/55468544/6622587
                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgbImage.shape
                bytesPerLine = ch * w
                convertToQtFormat = QImage(
                    rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
                p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)

                # cv2.setMouseCallback('PyQt5-Video', onMouse)

                self.changePixmap.emit(p)
                self.setVars.emit(initBB, tracker, faces, frame)
            mutex.unlock()
        cap.release()


class connect_dial_box(QWidget):  # dialog box class

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.ui = loadUi('GUI/dial.ui', self)

        self.COMportlineEdit = self.ui.COMportlineEdit
        self.connect_button = self.ui.connect_button
        self.connect_button.clicked.connect(self.check_if_can_connect)
        self.parent.dial = True

    def check_if_can_connect(self):
        port = self.COMportlineEdit.text()
        if (self.parent.ard_com.connect(port)):
            self.connect()
        else:
            self.COMportlineEdit.setText("Can't connect")

    def connect(self):
        self.close()
        self.parent.set_ui()

    def closeEvent(self, event):
        self.parent.dial = False


class ExtendedQLabel(QLabel):

    def __init__(self, parent):
        QLabel.__init__(self, parent)

    initBB = None
    tracker = None
    faces = None
    frame = None

    def closeEvent(self, event):
        self.th.stop()

    @pyqtSlot(object, object, object, object)
    def setVariables(self, initBB, tracker, faces, frame):
        self.initBB = initBB
        self.tracker = tracker
        self.faces = faces
        self.frame = frame

    def mouseReleaseEvent(self, ev):
        global initBB, tracker
        mutex.lock()
        if ev.button() == 1 and initBB is None:
            for (x1, y1, w, h) in self.faces:
                print(x1, ev.x(), x1 + w, y1, ev.y(), y1 + h)
                if ((ev.x() > x1 and ev.x() < x1 + w) and (ev.y() > y1 and ev.y() < y1 + h)):
                    self.initBB = (x1, y1, w, h)
                    self.tracker.init(self.frame, self.initBB)
                    tracker = self.tracker
                    initBB = self.initBB
                    break
        elif ev.button() == 2 and self.initBB is not None:
            self.tracker = cv2.TrackerKCF_create()
            tracker = self.tracker
            initBB = None
        mutex.unlock()


class Nerf_App(QWidget):  # main window class

    def __init__(self):
        super().__init__()
        self.title = 'PyQt5-Video'
        self.left = 50
        self.top = 50
        self.setWindowTitle(self.title)
        self.setFixedWidth(1600)
        # self.setFixedHeight(1200)
        self.th = Thread(self)
        self.th.changePixmap.connect(self.setImage)
        self.th.send_pos.connect(self.send_camera_pos)
        self.label = ExtendedQLabel(self)
        self.th.setVars.connect(self.label.setVariables)
        self.th.setTerminationEnabled(True)
        self.th.start()

        self.label.move(self.left, self.top)
        self.label.resize(640, 480)
        self.label.hide()
        self.label.setEnabled(False)
        self.ui = loadUi('GUI/nerf_turret.ui', self)  # read UI file
        self.show()  # display window
        self.COM_port = ""
        self.dial = False
        self.connected = False
        self.motor_on = False
        self.shoot = False
        self.x = 1
        self.y = 1
        self.on_pad = False
        self.ard_com = arduino_communication.com_ard(self)

        self.pad_label = self.ui.pad_label
        self.bluetooth_button = self.ui.bluetooth_button
        self.motor_on_button = self.ui.motor_on_button
        self.mode_button = self.ui.mode_button
        # self.mode_button.setEnabled(True)  # testing
        self.bluetooth_button.clicked.connect(self.connect_dial_box)
        self.motor_on_button.clicked.connect(self.motor_on_off)
        self.mode_button.clicked.connect(self.mode_change)

    @pyqtSlot(object)
    def send_camera_pos(self, box):
        if box is not None and self.connected:
            print(box)
            new_box = self.remap_box(box[0], box[1], box[2], box[3])
            self.x = int(self.remap(
                new_box[0], 0, 253, 70, 550))
            self.y = int(self.remap(
                new_box[1], 0, 253, 70, 550))
            
            print(self.x, self.y)
            self.set_arduino_message()

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))

    def connect_dial_box(self):  # create connection dialog box
        if not self.connected and not self.dial:
            dial_box = connect_dial_box(self)
            dial_box.show()

    def mode_change(self):  # change mode
        if self.connected:
            self.mode = self.mode_button.isChecked()
            self.pad_label.setEnabled(not self.mode)
            self.ui.pad_label.hide() if self.mode else self.ui.pad_label.show()
            self.label.setEnabled(self.mode)
            self.label.show() if self.mode else self.label.hide()
        # self.set_arduino_message()

    def set_ui(self):  # enable buttons and pad when conencted
        self.motor_on_button.setEnabled(True)
        self.mode_button.setEnabled(True)
        self.pad_label.setEnabled(True)
        new_button_img = QIcon('GUI/bluetooth_connect.png')
        self.bluetooth_button.setIcon(new_button_img)

    def motor_on_off(self):  # turn motor on/off
        if self.connected:
            self.motor_on = self.motor_on_button.isChecked()
            self.set_arduino_message()

    def mouseMoveEvent(self, event):
        if (69 < event.x() < 551 and 69 < event.y() < 551):
            self.x = int(self.remap(event.x(), 0, 253, 70, 550))
            self.y = int(self.remap(event.y(), 0, 253, 70, 550))
            self.on_pad = True
        else:
            self.on_pad = False
            self.shoot = False
        self.set_arduino_message()

    def mousePressEvent(self, event):
        if self.on_pad and self.motor_on:
            # if self.on_pad:
            self.shoot = True
            print("Shoot set to true")
            self.set_arduino_message()

    def mouseReleaseEvent(self, event):
        if self.on_pad:
            self.shoot = False
            self.set_arduino_message()

    def set_arduino_message(self):
        if self.connected:
            message = bytes(
                [255, self.x, self.y, self.motor_on, self.shoot, 254])
            self.ard_com.ser.write(message)

    def remap(self, value_to_map, new_range_min, new_range_max, old_range_min, old_range_max):

        remapped_val = (value_to_map - old_range_min) * (new_range_max - new_range_min) / (
            old_range_max - old_range_min) + new_range_min

        if (remapped_val > new_range_max):
            remapped_val = new_range_max
        elif (remapped_val < new_range_min):
            remapped_val = new_range_min

        return remapped_val

    def remap_box(self, x, y, w, h):
        # Calculate aspect ratio of original matrix
        aspect_ratio = 640 / 480
        
        # Determine whether original matrix is wider or taller than 600x600 matrix
        if aspect_ratio > 1:
            # Scale down width to 600 and height proportionally
            new_w = 600
            new_h = int(new_w / aspect_ratio)
        else:
            # Scale down height to 600 and width proportionally
            new_h = 600
            new_w = int(new_h * aspect_ratio)
        
        # Center the scaled matrix within 600x600 matrix
        x_offset = int((600 - new_w) / 2)
        y_offset = int((600 - new_h) / 2)
        
        # Map coordinates to scaled and centered matrix
        new_x = int((x / 640) * new_w)
        new_y = int((y / 480) * new_h)
        
        # Add offset to get final coordinates
        final_x = new_x + x_offset
        final_y = new_y + y_offset
        
        # Adjust width and height to match scaled and centered matrix
        final_w = int((w / 640) * new_w)
        final_h = int((h / 480) * new_h)
        
        return [final_x, final_y, final_w, final_h]
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Nerf_App()
    app.exec_()
    sys.exit(app.exec_())
