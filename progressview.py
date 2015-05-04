from PyQt4.QtGui import QWidget, QProgressBar, QVBoxLayout
from PyKDE4.kdecore import i18n, KGlobal


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
            fetched = dct['fetched_bytes']
            total = dct['total_bytes']
            self._progressBar.setMaximum(total)
            self._progressBar.setValue(fetched)
            locale = KGlobal.locale()
            self._progressBar.setFormat(i18n('Downloading... %1 / %2',
                                             locale.formatByteSize(fetched),
                                             locale.formatByteSize(total)
                                             ))
