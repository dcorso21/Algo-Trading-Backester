
"""
Demonstrate creation of a custom graphic (a candlestick plot)
"""
# import initExample ## Add path to library (just for examples; you do not need this)

from local_functions.main import global_vars as gl


# Create a subclass of GraphicsObject.
# The only required methods are paint() and boundingRect()
# (see QGraphicsItem documentation)


class CandlestickItem(gl.pg.GraphicsObject):
    def __init__(self, data):
        gl.pg.GraphicsObject.__init__(self)
        self.data = data  # data must have fields: time, open, close, min, max
        self.generatePicture()

    def generatePicture(self):
        # pre-computing a QPicture object allows paint() to run much more quickly,
        # rather than re-drawing the shapes every time.
        self.picture = gl.QtGui.QPicture()
        p = gl.QtGui.QPainter(self.picture)
        p.setPen(gl.pg.mkPen('w'))
        # w = (self.data[1][0] - self.data[0][0]) / 3.
        w = .33
        for (t, o, h, l, c) in zip(range(len(self.data)), self.data.open,
                                   self.data.high, self.data.low,
                                   self.data.close):
            p.drawLine(gl.QtCore.QPointF(t, l), gl.QtCore.QPointF(t, h))
            if o > c:
                p.setBrush(gl.pg.mkBrush('r'))
            else:
                p.setBrush(gl.pg.mkBrush('g'))
            p.drawRect(gl.QtCore.QRectF(t-w, o, w*2, c-o))

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        # boundingRect _must_ indicate the entire area that will be drawn on
        # or else we will get artifacts and possibly crashing.
        # (in this case, QPicture does all the work of computing the bouning rect for us)
        return gl.QtCore.QRectF(self.picture.boundingRect())


def chart_candles():

    df = gl.current_frame

    # if len(df) == 0:
    #     return

    item = CandlestickItem(df)

    win = gl.pg.GraphicsWindow(title="Plot auto-range examples")
    win.resize(800, 600)
    # win.setWindowTitle('pyqtgraph example: PlotAutoRange')
    p2 = win.addPlot(title="Auto Pan Only")
    p2.setAutoPan(y=True)
    plt = p2.plot(item)
    # plt.addItem(item)
    plt.setWindowTitle('pyqtgraph example: customGraphicsItem')
    # plt.enableAutoRange('y', 0.95)

    # Start Qt event loop unless running in interactive mode or using pyside.
    # if __name__ == '__main__':
    # import sys
    # if (sys.flags.interactive != 1) or not hasattr(gl.QtCore, 'PYQT_VERSION'):
    gl.QtGui.QApplication.instance().exec_()
