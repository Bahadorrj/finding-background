import numpy as np
from logic import smoothen, regression_curve
from scipy.signal import find_peaks


class Data:
    def __init__(self, filepath: str, condition_number: int, smoothness: float = 4):
        self.intensities = get_counts(filepath, condition_number)
        self.size = self.intensities.size
        self.smoothness = smoothness
        self.pixels = np.arange(0, self.size, 1)
        self.pixels_s, self.intensities_s = smoothen(self.pixels, self.intensities, self.size, smoothness)
        self.peaks_attributes = {'height': None, 'width': None, 'threshold': None, 'distance': None}
        self.peaks, _ = find_peaks(-self.intensities_s, **self.peaks_attributes)
        self.regression_curve = regression_curve(self.peaks, self.intensities_s)
        self.optimal_curve = (self.intensities_s - self.regression_curve).clip(min=0)
        self.pixels_curve_s, self.optimal_curve_s = smoothen(self.pixels_s, self.optimal_curve, self.size, smoothness)

    def smoothness_changed(self, level: float):
        self.smoothness = level
        self.calculate()

    def peaks_attributes_changed(self):
        self.calculate()

    def calculate(self):
        self.pixels_s, self.intensities_s = smoothen(self.pixels, self.intensities, self.size, self.smoothness)
        self.peaks, _ = find_peaks(-self.intensities_s, **self.peaks_attributes)
        self.regression_curve = regression_curve(self.peaks, self.intensities_s)
        self.optimal_curve = (self.intensities_s - self.regression_curve).clip(min=0)
        self.pixels_curve_s, self.optimal_curve_s = smoothen(self.pixels_s, self.optimal_curve, self.size,
                                                             self.smoothness)

    def curves(self) -> tuple:
        curves = (
            (self.pixels, self.intensities, 'Intensities'),
            (self.pixels_s, self.intensities_s, 'Smoothed Intensities'),
            (self.pixels_s[self.peaks], self.intensities_s[self.peaks], 'Maxima'),
            (self.pixels_s, self.regression_curve, 'Regression Curve'),
            (self.pixels_s, self.optimal_curve, 'Optimal Intensities'),
            (self.pixels_curve_s, self.optimal_curve_s, 'Smoothed Optimal')
        )
        return curves


def get_counts(filepath: str, condition_number: int) -> np.ndarray:
    flag = False
    with open(filepath, 'r') as f:
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
    with open(filepath, 'w') as f:
        for count in counts_list:
            f.write(str(count) + "\n")
