import numpy as np
from sklearn.linear_model import LinearRegression

class DataFilter:
    def regression(self, t_t_h: list) -> tuple:
        line = self.linear(t_t_h)
        return 1, 2, 3

    def linear(self, t_t_h: list) -> dict:
        x_list = []
        y_list = []
        for time in t_t_h:
            x_list.append(time['time_ms'])
            y_list.append(time['temperature'])
        x = np.array(x_list).reshape((-1, 1))
        y = np.array(y_list)
        model = LinearRegression().fit(x, y)
        r_sq = model.score(x, y)
        intercept = model.intercept_
        slope = model.coef_[0]
        return {'slope': slope, 'intercept': intercept, 'R_sq': r_sq}