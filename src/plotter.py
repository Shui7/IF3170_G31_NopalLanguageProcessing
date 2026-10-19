from PySide6.QtWidgets import QVBoxLayout, QSizePolicy, QWidget

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class Plotter(QWidget):
    def __init__(self, listValueX, listValueY, title, labelX, labelY, parent=None):
        super().__init__(parent)

        self.listValueX = listValueX
        self.listValueY = listValueY
        self.labelX = labelX
        self.labelY = labelY

        self.figure = Figure(layout="constrained")
        self.canvas = FigureCanvasQTAgg(self.figure)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

        self.setFixedHeight(200)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.setWindowTitle(title)
        self.render_state(title)

    def render_state(self, title: str):
        self.figure.clear()
        axis = self.figure.add_subplot(111)

        point_count = min(len(self.listValueX), len(self.listValueY))
        x_values = self.listValueX[:point_count]
        y_values = self.listValueY[:point_count]

        axis.set_title(title, fontsize=10)
        axis.set_xlabel(self.labelX, fontsize=9)
        axis.set_ylabel(self.labelY, fontsize=9)
        axis.tick_params(labelsize=8)
        axis.grid(True, alpha=0.3)

        if point_count:
            axis.plot(x_values, y_values, color="#4C9BE8", marker="o", markersize=3, linewidth=1.5)
        else:
            axis.text(0.5, 0.5, "No data available", ha="center", va="center", transform=axis.transAxes)

        self.canvas.draw_idle()