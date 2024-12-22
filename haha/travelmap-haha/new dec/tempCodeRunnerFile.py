import os
import folium
from functools import partial
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QTabWidget,
    QProgressBar, QComboBox, QFormLayout, QScrollArea, QHBoxLayout, QMessageBox
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl
from PySide6.QtGui import QFont, QPixmap
from data import get_data


class TravelApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Интерактивная карта путешествий")
        self.setGeometry(100, 100, 1000, 800)

        self.visited_places = set()
        self.total_places = 20
        self.dark_mode = False

        self.friends_data = get_data()

        self.generate_map()
        self.initUI()
        self.start_server()

    def initUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Карта
        map_tab = QWidget()
        map_layout = QVBoxLayout()
        map_tab.setLayout(map_layout)
        self.tabs.addTab(map_tab, "Карта")

        self.map_view = QWebEngineView()
        self.map_view.loadFinished.connect(self.on_map_loaded)
        self.update_map()
        map_layout.addWidget(self.map_view)

        self.progress_label = QLabel("Прогресс: 0%")
        self.progress_label.setFont(QFont("Arial", 14))
        map_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        map_layout.addWidget(self.progress_bar)

        self.place_selector = QComboBox()
        map_layout.addWidget(self.place_selector)

        self.reward_image_label = QLabel()
        self.reward_image_label.setPixmap(QPixmap("reward_placeholder.png").scaled(100, 100))
        map_layout.addWidget(self.reward_image_label)

        self.challenge_label = QLabel("Челлендж: Посетите 10 мест, чтобы получить награду!")
        map_layout.addWidget(self.challenge_label)

        self.reward_label = QLabel("")
        map_layout.addWidget(self.reward_label)

        self.theme_button = QPushButton("Переключить тему")
        map_layout.addWidget(self.theme_button)

        self.set_theme()

        # Друзья
        friends_tab = QWidget()
        friends_layout = QVBoxLayout()
        friends_tab.setLayout(friends_layout)
        self.tabs.addTab(friends_tab, "Друзья")

        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QFormLayout()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        friends_layout.addWidget(scroll_area)

        for friend, data in self.friends_data.items():
            friend_layout = QHBoxLayout()

            avatar = QLabel()
            avatar.setPixmap(QPixmap(f"avatars/{friend}.png").scaled(50, 50))
            friend_layout.addWidget(avatar)

            friend_label = QLabel(f"{friend}: Прогресс - {len(data['visited'])} мест из {self.total_places}")
            friend_layout.addWidget(friend_label)

            view_places_button = QPushButton("Посмотреть места")
            view_places_button.clicked.connect(partial(self.show_visited_places, friend))
            friend_layout.addWidget(view_places_button)

            scroll_layout.addRow(friend_layout)

            achievements = self.get_achievements(data['visited'])
            achievement_label = QLabel(f"Достижения: {', '.join(achievements) if achievements else 'Нет'}")
            scroll_layout.addRow(achievement_label)

    def show_visited_places(self, friend):
        visited_places = self.friends_data[friend]["visited"]
        places_info = []

        for place in visited_places:
            place_info = self.locations[place - 1]
            places_info.append(f"{place_info[2]} (Рейтинг: {place_info[3]}/5): {place_info[4]}")

        places_text = "\n".join(places_info) if places_info else "Нет посещенных мест."
        self.show_message(f"{friend} посетил следующие места:\n{places_text}")

    def show_message(self, message):
        msg_box = QMessageBox()
        msg_box.setText(message)
        msg_box.exec()

    def get_achievements(self, visited_places):
        achievements = []
        if len(visited_places) >= 5:
            achievements.append("Первопроходец: Посетите 5 мест.")
        if len(visited_places) >= 10:
            achievements.append("Исследователь: Посетите 10 мест.")
        if len(visited_places) >= 15:
            achievements.append("Гурман: Посетите 15 мест.")
        if len(visited_places) == self.total_places:
            achievements.append("Совершенный путник: Посетите все места!")
        return achievements

    def generate_map(self):
        map_object = folium.Map(location=[55.7558, 37.6173], zoom_start=12)

        self.locations = [
            (55.75202, 37.61749, "Московский Кремль", 4.9, "Исторический комплекс и резиденция президента России."),
            # Добавьте другие места
        ]

        for lat, lon, name, rating, description in self.locations:
            popup_content = f"<b>{name}</b><br>Рейтинг: {rating}/5<br>{description}"
            folium.Marker([lat, lon], popup=popup_content).add_to(map_object)

        self.map_filename = "map.html"
        map_path = os.path.join(os.getcwd(), self.map_filename)
        map_object.save(map_path)

    def update_map(self):
        map_url = "http://localhost:8000/map.html"
        self.map_view.setUrl(QUrl(map_url))

    def on_map_loaded(self):
        print("Карта успешно загружена!")

    def visit_place(self, place):
        if place not in self.visited_places:
            self.visited_places.add(place)
            place_info = self.locations[place - 1]
            name, rating, description = place_info[2], place_info[3], place_info[4]
            self.show_place_info(name, rating, description)
            self.update_progress()

    def update_progress(self):
        progress = len(self.visited_places) / self.total_places * 100
        self.progress_label.setText(f"Прогресс: {progress:.0f}%")
        self.progress_bar.setValue(progress)

    def update_map_with_progress(self):
        map_object = folium.Map(location=[55.7558, 37.6173], zoom_start=12)

        for i, (lat, lon, name, rating, description) in enumerate(self.locations, start=1):
            color = "green" if i in self.visited_places else "red"
            popup_content = f"<b>{name}</b><br>Рейтинг: {rating}/5<br>{description}"
            folium.Marker([lat, lon], popup=popup_content, icon=folium.Icon(color=color)).add_to(map_object)

        map_path = os.path.join(os.getcwd(), self.map_filename)
        map_object.save(map_path)
        self.update_map()

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.set_theme()

    def set_theme(self):
        if self.dark_mode:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                # Добавьте другие стили для темной темы
            """)
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f5f5f5;
                    color: #000000;
                }
                # Добавьте другие стили для светлой темы
            """)

    def start_server(self):
        from server import start_server
        start_server()

