import sys, aiohttp, asyncio
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QTextEdit, QLabel, QLineEdit, QProgressBar
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore
from PyQt5.QtCore import QThread

__author__ = 'Alan Baumgartner'

class Checker(QThread):

    update = QtCore.pyqtSignal(object)
    pupdate = QtCore.pyqtSignal(object)
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

class App(QWidget):
 
    def __init__(self):

        #Declare some shit
        super().__init__()
        self.title = 'Proxy Checker'
        self.left = 10
        self.top = 10
        self.width = 500
        self.height = 500
        self.initUI()

    def initUI(self):

        #Setup layout
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
 
        layout = QGridLayout()
        self.setLayout(layout)
 
        #Create Widgets
        self.start_button = QPushButton('Start')
        self.start_button.clicked.connect(self.start_clicked)

        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop_clicked)

        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.save_clicked)

        self.input_text = QTextEdit()
        self.output_text = QTextEdit()

        self.input_label = QLabel('Proxies to Check')
        self.input_label.setAlignment(QtCore.Qt.AlignCenter)

        self.output_label = QLabel('Working Proxies')
        self.output_label.setAlignment(QtCore.Qt.AlignCenter)

        self.save_entry = QLineEdit('Textfile.txt')
        self.save_entry.setAlignment(QtCore.Qt.AlignCenter)

        self.progress_bar = QProgressBar()
 
        #Add widgets to gui
        layout.addWidget(self.input_label, 0, 0)
        layout.addWidget(self.output_label, 0, 1)
        layout.addWidget(self.input_text, 1, 0)
        layout.addWidget(self.output_text, 1, 1)
        layout.addWidget(self.start_button, 2, 0)
        layout.addWidget(self.save_entry, 2, 1)
        layout.addWidget(self.stop_button, 3, 0)
        layout.addWidget(self.save_button, 3, 1)
        layout.addWidget(self.progress_bar, 4, 0, 5, 0)

    def start_clicked(self):
        proxies = get_proxies()
        self.progress_bar.setMaximum(len(proxies))
        self.output_text.setText('')
        self.thread = Checker(self)
        self.thread.update.connect(self.update_text)
        self.thread.pupdate.connect(self.update_progress)
        self.thread.start()

    def stop_clicked(self):
        try:
            self.thread.terminate()
        except:
            pass

    def save_clicked(self):
        self.save_proxies()
 
    def update_text(self, text):
        self.output_text.append(str(text))

    def update_progress(self, val):
        self.progress_bar.setValue(val)

    def save_proxies(self):
        proxies = self.output_text.toPlainText()
        proxies = proxies.strip()
        outputfile = self.save_entry.text()
        with open(outputfile, "a") as a:
            a.write(proxies)

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