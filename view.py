import os
import sys
from functools import partial

import matplotlib
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QApplication,
                             QLineEdit,
                             QSizePolicy,
                             QHBoxLayout,
                             QDoubleSpinBox,
                             QRadioButton,
                             QLabel,
                             QSpacerItem,
                             QGroupBox,
                             QWidget,
                             QStatusBar,
                             QGridLayout,
                             QVBoxLayout,
                             QFileDialog,
                             QMainWindow, QDialog, QComboBox, QPushButton)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from numpy import ndarray

from data import Data

matplotlib.use('QtAgg')

HIDDEN = 0
SHOWN = 1


class Dialog(QDialog):
    conditionSelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Condition')
        verticalLayout = QVBoxLayout(self)
        gridLayout = QGridLayout()
        label = QLabel(self)
        label.setText("Select the condition you want its background to be removed:")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gridLayout.addWidget(label, 0, 0, 1, 2)
        self._comboBox = QComboBox(self)
        self._comboBox.currentTextChanged.connect(self._comboBoxChanged)
        gridLayout.addWidget(self._comboBox, 1, 1, 1, 1)
        label = QLabel(self)
        label.setText("Condition")
        gridLayout.addWidget(label, 1, 0, 1, 1)
        verticalLayout.addLayout(gridLayout)
        horizontalLayout = QHBoxLayout()
        pushButton = QPushButton(self)
        pushButton.setText("Ok")
        pushButton.clicked.connect(self._conditionSelected)
        horizontalLayout.addWidget(pushButton)
        pushButton = QPushButton(self)
        pushButton.setText("Cancel")
        pushButton.clicked.connect(self.close)
        horizontalLayout.addWidget(pushButton)
        verticalLayout.addLayout(horizontalLayout)

        self._conditionNumber = None

    def setComboBoxValues(self, values: list) -> None:
        self._comboBox.addItems(values)

    def _comboBoxChanged(self, text: str):
        self._conditionNumber = text

    def _conditionSelected(self) -> None:
        self.conditionSelected.emit(self._conditionNumber)
        self.close()


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


