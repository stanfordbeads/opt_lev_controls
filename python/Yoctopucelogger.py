from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QListWidget, QGridLayout, QLabel, \
    QFileDialog, QLineEdit, QFormLayout
from PyQt5.QtCore import QTimer, QDateTime
import pyqtgraph as pg
import numpy as np
from os import path
import csv
from yoctopuce.yocto_api import *
from yoctopuce.yocto_temperature import *
from yoctopuce.yocto_humidity import *
from yoctopuce.yocto_pressure import *

from datetime import datetime


class loggerWidget(QWidget):
    """A widget that plots and logs sensor data. Must add to main window.
    Parameters:
            name (str): Measured quantity; humidity, temperature, e.g.
            sensor_method (func): Function that returns current sensor measurement.
    """
    def __init__(self, name, initdata, parent=None):
        super(loggerWidget, self).__init__(parent)
        layout = QGridLayout()
        self.setLayout(layout)

        #self.read = sensor_method

        self.title_widget = QLabel(name)
        self.vals = initdata 
        #self.times = [datetime.now()]

        # INITIALIZE THE PLOT WIDGET
        self.plot = pg.PlotWidget()
        # Change pen color + thickness
        pen = pg.mkPen(color=(114, 166, 151), width=3)
        # White background
        self.plot.setBackground('w')

        # Turn the x-axis into a date-time axis
        axis = pg.DateAxisItem()
        self.plot.setAxisItems({'bottom': axis})

        # This is the plotted data/"curve"
        self.curve = self.plot.getPlotItem().plot(pen=pen)

        # Add the widgets to the layout
        row1 = QGridLayout()
        row1.addWidget(self.title_widget, 1, 1)
        layout.addLayout(row1, 1,1)
        layout.addWidget(self.plot, 2,1)


