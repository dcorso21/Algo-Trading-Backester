# %%
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys


from local_functions.main import global_vars as gl
from local_functions.main import batch_testing as batch
from local_functions.plotting.candles import CandlestickItem



import pandas as pd

frame = {
    'open': [1, 2, 3],
    'high': [4, 5, 6],
    'low': [.5, 1, 2],
    'close': [2, 3, 4],
}

sample = pd.DataFrame(frame)


def get_plot():
    if (len(gl.current_frame) == 0) or (type(gl.current_frame) == str):
        df = sample
    else:
        df = gl.current_frame
    
    plt = gl.pg.plot()
    plt.addItem(CandlestickItem(df))
    plt.setWindowTitle('Algo Charts')
    vb = plt.getViewBox()
    vb.setYRange(df.low.min(), df.high.max(), padding=.05)
    return plt




class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        plot = get_plot()
        self.setCentralWidget(plot)

        self.timer = QTimer()
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

        batch.batch_test(stop_at=1)

    def update_plot_data(self):
        plot = get_plot()
        self.setCentralWidget(plot)


app = QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec_()


# %%
