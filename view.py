import sys

import matplotlib
import numpy as np
from PyQt6 import QtWidgets, QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from functools import partial

from data import Data

matplotlib.use('QtAgg')

HIDDEN = 0
SHOWN = 1


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class Window(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(1200, 800)
        self.setWindowTitle('Remove Background')

        mainLayout = QtWidgets.QVBoxLayout()
        self._gridLayout = QtWidgets.QGridLayout()
        self._radioButtonMap = dict()
        self._createSelectorBox()
        self._createAttributeBox()

        self._canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self._plt = self._canvas.axes
        self._gridLayout.addWidget(self._canvas, 0, 1, 2, 3)

        self._menubar = QtWidgets.QMenuBar(self)
        self.setMenuBar(self._menubar)

        self._statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self._statusbar)

        toolbar = NavigationToolbar(self._canvas, self)

        mainLayout.addWidget(toolbar)
        mainLayout.addLayout(self._gridLayout)

        self._data = Data('text samples/Au.txt', 7)
        self._plotState = [SHOWN for i in range(len(self._data.curves()))]
        # smoothed background is hidden at program init
        self._plotState[-1] = HIDDEN
        self._plotData()

        centralWidget = QtWidgets.QWidget(self)
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)

    def _createSelectorBox(self):
        selectorBox = QtWidgets.QGroupBox()
        verticalLayout = QtWidgets.QVBoxLayout(selectorBox)
        for i, buttonName in enumerate(
                ['Intensities', 'Smoothed Intensities', 'Maxima', 'Regression Curve', 'Removed Background']):
            button = self._createRadioButton(buttonName)
            button.toggled.connect(partial(self._buttonToggled, i))
            verticalLayout.addWidget(button)
        self._gridLayout.addWidget(selectorBox, 0, 0, 1, 1)

    def _createAttributeBox(self):
        attributeBox = QtWidgets.QGroupBox()

        verticalLayout = QtWidgets.QVBoxLayout(attributeBox)

        label = QtWidgets.QLabel()
        label.setText("Smoothing:")
        verticalLayout.addWidget(label)

        verticalLayout.addLayout(self._createSpinBoxLayout())

        self._smoothButton = QtWidgets.QRadioButton()
        self._smoothButton.setText("Smooth Background")
        self._smoothButton.toggled.connect(self._smoothOptimalCurve)
        verticalLayout.addWidget(self._smoothButton)

        spacerItem = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding
        )
        verticalLayout.addItem(spacerItem)

        label = QtWidgets.QLabel()
        label.setText("Peaks:")
        verticalLayout.addWidget(label)

        for label in ["Height", "Threshold", "Distance", "Width"]:
            verticalLayout.addLayout(self._createTextInputLayout(label))

        self._gridLayout.addWidget(attributeBox, 1, 0, 1, 1)

    def plot(self, x: np.ndarray, y: np.ndarray, *args, **kwargs) -> None:
        self._plt.plot(x, y, *args, **kwargs)

    def clearPlot(self) -> None:
        self._plt.cla()

    def legend(self):
        self._plt.legend()

    def _plotData(self):
        self.clearPlot()
        if SHOWN in self._plotState:
            for index, curve in enumerate(self._data.curves()):
                x, y, label = curve
                if self._plotState[index] == SHOWN:
                    self.plot(x, y, label=label)
            self.legend()
        self._canvas.draw()

    @staticmethod
    def _createRadioButton(text: str) -> QtWidgets.QRadioButton:
        radioButton = QtWidgets.QRadioButton()
        radioButton.setText(text)
        radioButton.setChecked(True)
        radioButton.setAutoExclusive(False)
        return radioButton

    def _createSpinBoxLayout(self) -> QtWidgets.QHBoxLayout:
        horizontalLayout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel()
        label.setText("Smooth Level")
        horizontalLayout.addWidget(label)
        doubleSpinBox = QtWidgets.QDoubleSpinBox()
        doubleSpinBox.setDecimals(2)
        doubleSpinBox.setMinimum(1.0)
        doubleSpinBox.setMaximum(20.0)
        doubleSpinBox.setSingleStep(0.01)
        doubleSpinBox.setValue(1.0)
        doubleSpinBox.valueChanged.connect(self._updateSmoothness)
        horizontalLayout.addWidget(doubleSpinBox)
        return horizontalLayout

    def _createTextInputLayout(self, label: str) -> QtWidgets.QHBoxLayout:
        horizontalLayout = QtWidgets.QHBoxLayout()
        lbl = QtWidgets.QLabel()
        lbl.setText(label)
        horizontalLayout.addWidget(lbl)
        lineEdit = QtWidgets.QLineEdit()
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(lineEdit.sizePolicy().hasHeightForWidth())
        lineEdit.setSizePolicy(sizePolicy)
        lineEdit.editingFinished.connect(partial(self._updateData, label.lower(), lineEdit))
        horizontalLayout.addWidget(lineEdit)
        return horizontalLayout

    def _buttonToggled(self, index: int, checked: bool) -> None:
        self._plotState[index] = int(checked)
        if index == 4:
            self._smoothButton.setCheckable(checked)
        self._plotData()

    def _updateSmoothness(self, level: float):
        success = self._data.update('smoothness', level)
        if success:
            self._plotData()

    def _smoothOptimalCurve(self, checked: bool) -> None:
        self._plotState[-1] = checked
        self._plotState[-2] = not checked
        self._plotData()

    def _updateData(self, propertyName: str, lineEdit: QtWidgets.QLineEdit):
        propertyValue = lineEdit.text()
        success = self._data.update(propertyName, propertyValue)
        if success:
            self._plotData()
        else:
            lineEdit.setText("Not a valid")
            lineEdit.selectAll()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon("icon.png"))
    ui = Window()
    ui.show()
    sys.exit(app.exec())
