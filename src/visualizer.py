
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget
import pyvista as pv
from pyvistaqt import QtInteractor

from src.model import Package, Truck, State
from src.geometry import dimensions, overlaps, supports, outOfBounds
from src.objective import score


class StateVisualizer(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.truck = None
        self.packages = {}
        self.state = None
        self.base_title = title

        layout = QVBoxLayout(self)
        self.title_label = QLabel(title)
        self.setWindowTitle(title)
        self.title_label.setStyleSheet("font-size: 10px; font-weight: bold;")
        layout.addWidget(self.title_label)

        hLayout = QHBoxLayout()
        self.plotter = QtInteractor(self)
        hLayout.addWidget(self.plotter.interactor, stretch=3)
        self.details = QListWidget()
        hLayout.addWidget(self.details, stretch=1)
        layout.addLayout(hLayout)

    def set_state(self, truck: Truck, packages, state: State, objective_function=score, objective_label="Maksimalkan score"):
        self.truck = truck
        self.packages = packages
        self.state = state
        self.objective_function = objective_function
        self.render_state()

    def clear_state(self):
        self.truck = None
        self.packages = {}
        self.state = None
        self.plotter.clear()
        self.details.clear()
        self.title_label.setText(self.base_title)

    def render_state(self):
        if self.truck is None or self.state is None:
            return
        self.plotter.clear()
        self.details.clear()

        truck = self.truck

        # Truck container boundary.
        container = pv.Cube(
            bounds=(
                0, truck.width,
                0, truck.length,
                0, truck.height,
            )
        )

        self.plotter.add_mesh(
            container,
            style="wireframe",
            color="black",
            line_width=2,
        )

        self.plotter.add_axes()
        self.plotter.show_grid(
            xtitle="Width (X)",
            ytitle="Length (Y)",
            ztitle="Height (Z)",
            font_size=8,
            n_xlabels=truck.width + 1,
            n_ylabels=truck.length + 1,
            n_zlabels=truck.height + 1,
            fmt="%.0f",
        )

        colors = [
             "#ff8000", "#ffbf00", "#bfff00", "#00ff00",
             "#00ffbf", "#00bfff", "#0080ff", "#0000ff", "#8000ff", 
             "#bf00ff", "#ff00ff", "#ff80ff", "#ffb0ff", "#ffffff", 
             "#888888", "#444444", "#000000"
        ]

        placed_count = 0
        outside_count = 0

        for index, (package_id, package) in enumerate(self.packages.items()):
            placement = self.state.placements.get(package_id)

            if placement is None:
                outside_count += 1
                self.details.addItem(
                    f"{package_id}: NOT PLACED | "
                    f"Dimensions: {package.width} x {package.length} x {package.height}"
                )
                continue

            placed_count += 1
            
            size = dimensions(package, placement.orientation)

            x, y, z = placement.x, placement.y, placement.z

            cube = pv.Cube(
                bounds=(
                    x, x + size[0],
                    y, y + size[1],
                    z, z + size[2],
                )
            )

            is_valid = outOfBounds(placement, size, self.truck) == 0
            has_support = placement.z == 0

            for other_package_id, other_placement in self.state.placements.items():
                if other_placement is None or other_package_id == package_id:
                    continue

                other_package = self.packages[other_package_id]
                other_size = dimensions(other_package, other_placement.orientation)

                if overlaps(placement, size, other_placement, other_size):
                    is_valid = False

                if supports(other_placement, other_size, placement, size):
                    has_support = True

                    if other_package.fragile:
                        is_valid = False

            if not has_support:
                is_valid = False

            color = colors[index % len(colors)]

            self.plotter.add_mesh(
                cube,
                color=color if is_valid else "#FF0000",
                opacity=0.85,
                show_edges=True,
                edge_color="black",
                line_width=1,
            )

            center = (
                x + size[0] / 2,
                y + size[1] / 2,
                z + size[2] / 2,
            )

            self.plotter.add_point_labels(
                [center],
                [package_id],
                font_size=10,
                point_size=0,
                shape=None,
                always_visible=True,
            )

            if is_valid:
                status = "INSIDE"
            else:
                status = "INSIDE (INVALID)"

            self.details.addItem(
                f"{package_id}: {status} | "
                f"Position: ({x}, {y}, {z}) | "
                f"Oriented dimensions: "
                f"{size[0]} x {size[1]} x {size[2]} | "
                f"Orientation: {placement.orientation.name}"
            )

        state_value = self.objective_function(self.truck, self.packages, self.state)

        self.title_label.setText(
            f"{self.windowTitle()} | "
            f"Value: {state_value:.2f} | "
            f"Inside: {placed_count} | "
            f"Outside: {outside_count}"
        )

        self.plotter.view_isometric()
        self.plotter.reset_camera()
        self.plotter.render()

    def closeEvent(self, event):
        self.plotter.close()
        super().closeEvent(event)
