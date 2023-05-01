from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, \
    QVBoxLayout, QLineEdit, QCheckBox, QFormLayout
import numpy as np
from nidaqmx.task import Task, AcquisitionType  
from nidaqmx.constants import TerminalConfiguration, LineGrouping
import warnings
from nidaqmx.errors import DaqWarning, DaqError
import time 

# config devices/inputs
pirani = "PXI1Slot4/ai3"
baratron1Torr = "PXI1Slot4/ai6"
baratron = "PXI1Slot4/ai4"
# group channels and create dictionaries//ordering matters because they are added (.add_ai chan()) in this order 
gaugechannels={'pirani': pirani, 'baratron1Torr': baratron1Torr, 'baratron': baratron}

monitorchannels = {'valve1M1': "PXI1Slot4/ai2", 'valve1M2': "PXI1Slot4/ai0", \
                   'valve3M1': "PXI1Slot4/ai1", 'valve3M2': "PXI1Slot4/ai9"}

valvedrivers = {'valve1D':  "PXI1Slot4/Port0/line6", 'valve3D': "PXI1Slot4/Port0/line2"}  # di0 reading--405 digilock 
 

class daqPXISlot4(QWidget):
    '''
    control and monitor pneumatic valves (2x) and read pressure gauges (3x)
    adapated from total_valve_control.vi (with valve 2 removed)
    '''
    rate =10000 
    samplesperch =100


    def __init__(self, layout, *args, **kwargs):
        
        # allows for adding data collecting arrays, etc
        self.args =args
        self.kwargs =kwargs

        QWidget.__init__(self)
        # init daq channels 
        try:
           
            with Task() as task_do,  Task() as task_ai:
                # need different tasks for ai & di
                # useful example: https://github.com/ni/nidaqmx-python/blob/master/nidaqmx_examples/ai_multi_task_pxie_ref_clk.py 

                # init gauges' channels
                for dummy in gaugechannels.values():
                    task_ai.ai_channels.add_ai_voltage_chan(dummy, max_val = 10, min_val =-10, \
                        terminal_config=TerminalConfiguration.RSE)
                    

                # init valve monitor channels 
                for dummy in monitorchannels.values():
                    task_ai.ai_channels.add_ai_voltage_chan(dummy, max_val = 10, min_val =-10, \
                        terminal_config=TerminalConfiguration.RSE)
                    # config sampling rate and mode, small/arb sample number for init 
                    task_ai.timing.cfg_samp_clk_timing(self.rate, sample_mode=AcquisitionType.FINITE, \
                                                       samps_per_chan=5)
                    task_ai.timing.ref_clk_src='OnboardClock'
                    

                
                # init valve driver channels
                for dummy in valvedrivers.values():
                    task_do.do_channels.add_do_chan(dummy, line_grouping=LineGrouping.CHAN_PER_LINE)
                                       
        except:
            raise OSError('failed to init usb daq')
         
        # init valve stat
        self.valve_stat = {'valve1': 0, 'valve3': 0}  # open =1 
        self.valve_stat_ind ={'valve1':  QCheckBox(), 'valve3':  QCheckBox()} 
        self.openBool ={'valve1':  QCheckBox(), 'valve3':  QCheckBox()} 

        # label stuff 
        self.piraniP_Qline = QLineEdit()
        self.piraniP_Qline.setReadOnly(True)
        self.baraton1Torr_Qline = QLineEdit()
        self.baraton1Torr_Qline.setReadOnly(True)
        self.baraton_Qline = QLineEdit()
        self.baraton_Qline.setReadOnly(True)
        self.piraniPset_Qline = QLineEdit()
        self.piraniPset_Qline.setStyleSheet("background-color: rgb(204, 255,0);") # electric lime
        # compare setpt to reading when value changed 
        self.piraniPset_Qline.textChanged.connect(self.updatesetpoint)

        self.valve_stat_ind['valve3'] = QCheckBox() # have to init this way otherwise cannot setStylesheet
        self.valve_stat_ind['valve3'].setStyleSheet("QCheckBox::indicator{width: 40 pt; height: 40 pt}"
                                       "QCheckBox::indicator::checked"
                                       "{"
                                       "background-color : green;"
                                       "}"
                                       "QCheckBox::indicator::unchecked"
                                       "{"
                                       "background-color : red;"
                                       "}")
        self.openBool['valve3'] = QPushButton('Open')
        self.valve_stat_ind['valve1'] = QCheckBox()
        self.valve_stat_ind['valve1'].setStyleSheet("QCheckBox::indicator{width: 40 pt; height: 40 pt}"
                                       "QCheckBox::indicator::checked"
                                       "{"
                                       "background-color : green;"
                                       "}"
                                       "QCheckBox::indicator::unchecked"
                                       "{"
                                       "background-color : red;"
                                       "}")
        self.openBool['valve1']= QPushButton('Open')

        # set preesure btn
        self.setPressure_btn = QPushButton('set Pressure')
        self.setPressure_btn.setCheckable(True)
        self.setPressure_Pgain = QLineEdit()

        # add pressure readings to layout
        initrow =  QFormLayout()
        layout.addLayout(initrow)
        initrow.addRow('P(pirani) [mbar]',self.piraniP_Qline)
        initrow.addRow('P(baraton1Torr) [mbar]', self.baraton1Torr_Qline)
        initrow.addRow('P(baraton) [mbar]', self.baraton_Qline)
        
        setptrow =  QHBoxLayout()
        initrow.addRow('Pset(pirani) [mbar]', setptrow)
        setptrow.addWidget(self.piraniPset_Qline)
        setptrow.addWidget(self.setPressure_btn)
        #setptrow.addWidget(self.setPressure_Pgain)

        secrow =  QHBoxLayout()
        initrow.addRow('valve1', secrow)
        secrow.addWidget(self.valve_stat_ind['valve1'])
        secrow.addWidget(self.openBool['valve1'])
        
        thrdrow =  QHBoxLayout()
        initrow.addRow('valve3', thrdrow)
        thrdrow.addWidget(self.valve_stat_ind['valve3'])
        thrdrow.addWidget(self.openBool['valve3'])

        ## action items
        # get pressure readings
        self.readPressureGauges() 
        # check valves' stat
        self.checkvalvestats()
         # open/close valve when clicked
        self.openBool['valve1'].clicked.connect(lambda: self.changevalvestat('valve1'))
        self.openBool['valve3'].clicked.connect(lambda: self.changevalvestat('valve3'))
        # init Pset pirani with its reading
        self.piraniPset_Qline.setText('{:.3E}'.format(self.Ppirani))        
   
    def readPressureGauges(self):
        '''get data via daq and cal pressures from volt-signals and calib. (inherited from vi) 
        '''
        try:
            with Task() as task_ai:
                for dummy in gaugechannels.values():
                    task_ai.ai_channels.add_ai_voltage_chan(dummy, max_val = 10, min_val =-10, \
                        terminal_config=TerminalConfiguration.RSE)
                    # config sampling rate and mode
                    task_ai.timing.cfg_samp_clk_timing(self.rate, sample_mode=AcquisitionType.FINITE, \
                                                        samps_per_chan=100)
                    task_ai.timing.ref_clk_src='OnboardClock'

                task_ai.start()
                # get 100 samples per channel
                data = task_ai.read(self.samplesperch) # 3x100 'array'
                task_ai.wait_until_done()
                task_ai.stop()
                #task_ai.close() # don't close


                # calculate pressures from calib.... inherited from total_valve_contrl
                self.Ppirani= 10**(np.mean(data[0])-5)
                self.piraniP_Qline.setText('{:.3E}'.format(self.Ppirani))
                self.Pbaraton1Torr= np.mean(data[1])*0.01
                self.baraton1Torr_Qline.setText('{:.3E}'.format(self.Pbaraton1Torr))
                self.Pbaraton= np.mean(data[2])*0.002
                self.baraton_Qline.setText('{:.3E}'.format(self.Pbaraton))
        except:
            print('error in readPressureGauges')

    def checkvalvestats(self):
        #try:

        with Task() as task_ai:
            #with warnings.catch_warnings(record=True) as w:
            for dummy in monitorchannels.values():
                #print(dummy)
                task_ai.ai_channels.add_ai_voltage_chan(dummy, max_val = 10, min_val =-10, \
                    terminal_config=TerminalConfiguration.RSE)
                # config sampling rate and mode
                task_ai.timing.cfg_samp_clk_timing(self.rate, sample_mode=AcquisitionType.FINITE, \
                                                    samps_per_chan=10)
                task_ai.timing.ref_clk_src='OnboardClock'

            task_ai.start()
            # get 10 samples per channel like in the vi
            data = task_ai.read(10) # 4x10 'array'
            task_ai.wait_until_done()
            task_ai.stop()


            for dummy2 in self.valve_stat.keys():

                #valve 1 ind=0; valve3 ind =1
                if dummy2 == 'valve1':
                    i=0
                else:
                    i=1

                # get avg of each monitor channel
                M1 = np.mean(data[2*i])
                M2 = np.mean(data[2*i+1])
                
                if M1 >5 and M2 <= 5: 
                    # open =1
                    self.valve_stat[dummy2] = 1 
                    self.openBool[dummy2].setText('OPEN')
                    #self.valve_stat_ind[dummy2].setChecked(self.valve_stat[dummy2])

                elif M1 <=5 and M2>5:
                    # closed =0 
                    self.valve_stat[dummy2] = 0
                    self.openBool[dummy2].setText('CLOSED')

                else:
                    # faluty =0
                    self.valve_stat[dummy2] = 0
                    self.openBool[dummy2].setText('fault')

                    print(dummy2 + ': M1=' + str(M1) + ', M2=' + str(M2))

                # update indicators
                self.valve_stat_ind[dummy2].setChecked(self.valve_stat[dummy2])

      

                #raise OSError('one of the valve is faulty')
        #except:
        #        print('error in checkvalvestats')

    def changevalvestat(self, ind):
        # get the driver's name
       
        drivername=valvedrivers[ind+'D']
        #try:
        with Task() as task_do:
            task_do.do_channels.add_do_chan(drivername, line_grouping=LineGrouping.CHAN_PER_LINE)   
            with warnings.catch_warnings(record=True) as w:

                if self.valve_stat[ind] == 0: 
                # if valve is closed, open it
                    task_do.write(True, auto_start=True)
                    
                    # close -> open: no error...
                elif self.valve_stat[ind] == 1: 
                # if valve is open, close it
                    task_do.write(False, auto_start=True)
           
            task_do.wait_until_done()
            task_do.stop()

          
        #except:
        #    print('error in changevalvestat')
    
    def updatesetpoint(self):
        '''
        check set point's format and range
        '''

        try: 
            # check if the new input is reasonable 
            #pirani's range: 1e-5 to 1 mbar ?? we are above this
            self.pset=float(self.piraniPset_Qline.text())
            pmax =10 # max set pt? 
            if self.pset > pmax: #or pset<  0.00001:
                print('set pt too high >10 mbar')
                # reinit Pset pirani with its reading
                self.piraniPset_Qline.setText('{:.3E}'.format(self.Ppirani)) 
                self.pset = self.Ppirani
            else:
                self.pset = self.Ppirani
                #print('setting pressure to {:.3E}'.format(pset))
                pass

        except: 
            print('check set pt format')
            # reinit Pset pirani with its reading
            self.piraniPset_Qline.setText('{:.3E}'.format(self.Ppirani)) 
            self.pset = self.Ppirani

