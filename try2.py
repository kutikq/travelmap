import folium
import os
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QApplication, QLabel, 
    QHBoxLayout, QProgressBar, QTabWidget, QScrollArea, QFormLayout, QComboBox, QDialog
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl
from PySide6.QtGui import QFont, QPixmap
from functools import partial
from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading
from PySide6.QtCore import Qt
from dialog_achievements import Ui_DialogAchievements  # Импортируйте ваш класс

class TravelApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Интерактивная карта путешествий")
        self.setGeometry(100, 100, 1000, 800)

        self.visited_places = set()
        self.total_places = 20
        self.dark_mode = False

        self.friends_data = {
            "Поручик": {"visited": {1, 3, 5, 7, 8, 2, 4, 13, 12, 15, 16, 20}, "achievements": []},
            "Бэк": {"visited": {2, 4, 6, 9, 10}, "achievements": []},
            "Мяу": {"visited": {1, 2, 3, 10, 15}, "achievements": []},
            "Кутик": {"visited": {4}, "achievements": []},
            "ЯКурица": {"visited": {1, 5, 9, 13, 15, 16, 2, 3, 4 , 6, 7, 8, 10, 11, 12, 14, 17, 18, 19, 20}, "achievements": []},
        }

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
        self.map_view.loadFinished.connect(self.on_map_loaded)
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
        for index, (_, _, name, _, _) in enumerate(self.locations, start=1):
            self.place_selector.addItem(f"Посетить {name}")
        self.place_selector.currentIndexChanged.connect(self.visit_selected_place)
        map_layout.addWidget(self.place_selector)

        # Слот для изображения награды
        self.reward_image_label = QLabel()
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

    def show_visited_places(self, friend):
        """Отображает места, посещенные другом."""
        visited_places = self.friends_data[friend]["visited"]
        places_info = []

        for place in visited_places:
            place_info = self.locations[place - 1]
            places_info.append(f"{place_info[2]} (Рейтинг: {place_info[3]}/5): {place_info[4]}")

        places_text = "\n".join(places_info) if places_info else "Нет посещенных мест."
        self.show_message(f"{friend} посетил следующие места:\n{places_text}")

    def show_message(self, message):
        """Отображает сообщение в диалоговом окне."""
        from PySide6.QtWidgets import QMessageBox
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
        # Генерация карты с местами
        map_object = folium.Map(location=[55.7558, 37.6173], zoom_start=12)

        self.locations = [
            (55.75202, 37.61749, "Московский Кремль", 4.9, "Исторический комплекс и резиденция президента России."),
            (55.75098, 37.61698, "Успенский собор", 4.8, "Один из главных православных соборов России."),
            (55.75076, 37.61849, "Царь-колокол", 4.7, "Самый большой колокол в мире, который никогда не звонил."),
            (55.74968, 37.6136, "Оружейная палата", 4.6, "Хранилище уникальных коллекций оружия и доспехов."),
            (55.760178, 37.618575, "Большой театр", 4.9, "Один из самых известных театров в мире."),
            (55.73955, 37.6177, "Площадь Революции", 4.7, "Одна из центральных площадей Москвы, где расположены памятники историческим деятелям."),
            (55.751244, 37.620577, "Красная площадь", 5.0, "Историческое сердце Москвы, место проведения многих значимых событий."),
            (55.7557, 37.6176, "Мавзолей Ленина", 4.5, "Мавзолей, в котором покоится тело Владимира Ленина."),
            (55.746047, 37.616264, "Парк Горького", 4.8, "Известный московский парк для отдыха и культурных мероприятий."),
            (55.74517, 37.61712, "Воробьёвы горы", 4.9, "Одна из самых высоких точек Москвы с панорамным видом на город."),
            (55.7644, 37.6155, "Третьяковская галерея", 4.9, "Один из крупнейших музеев искусства в России."),
            (55.7575, 37.6173, "Храм Василия Блаженного", 5.0, "Известный храм на Красной площади, символ Москвы."),
            (55.7536, 37.616, "ГУМ", 4.8, "Роскошный торговый центр на Красной площади."),
            (55.756, 37.603, "Станция метро 'Киевская'", 4.7, "Одно из самых известных московских метро, характерное своими архитектурными особенностями."),
            (55.7677, 37.6347, "Измайловский Кремль", 4.6, "Культурно-развлекательный комплекс в Москве, напоминающий старинную крепость."),
            (55.7471, 37.595, "ВДНХ", 4.8, "Выставочный комплекс и музей под открытым небом."),
            (55.7610, 37.5983, "Поклонная гора", 4.7, "Место исторических памятников и мемориалов."),
            (55.7701, 37.6215, "Музей космонавтики", 4.9, "Музей, посвященный истории освоения космоса."),
            (55.7237, 37.6727, "Московский зоопарк", 4.6, "Один из крупнейших зоопарков в России."),
            (55.7579, 37.6641, "Кремль в Измайлово", 4.7, "Культурный комплекс и туристическая достопримечательность.")
        ]

        # Добавление маркеров на карту
        for lat, lon, name, rating, description in self.locations:
            popup_content = f"<b>{name}</b><br>Рейтинг: {rating}/5<br>{description}"
            folium.Marker([lat, lon], popup=popup_content).add_to(map_object)

        # Сохранение карты как HTML файл
        self.map_filename = "map.html"
        map_path = os.path.join(os.getcwd(), self.map_filename)
        map_object.save(map_path)
        print(f"Карта сохранена в: {map_path}")

    def update_map(self):
        map_url = "http://localhost:8000/map.html"
        self.map_view.setUrl(QUrl(map_url))

    def on_map_loaded(self):
        print("Карта успешно загружена!")

    def visit_selected_place(self):
        place = self.place_selector.currentIndex() + 1
        self.visit_place(place)

    def visit_place(self, place):
        if place not in self.visited_places:
            self.visited_places.add(place)  # Добавляем место в список посещенных
            place_info = self.locations[place - 1]  # Получаем информацию о месте
            name, rating, description = place_info[2], place_info[3], place_info[4]
            self.show_place_info(name, rating, description)
            self.update_progress()  # Обновляем прогресс
            self.update_map_with_progress()  # Обновляем карту с посещенными местами

    def show_place_info(self, name, rating, description):
        info_message = f"<b>{name}</b><br>Рейтинг: {rating}/5<br>{description}"
        print(info_message)  # Вывод информации в консоль для теста

    def update_progress(self):
        progress = len(self.visited_places) / self.total_places * 100
        self.progress_label.setText(f"Прогресс: {progress:.0f}%")
        self.progress_bar.setValue(progress)

        # Проверка достижений
        achievements = []
        rewards = {  # Список достижений и связанные изображения
            "Первопроходец: Посетите 5 мест.": "achievement_5.png",
            "Исследователь: Посетите 10 мест.": "achievement_10.png",
            "Гурман: Посетите 15 мест.": "achievement_15.png",
            "Совершенный путник: Посетите все места!": "achievement_20.png",
        }

        # Проверяем, какие достижения получены
        if len(self.visited_places) == 5 and "Первопроходец: Посетите 5 мест." not in achievements:
            achievements.append("Первопроходец: Посетите 5 мест.")
        if len(self.visited_places) == 10 and "Исследователь: Посетите 10 мест." not in achievements:
            achievements.append("Исследователь: Посетите 10 мест.")
        if len(self.visited_places) == 15 and "Гурман: Посетите 15 мест." not in achievements:
            achievements.append("Гурман: Посетите 15 мест.")
        if len(self.visited_places) == self.total_places and "Совершенный путник: Посетите все места!" not in achievements:
            achievements.append("Совершенный путник: Посетите все места!")

        # Обновляем список достижений
        self.reward_image_label.clear()  # Очистить старые изображения
        if achievements:
            self.reward_label.setText(f"Получено достижений: {len(achievements)}")
            for achievement in achievements:
                achievement_layout = QHBoxLayout()

                # Текст достижения
                achievement_label = QLabel(achievement)
                achievement_layout.addWidget(achievement_label)


                self.reward_image_label.setLayout(achievement_layout)

            # Показываем диалог только для последнего достижения
            last_achievement = achievements[-1]
            last_image_path = rewards.get(last_achievement, "reward_placeholder.png")
            self.show_achievement_dialog(last_achievement, last_image_path)
        else:
            self.reward_label.setText("Нет достижений.")

        # Дополнительный челлендж
        if len(self.visited_places) < 10:
            self.challenge_label.setText("Челлендж: Посетите 10 мест, чтобы получить промокод!")
            self.reward_image_label.clear()  # Очистить изображение, если прогресс сбросился
        elif len(self.visited_places) == 10:
            self.challenge_label.setText("Поздравляем! Вы получили промокод на скидку 10% 🎉")

    def show_achievement_dialog(self, achievement_text, image_path):
        dialog = QDialog()
        ui = Ui_DialogAchievements()
        ui.setupUi(dialog)

        # Устанавливаем текст и изображение
        ui.textDialog.setText(f"Вы получили достижение: {achievement_text}")
        if os.path.exists(image_path):
            ui.pictureLabelDialog.setPixmap(QPixmap(image_path).scaled(100, 100))
        else:
            ui.pictureLabelDialog.setPixmap(QPixmap("reward_placeholder.png").scaled(100, 100))

        ui.dialogButton.clicked.connect(dialog.accept)

        dialog.exec()  # Показываем диалог

    def click_ok(self):
        self.close()



    def update_map_with_progress(self):
        # Создаем новую карту
        map_object = folium.Map(location=[55.7558, 37.6173], zoom_start=12)

        # Проходим по всем локациям и добавляем маркеры
        for i, (lat, lon, name, rating, description) in enumerate(self.locations, start=1):
            # Если место посещено, маркер зеленый, если нет — красный
            color = "green" if i in self.visited_places else "red"
            
            # Содержимое всплывающего окна
            popup_content = f"<b>{name}</b><br>Рейтинг: {rating}/5<br>{description}"
            
            # Добавляем маркер на карту
            folium.Marker(
                [lat, lon],
                popup=popup_content,
                icon=folium.Icon(color=color)
            ).add_to(map_object)

        # Сохраняем карту в файл
        map_path = os.path.join(os.getcwd(), self.map_filename)
        map_object.save(map_path)

        # Обновляем отображение карты в приложении
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
                QPushButton {
                    background-color: #444444;
                    color: #ffffff;
                    border-radius: 5px;
                    padding: 10px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #616161;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 14px;
                }
                QComboBox {
                    background-color: #444444;
                    color: #ffffff;
                    border-radius: 5px;
                    padding: 5px;
                    font-size: 14px;
                }
                QComboBox QAbstractItemView {
                    background-color: #444444;
                    color: #ffffff;
                }
                QProgressBar {
                    background-color: #444444;
                    border-radius: 10px;
                    height: 20px;
                }
                QProgressBar::chunk {
                    background-color: #42f554;
                    border-radius: 10px;
                }
                QProgressBar::horizontal {
                    border-radius: 10px;
                }
                
                /* Стиль для вкладки Друзья */
                QTabWidget::pane {
                    background-color: #2b2b2b;
                    border: none;
                }
                
                QTabBar {
                    background-color: #444444;
                    border: 1px solid #666666;
                    padding: 10px;
                }
                
                QTabBar::tab {
                    background-color: #444444;
                    color: #ffffff;
                    padding: 8px;
                    border-radius: 5px;
                }
                
                QTabBar::tab:selected {
                    background-color: #616161;
                }
                
                QTabBar::tab:hover {
                    background-color: #616161;
                }

                /* Список друзей */
                QListView {
                    background-color: #333333;
                    border-radius: 5px;
                    color: #ffffff;
                }
                
                QListView::item {
                    background-color: #444444;
                    padding: 8px;
                    border-radius: 5px;
                }
                
                QListView::item:selected {
                    background-color: #616161;
                }
                
                /* Ввод данных */
                QLineEdit {
                    background-color: #444444;
                    color: #ffffff;
                    border-radius: 5px;
                    padding: 8px;
                }
                QLineEdit:focus {
                    border: 1px solid #42f554;
                }

                /* Если есть другие элементы в панели друзей */
                QWidget {
                    background-color: #2b2b2b;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f5f5f5;
                    color: #000000;
                }
                QPushButton {
                    background-color: #87CEFA;
                    color: #000000;
                    border-radius: 5px;
                    padding: 10px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #5ab0cd;
                }
                QLabel {
                    color: #000000;
                    font-size: 14px;
                }
                QComboBox {
                    background-color: #ffffff;
                    color: #000000;
                    border-radius: 5px;
                    padding: 5px;
                    font-size: 14px;
                }
                QComboBox QAbstractItemView {
                    background-color: #ffffff;
                    color: #000000;
                }
                QProgressBar {
                    background-color: #d3d3d3;
                    border-radius: 10px;
                    height: 20px;
                }
                QProgressBar::chunk {
                    background-color: #42f554;
                    border-radius: 10px;
                }
                QProgressBar::horizontal {
                    border-radius: 10px;
                }
                
                /* Стиль для вкладки Друзья */
                QTabWidget::pane {
                    background-color: #f5f5f5;
                    border: none;
                }
                
                QTabBar {
                    background-color: #87CEFA;
                    border: 1px solid #CCCCCC;
                    padding: 10px;
                }
                
                QTabBar::tab {
                    background-color: #87CEFA;
                    color: #000000;
                    padding: 8px;
                    border-radius: 5px;
                }
                
                QTabBar::tab:selected {
                    background-color: #5ab0cd;
                }
                
                QTabBar::tab:hover {
                    background-color: #5ab0cd;
                }

                /* Список друзей */
                QListView {
                    background-color: #ffffff;
                    border-radius: 5px;
                    color: #000000;
                }
                
                QListView::item {
                    background-color: #f0f0f0;
                    padding: 8px;
                    border-radius: 5px;
                }
                
                QListView::item:selected {
                    background-color: #5ab0cd;
                }
                
                /* Ввод данных */
                QLineEdit {
                    background-color: #ffffff;
                    color: #000000;
                    border-radius: 5px;
                    padding: 8px;
                }
                QLineEdit:focus {
                    border: 1px solid #42f554;
                }

                /* Если есть другие элементы в панели друзей */
                QWidget {
                    background-color: #f5f5f5;
                }
            """)



    def start_server(self):
        def run_server():
            handler = SimpleHTTPRequestHandler
            self.server = HTTPServer(("localhost", 8000), handler)
            print("HTTP сервер запущен на http://localhost:8000")
            self.server.serve_forever()

        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TravelApp()
    window.show()
    sys.exit(app.exec())
