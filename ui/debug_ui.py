import asyncio
import sys
from threading import Thread

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QGuiApplication
from .ui import Ui_MainWindow
from raft import RaftServer


class MainWindow(QMainWindow):
    def __init__(self, raft: RaftServer, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.raft = raft

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui_refresh_timer = QTimer(self)
        self.ui_refresh_timer.timeout.connect(self.refresh_ui)
        self.ui_refresh_timer.start(30)

        self.place_window()
        self.setWindowTitle(f'Raft node at {self.raft.transport.self_node.ip}:{self.raft.transport.self_node.port}')

        self.ui.send_button.clicked.connect(self.send_data)

    def refresh_ui(self):
        self.ui.status_label.setText(f'ROLE: {self.raft.role.name}\ncommitIndex: {self.raft.commitIndex}\nterm: {self.raft.currentTerm}')

        log_text = ''
        for i, entry in enumerate(self.raft.log):
            line = f't={entry.term} i={i} data={entry.data} ci={self.raft.commitIndex}'
            if i <= self.raft.commitIndex:
                line = f'<b>{line}</b>'
            log_text += line + '<br>'
        self.ui.log_view.setText(log_text)


    def place_window(self):
        window_idx = self.raft.transport.self_node.port % 10
        n_windows = len(self.raft.transport.nodes) + 1

        screen_geometry = QGuiApplication.primaryScreen().geometry()
        screen_w = screen_geometry.width()
        screen_h = screen_geometry.height()
        x_coord = (screen_w/2) + (screen_w/2/n_windows)*window_idx

        self.move(int(x_coord), 0)
        self.setFixedWidth(int(screen_w/2/n_windows))

    def closeEvent(self, event):
        self.raft.shutdown()
        event.accept()

    def send_data(self):
        self.raft.append_log_entry(self.ui.data_line.text())
        self.ui.data_line.setText('')


async def run_debug_ui(raft: RaftServer):
    app = QApplication(sys.argv)
    w = MainWindow(raft)
    w.show()
    while True:
        await asyncio.sleep(1/30)
        app.sendPostedEvents()
        app.processEvents()

def start_debug_ui(raft: RaftServer):
    asyncio.create_task(run_debug_ui(raft))
