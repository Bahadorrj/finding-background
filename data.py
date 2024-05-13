import re
from typing import Optional, Union

import numpy as np
from logic import smoothen, regression_curve
from scipy.signal import find_peaks


class Data:
    def __init__(self, filepath: str, condition_number: int):
        self._intensities = get_counts(filepath, condition_number)
        self._size = self._intensities.size
        self._pixels = np.arange(0, self._size, 1)
        self._smoothness = 1
        self._pixels_s, self._intensities_s = smoothen(
            self._pixels, self._intensities, self._size, self._smoothness
        )
        self._peaks_attributes = {
            "height": None,
            "threshold": None,
            "distance": None,
            "width": None
        }
        self._peaks, _ = find_peaks(-self._intensities_s, **self._peaks_attributes)
        self._regression_curve = regression_curve(self._peaks, self._intensities_s)
        self._optimal_curve = (self._intensities_s - self._regression_curve).clip(min=0)
        self._pixels_curve_s, self._optimal_curve_s = smoothen(
            self._pixels_s, self._optimal_curve, self._size, self._smoothness
        )

    def update(self, property_name: str, property_value: Optional[Union[float, str]]) -> int:
        if hasattr(self, f"_{property_name}"):
            setattr(self, f"_{property_name}", property_value)
        elif self._interpret_string(property_value) != -1:
            if property_name in self._peaks_attributes:
                if self._interpret_string(property_value) == 0:
                    self._peaks_attributes[property_name] = None
                else:
                    self._peaks_attributes[property_name] = float(property_value)
            else:
                print(
                    f"Property '{property_name}' not found."
                )
                return -1
        return self._calculate()

    def _interpret_string(self, string: str) -> int:
        if string == "":
            return 0
        elif re.match(r'^-?\d+$', string) or re.match(r'^-?\d+(\.\d+)?$', string):
            return 1
        elif isinstance(string, tuple):
            return 2
        else:
            return -1

    def _calculate(self) -> int:
        self._pixels_s, self._intensities_s = smoothen(
            self._pixels, self._intensities, self._size, self._smoothness
        )
        try:
            self._peaks, _ = find_peaks(-self._intensities_s, **self._peaks_attributes)
            self._regression_curve = regression_curve(self._peaks, self._intensities_s)
            self._optimal_curve = (self._intensities_s - self._regression_curve).clip(min=0)
            self._pixels_curve_s, self._optimal_curve_s = smoothen(
                self._pixels_s, self._optimal_curve, self._size, self._smoothness
            )
            return 1
        except Exception as e:
            print(e)
            return -1

    def curves(self) -> tuple:
        curves = (
            (self._pixels, self._intensities, "Intensities"),
            (self._pixels_s, self._intensities_s, f"Smoothed Intensities: level {self._smoothness}"),
            (self._pixels_s[self._peaks], self._intensities_s[self._peaks], f"Maxima: {self._peaks_attributes}"),
            (self._pixels_s, self._regression_curve, "Regression Curve"),
            (self._pixels_s, self._optimal_curve, "Optimal Intensities"),
            (self._pixels_curve_s, self._optimal_curve_s, "Smoothed Optimal"),
        )
        return curves


def get_counts(filepath: str, condition_number: int) -> np.ndarray:
    flag = False
    with open(filepath, "r") as f:
        line = f.readline()  # read line
        counts = np.zeros(2048, dtype=np.int32)
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


def write_to_file(filepath: str, counts_list: np.ndarray) -> None:
    with open(filepath, "w") as f:
        for count in counts_list:
            f.write(str(count) + "\n")
