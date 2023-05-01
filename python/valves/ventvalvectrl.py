from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QLabel, \
    QVBoxLayout, QLineEdit, QCheckBox, QMainWindow, QFormLayout
from PyQt5.QtCore import QTimer, QDateTime
import sys
from datetime import datetime
import pyvisa as pyvisa

comm_port = 'COM7'  # com port for rvc300

# update every n msec 
samplingintervalmsec= 3000 # min=10 ms  
class RVC300(QWidget):
    '''
        control and monitor the vent valve
        adapted from serial_rvc300.py
    '''

    rvc300_firmware_string = 'VER=2.11'
    evr116_valve_string = 'VAV=116'
    rvc300_resource_name = 'ASRL7::INSTR' # last used ~Feb.2023

    # Set communication protocols
    baud_rate = 9600
    flow_control = pyvisa.constants.ControlFlow.none
    parity = pyvisa.constants.Parity.none

    def __init__(self, layout):
        '''
        Setup the standard communication settings for the RVC300.
        and labels for display
        '''
        
        # init variables 
        self.flowrate_setpt=1.0e-6 # [mbar*l/s], min=close valve 
        self.flowrate = 0 # reading [mbar*l/s]

        # config Qwidget
        QWidget.__init__(self)
        self.comstat=QCheckBox()
        self.comstat.setStyleSheet("QCheckBox::indicator{width: 40 pt; height: 40 pt}"
                                       "QCheckBox::indicator::checked"
                                       "{"
                                       "background-color : green;"
                                       "}"
                                       "QCheckBox::indicator::unchecked"
                                       "{"
                                       "background-color : red;"
                                       "}")
        self.comstat.setChecked(0)
        # init flow rate reading disp
        self.flowrate_read = QLineEdit()
        self.flowrate_read.setReadOnly(True)
        # init flow rate set point disp
        self.flowrate_set = QLineEdit("{:.2E}".format(self.flowrate_setpt))
        self.flowrate_set.setStyleSheet("background-color: rgb(204, 255,0);") # electric lime
        # init this with min flow rate, i.e.w w/ valve closed
        self.flowrate_set.editingFinished.connect(self.updatesetpoint)

        self.setflowrate_btn=QPushButton('set flow rate')

        # add stuff to widget
        initrow = QFormLayout()
        layout.addLayout(initrow)
       
        initrow.addRow('com status', self.comstat)
        initrow.addRow('flow rate reading [mbar*l/s]', self.flowrate_read)
        initrow.addRow('flow rate set pt [mbar*l/s]', self.flowrate_set)
        initrow.addRow(self.setflowrate_btn)

        ## actions
        # init devices: connect to RSV300 and EVR116
        self.find_rvc300()
        self.get_flow_rate()

        # set flow rate when the btn is clicked
        self.setflowrate_btn.clicked.connect(self.set_flow_rate)

       
    def updatesetpoint(self):
        
        try: 
            # get flow rate set point from QLineEdit
            self.flowrate_setpt = float(self.flowrate_set.text())
           
        except:
            # if failed close valve
            self.flowrate_setpt = 1.0e-6 
            print('failed to update set pt...')
          

    def find_rvc300(self, verbose=True):
        '''
        Function to loop over the available serial interfaces, trying to find
        the RVC300 and EVR116 controller/valve combo by using some of the 
        firmware version and valve indentification functions detailed in the
        Pfeiffer manual

        INPUT:

            verbose - boolean, Whethere to print any debugging messages or not

        '''

        #global rvc300_resource_name

        # try the last used resource name/comm port 
        if self.rvc300_resource_name is not None:
            # change com stat 
            self.comstat.setChecked(1)

            return None

        rm = pyvisa.ResourceManager()

        for resource_name in rm.list_resources():

            ### Ignore everything but the serial interfaces
            if 'ASRL' not in resource_name:
                continue

            firmware = False
            valve = False

            ### Try to open the serial resource first with its own try/except
            ### block since resources that are currently in use may raise 
            ### errors (I haven't tested ANYTHING besides the serial resource
            ### associated to the controller so this is just a guess about
            ### what might happen)
            try:
                resource = rm.open_resource(resource_name)
            except:
                if verbose:
                    print(f"Couldn't open: <{resource_name}>")
                continue

            ### Define the default communication settings--> already added at the beginning of the class
            #resource = _setup_serial_rvc300(resource)

            ### If a visa session could be established, query the instrument
            ### for the firmware version and valve type, which are hopefully
            ### unique to this controller!
            try:    
                if self.rvc300_firmware_string in resource.query('VER?').strip():
                    firmware = True
                if self.evr116_valve_string in resource.query('VAV?').strip():
                    valve = True
                resource.close()

                ### If everything matches up, define the global resource name
                ### for the controller
                if firmware:
                    self.rvc300_resource_name = resource_name

                ### Print a message if the valve was also found
                if firmware and valve:
                    if verbose:
                        print(f'Found RVC300 and EVR116 at: <{resource_name}>')
                    # change com stat
                    self.comstat.setChecked(1)

                    break
                ### Let the user know if we found the controller (i.e. the 
                ### firmware query made sense), but not the leak valve. 
                ### Don't break the loop just yet in case multiple
                ### controller units are hooked up to the computer but only
                ### one has the valve
                elif firmware and not valve:
                    if verbose:
                        print(f'Found RVC300 controller at: <{resource_name}>,'\
                               + ' but no leak valve')
                        


            except:
                if verbose:
                    print("'VAV?' and/or 'VER?' commands raise "\
                           + f"errors for: <{resource_name}>")
                    
                resource.close()
                continue

        ### Raise an error if we couldn't find the controller we wanted
        if self.rvc300_resource_name is None:
            raise IOError("Couldn't find RVC300 serial interface")

    def process_flow_string(self, flow_string):
        '''
        Parse the string with the flow value reported by the RVC300.
        Unlikely to change but this keeps the behavior consistent 
        across any functions that handle this value.
        '''

        flow_value = float(flow_string[4:-7])
        flow_units = flow_string[-7:]

        # update flowrate 
        self.flowrate = flow_value
         # disp flow rate reading
        self.flowrate_read.setText("{:.2E}".format(flow_value))

        return flow_value, flow_units

    def get_flow_rate(self):
        '''
        Command to query the flow rate in units of mbar * L / s, or 
        Torr * L / s (determined by a controller setting)
        '''

        #### Find the leak valve name if we haven't already
        #global rvc300_resource_name
        #_find_rvc300()

        ### Establish the VISA session
        rm = pyvisa.ResourceManager()
        rvc300 = rm.open_resource(self.rvc300_resource_name)

        ### Query the flow and close the VISA session
        flow_string = rvc300.query("FLO?").strip()
        rvc300.close()

        self.process_flow_string(flow_string)       
    
    def set_flow_rate(self):
        '''
        Command to set flow rate in units of mbar * L / s, or Torr * L / s,
        where the units are determined by a controller setting only
        accessible via the front panel.

        INPUTS:
            get flow_rate latestt set point from gui

        '''
       

        print('flow rate set point ={:.2E} mbar*l/s'.format(self.flowrate_setpt))
          

        flow_rate = self.flowrate_setpt

        ### Establish the VISA session
        rm = pyvisa.ResourceManager()
        rvc300 = rm.open_resource(self.rvc300_resource_name)

        ### Ensure that we're in Flow mode and that everything makes sense
        mode_string = rvc300.query("MOD=F").strip()
        assert "MOD=FLOW" in mode_string, "Valve not in 'FLOW' mode"

        ### Set the desired value
        
        command_string = f"FLO={flow_rate:0.2E}"
        command_result = rvc300.query(command_string).strip()
        rvc300.close()

        self.process_flow_string(command_result)
        
