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
    QSpinBox,
    QDoubleSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
    QFormLayout
)

from src.algorithms.genetic_algorithm import genetic_algorithm
from src.algorithms.hill_climbing import (
    random_restart,
    sideways_move,
    steepest_ascent,
    stochastic,
)
from src.algorithms.simulated_annealing import simulated_annealing
from src.model import Package, Truck
from src.moves import generateRandomState
from src.objective import package_count, score
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
        except:
            raise RuntimeError(f"Unable to open UI file: {ui_path}")
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
        self.truck_length = self.findWidget(QSpinBox, "editTruckLength")
        self.truck_width = self.findWidget(QSpinBox, "editTruckWidth")
        self.truck_height = self.findWidget(QSpinBox, "editTruckHeight")
        self.max_capacity = self.findWidget(QSpinBox, "editTruckMaxCapacity")

        self.algorithm_layout = self.findWidget(QFormLayout, "algorithmLayout")
        self.algorithm_choice = self.findWidget(QComboBox, "comboAlgorithm")
        self.algorithm_choice.addItem("Hill Climbing")
        self.algorithm_choice.addItem("Simulated Annealing")
        self.algorithm_choice.addItem("Genetic Algorithm")
        self.objective_choice = self.findWidget(QComboBox, "comboObjective")
        self.objective_choice.addItem("Maximize score")
        self.objective_choice.addItem("Maximize packet count")

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

        self.btn_select_file.clicked.connect(self.select_input_file)
        self.btn_add_package.clicked.connect(self.add_package_row)
        self.btn_remove_selected.clicked.connect(self.remove_selected_package_rows)
        self.btn_run.clicked.connect(self.run_algorithm)
        self.btn_reset.clicked.connect(self.reset_form)
        self.btn_save.clicked.connect(self.save_result)
        self.algorithm_choice.currentTextChanged.connect(self.update_algorithm_configuration)
        self.objective_choice.currentTextChanged.connect(self.update_algorithm_configuration)

        self.hill_version = QComboBox()
        self.hill_version.addItems([
            "Steepest Ascent",
            "Sideways Move",
            "Random Restart",
            "Stochastic",
        ])
        self.hill_version.currentTextChanged.connect(self.update_algorithm_configuration)

        self.configuration_widgets = {}
        self.update_algorithm_configuration()

        self.result_objective_used = self.findWidget(QLabel, "lblObjectiveUsed")
        self.result_algorithm_used = self.findWidget(QLabel, "lblAlgorithmUsed")
        self.result_configuration_used = self.findWidget(QLabel, "lblConfigurationUsed")
        self.result_statistic = self.findWidget(QLabel, "lblStatisticDetail")

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

    def update_algorithm_configuration(self):
        self.algorithm_layout.removeWidget(self.hill_version)

        while self.algorithm_layout.rowCount() > 2:
            self.algorithm_layout.removeRow(2)

        self.configuration_widgets.clear()

        algorithm = self.algorithm_choice.currentText()

        if algorithm == "Hill Climbing":
            self.algorithm_layout.insertRow(2, "Version:", self.hill_version)
            configurations = {
                "Steepest Ascent": [
                    ("max_iterations", "Maximum iterations", "int", 100),
                ],
                "Sideways Move": [
                    ("max_sideways_moves", "Maximum sideways moves", "int", 100),
                    ("max_iterations", "Maximum iterations", "int", 100),
                ],
                "Random Restart": [
                    ("max_restarts", "Maximum restarts", "int", 10),
                    ("max_iterations", "Maximum iterations per restart", "int", 100),
                ],
                "Stochastic": [
                    ("max_iterations", "Maximum iterations", "int", 100),
                ],
            }[self.hill_version.currentText()]
        elif algorithm == "Simulated Annealing":
            configurations = [
                ("temperature", "Initial temperature", "float", 100.0),
                ("cooling_rate", "Cooling rate", "float", 0.95),
                ("max_iterations", "Maximum iterations", "int", 100),
            ]
        elif algorithm == "Genetic Algorithm":
            configurations = [
                ("population_count", "Initial population", "int", 100),
                ("iteration_count", "Iterations", "int", 100),
            ]
        else:
            configurations = []

        for name, label, value_type, default in configurations:
            if value_type == "float":
                field = QDoubleSpinBox(self)
                field.setDecimals(4)
                field.setRange(0.0001, 1.0 if name == "cooling_rate" else 1_000_000.0)
                field.setSingleStep(0.05 if name == "cooling_rate" else 1.0)
            else:
                field = QSpinBox(self)
                field.setRange(0, 1_000_000)
                field.setSingleStep(1)

            field.setValue(default)
            self.configuration_widgets[name] = field
            self.algorithm_layout.addRow(label + ":", field)

    def read_algorithm_configuration(self):
        return {
            name: field.value()
            for name, field in self.configuration_widgets.items()
        }

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
            field.setValue(int(float(value)))

    def read_packages(self):
        packages: dict[str, Package] = {}
        for row in range(self.package_table.rowCount()):
            values = []
            for column in range(8):
                item = self.package_table.item(row, column)
                if column == 6:     # fragile column, has checkbox instead of text
                    values.append(item is not None and item.checkState() == Qt.CheckState.Checked)
                else:
                    values.append(item.text().strip() if item is not None else "")

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
                width=self.truck_width.value(),
                length=self.truck_length.value(),
                height=self.truck_height.value(),
                max_capacity=self.max_capacity.value(),
            )

            self.btn_run.setEnabled(False)
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            QApplication.processEvents()

            initial_state = generateRandomState(truck, packages)
            objective_label = self.objective_choice.currentText()
            if objective_label == "Maximize score":
                objective_function = score
            elif objective_label == "Maximize packet count":
                objective_function = package_count
            else:
                raise ValueError(f"Unsupported objective: {objective_label}")

            initial_value = objective_function(truck, packages, initial_state)
            algorithm = self.algorithm_choice.currentText()
            configuration = self.read_algorithm_configuration()
            start_time = time.perf_counter()

            version = ""

            if algorithm == "Genetic Algorithm":
                result = genetic_algorithm(truck, packages, initial_state, configuration["population_count"], configuration["iteration_count"], objective_function)
            elif algorithm == "Simulated Annealing":
                result = simulated_annealing(truck, packages, initial_state, configuration["temperature"], configuration["cooling_rate"], configuration["max_iterations"], objective_function)
            elif algorithm == "Hill Climbing":
                version = self.hill_version.currentText()
                if version == "Steepest Ascent":
                    result = steepest_ascent(truck, packages, initial_state, configuration["max_iterations"], objective_function)
                elif version == "Sideways Move":
                    result = sideways_move(truck, packages, initial_state, configuration["max_sideways_moves"], configuration["max_iterations"], objective_function)
                elif version == "Random Restart":
                    result = random_restart(truck, packages, initial_state, configuration["max_restarts"], configuration["max_iterations"], objective_function)
                else:
                    result = stochastic(truck, packages, initial_state, max_iterations=configuration["max_iterations"], objective_function=objective_function)
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")

            elapsed = time.perf_counter() - start_time
            final_state = result["final_state"]
            final_value = result["final_value"]

            if algorithm == "Hill Climbing":
                algorithm_label = f"Algorithm used: Hill Climbing ({version})"
            else:
                algorithm_label = f"Algorithm used: {algorithm}"

            configuration_text = "Configuration: " + ", ".join(
                f"{name} = {value}" for name, value in configuration.items()
            )


            statistic = f" Execution time:\t{elapsed:.4f} seconds\n"
            statistic += f" Initial objective:\t{initial_value:.4f}\n"
            statistic += f" Final objective:\t{final_value:.4f}\n"

            if algorithm == "Hill Climbing":
                if version == "Steepest Ascent":
                    statistic += f" Iteration count:\t{result["iterations"]}\n"
                elif version == "Sideways Move":
                    statistic += f" Iteration count:\t{result["iterations"]}\n"
                    statistic += f" Sideways move count:\t{result["sideways_moves"]}\n"
                elif version == "Random Restart":
                    statistic += f" Restart count:\t{result["restarts"]}\n"
                    statistic += f" Iterations per restart:\t{result["iterations_per_restart"]}\n"
                elif version == "Stochastic":
                    statistic += f" Iteration count:\t{result["iterations"]}\n"
            elif algorithm == "Simulated Annealing":
                statistic += f" Stuck count:\t{result["stagnant_count"]}\n"
            elif algorithm == "Genetic Algorithm":
                statistic += f" Population count:\t{result["population_count"]}\n"
                statistic += f" Iteration count:\t{result["iterations"]}\n"

            self.result_objective_used.setText(f"Objective: {objective_label}")
            self.result_algorithm_used.setText(algorithm_label)
            self.result_configuration_used.setText(configuration_text)
            self.result_statistic.setText(statistic)

            self.initial_visualizer.set_state(truck, packages, initial_state, objective_function, objective_label)
            self.final_visualizer.set_state(truck, packages, final_state, objective_function, objective_label)

            self.clear_plotters()
            history = result["history"]
            iterations = [record["iteration"] for record in history]

            self.plotters = []
            if algorithm != "Genetic Algorithm":
                self.plotters.append(Plotter(iterations, [record["current_value"] for record in history], f"Current Objective by Iteration ({objective_label})", "Iteration", objective_label))
                if algorithm == "Simulated Annealing":
                    self.plotters.append(Plotter(iterations, [record["exp_delta_over_temp"] for record in history], f"e^(Delta({objective_label})/T) by Iteration", "Iteration", f"e^(Delta({objective_label})/T)"))
            else:
                self.plotters.append(Plotter(iterations, [record["best_value"] for record in history], f"Best Objective by Iteration ({objective_label})", "Iteration", objective_label))
                self.plotters.append(Plotter(iterations, [record["average_value"] for record in history], f"Average Objective by Iteration ({objective_label})", "Iteration", f"Average {objective_label}"))

            for plotter in self.plotters:
                self.plot_content_layout.addWidget(plotter)

            self.last_result = (
                f"{algorithm_label}\n"
                f"{configuration_text}\n"
                "Statistic:\n"
                f"{statistic}\n"
            )
        except Exception as error:
            QMessageBox.critical(self, "Execution Error", f"{type(error).__name__}: {error}")
        finally:
            QApplication.restoreOverrideCursor()
            self.btn_run.setEnabled(True)

    def reset_form(self):
        for field in (self.truck_length, self.truck_width, self.truck_height, self.max_capacity):
            field.clear()

        self.package_table.setRowCount(0)

        self.file_label.setText("No file has been inserted")

        self.result_algorithm_used.setText("Algorithm used:")
        self.result_configuration_used.setText("Configuration:")
        self.result_statistic.setText("")

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
            state_configs = ""
            if len(self.visualizers) == 2:
                state_configs += "Initial state configuration:"
                for item in [self.visualizers[0].details.item(i) for i in range(self.visualizers[0].details.count())]:
                    state_configs += " " + item.text() + "\n"
                state_configs += "Final state configuration:"
                for item in [self.visualizers[1].details.item(i) for i in range(self.visualizers[1].details.count())]:
                    state_configs += " " + item.text() + "\n"
            with open(path, "w", encoding="utf-8") as output_file:
                output_file.write(self.last_result + "\n" + state_configs)
