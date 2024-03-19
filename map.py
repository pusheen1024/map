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
        for button in self.buttonGroup.buttons():
            button.clicked.connect(self.change_type)
        self.mapButton.setChecked(True)
        self.coordsSearch.clicked.connect(lambda: self.search(new_search=True))
        self.nameSearch.clicked.connect(lambda: self.search(new_search=True))
        self.clearResult.clicked.connect(self.clear)
        self.search(new_search=True)

    def keyPressEvent(self, event):
        deltas = {Qt.Key_S: (0, -1), Qt.Key_W: (0, 1), Qt.Key_D: (1, 0), Qt.Key_A: (-1, 0)}
        if event.key() == Qt.Key_PageUp:
            self.api.change_scale(1)
        elif event.key() == Qt.Key_PageDown:
            self.api.change_scale(-1)
        elif event.key() in deltas.keys():
            self.api.move_map(*deltas[event.key()])
        self.search(new_search=False)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.api.change_scale(1)
        elif event.angleDelta().y() < 0:
            self.api.change_scale(-1)
        self.search(new_search=False)

    def search(self, new_search):
        if self.sender() and self.sender().objectName() == 'nameSearch':
            place_name = self.placeName.text()
            result = self.api.search_by_name(place_name)
            if not result:
                self.statusBar.showMessage('Объект не найден!')
                return
        else:
            lon = self.longitude.value()
            lat = self.latitude.value()
            result = self.api.search_by_coords(lon, lat, new_search)
        try:
            Image.open(BytesIO(result)).save('temp.png')
            self.mapLabel.setPixmap(QPixmap('temp.png'))
            self.statusBar.showMessage('')
        except UnidentifiedImageError:
            self.statusBar.showMessage('Возникла ошибка при работе с API!')

    def clear(self):
        self.api.clear_result()
        self.search(new_search=False)

    def change_type(self):
        if self.sender().text() == 'Карта':
            map_type = 'map'
        if self.sender().text() == 'Спутник':
            map_type = 'sat'
        if self.sender().text() == 'Гибрид':
            map_type = 'sat,skl'
        self.api.change_type(map_type)
        self.search(new_search=False)


class API:
    def __init__(self):
        self.api_server = "http://static-maps.yandex.ru/1.x/"
        self.geocoder_server = "http://geocode-maps.yandex.ru/1.x/"
        self.lon_size, self.lat_size = 180, 90
        self.x_size, self.y_size = 600, 360
        self.points = list()
        self.z = 12
        self.type = 'map'

    def search_by_coords(self, lon, lat, new_search=True):
        if new_search:
            self.lon, self.lat = lon, lat
        self.params = {'l': self.type,
                       'll': ','.join([str(self.lon), str(self.lat)]),
                       'z': self.z,
                       'size': ','.join([str(self.x_size), str(self.y_size)])}
        self.params['pt'] = '~'.join([','.join([str(p[0]), str(p[1])]) for p in self.points])
        response = requests.get(self.api_server, params=self.params)
        return response.content

    def search_by_name(self, object_name):
        geocoder_params = {'apikey': '40d1649f-0493-4b70-98ba-98533de7710b',
                           'geocode': object_name,
                           'format': 'json'}
        try:
            response = requests.get(self.geocoder_server, params=geocoder_params).json()
            toponym = response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
            lon, lat = map(float, toponym["Point"]["pos"].split())
            self.clear_result()
            self.points.append((lon, lat))
            return self.search_by_coords(lon, lat, new_search=True)
        except (KeyError, IndexError):
            pass

    def clear_result(self):
        self.points.clear()

    def change_type(self, map_type):
        self.type = map_type

    def change_scale(self, incr):
        if incr > 0 and self.z < 17 or incr < 0 and self.z > 1:
            self.z += incr

    def move_map(self, dx, dy):
        self.lon = self.lon + dx * self.lon_size / 2 ** (self.z - 1)
        self.lat = self.lat + dy * self.lat_size / 2 ** (self.z - 1)
        self.lon = -abs(self.lon % 90) if self.lon < 0 else self.lon % 90
        self.lat = -abs(self.lat % 90) if self.lat < 0 else self.lat % 90


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Map()
    window.show()
    sys.excepthook = except_hook
    app.exec()
