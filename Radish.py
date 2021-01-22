import vlc
import sys
import json
import re
import struct
import urllib.request as urllib2
from time import sleep
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QLineEdit, QLabel, QComboBox, QMenuBar, QPushButton, QMessageBox, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QGridLayout, QSlider, QSizePolicy, QListWidget
from PyQt5.QtCore import QSize, Qt, QThread, QObject, pyqtSignal
from PyQt5.QtGui import QIcon

config = {}
lang = {}
stations = {}

class Player(QObject):
    vlci = vlc.Instance('--input-repeat=-1','--fullscreen','-q')
    vlcp = vlci.media_player_new()

    def setParent(self,parent):
        self.parent=parent

    def run(self):
        while(True):
            sleep(1)

    def changeStation(self, url):
        self.vlcp.stop()
        media = self.vlci.media_new(url)
        self.vlcp.set_media(media)
        self.vlcp.play()
        self.parent.updateMetadata()

    def stop(self):
        self.vlcp.stop()
            
class StatusManager(QObject):
    def setParent(self,parent):
        self.parent=parent
    
    def run(self):
        i=0
        while(True):
            if(i==0):
                self.parent.updateMetadata()
            self.parent.updateLabel()
            i=i+1
            if(i==10):
                i=0
            sleep(1)

