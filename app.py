import sys
import cv2
import numpy as np
import requests
import subprocess
from datetime import datetime
from ultralytics import YOLO
from paddleocr import PaddleOCR
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QHeaderView, QFileDialog
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
import psutil


class PlateDetectionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Automatic Number Plate Detection Dashboard")
        self.setGeometry(100, 100, 1200, 800)

        self.dark_theme = True
        self.toggle_theme_button = QPushButton("🌙 Toggle Theme")
        self.toggle_theme_button.clicked.connect(self.toggle_theme)

        # Layouts
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        middle_layout = QHBoxLayout()
        bottom_layout = QVBoxLayout()

        # Server + detection buttons
        self.start_server_button = QPushButton("Start Server")
        self.start_detection_button = QPushButton("Start Detection")
        self.start_server_button.clicked.connect(self.start_server)
        self.start_detection_button.clicked.connect(self.start_detection)
        self.start_detection_button.setEnabled(False)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_server_button)
        button_layout.addWidget(self.start_detection_button)
        button_layout.addWidget(self.toggle_theme_button)

        # Video Feed
        self.video_label = QLabel("Live Video Feed")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setFixedSize(1020, 500)
        self.video_label.setStyleSheet("background-color: black;")

        top_layout.addWidget(self.video_label)

        # Search & controls
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search plate number")
        self.filter_button = QPushButton("Search")
        self.export_button = QPushButton("Export Data")
        self.fetch_button = QPushButton("Fetch Details")

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.filter_button)
        search_layout.addWidget(self.fetch_button)
        search_layout.addWidget(self.export_button)

        # Data Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Date", "Time", "Plate Number", "Confidence"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Summary
        self.summary_table = QTableWidget(2, 2)
        self.summary_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.summary_table.verticalHeader().setVisible(False)
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.summary_table.setItem(0, 0, QTableWidgetItem("Total Plates"))
        self.summary_table.setItem(1, 0, QTableWidgetItem("Avg Confidence"))
        self.status_label = QLabel("Camera: Offline\nDB: Not Connected\nLoad: 0%")

        summary_layout = QVBoxLayout()
        summary_layout.addWidget(self.summary_table)
        summary_layout.addWidget(self.status_label)

        middle_layout.addWidget(self.table)
        middle_layout.addLayout(summary_layout)

        bottom_layout.addLayout(search_layout)
        bottom_layout.addLayout(middle_layout)

        # Set layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)
        self.central_widget.setLayout(main_layout)

        # Initialize model and timers
        self.cap = None
        self.model = None
        self.ocr = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.detected_plates = []
        self.area = [(5, 180), (3, 249), (984, 237), (950, 168)]

        self.filter_button.clicked.connect(self.filter_table)
        self.export_button.clicked.connect(self.export_data)
        self.fetch_button.clicked.connect(self.fetch_data_from_db)

        self.apply_theme()

    def apply_theme(self):
        if self.dark_theme:
            self.central_widget.setStyleSheet("""
                QWidget {
                    background-color: #121212;
                    color: #ffffff;
                    font-family: 'Segoe UI';
                }
                QPushButton {
                    background-color: #1e88e5;
                    color: white;
                    padding: 6px;
                    border-radius: 5px;
                    border: 2px solid #0f5cab;
                }
                QPushButton:hover {
                    background-color: #1565c0;
                }
                QLineEdit {
                    background-color: #1e1e1e;
                    border: 1px solid #333;
                    padding: 4px;
                    color: white;
                }
                QTableWidget {
                    background-color: #1e1e1e;
                    color: white;
                    gridline-color: #333;
                }
                QHeaderView::section {
                    background-color: #333;
                    color: white;
                }
                QLabel {
                    color: white;
                }
            """)
        else:
            self.central_widget.setStyleSheet("""
                QWidget {
                    background-color: #f5f5f5;
                    color: #000000;
                    font-family: 'Segoe UI';
                }
                QPushButton {
                    background-color: #e0e0e0;
                    color: #000000;
                    padding: 6px;
                    border-radius: 5px;
                    border: 2px solid #b0b0b0;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
                QLineEdit {
                    background-color: #ffffff;
                    border: 1px solid #ccc;
                    padding: 4px;
                    color: black;
                }
                QTableWidget {
                    background-color: #ffffff;
                    color: black;
                    gridline-color: #ccc;
                }
                QHeaderView::section {
                    background-color: #eeeeee;
                    color: black;
                }
                QLabel {
                    color: black;
                }
            """)

    def toggle_theme(self):
        self.dark_theme = not self.dark_theme
        self.apply_theme()

    def start_server(self):
        try:
            subprocess.Popen([sys.executable, "server.py"])
            self.status_label.setText("Camera: Offline\nDB: Starting...\nLoad: 0%")
            self.start_server_button.setEnabled(False)
            self.start_detection_button.setEnabled(True)
        except Exception as e:
            self.status_label.setText(f"Server error: {e}")

    def start_detection(self):
        self.cap = cv2.VideoCapture(0)
        self.model = YOLO("license_plate_detector.pt")
        self.ocr = PaddleOCR()
        self.timer.start(30)
        self.start_detection_button.setEnabled(False)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = cv2.resize(frame, (1020, 500))
        results = self.model(frame)

        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy()
            confidences = result.boxes.conf.cpu().numpy()
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = map(int, box)
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                if cv2.pointPolygonTest(np.array(self.area, np.int32), (cx, cy), False) >= 0:
                    crop = frame[y1:y2, x1:x2]
                    crop = cv2.resize(crop, (120, 70))
                    text = self.perform_ocr(crop)
                    confidence = round(float(confidences[i]) * 100, 2)
                    if text and text not in [item['plate'] for item in self.detected_plates]:
                        now = datetime.now()
                        self.detected_plates.append({
                            'date': now.strftime("%Y-%m-%d"),
                            'time': now.strftime("%H:%M:%S"),
                            'plate': text,
                            'confidence': confidence
                        })
                        self.add_table_row(self.detected_plates[-1])
                        try:
                            requests.post("http://127.0.0.1:8000/store_plate/", json={"plate": text})
                        except:
                            pass
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{text} ({confidence}%)", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        cv2.polylines(frame, [np.array(self.area, np.int32)], True, (255, 0, 0), 2)
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        qimg = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qimg))

        total = len(self.detected_plates)
        avg_conf = round(sum([p['confidence'] for p in self.detected_plates]) / total, 2) if total > 0 else 0
        self.summary_table.setItem(0, 1, QTableWidgetItem(str(total)))
        self.summary_table.setItem(1, 1, QTableWidgetItem(f"{avg_conf}%"))
        self.status_label.setText(f"Camera: Online\nDB: Connected\nLoad: {psutil.cpu_percent()}%")

    def perform_ocr(self, img):
        try:
            result = self.ocr.ocr(img, rec=True)
            if result[0] is not None:
                return ''.join([line[1][0] for line in result[0]])
        except:
            return ""
        return ""

    def add_table_row(self, data):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(data['date']))
        self.table.setItem(row, 1, QTableWidgetItem(data['time']))
        self.table.setItem(row, 2, QTableWidgetItem(data['plate']))
        self.table.setItem(row, 3, QTableWidgetItem(f"{data['confidence']}%"))

    def filter_table(self):
        text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            match = any(text in self.table.item(row, col).text().lower()
                        for col in range(self.table.columnCount()))
            self.table.setRowHidden(row, not match)

    def export_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Data", "data.csv", "CSV Files (*.csv)")
        if path:
            with open(path, 'w') as file:
                file.write("Date,Time,Plate Number,Confidence\n")
                for row in range(self.table.rowCount()):
                    values = [self.table.item(row, col).text() for col in range(self.table.columnCount())]
                    file.write(','.join(values) + "\n")

    def fetch_data_from_db(self):
        try:
            response = requests.get("http://127.0.0.1:8000/plates/")
            plates = response.json()["plates"]
            self.table.setRowCount(0)
            for plate in plates:
                self.table.insertRow(self.table.rowCount())
                self.table.setItem(self.table.rowCount() - 1, 0, QTableWidgetItem(plate['entry_date']))
                self.table.setItem(self.table.rowCount() - 1, 1, QTableWidgetItem(plate['entry_time']))
                self.table.setItem(self.table.rowCount() - 1, 2, QTableWidgetItem(plate['numberplate']))
                self.table.setItem(self.table.rowCount() - 1, 3, QTableWidgetItem("--"))
        except Exception as e:
            print("Failed to fetch data:", e)

    def closeEvent(self, event):
        if self.cap:
            self.cap.release()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PlateDetectionApp()
    window.show()
    sys.exit(app.exec_())
