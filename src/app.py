import time
import json
from pathlib import Path
from typing import TypeVar

from PySide6.QtCore import QFile, QIODevice, Qt, QObject
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
    QFormLayout
)

from src.algorithms.genetic_algorithm import genetic_algorithm
from src.geometry import score
from src.model import Package, Truck
from src.moves import generateRandomState
from src.plotter import Plotter
from src.visualizer import StateVisualizer

T = TypeVar("T", bound=QObject)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        ui_path = Path(__file__).resolve().parent / "ui" / "mainwindow.ui"
        ui_file = QFile(str(ui_path))
        if not ui_file.open(QIODevice.OpenModeFlag.ReadOnly):
            raise RuntimeError(f"Unable to open UI file: {ui_path}")
        try:
            loaded_ui = QUiLoader().load(ui_file)
        finally:
            ui_file.close()
        if loaded_ui is None:
            raise RuntimeError(f"Unable to load UI file: {ui_path}")

        self.setWindowTitle(loaded_ui.windowTitle())
        self.resize(loaded_ui.size())
        centralWidget = loaded_ui.findChild(QWidget, "centralWidget")
        if centralWidget is not None:
            self.ui = centralWidget
        else:
            self.ui = loaded_ui
        self.setCentralWidget(self.ui)
        self.visualizers = []
        self.plotters = []
        self.last_result = None

        self.package_table = self.findWidget(QTableWidget, "tablePackages")
        self.truck_length = self.findWidget(QLineEdit, "editTruckLength")
        self.truck_width = self.findWidget(QLineEdit, "editTruckWidth")
        self.truck_height = self.findWidget(QLineEdit, "editTruckHeight")
        self.max_capacity = self.findWidget(QLineEdit, "editTruckMaxCapacity")

        self.algorithm_layout = self.findWidget(QFormLayout, "algorithmLayout")
        self.algorithm_choice = self.findWidget(QComboBox, "comboAlgorithm")

        self.visualizer_frame = self.findWidget(QFrame, "visualizer")
        self.plot_frame = self.findWidget(QScrollArea, "plotFrame")
        self.plot_content = self.findWidget(QWidget, "plotContent")
        pLayout = self.plot_content.layout()
        if pLayout is None:
            raise RuntimeError(f"Unable to access plot content layout")
        self.plot_content_layout = pLayout
        
        self.file_label = self.findWidget(QLabel, "lblFileInserted")

        self.btn_select_file = self.findWidget(QPushButton, "btnSelectFile")
        self.btn_add_package = self.findWidget(QPushButton, "btnAddPackage")
        self.btn_remove_selected = self.findWidget(QPushButton, "btnRemoveSelected")
        self.btn_run = self.findWidget(QPushButton, "btnRun")
        self.btn_reset = self.findWidget(QPushButton, "btnReset")
        self.btn_save = self.findWidget(QPushButton, "btnSave")

        self.algorithm_choice.addItem("Hill Climbing")
        self.algorithm_choice.addItem("Simulated Annealing")
        self.algorithm_choice.addItem("Genetic Algorithm")

        self.btn_select_file.clicked.connect(self.select_input_file)
        self.btn_add_package.clicked.connect(self.add_package_row)
        self.btn_remove_selected.clicked.connect(self.remove_selected_package_rows)
        self.btn_run.clicked.connect(self.run_algorithm)
        self.btn_reset.clicked.connect(self.reset_form)
        self.btn_save.clicked.connect(self.save_result)

        vLayout = self.visualizer_frame.layout()
        if vLayout is None:
            raise RuntimeError(f"Unable to access visualizer frame layout")
        while vLayout.count():
            item = vLayout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        self.initial_visualizer = StateVisualizer("Initial State", parent=self.visualizer_frame)
        self.final_visualizer = StateVisualizer("Final State", parent=self.visualizer_frame)
        vLayout.addWidget(self.initial_visualizer)
        vLayout.addWidget(self.final_visualizer)
        self.visualizers = [self.initial_visualizer, self.final_visualizer]

    def findWidget(self, widget_type: type[T], name: str) -> T:
        widget = self.ui.findChild(widget_type, name)
        if widget is None:
            raise RuntimeError(f"UI widget not found: {name}")
        return widget

    def add_package_row(self):
        row = self.package_table.rowCount()
        self.package_table.insertRow(row)
        for column, value in enumerate([f"P{row}", "", "", "", "", ""]):
            self.package_table.setItem(row, column, QTableWidgetItem(value))
        self.set_fragile_checkbox(row, False)
        self.package_table.setItem(row, 7, QTableWidgetItem("")) # ETA

    def set_fragile_checkbox(self, row, checked):
        item = QTableWidgetItem()
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self.package_table.setItem(row, 6, item)

    def remove_selected_package_rows(self):
        rows = sorted(
            {index.row() for index in self.package_table.selectedIndexes()},
            reverse=True,
        )
        for row in rows:
            self.package_table.removeRow(row)

    def select_input_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open package file",
            "",
            "JSON files (*.json);;All files (*)",
        )
        if not path:
            return

        try:
            with open(path, newline="", encoding="utf-8-sig") as input_file:
                data_json = json.load(input_file)

            if not isinstance(data_json, dict):
                raise ValueError("The JSON root must be an object.")

            truck_json = self.json_value(data_json, "truck")
            if isinstance(truck_json, dict):
                self.set_json_field(self.truck_length, truck_json, "length", "l")
                self.set_json_field(self.truck_width, truck_json, "width", "w")
                self.set_json_field(self.truck_height, truck_json, "height", "h")
                self.set_json_field(self.max_capacity, truck_json, "max_capacity", "capacity", "max_weight")

            packages_json = self.json_value(data_json, "packages")
            if packages_json is not None:
                if not isinstance(packages_json, list):
                    raise ValueError("The packages value must be an array.")

                self.package_table.setRowCount(0)
                for package_json in packages_json:
                    if not isinstance(package_json, dict):
                        raise ValueError("Each package must be a JSON object.")

                    values = [
                        self.json_text(self.json_value(package_json, "id", "package_id"),),
                        self.json_text(self.json_value(package_json, "length", "l"),),
                        self.json_text(self.json_value(package_json, "width", "w"),),
                        self.json_text(self.json_value(package_json, "height", "h"),),
                        self.json_text(self.json_value(package_json, "weight", "mass"),),
                        self.json_text(self.json_value(package_json, "value", "price"),),
                    ]
                    fragile = self.json_bool(self.json_value(package_json, "fragile", "is_fragile"))
                    row = self.package_table.rowCount()
                    self.package_table.insertRow(row)
                    for column, value in enumerate(values):
                        self.package_table.setItem(row, column, QTableWidgetItem(value))
                    self.set_fragile_checkbox(row, fragile)
            self.file_label.setText(f"Loaded: {Path(path).name}")
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
            QMessageBox.critical(self, "Input Error", str(error))

    @staticmethod
    def json_key(key):
        return "".join(character for character in str(key).lower() if character.isalnum())

    @staticmethod
    def json_value(data, *names):
        normalized = {
            MainWindow.json_key(key): value
            for key, value in data.items()
        }
        for name in names:
            key = MainWindow.json_key(name)
            if key in normalized:
                return normalized[key]
        return None

    @staticmethod
    def json_text(value):
        return "" if value is None else str(value)

    @staticmethod
    def json_bool(value):
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip().lower() in {
                "true", "1", "yes", "y", "on"
            }
        return bool(value)

    def set_json_field(self, field, data, *names):
        value = self.json_value(data, *names)
        if value is not None:
            field.setText(self.json_text(value))

    def read_packages(self):
        packages = {}
        for row in range(self.package_table.rowCount()):
            values = []
            for column in range(8):
                item = self.package_table.item(row, column)
                if item is not None:
                    if self.package_table.item(row, column):
                        if column == 6: # fragile column, has checkbox instead of text
                            values.append(item.checkState() == Qt.CheckState.Checked)
                                
                        else:
                            values.append(item.text().strip())
                    else:
                        values.append("")

            package_id = values[0]
            if not package_id:
                raise ValueError(f"Package ID cannot be empty (row {row + 1}).")
            if package_id in packages:
                raise ValueError(f"Duplicate package ID: {package_id}")

            try:
                length = int(values[1])
                width = int(values[2])
                height = int(values[3])
                weight = int(values[4])
                value = int(values[5])
                fragile = values[6]
                if values[7] == "":
                    eta = 0
                else:
                    eta = int(values[7])
            except ValueError:
                raise ValueError(f"Package fields must be integers (row {row + 1}).")
            
            if width <= 0 or length <= 0 or height <= 0:
                raise ValueError(f"Package dimensions must be positive ({package_id}).")
            if weight < 0 or value < 0 or eta < 0:
                raise ValueError(f"Weight, value, or eta cannot be negative ({package_id}).")

            packages[package_id] = Package(
                id=package_id,
                width=width,
                length=length,
                height=height,
                weight=weight,
                value=value,
                fragile=fragile,
                eta=eta
            )

        if not packages:
            raise ValueError("Enter at least one package.")
        return packages

    @staticmethod
    def read_positive_int(field, label):
        try:
            value = int(field.text().strip())
        except ValueError:
            raise ValueError(f"{label} must be an integer.")
        if value <= 0:
            raise ValueError(f"{label} must be positive.")
        return value

    def clear_visualizers(self):
        for visualizer in self.visualizers:
            visualizer.clear_state()

    def clear_plotters(self):
        while self.plot_content_layout.count():
            item = self.plot_content_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                    widget.deleteLater()
        self.plotters.clear()

    def run_algorithm(self):
        try:
            packages = self.read_packages()
            truck = Truck(
                width=self.read_positive_int(self.truck_width, "Truck width"),
                length=self.read_positive_int(
                    self.truck_length, "Truck length"
                ),
                height=self.read_positive_int(
                    self.truck_height, "Truck height"
                ),
                max_capacity=self.read_positive_int(
                    self.max_capacity, "Maximum capacity"
                ),
            )
            if self.algorithm_choice.currentText() != "Genetic Algorithm":
                raise ValueError("The selected algorithm is not implemented.")

            self.btn_run.setEnabled(False)
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            QApplication.processEvents()

            initial_state = generateRandomState(truck, packages)
            initial_value = score(truck, packages, initial_state)
            start_time = time.perf_counter()
            listMax = []
            listAvg = []
            final_state = genetic_algorithm(
                truck, packages, 100, 100, listMax, listAvg
            )
            elapsed = time.perf_counter() - start_time
            final_value = score(truck, packages, final_state)

            self.set_output("valAlgorithmUsed", "Genetic Algorithm")
            self.set_output(
                "valConfiguration",
                f"Initial population = {100}, "
                f"Iterations = {100}",
            )
            self.set_output("valExecutionTime", f"{elapsed:.4f} seconds")
            self.set_output("valInitialStateValue", f"{initial_value:.4f}")
            self.set_output("valFinalStateValue", f"{final_value:.4f}")

            self.initial_visualizer.set_state(truck, packages, initial_state)
            self.final_visualizer.set_state(truck, packages, final_state)

            self.clear_plotters()
            iterations = list(range(1, len(listMax) + 1))
            max_plotter = Plotter(iterations, listMax, "Maximum Score by Iteration", "Iteration", "Maximum score")
            avg_plotter = Plotter(iterations, listAvg, "Average Score by Iteration", "Iteration", "Average score")
            self.plotters = [max_plotter, avg_plotter]
            for plotter in self.plotters:
                self.plot_content_layout.addWidget(plotter)

            self.last_result = (
                "Algorithm: Genetic Algorithm\n"
                f"Initial value: {initial_value:.4f}\n"
                f"Final value: {final_value:.4f}\n"
                f"Execution time: {elapsed:.4f} seconds\n"
            )
        except Exception as error:
            QMessageBox.critical(self, "Execution Error", f"{type(error).__name__}: {error}")
        finally:
            QApplication.restoreOverrideCursor()
            self.btn_run.setEnabled(True)

    def set_output(self, name, value):
        self.findWidget(QLabel, name).setText(value)

    def reset_form(self):
        for field in (self.truck_length, self.truck_width, self.truck_height, self.max_capacity):
            field.clear()

        self.package_table.setRowCount(0)

        self.file_label.setText("No file has been inserted")

        for name in (
            "valAlgorithmUsed",
            "valConfiguration",
            "valExecutionTime",
            "valInitialStateValue",
            "valFinalStateValue",
        ):
            self.set_output(name, "")

        self.last_result = None

        self.clear_visualizers()
        self.clear_plotters()

    def save_result(self):
        if self.last_result is None:
            QMessageBox.information(
                self, "No result", "Run the algorithm before saving."
            )
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save result", "", "Text files (*.txt);;All files (*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as output_file:
                output_file.write(self.last_result)