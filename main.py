import io
from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QPixmap, QImage
import sys

import requests
from PIL import Image

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


class DBSample(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('designer.ui', self)
        self.delta = 0.01

        toponyms = json_response["response"]["GeoObjectCollection"][
            "featureMember"][0]["GeoObject"]
        toponym_coodrinates = toponyms["Point"]["pos"]
        # Долгота и широта:
        self.toponym_longitude, self.toponym_lattitude = (float(elem) for elem in toponym_coodrinates.split(" "))

        self.draw_image()

    def draw_image(self):
        im = self.get_im()
        im = im.convert("RGB")
        data = im.tobytes("raw", "RGB")
        qi = QImage(data, im.size[0], im.size[1], im.size[0] * 3, QImage.Format.Format_RGB888)
        self.pixmap = QPixmap.fromImage(qi)
        self.label_im.setPixmap(self.pixmap)

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_W:
            if self.delta > 0.001:
                self.delta -= self.delta / 1.5
                self.draw_image()
        elif key == QtCore.Qt.Key_S:
            if self.delta < 50:
                self.delta += self.delta / 1.5
                self.draw_image()
        elif key == QtCore.Qt.Key_Left:
            if not (self.toponym_longitude - self.delta < -180):
                self.toponym_longitude -= self.delta
            else:
                self.toponym_longitude = 179
            self.draw_image()
        elif key == QtCore.Qt.Key_Right:
            if not (self.toponym_longitude + self.delta > 180):
                self.toponym_longitude += self.delta
            else:
                self.toponym_longitude = -179
            self.draw_image()
        elif key == QtCore.Qt.Key_Up:
            if not (self.toponym_lattitude + self.delta / 1.5 > 90):
                self.toponym_lattitude += self.delta / 1.5
            else:
                self.toponym_lattitude = 80
            self.draw_image()
        elif key == QtCore.Qt.Key_Down:
            if not (self.toponym_lattitude - self.delta / 1.5 < -90):
                self.toponym_lattitude -= self.delta / 1.5
            else:
                self.toponym_lattitude = -80
            self.draw_image()

    def get_im(self):
        # Собираем параметры для запроса к StaticMapsAPI:
        map_params = {
            "ll": ",".join([str(self.toponym_longitude),
                            str(self.toponym_lattitude)]),
            "spn": ",".join([str(self.delta), str(self.delta)]),
            "l": "map"
        }

        map_api_server = "http://static-maps.yandex.ru/1.x/"
        responses = requests.get(map_api_server, params=map_params)

        image = Image.open(io.BytesIO(responses.content))
        return image


if __name__ == '__main__':
    app = QApplication(sys.argv)

    ex = DBSample()
    ex.show()

    sys.exit(app.exec_())