class MainWindow(QMainWindow):
    '''
    this generates a standalone window for vent valve control.
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
        #self.resize(800, 600)
        layout = QHBoxLayout()
        leftbox = QVBoxLayout()  # add sub-layouts vertically; first one added appears 1st
        layout.addLayout(leftbox)
        #save = SaveStuff(leftbox)
        rvc300 = RVC300(leftbox)
        self.setCentralWidget(rvc300)
        rvc300.setLayout(layout)

        

        self.setWindowTitle('RVC300/EVR116--vent valve ctrl')
        #wavemeter = WavemeterWS7(leftbox, errorarray=[], data=[])
        #daq = USBdaq(leftbox, aoarray=[])
        #self.setCentralWidget(daq)
        #daq.setLayout(layout)

        # set timer and dispay it in in Hbox--next to leftbox center aligned
        self.time_label=QLabel()
        leftbox.addWidget(self.time_label)   
        self.timer = QTimer()
        self.timer.start(int(samplingintervalmsec))
        self.timer.timeout.connect(lambda: self.update(rvc300))
        

    def update(self, rvc):
        """
        Updates the plot and logs new data.
        """

        timeDisplay = QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')
        self.time_label.setText(timeDisplay)
        # get flow rate and the latest setpoint
        rvc.get_flow_rate()      
        rvc.updatesetpoint()
    

#app = QApplication(sys.argv)
## set font size 
#app.setStyleSheet("QLineEdit{font-size: 16pt;}"
#                  "QLabel{font-size: 16pt;}"
#                  "QPushButton{font-size: 16pt;}")
#screen = MainWindow()
#screen.show()
#sys.exit(app.exec_())