
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
    import time
    while len(gl.current_frame) == 0:
        time.sleep(.1)

    df = gl.current_frame
    item = CandlestickItem(df)

    plt = gl.pg.plot()
    plt.addItem(item)
    plt.setWindowTitle('Algo Charts')

    vb = plt.getViewBox()
    vb.setYRange(df.low.min(), df.high.max(), padding=.05)

    gl.QtGui.QApplication.instance().exec_()
    return


if __name__ == "__main__":
    chart_candles()
