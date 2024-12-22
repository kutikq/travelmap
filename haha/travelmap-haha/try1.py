from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl
import sys
import folium
import os

class TravelApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Интерактивная карта путешествий")
        self.setGeometry(100, 100, 800, 600)
        
        # Настройка интерфейса
        self.initUI()

    def initUI(self):
        # Основной виджет
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # Отображение карты
        self.map_view = QWebEngineView()
        self.update_map()
        layout.addWidget(self.map_view)

        # Кнопка обновления карты
        update_button = QPushButton("Обновить карту")
        update_button.clicked.connect(self.update_map)
        layout.addWidget(update_button)

    def update_map(self):
        # Создаём карту с помощью folium
        map_object = folium.Map(location=[55.751244, 37.618423], zoom_start=10)  # Москва
        folium.Marker([55.751244, 37.618423], popup="Москва", tooltip="Кликните для информации").add_to(map_object)
        
        # Сохраняем карту как HTML
        map_path = os.path.join(os.getcwd(), "map.html")
        map_object.save(map_path)

        # Загружаем карту в QWebEngineView
        self.map_view.setUrl(QUrl.fromLocalFile(map_path))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TravelApp()
    window.show()
    sys.exit(app.exec())
