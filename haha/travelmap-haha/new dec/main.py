import sys
from PySide6.QtWidgets import QApplication
from travel_app import TravelApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TravelApp()
    window.show()
    sys.exit(app.exec())
