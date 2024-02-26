import sys
from io import BytesIO
import requests
from PIL import Image, UnidentifiedImageError
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QPixmap


class Map(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('map.ui', self)
        self.api = API()
        self.searchButton.clicked.connect(self.search)
        for button in self.buttonGroup.buttons():
            button.clicked.connect(self.change_type)
        self.mapButton.setChecked(True)
        self.search()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_PageUp:
            self.api.change_scale(1)
        elif event.key() == Qt.Key_PageDown:
            self.api.change_scale(-1)
        self.search()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.api.change_scale(1)
        elif event.angleDelta().y() < 0:
            self.api.change_scale(-1)
        self.search()

    def search(self):
        lon = self.longitude.value()
        lat = self.latitude.value()
        try:
            result = self.api.search_by_coords(lon, lat)
            Image.open(BytesIO(result)).save('temp.png')
            self.mapLabel.setPixmap(QPixmap('temp.png'))
        except UnidentifiedImageError:
            self.statusBar().showMessage('Возникла ошибка при работе с API!')

    def change_type(self):
        if self.sender().text() == 'Карта':
            map_type = 'map'
        if self.sender().text() == 'Спутник':
            map_type = 'sat'
        if self.sender().text() == 'Гибрид':
            map_type = 'sat,skl'
        self.api.change_type(map_type)
        self.search()


class API:
    def __init__(self):
        self.api_server = "http://static-maps.yandex.ru/1.x/"
        self.z = 12
        self.type = 'map'

    def search_by_coords(self, lon, lat):
        self.params = {'l': self.type, 'll': ','.join([str(lon), str(lat)]), 'z': self.z}
        response = requests.get(self.api_server, params=self.params)
        return response.content

    def change_type(self, map_type):
        self.type = map_type

    def change_scale(self, incr):
        if incr > 0 and self.z < 15 or incr < 0 and self.z > 1:
            self.z += incr

    def move(self):
        pass


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Map()
    window.show()
    sys.excepthook = except_hook
    app.exec()