class Radish(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.setMinimumSize(QSize(700,180))
        self.setWindowTitle("Radish")
        self.status = QLabel()
        self.stationSelector = QComboBox()
        self.metadata = ""
        self.songName = ""
        self.artist = ""

        self.pThread = QThread()
        self.player = Player()
        self.player.setParent(self)
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
        self.refreshStations()
        self.stationSelector.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.stationSelector.currentIndexChanged.connect(self.changeStation)
        self.volSlider = QSlider(Qt.Horizontal)
        self.volSlider.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.volSlider.setMinimum(0)
        self.volSlider.setMaximum(100)
        self.volSlider.setValue(100)
        self.volSlider.valueChanged.connect(self.changeVolume)
        radioGrid.addWidget(self.stationSelector,0,0,1,3)
        radioGrid.addWidget(self.volSlider,0,3,1,1)
        mainArea.addLayout(radioGrid,0)

        self.status.setText(lang['welcome'])
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

    def updateMetadata(self):
        stationUrl = stations.get(self.stationSelector.currentText())
        if(stationUrl=='Don\'t play' or not stationUrl):
            return
        encoding = 'latin1'
        request = urllib2.Request(stationUrl, headers={'Icy-MetaData': 1})
        response = urllib2.urlopen(request)
        metaint = int(response.headers['icy-metaint'])
        for _ in range(10):
            response.read(metaint)
            metadata_length = struct.unpack('B', response.read(1))[0]*16
            metadata = response.read(metadata_length).rstrip(b'\0')
            m = re.search(br"StreamTitle='([^']*)';", metadata)
            if m:
                title = m.group(1)
                if title:
                    break
        else:
            self.metadata = ''
            return
        self.metadata=str(title.decode(encoding, errors='replace'))


    def updateLabel(self):
        state = str(self.player.vlcp.get_state())
        if(state=='State.NothingSpecial' or state=='State.Stopped'):
            self.status.setText('')
        elif(state=='State.Opening'):
            self.status.setText(lang['loading_stream'])
        elif(state=='State.Playing'):
            self.status.setText(self.metadata)
        else:
            self.status.setText(state)

    def changeVolume(self):
        self.player.vlcp.audio_set_volume(self.volSlider.value())



class ManageStations(QMainWindow):
    def __init__(self, parent=None):
        self.parent=parent
        QMainWindow.__init__(self)

        self.setMinimumSize(QSize(700,300))
        self.setWindowTitle(lang['ms_title'])
        self.editStationWin = StationEditor(self)

        widget = QWidget()
        mainArea = QGridLayout()
        widget.setLayout(mainArea)
        self.setCentralWidget(widget)

        self.stationsList = QListWidget()
        for station in stations:
            self.stationsList.addItem(station)
        self.stationsList.itemDoubleClicked.connect(self.playStation)
        mainArea.addWidget(self.stationsList,0,0,1,2)

        buttonsGrid = QGridLayout()
        playButton = QPushButton(lang['ms_play'])
        playButton.clicked.connect(self.playStation)
        addButton = QPushButton(lang['ms_add'])
        addButton.clicked.connect(self.addStation)
        editButton = QPushButton(lang['ms_edit'])
        editButton.clicked.connect(lambda: self.editStation(self.stationsList.currentRow()))
        removeButton = QPushButton(lang['ms_remove'])
        removeButton.clicked.connect(lambda: self.removeStation(self.stationsList.currentRow()))
        supportedButton = QPushButton(lang['ms_supported'])
        buttonsGrid.addWidget(playButton,0,0)
        buttonsGrid.addWidget(addButton,1,0)
        buttonsGrid.addWidget(editButton,2,0)
        buttonsGrid.addWidget(removeButton,3,0)
        buttonsGrid.addWidget(supportedButton,4,0)
        mainArea.addLayout(buttonsGrid,0,2,1,1)

    def playStation(self):
        index = self.parent.stationSelector.findText(self.stationsList.currentItem().text())
        if(index != -1):
            self.parent.stationSelector.setCurrentIndex(index)

    def addStation(self):
        if(self.editStationWin):
            self.editStationWin.close()
        self.editStationWin = StationEditor(self)
        self.editStationWin.show()

    def editStation(self,stationIndex):
        if(self.editStationWin):
            self.editStationWin.close()
        self.editStationWin = StationEditor(self,stationIndex)
        self.editStationWin.show()

    def removeStation(self,stationIndex):
        name = list(stations)[stationIndex]
        reply = QMessageBox.question(self, name, lang['se-remove-q'], QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if(reply==QMessageBox.Yes):
            stations.pop(name)
            with open('stations.json', 'w') as outfile:
                json.dump(stations,outfile)
            self.updateList()

    def updateList(self):
        self.stationsList.clear()
        for station in stations:
            self.stationsList.addItem(station)
        self.parent.refreshStations()

class StationEditor(QMainWindow):
    def __init__(self, parent=None, stationIndex=-1):
        self.parent=parent
        self.index=stationIndex
        QMainWindow.__init__(self)

        self.setMinimumSize(QSize(400,200))
        self.setWindowTitle(lang['se-title'])

        widget = QWidget()
        mainArea = QGridLayout()
        widget.setLayout(mainArea)
        self.setCentralWidget(widget)

        nameLabel = QLabel(lang['se-station-name'])
        urlLabel = QLabel(lang['se-station-url'])
        self.nameField = QLineEdit()
        self.urlField = QLineEdit()
        saveButton = QPushButton(lang['se-apply'])
        saveButton.clicked.connect(self.saveStation)
        cancelButton = QPushButton(lang['se-cancel'])
        cancelButton.clicked.connect(self.close)

        if(stationIndex!=-1 and stationIndex!=None):
            self.nameField.setText(list(stations)[stationIndex])
            self.urlField.setText(list(stations.values())[stationIndex])

        mainArea.addWidget(nameLabel,0,0,1,1)
        mainArea.addWidget(urlLabel,1,0,1,1)
        mainArea.addWidget(self.nameField,0,1,1,5)
        mainArea.addWidget(self.urlField,1,1,1,5)
        mainArea.addWidget(cancelButton,2,4,1,1)
        mainArea.addWidget(saveButton,2,5,1,1)


    def saveStation(self):
        if(self.index==-1):
            stations[self.nameField.text()]=self.urlField.text()
        else:
            stationsNew = {}
            stationsList = list(stations)
            stationsListVal = list(stations.values())
            for i in range(0,self.index):
                stationsNew[stationsList[i]] = stationsListVal[i]
            stationsNew[self.nameField.text()]=self.urlField.text()
            for i in range(self.index+1, len(stations)):
                stationsNew[stationsList[i]] = stationsListVal[i]
            stations.clear()
            stations.update(stationsNew)

        with open('stations.json', 'w') as outfile:
            json.dump(stations,outfile)
        
        self.parent.updateList()




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
