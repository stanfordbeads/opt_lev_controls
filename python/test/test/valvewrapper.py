from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QGridLayout, QLabel, \
    QVBoxLayout, QLineEdit, QCheckBox, QDoubleSpinBox, QMessageBox, QMainWindow, QFormLayout
from PyQt5.QtCore import QTimer, QDateTime, Qt, QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap
import numpy as np
import csv, sys, time, traceback
from datetime import datetime
from nidaqmx.task import Task, AcquisitionType   # for the DAQ
from nidaqmx.constants import TerminalConfiguration, LineGrouping, Edge

# import valve classes 
sys.path.append('C:\\Users\\beads\\opt_lev_controls\\python\\valves')
import ventvalvectrl, morevalvesandgauges 

# execfile('valvewrapper.py')  # run this in main...

app = QApplication(sys.argv)
app.setStyleSheet("QLineEdit{font-size: 16pt;}"
                     "QLabel{font-size: 16pt;}"
                      "QPushButton{font-size: 16pt;}")
screen = morevalvesandgauges.MainWindow()
screen.show()
sys.exit(app.exec_())


##### add image to app? 
#        self.label = QLabel()
#        #self.pixmap = QPixmap()
#        self.pixmap = QPixmap('valvesettings.png')
#        self.label.setPixmap(self.pixmap)
#        self.label.resize(self.pixmap.width(),
#                          self.pixmap.height())
#        leftbox.addWidget(self.label)   
#        self.setCentralWidget(self.label)