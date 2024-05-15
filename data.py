import re
from typing import Optional, Union

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.signal import find_peaks


class Data:
    def __init__(self, filepath: str, condition_number: int):
        self.filepath = filepath
        self.condition_number = condition_number
        self.intensities = self._get_counts(filepath, condition_number)
        self.size = self.intensities.size
        self.pixels = np.arange(0, self.size, 1)
        self.smoothness = 1
        self.peaks_attributes = {
            "height": None,
            "threshold": None,
            "distance": None,
            "width": None
        }
        self._calculate()

    def update(self, property_name: str, property_value: Optional[Union[float, str]]) -> int:
        if hasattr(self, property_name):
            setattr(self, property_name, property_value)
        elif self._interpret_string(property_value) != -1:
            if property_name in self.peaks_attributes:
                if self._interpret_string(property_value) == 0:
                    self.peaks_attributes[property_name] = None
                else:
                    self.peaks_attributes[property_name] = float(
                        property_value)
            else:
                print(
                    f"Property '{property_name}' not found."
                )
                return -1
        return self._calculate()

    def _calculate(self) -> int:
        try:
            self.pixels_s, self.intensities_s = self.smoothen(
                self.pixels, self.intensities, self.size, self.smoothness
            )
            self.peaks, _ = find_peaks(
                -self.intensities_s, **self.peaks_attributes
            )
            self.regression_curve = np.interp(
                self.pixels, self.pixels_s[self.peaks], self.intensities_s[self.peaks]
            )
            self.optimal_curve = (self.intensities - self.regression_curve).clip(min=0)
            return 1
        except Exception as e:
            print(e)
            return -1

    def curves(self) -> tuple:
        curves = (
            (self.pixels, self.intensities),
            (self.pixels_s, self.intensities_s),
            (self.pixels, self.regression_curve),
            (self.pixels, self.optimal_curve)
        )
        return curves

    def save(self, filename: str, condition: int) -> None:
        with open(filename, "w") as f:
            f.write(f"Condition {condition}\n")
            for attr, val in self.peaks_attributes.items():
                f.write(attr + ": " + str(val) + "\n")
            for count in self.optimal_curve:
                f.write(str(count) + "\n")

    @staticmethod
    def smoothen(x: np.ndarray, y: np.ndarray, size: int, level: float) -> tuple[np.ndarray, np.ndarray]:
        cs = CubicSpline(x, y)
        # Generate finer x values for smoother plot
        X = np.linspace(0, size, int(x.size / level))
        # Interpolate y values for the smoother plot
        Y = cs(X)
        return X, Y

    @staticmethod
    def _interpret_string(string: str) -> int:
        if string == "":
            return 0
        elif re.match(r'^-?\d+$', string) or re.match(r'^-?\d+(\.\d+)?$', string):
            return 1
        elif isinstance(string, tuple):
            return 2
        else:
            return -1

    @staticmethod
    def _get_counts(filepath: str, condition_number: int) -> np.ndarray:
        flag = False
        with open(filepath, "r") as f:
            line = f.readline()  # read line
            counts = np.zeros(2048, dtype=np.uint32)
            index = 0
            while line:
                try:
                    count = int(line.strip())
                    if index < 2048:
                        counts[index] = count
                        index += 1
                        if index == 2048:
                            index = 0
                            if flag:
                                return counts
                except ValueError:
                    if line.strip() == f"Condition {condition_number}":
                        flag = True
                    pass
                line = f.readline()
