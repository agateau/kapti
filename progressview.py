from PyQt5.QtWidgets import QWidget, QProgressBar, QVBoxLayout


MEGA = 1024 * 1024
KILO = 1024


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
                self._progressBar.setFormat(self.tr('Installing... %p%'))
            else:
                self._progressBar.setFormat(self.tr('Removing... %p%'))
        elif step == 'acquire':
            fetched = dct['fetched_bytes']
            total = dct['total_bytes']

            message = self.tr('Downloading... {} / {}') \
                .format(self.formatByteSize(fetched),
                        self.formatByteSize(total))

            self._progressBar.setMaximum(total)
            self._progressBar.setValue(fetched)
            self._progressBar.setFormat(message)

    def formatByteSize(self, size):
        if size > MEGA:
            return self.tr("{:.1f} MB").format(size / MEGA)
        if size > KILO:
            return self.tr("{:.1f} KB").format(size / KILO)
        return self.tr("{} bytes").format(size)
