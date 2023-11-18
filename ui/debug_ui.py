import asyncio
import sys
from threading import Thread

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QGuiApplication
from .ui import Ui_MainWindow
from raft import RaftServer
from multiprocessing import Process
import sys
import os
import subprocess
from distributed_map import MapSet, MapRemove

class MainWindow(QMainWindow):
    def __init__(self, raft: RaftServer, ddict: dict, *args, **kwargs):
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

        self.ui.restart_button.clicked.connect(self.restart_raft)
        self.ui.downlink_button.clicked.connect(self.toggle_downlink)
        self.ui.uplink_button.clicked.connect(self.toggle_uplink)

        self.update_link_buttons()
        self.ddict = ddict

        self.ui.map_del_button.clicked.connect(self.send_map_delete)
        self.ui.map_set_button.clicked.connect(self.send_map_set)



    def refresh_ui(self):
        self.ui.status_label.setText(f'ROLE: {self.raft.role.name}\ncommitIndex: {self.raft.commitIndex}\nterm: {self.raft.currentTerm}')

        log_text = ''
        for i, entry in enumerate(self.raft.log):
            line = f't={entry.term} i={i} data={entry.data} ci={self.raft.commitIndex}'
            if i <= self.raft.commitIndex:
                line = f'<b>{line}</b>'
            log_text += line + '<br>'
        self.ui.log_view.setText(log_text)

        self.ui.uplink_button.setText(f'Up ({self.raft.transport.send_queue.sync_q.qsize()})')
        self.ui.downlink_button.setText(f'Down ({self.raft.transport.receive_queue.sync_q.qsize()})')

        self.ui.map_data_label.setText(f'Map: {self.ddict}')


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

    def restart_raft(self):
        self.raft.shutdown()
        cmdline = ' '.join([sys.executable] + sys.argv)
        subprocess.Popen(["/bin/bash", "-c", "sleep 3; " + cmdline], close_fds=True)
        exit(0)

    def toggle_uplink(self):
        if self.raft.transport.uplink_enabled_event.is_set():
            self.raft.transport.uplink_enabled_event.clear()
        else:
            self.raft.transport.uplink_enabled_event.set()
        self.update_link_buttons()

    def toggle_downlink(self):
        if self.raft.transport.downlink_enabled_event.is_set():
            self.raft.transport.downlink_enabled_event.clear()
        else:
            self.raft.transport.downlink_enabled_event.set()
        self.update_link_buttons()

    def update_link_buttons(self):
        de = self.raft.transport.downlink_enabled_event.is_set()
        ue = self.raft.transport.uplink_enabled_event.is_set()
        def color(b: bool):
            return f"background-color: {'green' if b else 'red'}"
        self.ui.downlink_button.setStyleSheet(color(de))
        self.ui.uplink_button.setStyleSheet(color(ue))

    def clear_map_inputs(self):
        self.ui.map_action_key.clear()
        self.ui.map_action_value.clear()

    def send_map_delete(self):
        self.raft.append_log_entry(MapRemove(self.ui.map_action_key.text()))
        self.clear_map_inputs()

    def send_map_set(self):
        self.raft.append_log_entry(MapSet(self.ui.map_action_key.text(), self.ui.map_action_value.text()))
        self.clear_map_inputs()



async def run_debug_ui(raft: RaftServer, ddict: dict):
    app = QApplication(sys.argv)
    w = MainWindow(raft, ddict)
    w.show()
    while True:
        await asyncio.sleep(1/30)
        app.sendPostedEvents()
        app.processEvents()

def start_debug_ui(raft: RaftServer, ddict):
    asyncio.create_task(run_debug_ui(raft, ddict))


# def child_process_fn(path, argv):
#     import time
#     print('ama child', flush=True)
#     time.sleep(3)
#     print('ama child down sleeping', flush=True)
#     os.execv(sys.executable, [sys.executable]+argv)