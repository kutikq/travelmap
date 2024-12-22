import sys
from PySide6.QtWidgets import QApplication, QWidget
from achievements import Ui_Form

'''Вообщем при нажатии кнопки "достижения" в мейнике, у нас должно открыться данное окно
    здесь особо ниче интересного, кнопка ок для выхода из того окна, просто просмотр достижений
    их иконки должны быть слева (но я ниче не вставила пока). Единственное, над чем задуматься
    это над "пройдено ...", где "..." должен быть прогресс пользователя (0/5, 0/10 и тд)
    я хз смогу ли осуществить этот самый прогресс, так как в try2 у меня не получилось
'''
class AchievementsWindow(QWidget):
    def __init__(self, parent=None):
        super(AchievementsWindow, self).__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AchievementsWindow()
    window.show()
    sys.exit(app.exec())
