import pandas as pd
from plotnine import *

from paths import PLOT_STATISTICS_OUTPUT


class Plotter:
    """
    Think of it as the plotter engine
    """

    def __init__(self, width=6, height=4, dpi=300):
        self.width = width
        self.height = height
        self.dpi = dpi
        self.theme = theme_classic()

    def plot_2D_line(self, df, x, y, title, filename):
        p = (
            ggplot(data=df, mapping=aes(x=x, y=y))
            + geom_line()
            + labs(title=title)
            + self.theme
        )
        p.save(filename, width=self.width, height=self.height, dpi=self.dpi)


class ExperimentPlotter:
    """
    This class is domain specific (combines the engine plotter
    with my particular problem using domain functions like mean_travel_time)
    """

    def __init__(self):
        self.plotter = Plotter()

    def statistics_output(self, results):
        df = pd.DataFrame(results)
        keys = list(df.columns[1:])
        x = df["episode"]
        for key in keys:
            y = df[key]
            title = f"{key} over episodes"
            filename = PLOT_STATISTICS_OUTPUT
            filename = filename.with_name(f"{key}_{filename.name}")

            self.plotter.plot_2D_line(df=df, x=x, y=y, title=title, filename=filename)
