from PySide6.QtCore import QCoreApplication, QRect, QSize, Qt, QMetaObject
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QPushButton


class Ui_DialogAchievements(object):
    def setupUi(self, DialogAchievements):
        if not DialogAchievements.objectName():
            DialogAchievements.setObjectName("DialogAchievements")
        DialogAchievements.resize(401, 300)
        DialogAchievements.setStyleSheet(
            "background-color: qlineargradient(spread:pad, x1:1, y1:1, x2:0, y2:0, "
            "stop:0 rgba(81, 0, 135, 255), stop:0.427447 rgba(41, 61, 132, 235), "
            "stop:1 rgba(155, 79, 165, 255));"
            "font-family: Noto Sans SC;"
        )
        # Кнопка
        self.dialogButton = QPushButton(DialogAchievements)
        self.dialogButton.setObjectName("dialogButton")
        self.dialogButton.setGeometry(QRect(163, 267, 75, 23))

        # Текст
        self.textDialog = QLabel(DialogAchievements)
        self.textDialog.setObjectName("textDialog")
        self.textDialog.setGeometry(QRect(20, 117, 400, 16))

        # Изображение
        self.pictureLabelDialog = QLabel(DialogAchievements)
        self.pictureLabelDialog.setObjectName("pictureLabelDialog")
        self.pictureLabelDialog.setGeometry(QRect(150, 11, 100, 100))
        self.pictureLabelDialog.setMaximumSize(QSize(100, 100))
        self.pictureLabelDialog.setPixmap(
            QPixmap("../labproga/otcp/dialog_achievements/7gId4RidGh8.jpg")
        )
        self.pictureLabelDialog.setScaledContents(True)
        self.pictureLabelDialog.setAlignment(Qt.AlignCenter)

        self.retranslateUi(DialogAchievements)

        QMetaObject.connectSlotsByName(DialogAchievements)

    def retranslateUi(self, DialogAchievements):
        DialogAchievements.setWindowTitle(
            QCoreApplication.translate("DialogAchievements", "Dialog")
        )
        self.dialogButton.setText(
            QCoreApplication.translate("DialogAchievements", "Ура!")
        )
        self.textDialog.setText(
            QCoreApplication.translate(
                "DialogAchievements", "Вы получили достижение: не спать 24 часа"
            )
        )


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    dialog = QDialog()
    ui = Ui_DialogAchievements()
    ui.setupUi(dialog)
    dialog.show()
    sys.exit(app.exec())
