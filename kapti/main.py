import sys

from jinja2 import Environment, PackageLoader

from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, QLineEdit, QWidget, QVBoxLayout
from PyQt5.QtWebKitWidgets import QWebView, QWebPage

from kapti import pkgmanager

from kapti.progressview import ProgressView


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.history = [QUrl("welcome:/")]
        self.posInHistory = 0
        self.createJinjaEnv()
        self.createActions()
        self.createUi()
        self.refresh()

    def createJinjaEnv(self):
        self.jinjaEnv = Environment(loader=PackageLoader("kapti", "templates"))

    def createActions(self):
        self.backAction = QAction(QIcon.fromTheme("go-back"), self.tr("Back"), self)
        self.backAction.triggered.connect(self.goBack)
        self.forwardAction = QAction(QIcon.fromTheme("go-forward"), self.tr("Forward"), self)
        self.forwardAction.triggered.connect(self.goForward)

    def createUi(self):
        self.toolBar = self.addToolBar(self.tr("Toolbar"))
        self.toolBar.addAction(self.backAction)
        self.toolBar.addAction(self.forwardAction)

        self.searchLineEdit = QLineEdit(self)
        self.searchLineEdit.setPlaceholderText(self.tr("Search"))
        self.toolBar.addWidget(self.searchLineEdit)

        self.packageView = QWebView(self)
        self.packageView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)

        self.progressView = ProgressView()
        self.progressView.hide()

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.packageView)
        layout.addWidget(self.progressView)
        self.setCentralWidget(central)

        self.searchLineEdit.returnPressed.connect(self.startSearch)
        self.packageView.linkClicked.connect(self.openUrl)

        self.updateHistoryActions()
        self.searchLineEdit.setFocus()

    def updateHistoryActions(self):
        self.backAction.setEnabled(self.posInHistory > 0)
        self.forwardAction.setEnabled(self.posInHistory < len(self.history) - 1)

    def goBack(self):
        self.posInHistory -= 1
        self.refresh()
        self.updateHistoryActions()

    def goForward(self):
        self.posInHistory += 1
        self.refresh()
        self.updateHistoryActions()

    def startSearch(self):
        criterias = self.searchLineEdit.text()
        self.openUrl(QUrl("search:" + criterias))

    def refresh(self):
        self.openUrl(self.history[self.posInHistory], addToHistory=False)

    def openUrl(self, url, addToHistory=True):
        action = url.scheme()
        path = url.path()

        if action == "install":
            self.install(path)
            return
        if action == "remove":
            self.remove(path)
            return

        try:
            method = getattr(self, "url_" + action)
        except AttributeError:
            method = None

        if method:
            method(path)
            if addToHistory:
                self.history = self.history[:self.posInHistory + 1]
                self.history.append(url)
                self.posInHistory += 1
                self.updateHistoryActions()
        else:
            QDesktopServices.openUrl(url)

    def install(self, name):
        runner = pkgmanager.install(name)
        runner.setParent(self)
        self.progressView.setRunner(runner)
        runner.done.connect(self.refresh)

    def remove(self, name):
        runner = pkgmanager.remove(name)
        runner.setParent(self)
        self.progressView.setRunner(runner)
        runner.done.connect(self.refresh)

    def url_welcome(self, arg):
        self.setHtml("welcome.html")

    def url_search(self, arg):
        criterias = arg.split(" ")
        packages = pkgmanager.searchPackages(criterias)
        if packages:
            errorMessage = ""
        else:
            errorMessage = self.tr("Sorry, could not find any package matching \"{}\".").format(" ".join(criterias))

        self.setHtml("search.html", packages=packages,
                     errorMessage=errorMessage)

    def url_info(self, name):
        package = pkgmanager.getPackage(name)
        self.setHtml("info.html", package=package)

    def url_screenshot(self, name):
        package = pkgmanager.getPackage(name)
        self.setHtml("screenshot.html", package=package)

    def setHtml(self, templateName, **args):
        tmpl = self.jinjaEnv.get_template(templateName)
        self.packageView.setHtml(tmpl.render(**args))


def main():
    app = QApplication(sys.argv)

    window = Window()
    if len(sys.argv) > 1:
        lst = sys.argv[1:]
        window.searchLineEdit.setText(" ".join(lst))
        QTimer.singleShot(0, window.startSearch)

    window.show()
    app.exec_()
    return 0


if __name__=="__main__":
    sys.exit(main())
# vi: ts=4 sw=4 et
