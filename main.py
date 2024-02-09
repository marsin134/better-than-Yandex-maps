import io
from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QPixmap, QImage
import sys

import requests
from PIL import Image

template = """<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>QMainWindow</class>
 <widget class="QMainWindow" name="QMainWindow">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>538</width>
    <height>414</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>Dialog</string>
  </property>
  <widget class="QLabel" name="label_im">
   <property name="geometry">
    <rect>
     <x>20</x>
     <y>20</y>
     <width>501</width>
     <height>301</height>
    </rect>
   </property>
   <property name="text">
    <string/>
   </property>
  </widget>
 </widget>
 <resources/>
 <connections/>
</ui>
"""

toponym_to_find = " ".join(sys.argv[1:])

geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

geocoder_params = {
    "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
    "geocode": toponym_to_find,
    "format": "json"}

response = requests.get(geocoder_api_server, params=geocoder_params)

if not response:
    geocoder_params['geocode'] = 'Россия, Москва, Красная площадь'
    response = requests.get(geocoder_api_server, params=geocoder_params)

# Преобразуем ответ в json-объект
json_response = response.json()
# Получаем первый топоним из ответа геокодера.
toponym = json_response["response"]["GeoObjectCollection"][
    "featureMember"][0]["GeoObject"]

low = toponym['boundedBy']['Envelope']['lowerCorner']
up = toponym['boundedBy']['Envelope']['upperCorner']


def get_im(delta, toponyms=json_response["response"]["GeoObjectCollection"][
    "featureMember"][0]["GeoObject"]):
    # Координаты центра топонима:
    toponym_coodrinates = toponyms["Point"]["pos"]
    # Долгота и широта:
    toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")

    # Собираем параметры для запроса к StaticMapsAPI:
    map_params = {
        "ll": ",".join([toponym_longitude, toponym_lattitude]),
        "spn": ",".join([str(delta), str(delta)]),
        "l": "map"
    }

    map_api_server = "http://static-maps.yandex.ru/1.x/"
    responses = requests.get(map_api_server, params=map_params)

    image = Image.open(io.BytesIO(responses.content))
    return image


class DBSample(QMainWindow):
    def __init__(self):
        super().__init__()
        f = io.StringIO(template)
        uic.loadUi(f, self)
        self.delta = 0.01
        self.start()

    def start(self):
        im = get_im(self.delta)
        im = im.convert("RGB")
        data = im.tobytes("raw", "RGB")
        qi = QImage(data, im.size[0], im.size[1], im.size[0] * 3, QImage.Format.Format_RGB888)
        self.pixmap = QPixmap.fromImage(qi)
        self.label_im.setPixmap(self.pixmap)

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Up:
            if self.delta > 0.001:
                self.delta -= self.delta / 1.5
                self.start()
        elif key == QtCore.Qt.Key_Down:
            if self.delta < 50:
                self.delta += self.delta / 1.5
                self.start()
        print(self.delta)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    ex = DBSample()
    ex.show()

    sys.exit(app.exec_())
