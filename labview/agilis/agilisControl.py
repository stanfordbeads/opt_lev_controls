# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\gravity_2\Documents\Python Scripts\Agilis\UIs\catcherDropper.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_catcherDropperUI(object):
    def setupUi(self, catcherDropperUI):
        catcherDropperUI.setObjectName("catcherDropperUI")
        catcherDropperUI.resize(549, 391)
        self.label = QtWidgets.QLabel(catcherDropperUI)
        self.label.setGeometry(QtCore.QRect(160, 30, 261, 20))
        font = QtGui.QFont()
        font.setFamily("Comic Sans MS")
        font.setPointSize(14)
        font.setBold(True)
        font.setItalic(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.nSteps_catcher = QtWidgets.QLCDNumber(catcherDropperUI)
        self.nSteps_catcher.setGeometry(QtCore.QRect(290, 130, 60, 23))
        self.nSteps_catcher.setObjectName("nSteps_catcher")
        self.nSteps_dropper = QtWidgets.QLCDNumber(catcherDropperUI)
        self.nSteps_dropper.setGeometry(QtCore.QRect(290, 240, 60, 23))
        self.nSteps_dropper.setObjectName("nSteps_dropper")
        self.reset = QtWidgets.QPushButton(catcherDropperUI)
        self.reset.setGeometry(QtCore.QRect(450, 310, 75, 23))
        self.reset.setObjectName("reset")
        self.firmware = QtWidgets.QLabel(catcherDropperUI)
        self.firmware.setGeometry(QtCore.QRect(450, 360, 81, 16))
        self.firmware.setText("")
        self.firmware.setObjectName("firmware")
        self.Connect = QtWidgets.QPushButton(catcherDropperUI)
        self.Connect.setGeometry(QtCore.QRect(450, 280, 75, 23))
        self.Connect.setObjectName("Connect")
        self.Catcher = QtWidgets.QLabel(catcherDropperUI)
        self.Catcher.setGeometry(QtCore.QRect(130, 110, 81, 16))
        font = QtGui.QFont()
        font.setFamily("Courier")
        font.setPointSize(12)
        font.setBold(True)
        font.setItalic(True)
        font.setWeight(75)
        self.Catcher.setFont(font)
        self.Catcher.setObjectName("Catcher")
        self.Catcher_2 = QtWidgets.QLabel(catcherDropperUI)
        self.Catcher_2.setGeometry(QtCore.QRect(130, 220, 81, 16))
        font = QtGui.QFont()
        font.setFamily("Courier")
        font.setPointSize(12)
        font.setBold(True)
        font.setItalic(True)
        font.setWeight(75)
        self.Catcher_2.setFont(font)
        self.Catcher_2.setObjectName("Catcher_2")
        self.catcherStatus = QtWidgets.QLabel(catcherDropperUI)
        self.catcherStatus.setGeometry(QtCore.QRect(370, 130, 107, 16))
        self.catcherStatus.setText("")
        self.catcherStatus.setObjectName("catcherStatus")
        self.dropperStatus = QtWidgets.QLabel(catcherDropperUI)
        self.dropperStatus.setGeometry(QtCore.QRect(370, 240, 107, 16))
        self.dropperStatus.setText("")
        self.dropperStatus.setObjectName("dropperStatus")
        self.stopCatcher = QtWidgets.QPushButton(catcherDropperUI)
        self.stopCatcher.setGeometry(QtCore.QRect(70, 170, 51, 23))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.stopCatcher.setFont(font)
        self.stopCatcher.setStyleSheet("background-color: rgb(255, 0, 0);\n"
"color: rgb(255, 255, 0);")
        self.stopCatcher.setObjectName("stopCatcher")
        self.stopDropper = QtWidgets.QPushButton(catcherDropperUI)
        self.stopDropper.setGeometry(QtCore.QRect(70, 280, 51, 23))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.stopDropper.setFont(font)
        self.stopDropper.setStyleSheet("background-color: rgb(255, 0, 0);\n"
"color: rgb(255, 255, 0);")
        self.stopDropper.setObjectName("stopDropper")
        self.catcher_speedSelector = QtWidgets.QComboBox(catcherDropperUI)
        self.catcher_speedSelector.setGeometry(QtCore.QRect(150, 130, 69, 22))
        self.catcher_speedSelector.setObjectName("catcher_speedSelector")
        self.catcher_speedSelector.addItem("")
        self.catcher_speedSelector.addItem("")
        self.catcher_speedSelector.addItem("")
        self.catcher_speedSelector.addItem("")
        self.catcherJog_In = QtWidgets.QPushButton(catcherDropperUI)
        self.catcherJog_In.setGeometry(QtCore.QRect(140, 160, 41, 31))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.catcherJog_In.setFont(font)
        self.catcherJog_In.setStyleSheet("background-color: rgb(60, 255, 46);\n"
"color: rgb(0, 0, 0);")
        self.catcherJog_In.setObjectName("catcherJog_In")
        self.catcherJog_Out = QtWidgets.QPushButton(catcherDropperUI)
        self.catcherJog_Out.setGeometry(QtCore.QRect(190, 160, 41, 31))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.catcherJog_Out.setFont(font)
        self.catcherJog_Out.setStyleSheet("background-color: rgb(125, 65, 35);\n"
"color: rgb(255, 255, 0);")
        self.catcherJog_Out.setObjectName("catcherJog_Out")
        self.dropper_speedSelector = QtWidgets.QComboBox(catcherDropperUI)
        self.dropper_speedSelector.setGeometry(QtCore.QRect(150, 240, 69, 22))
        self.dropper_speedSelector.setObjectName("dropper_speedSelector")
        self.dropper_speedSelector.addItem("")
        self.dropper_speedSelector.addItem("")
        self.dropper_speedSelector.addItem("")
        self.dropper_speedSelector.addItem("")
        self.dropperJog_Out = QtWidgets.QPushButton(catcherDropperUI)
        self.dropperJog_Out.setGeometry(QtCore.QRect(190, 270, 41, 31))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.dropperJog_Out.setFont(font)
        self.dropperJog_Out.setStyleSheet("background-color: rgb(125, 65, 35);\n"
"color: rgb(255, 255, 0);")
        self.dropperJog_Out.setObjectName("dropperJog_Out")
        self.dropperJog_In = QtWidgets.QPushButton(catcherDropperUI)
        self.dropperJog_In.setGeometry(QtCore.QRect(140, 270, 41, 31))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.dropperJog_In.setFont(font)
        self.dropperJog_In.setStyleSheet("background-color: rgb(60, 255, 46);\n"
"color: rgb(0, 0, 0);")
        self.dropperJog_In.setObjectName("dropperJog_In")
        self.Catcher_3 = QtWidgets.QLabel(catcherDropperUI)
        self.Catcher_3.setGeometry(QtCore.QRect(230, 130, 81, 16))
        font = QtGui.QFont()
        font.setFamily("Comic Sans MS")
        font.setPointSize(10)
        font.setBold(True)
        font.setItalic(True)
        font.setWeight(75)
        self.Catcher_3.setFont(font)
        self.Catcher_3.setObjectName("Catcher_3")
        self.Catcher_4 = QtWidgets.QLabel(catcherDropperUI)
        self.Catcher_4.setGeometry(QtCore.QRect(230, 240, 81, 16))
        font = QtGui.QFont()
        font.setFamily("Comic Sans MS")
        font.setPointSize(10)
        font.setBold(True)
        font.setItalic(True)
        font.setWeight(75)
        self.Catcher_4.setFont(font)
        self.Catcher_4.setObjectName("Catcher_4")

        self.retranslateUi(catcherDropperUI)
        QtCore.QMetaObject.connectSlotsByName(catcherDropperUI)

        # Button pushes
        self.Connect.clicked.connect(self.connectAGL)
        self.reset.clicked.connect(self.resetAGL)
        self.stopCatcher.clicked.connect(lambda: self.stopAxis("X"))
        self.stopDropper.clicked.connect(lambda: self.stopAxis("Y"))
        self.catcherJog_In.clicked.connect(lambda: self.jog("X",'in'))
        self.catcherJog_Out.clicked.connect(lambda: self.jog("X",'out'))
        self.dropperJog_In.clicked.connect(lambda: self.jog("Y",'in'))
        self.dropperJog_Out.clicked.connect(lambda: self.jog("Y",'out'))

    def retranslateUi(self, catcherDropperUI):
        _translate = QtCore.QCoreApplication.translate
        catcherDropperUI.setWindowTitle(_translate("catcherDropperUI", "Catcher / Dropper UI"))
        self.label.setText(_translate("catcherDropperUI", "Catcher / Dropper Control"))
        self.reset.setText(_translate("catcherDropperUI", "RESET"))
        self.Connect.setText(_translate("catcherDropperUI", "Connect"))
        self.Catcher.setText(_translate("catcherDropperUI", "Catcher"))
        self.Catcher_2.setText(_translate("catcherDropperUI", "Dropper"))
        self.stopCatcher.setText(_translate("catcherDropperUI", "STOP"))
        self.stopDropper.setText(_translate("catcherDropperUI", "STOP"))
        self.catcher_speedSelector.setItemText(0, _translate("catcherDropperUI", "5"))
        self.catcher_speedSelector.setItemText(1, _translate("catcherDropperUI", "100"))
        self.catcher_speedSelector.setItemText(2, _translate("catcherDropperUI", "666"))
        self.catcher_speedSelector.setItemText(3, _translate("catcherDropperUI", "1700"))
        self.catcherJog_In.setText(_translate("catcherDropperUI", "IN"))
        self.catcherJog_Out.setText(_translate("catcherDropperUI", "OUT"))
        self.dropper_speedSelector.setItemText(0, _translate("catcherDropperUI", "5"))
        self.dropper_speedSelector.setItemText(1, _translate("catcherDropperUI", "100"))
        self.dropper_speedSelector.setItemText(2, _translate("catcherDropperUI", "666"))
        self.dropper_speedSelector.setItemText(3, _translate("catcherDropperUI", "1700"))
        self.dropperJog_Out.setText(_translate("catcherDropperUI", "OUT"))
        self.dropperJog_In.setText(_translate("catcherDropperUI", "IN"))
        self.Catcher_3.setText(_translate("catcherDropperUI", "steps/s"))
        self.Catcher_4.setText(_translate("catcherDropperUI", "steps/s"))

    def connectAGL(self):
        import instruments as ik
        # Connect to the Agilis
        self.agl = ik.newport.AGUC2.open_serial(port='COM6', baud=921600)
        # sleep(3)
        self.agl.enable_remote_mode = True
        self.firmware.setText(self.agl.firmware_version)
        print(self.agl.firmware_version)
        self.speeds = {'5':1, '100':2, '666':4, '1700':3}
        return
    def resetAGL(self):
        '''
        Just reset the controller, and re-enable
        remote control. Handy for when the 
        device "freezez".
        '''
        self.agl.reset_controller()
        self.agl.enable_remote_mode = True
        return

    def stopAxis(self, ax):
        '''
        Send a stop command to an axis
        '''
        try:
            self.agl.axis[ax].stop()
            print(f'Stopped Axis {ax}')
        except AttributeError:
            print("Connection to AGILIS not established!")
        return()

    def jog(self, ax, dirn):
            '''
            Start the jogging motion for a given axis.
            '''
            if ax=='X':
                speed = self.catcher_speedSelector.currentText()
                ax = self.agl.axis["X"]
            elif ax=='Y':
                speed = self.dropper_speedSelector.currentText()
                ax = self.agl.axis["Y"]
            if speed=='5':
                if dirn=='in':
                    ax.jog = -1
                    print(f'Moving {ax} {dirn} at {speed} steps/s...')
                elif dirn == 'out':
                    ax.jog = 1
                    print(f'Moving {ax} {dirn} at {speed} steps/s...')
                else:
                    print('Unknown direction. Breaking...')
                    stopAxis(ax)
                    return()
            elif speed=='100':
                if dirn=='in':
                    ax.jog = -2
                    print(f'Moving {ax} {dirn} at {speed} steps/s...')
                elif dirn == 'out':
                    ax.jog = 2
                    print(f'Moving {ax} {dirn} at {speed} steps/s...')
                else:
                    print('Unknown direction. Breaking...')
                    stopAxis(ax)
                    return()
            elif speed == '666':
                if dirn=='in':
                    ax.jog = -4
                    print(f'Moving {ax} {dirn} at {speed} steps/s...')
                elif dirn == 'out':
                    ax.jog = 4
                    print(f'Moving {ax} {dirn} at {speed} steps/s...')
                else:
                    print('Unknown direction. Breaking...')
                    stopAxis(ax)
                    return()
            elif speed == '1700':
                if dirn=='in':
                    ax.jog = -3
                    print(f'Moving {ax} {dirn} at {speed} steps/s...')
                elif dirn == 'out':
                    ax.jog = 3
                    print(f'Moving {ax} {dirn} at {speed} steps/s...')
                else:
                    print('Unknown direction. Breaking...')
                    stopAxis(ax)
                    return()
            else:
                print('Unknown speed. Breaking...')
                stopAxis(ax)
                return()
            return()
            


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    catcherDropperUI = QtWidgets.QWidget()
    ui = Ui_catcherDropperUI()
    ui.setupUi(catcherDropperUI)
    catcherDropperUI.show()
    sys.exit(app.exec_())
