from PyQt5.QtWidgets import QApplication, QPushButton, QHBoxLayout, QLabel, \
    QVBoxLayout, QMainWindow, QFormLayout
from PyQt5.QtCore import QTimer, QDateTime
from PyQt5.QtGui import QPixmap
import sys, time


# update every n msec 
samplingintervalmsec= 1000 # min=10 ms 

sys.path.append('C:\\Users\\beads\\opt_lev_controls\\python\\valves')
# import RVC300 for vent valve
from ventvalvectrl import RVC300
# import daqPXISlot4 for pheumatic valves and gauges
from pneumaticvalvesandgauges import daqPXISlot4


class MainWindow(QMainWindow):
    '''
    this generates a standalone window for all valve/gauge control.
    to use it: 
    #app = QApplication(sys.argv)
    ## set font size 
    #app.setStyleSheet("QLineEdit{font-size: 16pt;}"
    #                  "QLabel{font-size: 16pt;}"
    #                  "QPushButton{font-size: 16pt;}")
    #screen = MainWindow()
    #screen.show()
    #sys.exit(app.exec_())
    '''
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        # set layout and add stuff
        layout = QHBoxLayout()
        leftbox = QVBoxLayout()  # add sub-layouts vertically; first one added appears 1st
        layout.addLayout(leftbox)
        #save = SaveStuff(leftbox)

        # set timer and dispay it in in Hbox--next to leftbox center aligned
        self.time_label=QLabel()
        #rightbox.addWidget(self.time_label)   
        self.timer = QTimer()
        self.timer.start(int(samplingintervalmsec))
        # events triggered by timeout
        self.timer.timeout.connect(lambda: self.update(daq, rvc300))
        
        # pause btn
        self.pause_btn = QPushButton('Pause')
        self.pause_btn.setCheckable(True)
        self.pause_btn.setChecked(True)
        #rightbox.addWidget(self.pause_btn)   

        # add pause and time label to rightbox
        pausebox=QFormLayout()
        pausebox.addRow(self.time_label, self.pause_btn)
        leftbox.addLayout(pausebox)

        daq = daqPXISlot4(leftbox)

        self.setCentralWidget(daq)
        daq.setLayout(layout)

        self.setWindowTitle('valves and gauges')
      
        #rightbox = QVBoxLayout()  # add sub-layouts vertically; first one added appears 1st
        #layout.addLayout(rightbox)

        # add the diagram as a label (https://www.geeksforgeeks.org/pyqt5-how-to-add-image-in-window/)
        # creating label
        self.label1 = QLabel()
         
        # loading image
        self.pixmap = QPixmap('C:\\Users\\beads\\Pictures\\Screenshots\\valvesdiagram.png')
         # adding image to label
        self.label1.setPixmap(self.pixmap)
 
        ## Optional, resize label to image size
        #self.label1.resize(self.pixmap.width(),
        #                  self.pixmap.height())
        leftbox.addWidget(self.label1) 

        rvc300 = RVC300(leftbox)

        ############## to be tested #############
       # increase flow rate Pset<Pread, decrease open valve 3 if Pset>Pread
        daq.setPressure_btn.clicked.connect(lambda: self.vent2NIT(daq, rvc300))


    def update(self, USBdaq, rvc):
        """
        Updates the plot and logs new data.
        """
        if not self.pause_btn.isChecked():

            timeDisplay = QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')
            self.time_label.setText(timeDisplay)

            # update pressures and valve stats
            USBdaq.readPressureGauges()
            USBdaq.checkvalvestats()
            USBdaq.updatesetpoint()

            # update vent valve
            rvc.get_flow_rate()  
            rvc.updatesetpoint()

            # adjust pressure if set P is checked
            if USBdaq.setPressure_btn.isChecked() is True:
                self.vent2NIT(USBdaq, rvc)

    
    def vent2NIT(self, daq, rvc300):
        ''' vent to nitrogen...to be tested...
        '''
        margin = .05 # [mbar] pressure's error margin

        if daq.setPressure_btn.isChecked() is True:
           
            if float(daq.piraniPset_Qline.text()) > (float(daq.piraniP_Qline.text())+ margin):
             # if set point is above reading by some margin=0.05 mbar, vent to NIT

                print('venting to NIT ...')

                # first make sure valve3 is closed 
                if daq.valve_stat['valve3'] == 1:
                    daq.changevalvestat('valve3')

                # vent at 1E-2 mbar l/s
                rvc300.flowrate_setpt=0.01
                
                # update flow rate display
                rvc300.flowrate_set.setText("{:.2E}".format(rvc300.flowrate_setpt))
                rvc300.setflowrate_btn.click()

                error = float(daq.piraniP_Qline.text())-float(daq.piraniPset_Qline.text())

                # vent at const rate: empirically, for set~1e-2 when venting from <0.01 mbar or error ~2.5, this takes 20s???
                N = -error/2.5*20
                # go at set flow rate for N s
                time.sleep(round(N,2))

                # turn it off after that
                print('stopping ...')

                rvc300.flowrate_setpt=0.000001
                 # update flow rate display
                rvc300.flowrate_set.setText("{:.2E}".format(rvc300.flowrate_setpt))
                rvc300.setflowrate_btn.click()

                #daq.setPressure_btn.setChecked(False) 

            elif float(daq.piraniPset_Qline.text()) >0.0001 and float(daq.piraniPset_Qline.text()) < (float(daq.piraniP_Qline.text())- margin):
                # if set point pressure is lower than reading and higher than pirani's min, rough pummp

                print('opening valve 3 to rough pump...')
                # open valve 3
                if daq.valve_stat['valve3'] == 0:
                    daq.changevalvestat('valve3')

                rvc300.flowrate_setpt=0.000002
                rvc300.setflowrate_btn.click()
            elif abs(float(daq.piraniPset_Qline.text()) - float(daq.piraniP_Qline.text()) ) <= margin:
                print('reached set point...')
                daq.setPressure_btn.setChecked(False) 
   
app = QApplication(sys.argv)
## set font size 
app.setStyleSheet("QLineEdit{font-size: 16pt;}"
                  "QLabel{font-size: 16pt;}"
                  "QPushButton{font-size: 16pt;}")
screen = MainWindow()
screen.show()
sys.exit(app.exec_())


