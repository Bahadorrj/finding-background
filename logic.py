import numpy as np
from scipy.interpolate import CubicSpline


def polynomial(x: np.ndarray, y: np.ndarray, degree: int) -> np.ndarray:
    coefficients = np.polyfit(x, y, degree)
    y_curve = np.polyval(coefficients, x)
    return y_curve


def improved_polynomial(peaks: np.ndarray, y: np.ndarray, degree: int) -> list:
    p = []
    for i in range(0, peaks.size - 1, 5):
        start, stop = peaks[i], peaks[i + 5]
        X = np.arange(start, stop, 1)
        Y = np.linspace(y[start], y[stop], X.size)
        poly = polynomial(X, Y, degree)
        p.append((X, poly))
    return p


def smoothen(x: np.ndarray, y: np.ndarray, size: int, level: float) -> tuple[np.ndarray, np.ndarray]:
    cs = CubicSpline(x, y)
    # Generate finer x values for smoother plot
    X = np.linspace(0, size, int(x.size / level))
    # Interpolate y values for the smoother plot
    Y = cs(X)
    return X, Y


def create_curve(peaks: np.ndarray, y: np.ndarray) -> np.ndarray:
    lspace = np.zeros(y.size, dtype=np.float64)
    for i in range(peaks.size - 1):
        start, stop = int(peaks[i]), int(peaks[i + 1])
        Y = np.linspace(y[start], y[stop], stop - start)
        pointer = 0
        for px in range(start, stop):
            lspace[px] = Y[pointer]
            pointer += 1
    return lspace