class WinForm(QWidget):
    def __init__(self, handle, logfile, parent=None):
        super(WinForm, self).__init__(parent)

        self.setWindowTitle('Logger ' + handle )

        # Arrange the widgets on a grid
        layout = QGridLayout()
        self.setLayout(layout)

        # Timestamp widget
        self.time_label = QLabel()
        
        # Status widgets
        self.hum_txt = QLabel()
        self.temp_txt = QLabel()
        self.pressure_txt = QLabel()

        # ## Change log file button
        #self.file_btn = QPushButton("Change file")
        #self.file_btn.clicked.connect(self.get_file)

        ## Pause logging button
        self.pause_btn = QPushButton("Pause logger")
        self.pause_btn.setCheckable(True)
        self.pause_btn.clicked.connect(self.toggle_pause)

        # file name and dir
        self.log_file = logfile + fextension

        # Display the log file
        self.save_txt = QLabel('Saving to ' + self.log_file)
        self.save_txt.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        # Default sampling rate = 10 s
        self.defaultTime = 10
        # In-line editor to change the sampling time
        self.sample_time = QLineEdit(str(self.defaultTime), self)
        # Click to focus (display the blinking cursor)
        self.sample_time.setFocusPolicy(QtCore.Qt.ClickFocus)

        # Only accept numbers > .001 (minutes)
        self.sample_time.setValidator(QDoubleValidator(bottom=.001))
        # Upon finished, trigger function to change sample time
        self.sample_time.editingFinished.connect(self.new_sample_time)
        self.sample_time.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

        savefileBox = QHBoxLayout()
        layout.addLayout(savefileBox, 1, 1)
        #savefileBox.addWidget(self.file_btn)
        savefileBox.addWidget(self.save_txt)

        samplingbox = QFormLayout()
        layout.addLayout(samplingbox, 1, 2)
        samplingbox.addRow("Sampling interval [s]", self.sample_time)

        pausebox = QFormLayout()
        pausebox.addRow(self.time_label, self.pause_btn)
        layout.addLayout(pausebox, 1, 3)
      
        errmsg = YRefParam()

        if YAPI.RegisterHub("127.0.0.1", errmsg) != YAPI.SUCCESS:
            # use YAPI.RegisterHub("127.0.0.1", errmsg) if dev is connected to the same pc
            # if this failed, try YAPI.RegisterHub("usb", errmsg)
            sys.exit("init error :" + errmsg.value)
        try:
            # init temperature sensor
            #self.temperature = YTemperature.FirstTemperature()

            # logger w/ red extension cable
            self.temperature = YTemperature.FindTemperature(handle+'.temperature')
            # logger near gas lines
            #self.temperature = YTemperature.FindTemperature('METEOMK2-23B50F.temperature')

            self.tempFound = True
            self.tempstatus = ""
        except Exception as e:
            self.tempFound = False
            print(e)
            self.tempstatus = "Temp. sensor error."

        try:
            #self.humidity = YHumidity.FirstHumidity()
            self.humidity = YHumidity.FindHumidity(handle+'.humidity')

            self.humFound = True
            self.humstatus = ""
        except Exception as e:
            self.humFound= False
            print(e)
            self.humstatus = "Humidity sensor error."

        try:
            #self.pressure = YPressure.FirstPressure()
            self.pressure = YPressure.FindPressure(handle+'.pressure')
            self.presFound = True
            self.presstatus = ""
        except Exception as e:
            self.presFound= False
            print(e)
            self.presstatus = "Humidity sensor error."

        # If sensors found, create plot panels.
        if self.tempFound:
            temp_panel= loggerWidget("Temperature", [self.temperature.get_currentValue()])
            layout.addWidget(temp_panel, 2,1)
            temp_panel.show()

        if self.humFound:
            hum_panel = loggerWidget("Humidity", [self.humidity.get_currentValue()])
            layout.addWidget(hum_panel, 2, 2)
            hum_panel.show()

        if self.presFound:
            press_panel = loggerWidget("Pressure", [self.pressure.get_currentValue()])
            layout.addWidget(press_panel, 2, 3)
            press_panel.show()

        # Use a timer to update plot and log data
        self.timer = QTimer()
        self.paused = False
        
        self.timer.start(int(self.defaultTime *1000))
        
        # Trigger update function on timeout
        self.timer.timeout.connect(lambda: self.update(temp_panel, hum_panel, press_panel))
        # init time array in main 
        self.times = [datetime.now().timestamp()]

        ## save data 
        #self.savedata_timer = QTimer()
        #self.savedata_timer.start(Tsave)
        #self.savedata_timer.timeout.connect(lambda: self.saveh5(temp_panel, hum_panel, press_panel))


    # Function to update the timestamp.
    #def updateTime(self):
    #    timeDisplay = QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')
    #    self.time_label.setText(timeDisplay)

    #def get_file(self):
    #    fname = QFileDialog.getSaveFileName(self, 'Save file',
    #                                        'c:\\', "h5 files (*.h5)")
    #    if fname[0] != "":
    #        self.log_file = fname[0]
    #    #Modify the file name widget.
    #    self.save_txt.setText('Saving to ' + self.log_file)

    def toggle_pause(self):
        if self.pause_btn.isChecked():
            self.paused = True
        else:
            self.paused = False

    def new_sample_time(self):
        """Modify the timer's timeout value. """
        # If the in-line editor value has changed:
        if self.sample_time.isModified():
            # Fetch the text from the in-line editor.
            time = int(float(self.sample_time.text()) * 1000 * 60)
            # Restart the timer.
            self.timer.stop()
            self.timer.start(time)
            # Reset the modified flag.
            self.sample_time.setModified(False)

    def update(self, temp_panel, hum_panel, press_panel):
        """Updates the plot and logs new data."""
        if not self.paused:
         
            currentT= self.temperature.get_currentValue()
            currentH=self.humidity.get_currentValue()
            currentP=self.pressure.get_currentValue()
            currenttime = datetime.now().timestamp()
            timedisplay= QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')

            temp_panel.vals = np.append(temp_panel.vals, currentT)
            hum_panel.vals = np.append(hum_panel.vals, currentH)
            press_panel.vals = np.append(press_panel.vals, currentP)

            self.times.append(currenttime)
            

            n=round(3600*5/self.defaultTime) # plot last 5hr 
            temp_panel.curve.setData(self.times[-n:], temp_panel.vals[-n:])
            hum_panel.curve.setData(self.times[-n:], hum_panel.vals[-n:])
            press_panel.curve.setData(self.times[-n:], press_panel.vals[-n:])

            ## Save to file. Append if exists, otherwise create.
            if path.exists(self.log_file):
                type = 'a'
            else:
                type = 'w'
                with open(self.log_file, type, newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(['time', 'temp [C]', 'RH [%]', 'P [mbar]'])

            with open(self.log_file, type, newline='') as file:
                writer = csv.writer(file)
                writer.writerow([timedisplay, currentT, currentH, currentP])

           
    def saveh5(self, temp_panel, hum_panel, press_panel):
         
        if path.exists(self.log_file):
            
            today =datetime.now()
            # change filename if exists 
            self.log_file =path_name + '\\' + today.strftime('%Y-%m-%d-%H_%M')+ fextension

         # create h5 files       
        hf = h5py.File(self.log_file , 'w')
        # create a yoctopuce group with 4 datasets
        g1 = hf.create_group('yoctopuce')
        g1.create_dataset('timestamp', data=self.times)
        g1.create_dataset('temperature', data=temp_panel.vals)
        g1.create_dataset('humidity', data=hum_panel.vals)
        g1.create_dataset('pressure', data=press_panel.vals)

        #compress data into gzip? https://www.christopherlovell.co.uk/blog/2016/04/27/h5py-intro.html
        hf.close()

        # reinit timer and data arrays
        # Use a timer to update plot and log data
        self.timer = QTimer()
        
        self.timer.start(int(self.defaultTime *1000))
        
        # Trigger update function on timeout
        self.timer.timeout.connect(lambda: self.update(temp_panel, hum_panel, press_panel))
        # init time array in main 
        self.times = [datetime.now().timestamp()]
        temp_panel.vals = [self.temperature.get_currentValue()]
        hum_panel.vals = [self.humidity.get_currentValue()]
        press_panel.vals = [self.pressure.get_currentValue()]


# filenames for log
# filename = yyyy-mm-dd
today =datetime.now()
# save to a folder
path_name = 'C:\\Users\\beads\\Documents\\yoctopuce'
filename = path_name + '\\' + today.strftime('%Y-%m-%d-%H_%M') +'a'
filename2 = path_name + '\\' + today.strftime('%Y-%m-%d-%H_%M') +'b'
filename3 = path_name + '\\' + today.strftime('%Y-%m-%d-%H_%M') +'c'

#filename = path_name + '\\' + 'dummy2a'
#filename2 = path_name + '\\' + 'dummy2b'
#filename2 = path_name + '\\' + 'dummy2b'
fextension = '.csv'

## save data to a new h5 file every N ms
#Tsave= 12*3600*1000


# logger w/ red extension cable
logger1name = 'METEOMK2-23B47A'
# new trap side: side
logger2name = 'METEOMK2-23B50F'
# new trap side: 
logger3name = 'METEOMK2-23CAC1'
# new trap side: 
logger4name = 'METEOMK2-23CDC30'

app = QApplication(sys.argv)
form = WinForm(logger1name, filename)
form.show()
#form2 = WinForm(logger2name, filename2)
#form2.show()
#form3 = WinForm(logger3name, filename3)
#form3.show()
sys.exit(app.exec_())