# noinspection PyUnresolvedReferences
class Window(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._condition = None
        self._data = None
        self._plotsLegend = ["Intensities", "Smoothed Intensities", "Regression Curve", "Optimal Intensities"]
        self._plotState = [HIDDEN for _ in range(len(self._plotsLegend))]
        self._inputs = []

        self.resize(1200, 800)
        self.setWindowTitle('Remove Background')

        mainLayout = QVBoxLayout()
        self._gridLayout = QGridLayout()
        self._radioButtonMap = dict()
        self._createSelectorBox()
        self._createAttributeBox()

        self._canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self._plt = self._canvas.axes
        self._gridLayout.addWidget(self._canvas, 0, 1, 2, 3)

        self._statusbar = QStatusBar(self)
        self.setStatusBar(self._statusbar)

        menuBar = self.menuBar()
        openMenu = menuBar.addMenu('&File')
        openAction = openMenu.addAction('Open')
        openAction.triggered.connect(self._getDataDialog)
        saveAction = openMenu.addAction('Save')
        saveAction.triggered.connect(self._saveDataDialog)
        menuBar.addMenu(openMenu)

        self._toolbar = NavigationToolbar(self._canvas, self)
        mainLayout.addWidget(self._toolbar)

        mainLayout.addLayout(self._gridLayout)

        centralWidget = QWidget(self)
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)

    def _createSelectorBox(self):
        selectorBox = QGroupBox()
        verticalLayout = QVBoxLayout(selectorBox)
        for buttonName in self._plotsLegend:
            button = self._createRadioButton(buttonName)
            self._radioButtonMap[buttonName] = button
            self._inputs.append(button)
            verticalLayout.addWidget(button)
        self._gridLayout.addWidget(selectorBox, 0, 0, 1, 1)

    def _createAttributeBox(self):
        attributeBox = QGroupBox()

        verticalLayout = QVBoxLayout(attributeBox)

        label = QLabel()
        label.setText("Smoothing:")
        verticalLayout.addWidget(label)

        verticalLayout.addLayout(self._createSpinBoxLayout())

        spacerItem = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        verticalLayout.addItem(spacerItem)

        label = QLabel()
        label.setText("Peaks:")
        verticalLayout.addWidget(label)

        for label in ["Height", "Threshold", "Distance", "Width"]:
            verticalLayout.addLayout(self._createTextInputLayout(label))

        self._gridLayout.addWidget(attributeBox, 1, 0, 1, 1)

    def _createRadioButton(self, buttonName: str) -> QRadioButton:
        radioButton = QRadioButton()
        radioButton.setText(buttonName)
        radioButton.setChecked(False)
        radioButton.setAutoExclusive(False)
        radioButton.setDisabled(True)
        radioButton.toggled.connect(partial(self._buttonToggled, radioButton))
        self._inputs.append(radioButton)
        return radioButton

    def _createSpinBoxLayout(self) -> QHBoxLayout:
        horizontalLayout = QHBoxLayout()
        label = QLabel()
        label.setText("Smooth Level")
        horizontalLayout.addWidget(label)
        doubleSpinBox = QDoubleSpinBox()
        doubleSpinBox.setDecimals(2)
        doubleSpinBox.setMinimum(1.0)
        doubleSpinBox.setMaximum(20.0)
        doubleSpinBox.setSingleStep(0.01)
        doubleSpinBox.setValue(1.0)
        doubleSpinBox.setDisabled(True)
        doubleSpinBox.valueChanged.connect(self._updateSmoothness)
        horizontalLayout.addWidget(doubleSpinBox)
        self._inputs.append(doubleSpinBox)
        return horizontalLayout

    def _createTextInputLayout(self, label: str) -> QHBoxLayout:
        horizontalLayout = QHBoxLayout()
        lbl = QLabel()
        lbl.setText(label)
        horizontalLayout.addWidget(lbl)
        lineEdit = QLineEdit()
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(lineEdit.sizePolicy().hasHeightForWidth())
        lineEdit.setSizePolicy(sizePolicy)
        lineEdit.setDisabled(True)
        lineEdit.editingFinished.connect(partial(self._updateData, lineEdit, label.lower()))
        horizontalLayout.addWidget(lineEdit)
        self._inputs.append(lineEdit)
        return horizontalLayout

    def plot(self, x: ndarray, y: ndarray, *args, **kwargs) -> None:
        self._plt.plot(x, y, *args, **kwargs)

    def clearPlot(self) -> None:
        self._plt.cla()

    def legend(self) -> None:
        self._plt.legend()

    @pyqtSlot()
    def _getDataDialog(self) -> None:
        filename = self._getFileName(QFileDialog.AcceptMode.AcceptOpen)
        self._getCondition(filename)

    def _getFileName(self, mode: QFileDialog.AcceptMode) -> str:
        if mode == QFileDialog.AcceptMode.AcceptOpen:
            filename, _ = QFileDialog.getOpenFileName(
                self, caption='Open File', filter='Text files(*.txt)', directory=os.getcwd()
            )
            return filename
        elif mode == QFileDialog.AcceptMode.AcceptSave:
            filename, _ = QFileDialog.getSaveFileName(
                self, caption='Open File', filter='Text files(*.txt)', directory=os.getcwd()
            )
            return filename
        return ""

    def _getCondition(self, filename: str) -> None:
        dialog = Dialog(self)
        dialog.setComboBoxValues(self._getConditionsOfFile(filename))
        dialog.conditionSelected.connect(partial(self.addData, filename))
        dialog.exec()

    @staticmethod
    def _getConditionsOfFile(filename: str) -> list:
        conditions = []
        with open(filename, "r") as f:
            line = f.readline()
            while line:
                if "condition" in line.lower():
                    conditions.append(line.strip().split(' ')[-1])
                line = f.readline()
        conditions.sort()
        return conditions

    @pyqtSlot(str)
    def addData(self, filename: str, condition: str) -> None:
        self._condition = condition
        self._data = Data(filename, int(condition))
        self._enableInputs()
        self._checkAllButtons()
        self._plotData()

    def _enableInputs(self) -> None:
        for widget in self._inputs:
            widget.setDisabled(False)

    def _checkAllButtons(self) -> None:
        for button in self._radioButtonMap.values():
            button.setChecked(True)

    def _plotData(self) -> None:
        self.clearPlot()
        if SHOWN in self._plotState:
            for index, curve in enumerate(self._data.curves()):
                x, y = curve
                label = self._plotsLegend[index]
                if self._plotState[index] == SHOWN:
                    self.plot(x, y, label=label)
            self.legend()
        self._canvas.draw()

    @pyqtSlot(QRadioButton)
    def _buttonToggled(self, button: QRadioButton, checked: bool) -> None:
        if self._data is not None:
            buttonName = button.text()
            index = self._plotsLegend.index(buttonName)
            self._plotState[index] = int(checked)
            if index == 4:
                self._smoothButton.setCheckable(checked)
            self._plotData()

    @pyqtSlot(float)
    def _updateSmoothness(self, level: float) -> None:
        if self._data is not None:
            success = self._data.update('smoothness', level)
            if success:
                self._plotData()

    @pyqtSlot()
    def _updateData(self, lineEdit: QLineEdit, propertyName: str) -> None:
        if self._data is not None:
            propertyValue = lineEdit.text()
            success = self._data.update(propertyName, propertyValue)
            if success:
                self._plotData()
            else:
                lineEdit.setText("Not a valid")
                lineEdit.selectAll()

    def _saveDataDialog(self) -> None:
        filename = self._getFileName(QFileDialog.AcceptMode.AcceptSave)
        self.saveData(filename)

    def saveData(self, filename: str) -> None:
        self._data.save(filename, self._condition)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("CSAN.ico"))
    ui = Window()
    ui.show()
    sys.exit(app.exec())
