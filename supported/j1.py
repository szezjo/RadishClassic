from requests_html import HTMLSession
from _object import _RadioStation


class Station(_RadioStation):
    name = 'J1 Hits'
    lang = 'jp'

    def getURL(self):
        return 'http://jenny.torontocast.com:8056/'

    def getENSongData(self):
        session = HTMLSession()
        r = session.get('https://www.delmarvafm.org/player/j1-hits/')
        r.html.render()
        s=r.html.find('div.nowPlay.cf', first=True).text
        return s.splitlines()

    def getJPSongData(self):
        session = HTMLSession()
        j = session.get('https://j1fm.com/player/en/onair_aiir.php')
        ja=j.html.find('TD.onair_artist_j_aiir', first=True).text
        jt=j.html.find('TD.onair_title_j_aiir', first=True).text
        return [ja, jt]

    def getSongData(self):
        if(self.lang=='jp'):
            return self.getJPSongData()
        else:
            return self.getENSongData()


