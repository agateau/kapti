from PyQt4.QtGui import QWidget, QProgressBar, QVBoxLayout


class ProgressView(QWidget):
    def __init__(self, parent=None):
        super(ProgressView, self).__init__(parent)

        self._progressBar = QProgressBar()

        layout = QVBoxLayout(self)
        layout.addWidget(self._progressBar)

    def setRunner(self, runner):
        self.show()
        runner.progress.connect(self._showProgress)
        runner.done.connect(self.hide)

    def _showProgress(self, dct):
        step = dct['step']
        if step == 'install.progress':
            self._progressBar.setMaximum(100)
            self._progressBar.setValue(dct['percent'])
            self._progressBar.setFormat('%p%')
        elif step == 'acquire.fetch':
            self._progressBar.setMaximum(dct['total_bytes'])
            self._progressBar.setValue(dct['fetched_bytes'])
            self._progressBar.setFormat('Downloading %v / %m')
