from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QFormLayout
from PyQt5.QtCore import QTimer, QDateTime
from os import path, makedirs
import csv
from yoctopuce.yocto_api import *
from yoctopuce.yocto_temperature import *
from yoctopuce.yocto_humidity import *
from yoctopuce.yocto_pressure import *

from datetime import datetime
import schedule
import time


class yoctopucelogger():
    def __init__(self, handle, logfile, layout=None):
        # logger class with init and update methods
        # input: logger's name/handle (METEO...), log file w/ extension, parent's layout

        # file name and dir
        self.log_file = logfile

        ## Display the log file
        #self.save_txt = QLabel(self.log_file)
        #savefileBox = QFormLayout() 
        #layout.addLayout(savefileBox)
        #savefileBox.addRow(handle+': ', self.save_txt)


        errmsg = YRefParam()

        if YAPI.RegisterHub("127.0.0.1", errmsg) != YAPI.SUCCESS:
            # use YAPI.RegisterHub("127.0.0.1", errmsg) if dev is connected to the same pc
            # if this failed, try YAPI.RegisterHub("usb", errmsg)
            sys.exit("init error :" + errmsg.value)
        try:
            self.temperature = YTemperature.FindTemperature(handle+'.temperature')

            self.tempFound = True
            self.tempstatus = ""
        except Exception as e:
            self.tempFound = False
            print(e)
            self.tempstatus = "Temp. sensor error."

        try:
            self.humidity = YHumidity.FindHumidity(handle+'.humidity')

            self.humFound = True
            self.humstatus = ""
        except Exception as e:
            self.humFound= False
            print(e)
            self.humstatus = "Humidity sensor error."

        try:
            self.pressure = YPressure.FindPressure(handle+'.pressure')
            self.presFound = True
            self.presstatus = ""
        except Exception as e:
            self.presFound= False
            print(e)
            self.presstatus = "Humidity sensor error."

        # init time array in main 
        self.times = [datetime.now().timestamp()]
        # init TPH arrays in main 
        self.Tvals=[self.temperature.get_currentValue()]
        self.Pvals=[self.pressure.get_currentValue()]
        self.Hvals=[self.humidity.get_currentValue()]


    def update(self):
        """Updates TPH and time. save to file."""
        try:
            currentT= self.temperature.get_currentValue()
            currentH=self.humidity.get_currentValue()
            currentP=self.pressure.get_currentValue()
            currenttime = datetime.now().timestamp()
            timedisplay= QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')
        except:
            YAPI.Sleep(1000)
            print('update error. try again...')
            currentT= self.temperature.get_currentValue()
            currentH=self.humidity.get_currentValue()
            currentP=self.pressure.get_currentValue()
            currenttime = datetime.now().timestamp()
            timedisplay= QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')

        self.Tvals.append(currentT)
        self.Pvals.append(currentP)
        self.Hvals.append(currentH)
        self.times.append(currenttime)

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
           
class WinForm(QWidget):
    def __init__(self, path_name, samplingintervalSec=10, closingtime='0100'):
        super(WinForm, self).__init__()

        self.setWindowTitle('YoctopuceLoggers')
        # Arrange the widgets on a grid
        layout = QVBoxLayout()
        self.setLayout(layout)
       
        # new trap side: side/near input beam
        logger2name = 'METEOMK2-23B50F'
        # new trap: fiber
        logger3name = 'METEOMK2-23CD30'
        # new trap: output
        logger4name = 'METEOMK2-23CAC1'
         # old trap logger w/ red extension cable
        logger1name = 'METEOMK2-23B47A'


        # filenames for log
        today =datetime.now()

        fextension = '.csv'
        filename = path_name + '\\'  +'yoctopuce_oldtrap'+ fextension
        filename2 = path_name + '\\' +'yoctopuce_newtrap_input'+ fextension

        filename3 = path_name + '\\' + 'yoctopuce_newtrap_fiber'+ fextension
        filename4 = path_name + '\\' + 'yoctopuce_newtrap_output'+ fextension

        #filename = path_name + '\\' + 'dummy3a'+ fextension
        #filename2 = path_name + '\\' + 'dummy3b'+ fextension
        #filename3 = path_name + '\\' + 'dummy3c'+ fextension
        #filename4 = path_name + '\\' + 'dummy3d'+ fextension

        self.Y2= yoctopucelogger(logger2name, filename2, layout)
        self.Y3= yoctopucelogger(logger3name, filename3, layout)

        self.Y4 = yoctopucelogger(logger4name, filename4, layout)
        self.Y1= yoctopucelogger(logger1name, filename, layout)
         
        ## Display the log file
        #self.save_txt = QLabel(self.log_file)
        savefileBox = QFormLayout() 
        layout.addLayout(savefileBox)
        savefileBox.addRow(logger2name, QLabel(filename2))
        savefileBox.addRow(logger3name, QLabel(filename3))
        savefileBox.addRow(logger4name, QLabel(filename4))
        savefileBox.addRow(logger1name, QLabel(filename))


        # Use a timer to update plot and log data
        self.timer = QTimer()
         # Default sampling rate = 10 s
        self.defaultTime = samplingintervalSec
        self.timer.start(int(self.defaultTime *1000))
        #print('started timer...')

        # Trigger update function on timeout
        self.timer.timeout.connect(lambda: self.updateall(closingtime=closingtime))
        
        

    def updateall(self, closingtime='0100'):
        ''' 
        closes itslef at closing time (everyday) otherwise update logs
        closing time: HHMM, default= 1am
        '''

        today =datetime.now()

        if today.strftime('%H%M')== closingtime:
            print('closing app at ' + today.strftime('%m%d-%H%M'))

            self.timer.stop()
            self.close()

         # old trap logger w/ red extension cable
        self.Y1.update()
        # new trap side: side/near input beam
        self.Y2.update()
        # new trap: fiber
        self.Y3.update()
        # new trap: output
        self.Y4.update()

        

def job(closingtime='0100'):
    # scheduled job = init loggers 

    ## close current app at closing time HHMM (default=1am)

    # start a new app
    app2 = QApplication(sys.argv)
    today =datetime.now()

    # save to a sub folder
    path_name = 'C:\\Users\\beads\\Documents\\yoctopuce\\'+ today.strftime('%Y%m%d%H%M') 

    if not path.exists(path_name):
        makedirs(path_name)

    ui2 =  WinForm(path_name, closingtime=closingtime)
    
    ui2.show()
    print('init loggers at ' + today.strftime('%m%d-%H%M'))
    finish_app2 = app2.exec_()
   

#### test
# schedule.every().minute.at(":17").do(job)

# start the scheduling job
schedule.every().day.at("18:07").do(job, '1805')
# start initial app and schedule to close it at 18:06
# closingtime + 1s (sleep) needs to be before the scheduled job time ('18:07' above) otherwise it won't restart
job(closingtime='1805')
# keep going 
while True:
    schedule.run_pending()
    time.sleep(1) # wait 1s 