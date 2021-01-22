import vlc
import sys
import json
from time import sleep
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QLabel, QComboBox, QMenuBar, QPushButton, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QGridLayout, QSlider, QSizePolicy
from PyQt5.QtCore import QSize, Qt, QThread, QObject, pyqtSignal
from PyQt5.QtGui import QIcon

config = {}
lang = {}
stations = {}

class Player(QObject):
    vlci = vlc.Instance('--input-repeat=-1','--fullscreen','-q')
    vlcp = vlci.media_player_new()

    def run(self):
        while(True):
            sleep(1)

    def changeStation(self, url):
        self.vlcp.stop()
        media = self.vlci.media_new(url)
        self.vlcp.set_media(media)
        self.vlcp.play()

    def stop(self):
        self.vlcp.stop()
            
class StatusManager(QObject):
    def setParent(self,parent):
        self.parent=parent
    
    def run(self):
        while(True):
            self.parent.updateLabel()
            sleep(1)

class Radish(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.setMinimumSize(QSize(700,180))
        self.setWindowTitle("Radish")
        self.status = QLabel()

        self.pThread = QThread()
        self.player = Player()
        self.player.moveToThread(self.pThread)
        self.pThread.started.connect(self.player.run)
        self.pThread.start()

        self.sThread = QThread()
        self.statusManager = StatusManager()
        self.statusManager.setParent(self)
        self.statusManager.moveToThread(self.sThread)
        self.sThread.started.connect(self.statusManager.run)
        self.sThread.start()

        widget = QWidget()
        mainArea = QVBoxLayout()
        widget.setLayout(mainArea)
        self.setCentralWidget(widget)

        self.manageStationsWin = ManageStations(self)

        # Menubar
        menuBar = QMenuBar()
        menuBarOptions = menuBar.addMenu(lang['options'])
        menuBarOptions_manage = menuBarOptions.addAction(lang['manage_stations'])
        menuBarOptions_manage.triggered.connect(self.openManageStations)
        menuBarOptions.addSeparator()
        menuBarOptions_quit = menuBarOptions.addAction(lang['quit'])
        menuBarOptions_quit.triggered.connect(self.closeAllWindows)
        mainArea.addWidget(menuBar)

        # Radio selector and volume slider
        radioGrid = QGridLayout()
        self.stationSelector = QComboBox()
        self.refreshStations()
        self.stationSelector.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.stationSelector.currentIndexChanged.connect(self.changeStation)
        volSlider = QSlider(Qt.Horizontal)
        volSlider.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        radioGrid.addWidget(self.stationSelector,0,0,1,3)
        radioGrid.addWidget(volSlider,0,3,1,1)
        mainArea.addLayout(radioGrid,0)

        self.status.setText('Welcome to Radish!')
        self.status.setAlignment(Qt.AlignCenter)
        mainArea.addWidget(self.status,1)


    def openManageStations(self):
        self.manageStationsWin.show()

    def closeAllWindows(self):
        self.manageStationsWin.close()
        self.close()

    def refreshStations(self):
        for i in range(0,self.stationSelector.count()):
            self.stationSelector.removeItem(0)
        self.stationSelector.addItem(lang['dont_play'])
        for station in stations:
            self.stationSelector.addItem(station)

    def changeStation(self):
        stationUrl = stations.get(self.stationSelector.currentText())
        
        if(stationUrl=='Don\'t play'):
            self.player.stop()
        elif(stationUrl):
            self.player.changeStation(stationUrl)
        else:
            self.player.stop()

    def updateLabel(self):
        state = str(self.player.vlcp.get_state())
        if(state=='State.NothingSpecial' or state=='State.Stopped'):
            self.status.setText('')
        elif(state=='State.Opening'):
            self.status.setText(lang['loading_stream'])
        elif(state=='State.Playing'):
            self.status.setText('artist\nsong')
        else:
            self.status.setText(state)

class ManageStations(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self)

        self.setMinimumSize(QSize(700,300))
        self.setWindowTitle(lang['ms_title'])

        widget = QWidget()
        mainArea = QHBoxLayout()
        widget.setLayout(mainArea)
        self.setCentralWidget(widget)


if __name__ == "__main__":
    with open('config.json') as cfg_file:
        config = json.load(cfg_file)

    try:
        with open('lang/'+config['language']+'.json') as json_file:
            lang = json.load(json_file)
    except OSError as e:
        with open('lang/en.json') as json_file:
            lang = json.load(json_file)

    with open('stations.json') as json_file:
        stations = json.load(json_file)

    

    app = QtWidgets.QApplication(sys.argv)
    mainWin = Radish()
    mainWin.show()
    mainWin.pThread.quit()
    sys.exit( app.exec_() )
