import sys, aiohttp, asyncio
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

__author__ = 'Alan Baumgartner'

class ImportDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('Import usernames')
        layout = QGridLayout()

        self.file_label = QLabel('Filename')
        self.file_text = QLineEdit()

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(self.file_label, 0, 0)
        layout.addWidget(self.file_text, 0, 1)

        layout.addWidget(buttons, 1, 0, 2, 0)

        self.setLayout(layout)
        self.setGeometry(400, 400, 300, 60)

    @staticmethod
    def getFileInfo():
        dialog = ImportDialog()
        result = dialog.exec_()
        return dialog.file_text.text(), result == QDialog.Accepted


class ExportDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('Export usernames')
        layout = QGridLayout()

        self.file_label = QLabel('Filename')
        self.file_text = QLineEdit()

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(self.file_label, 0, 0)
        layout.addWidget(self.file_text, 0, 1)

        layout.addWidget(buttons, 1, 0, 2, 0)

        self.setLayout(layout)
        self.setGeometry(400, 400, 300, 60)

    @staticmethod
    def getFileInfo():
        dialog = ExportDialog()
        result = dialog.exec_()
        return dialog.file_text.text(), result == QDialog.Accepted

class Checker(QThread):

    update = pyqtSignal(object)
    pupdate = pyqtSignal(object)
    count = 0

    URL = 'http://check-host.net/ip'

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.main())
        finally:
            loop.close()

    async def check_proxies(self, proxy, orginal_ip, session, sem, lock):
        async with sem:
                try:
                    async with session.get(self.URL, proxy=proxy, timeout=3) as resp:
                        response = (await resp.read()).decode()
                        if response != orginal_ip:
                            self.update.emit(proxy)

                except:
                    pass

                finally:
                    with await lock:
                        self.count += 1
                    self.pupdate.emit(self.count)

    async def main(self):
        sem = asyncio.BoundedSemaphore(50)
        lock = asyncio.Lock()
        async with aiohttp.ClientSession() as session:
            async with session.get(self.URL) as resp:
                orginal_ip = (await resp.read()).decode()
                proxies = get_proxies()
                tasks = [self.check_proxies(proxy, orginal_ip, session, sem, lock) for proxy in proxies]
                await asyncio.gather(*tasks)

class App(QMainWindow):
 
    def __init__(self):

        #Declare some shit
        super().__init__()
        self.title = 'Proxy Checker'
        self.left = 300
        self.top = 300
        self.width = 500
        self.height = 500
        self.initUI()

    def initUI(self):

        #Setup layout
        wid = QWidget(self)
        self.setCentralWidget(wid)
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
 
        layout = QGridLayout()
        wid.setLayout(layout)
 
        #Create Widgets
        menu_bar = self.menuBar()

        menu = menu_bar.addMenu("File")

        import_action = QAction("Import Usernames", self)
        import_action.triggered.connect(self.import_usernames)

        export_action = QAction("Export Usernames", self)
        export_action.triggered.connect(self.export_usernames)

        quit_action = QAction("Close", self)
        quit_action.triggered.connect(self.quit)

        menu.addAction(import_action)
        menu.addAction(export_action)
        menu.addAction(quit_action)

        self.start_button = QPushButton('Start')
        self.start_button.clicked.connect(self.start_clicked)

        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop_clicked)

        self.input_text = QTextEdit()
        self.output_text = QTextEdit()

        self.input_label = QLabel('Proxies to Check')
        self.input_label.setAlignment(Qt.AlignCenter)

        self.output_label = QLabel('Working Proxies')
        self.output_label.setAlignment(Qt.AlignCenter)

        self.progress_bar = QProgressBar()
 
        #Add widgets to gui
        layout.addWidget(self.input_label, 0, 0)
        layout.addWidget(self.output_label, 0, 1)
        layout.addWidget(self.input_text, 1, 0)
        layout.addWidget(self.output_text, 1, 1)
        layout.addWidget(self.start_button, 2, 0)
        layout.addWidget(self.stop_button, 2, 1)
        layout.addWidget(self.progress_bar, 3, 0, 4, 0)

    #When start button is clicked, start the QThread to check for proxies
    def start_clicked(self):
        proxies = get_proxies()
        self.progress_bar.setMaximum(len(proxies))
        self.output_text.setText('')
        self.thread = Checker(self)
        self.thread.update.connect(self.update_text)
        self.thread.pupdate.connect(self.update_progress)
        self.thread.start()

    #When stop button is clicked, terminate the thread
    def stop_clicked(self):
        try:
            self.thread.terminate()
        except:
            pass
 
    def update_text(self, text):
        self.output_text.append(str(text))

    def update_progress(self, val):
        self.progress_bar.setValue(val)

    #Saves usernames from the output text.
    def export_usernames(self):
        exportDialog = ExportDialog()
        filename, result = exportDialog.getFileInfo()
        if result:
            try:
                proxies = self.output_text.toPlainText()
                proxies = proxies.strip()
                with open(filename, "w") as a:
                    a.write(proxies)
            except:
                pass
        else:
            pass

    def import_usernames(self):
        importDialog = ImportDialog()
        filename, result = importDialog.getFileInfo()
        if result:
            try:
                with open(filename, "r") as f:
                    out = f.read()
                    self.input_text.setText(out)
            except:
                pass
        else:
            pass

    def quit(self):
        sys.exit()

if __name__ == '__main__':

    def get_proxies():
        proxies = window.input_text.toPlainText()
        proxies = proxies.strip()
        proxies = proxies.split('\n')
        return proxies

    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())