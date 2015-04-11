from PyQt4.QtGui import QWidget, QProgressBar, QVBoxLayout
from PyKDE4.kdecore import i18n


class ProgressView(QWidget):
    def __init__(self, parent=None):
        super(ProgressView, self).__init__(parent)

        self._progressBar = QProgressBar()

        layout = QVBoxLayout(self)
        layout.addWidget(self._progressBar)

    def setRunner(self, runner):
        self.show()
        self._progressBar.setMaximum(0)
        runner.progress.connect(self._showProgress)
        runner.done.connect(self.hide)

    def _showProgress(self, dct):
        step = dct['step']
        if step in ('install', 'remove'):
            self._progressBar.setMaximum(100)
            self._progressBar.setValue(dct['percent'])
            if step == 'install':
                self._progressBar.setFormat(i18n('Installing... %p%'))
            else:
                self._progressBar.setFormat(i18n('Removing... %p%'))
        elif step == 'acquire':
            self._progressBar.setMaximum(dct['total_bytes'])
            self._progressBar.setValue(dct['fetched_bytes'])
            self._progressBar.setFormat(i18n('Downloading... %v / %m'))
