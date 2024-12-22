import folium
import os
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QApplication, QLabel,
    QHBoxLayout, QProgressBar, QTabWidget, QScrollArea, QFormLayout, QComboBox,  QMessageBox
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl
from PySide6.QtGui import QFont, QPixmap
from functools import partial
from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading

# Импорт данных из data.py
from data import locations, friends_data


class TravelApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Интерактивная карта путешествий")
        self.setGeometry(100, 100, 1000, 800)

        self.visited_places = set()
        self.total_places = len(locations)  # Общее количество мест, зависит от данных из data.py
        self.dark_mode = False

        self.friends_data = friends_data  # Данные о друзьях из data.py

        self.generate_map()
        self.initUI()
        self.start_server()

    def initUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # Виджет для вкладок
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
            }
            QTabBar::tab {
                background-color: #87CEFA;
                padding: 10px;
                margin: 2px;
                border-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #5ab0cd;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.tabs)

        # Вкладка карты
        map_tab = QWidget()
        map_layout = QVBoxLayout()
        map_tab.setLayout(map_layout)
        self.tabs.addTab(map_tab, "Карта")

        # Виджет для отображения карты
        self.map_view = QWebEngineView()
        self.map_view.loadFinished.connect(self.on_map_loaded)  # Добавляем обработчик загрузки
        self.update_map()
        map_layout.addWidget(self.map_view)

        # Метка прогресса
        self.progress_label = QLabel("Прогресс: 0%")
        self.progress_label.setFont(QFont("Arial", 14))
        map_layout.addWidget(self.progress_label)

        # Шкала прогресса
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        map_layout.addWidget(self.progress_bar)

        # Комбинированный бокс для выбора мест
        self.place_selector = QComboBox()
        for index, (_, _, name, _, _) in enumerate(locations, start=1):
            self.place_selector.addItem(f"Посетить {name}")
        self.place_selector.currentIndexChanged.connect(self.visit_selected_place)
        map_layout.addWidget(self.place_selector)

        # Слот для изображения награды
        self.reward_image_label = QLabel()
        self.reward_image_label.setPixmap(QPixmap("reward_placeholder.png").scaled(100, 100))
        map_layout.addWidget(self.reward_image_label)

        # Текст челленджа
        self.challenge_label = QLabel("Челлендж: Посетите 10 мест, чтобы получить награду!")
        self.challenge_label.setFont(QFont("Arial", 12))
        map_layout.addWidget(self.challenge_label)

        # Метка награды
        self.reward_label = QLabel("")
        self.reward_label.setFont(QFont("Arial", 12))
        self.reward_label.setStyleSheet("color: green;")
        map_layout.addWidget(self.reward_label)

        # Кнопка переключения темы
        self.theme_button = QPushButton("Переключить тему")
        self.theme_button.setStyleSheet("""
            QPushButton {
                background-color: #d3d3d3;
                border-radius: 10px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #a9a9a9;
                color: white;
            }
        """)
        self.theme_button.clicked.connect(self.toggle_theme)
        map_layout.addWidget(self.theme_button)

        # Установка начальной темы
        self.set_theme()

        # Вкладка с друзьями
        friends_tab = QWidget()
        friends_layout = QVBoxLayout()
        friends_tab.setLayout(friends_layout)
        self.tabs.addTab(friends_tab, "Друзья")

        # Прокручиваемый список друзей
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QFormLayout()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        friends_layout.addWidget(scroll_area)

        # Добавление друзей, их аватарок и прогресса
        for friend, data in self.friends_data.items():
            friend_layout = QHBoxLayout()

            # Добавление аватарки друга
            avatar = QLabel()
            avatar.setPixmap(QPixmap(f"avatars/{friend}.png").scaled(50, 50))  # Замените на реальные пути к изображениям
            friend_layout.addWidget(avatar)

            # Метка с именем друга и прогрессом
            friend_label = QLabel(f"{friend}: Прогресс - {len(data['visited'])} мест из {self.total_places}")
            friend_layout.addWidget(friend_label)

            # Кнопка для просмотра посещенных мест
            view_places_button = QPushButton("Посмотреть места")
            view_places_button.clicked.connect(partial(self.show_visited_places, friend))
            friend_layout.addWidget(view_places_button)

            # Добавление к layout
            scroll_layout.addRow(friend_layout)

            # Добавление достижений
            achievements = self.get_achievements(data['visited'])
            achievement_label = QLabel(f"Достижения: {', '.join(achievements) if achievements else 'Нет'}")
            scroll_layout.addRow(achievement_label)

    def visit_selected_place(self):
        """Обработчик выбора места из комбинированного списка."""
        selected_index = self.place_selector.currentIndex()  # Получаем индекс выбранного места
        if selected_index == -1:
            return

        # Место, выбранное пользователем (индексация начинается с 0, поэтому добавляем 1)
        place_index = selected_index + 1
        if place_index not in self.visited_places:
            self.visited_places.add(place_index)
            self.update_progress()

    def update_progress(self):
        """Обновляет прогресс посещенных мест и отображает его на экране."""
        visited_count = len(self.visited_places)
        progress_percent = (visited_count / self.total_places) * 100
        self.progress_bar.setValue(progress_percent)
        self.progress_label.setText(f"Прогресс: {int(progress_percent)}%")

        # Проверка достижений
        achievements = self.get_achievements(self.visited_places)
        self.reward_label.setText(f"Достижения: {', '.join(achievements)}")
        
        # Показываем изображение достижения
        self.reward_image_label.setPixmap(QPixmap("reward_placeholder.png").scaled(100, 100))

    def get_achievements(self, visited_places):
        """Получает достижения на основе количества посещенных мест."""
        achievements = []
        if len(visited_places) >= 5:
            achievements.append("Новичок")
        if len(visited_places) >= 10:
            achievements.append("Опытный путешественник")
        if len(visited_places) >= 15:
            achievements.append("Мастеровед")
        return achievements

    def generate_map(self):
        """Генерация карты с метками."""
        map_object = folium.Map(location=[51.5074, -0.1278], zoom_start=6)

        # Добавление маркеров на карту
        for lat, lon, name, rating, description in locations:
            popup_content = f"<b>{name}</b><br>Рейтинг: {rating}/5<br>{description}"
            folium.Marker([lat, lon], popup=popup_content).add_to(map_object)

        # Сохранение карты как HTML файл
        self.map_filename = "map.html"
        map_path = os.path.join(os.path.dirname(__file__), self.map_filename)
        map_object.save(map_path)

    def update_map(self):
        """Обновляет отображение карты в QWebEngineView."""
        map_path = QUrl.fromLocalFile(os.path.abspath(self.map_filename))
        self.map_view.setUrl(map_path)

    def on_map_loaded(self):
        """Этот метод вызывается, когда карта загружена в QWebEngineView."""
        print("Карта загружена и отображается.")

    def start_server(self):
        """Запуск HTTP сервера для обслуживания HTML файлов (например, карты)."""
        def run():
            httpd = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)
            print("Сервер запущен на http://localhost:8000")
            httpd.serve_forever()

        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def toggle_theme(self):
        """Переключение темы между светлой и темной."""
        self.dark_mode = not self.dark_mode
        self.set_theme()

    def set_theme(self):
        """Устанавливает тему приложения (светлая или темная)."""
        if self.dark_mode:
            self.setStyleSheet("""
                QWidget {
                    background-color: #2e2e2e;
                    color: white;
                }
                QPushButton {
                    background-color: #5a5a5a;
                    color: white;
                }
                QTabBar::tab {
                    background-color: #444;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: #ffffff;
                    color: black;
                }
                QPushButton {
                    background-color: #d3d3d3;
                    color: black;
                }
                QTabBar::tab {
                    background-color: #87CEFA;
                }
            """)
    def show_visited_places(self, friend):
        """Отображает посещенные места для указанного друга."""
        if friend not in self.friends_data:
            return

        # Получаем данные о посещенных местах
        visited_places = self.friends_data[friend]["visited"]
        visited_places_names = []

        for place_id in visited_places:
            # Находим название места по ID
            for lat, lon, name, _, _ in locations:
                if place_id == locations.index((lat, lon, name, _, _)) + 1:  # Места в locations индексируются с 1
                    visited_places_names.append(name)
                    break

        # Отображаем список посещенных мест
        visited_places_text = "\n".join(visited_places_names) if visited_places_names else "Нет посещенных мест"
        
        # Создаем диалоговое окно для отображения мест
        msg = QMessageBox(self)
        msg.setWindowTitle(f"Посещенные места {friend}")
        msg.setText(f"Друг {friend} посетил следующие места:\n{visited_places_text}")
        msg.exec()
