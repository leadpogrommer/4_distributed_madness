# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/raft.ui'
#
# Created by: PyQt5 UI code generator 5.15.10
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(753, 604)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.status_label = QtWidgets.QLabel(self.centralwidget)
        self.status_label.setObjectName("status_label")
        self.verticalLayout.addWidget(self.status_label)
        self.top_panel_widget = QtWidgets.QWidget(self.centralwidget)
        self.top_panel_widget.setObjectName("top_panel_widget")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.top_panel_widget)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.send_widget = QtWidgets.QWidget(self.top_panel_widget)
        self.send_widget.setObjectName("send_widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.send_widget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.data_line = QtWidgets.QLineEdit(self.send_widget)
        self.data_line.setObjectName("data_line")
        self.horizontalLayout.addWidget(self.data_line)
        self.send_button = QtWidgets.QPushButton(self.send_widget)
        self.send_button.setObjectName("send_button")
        self.horizontalLayout.addWidget(self.send_button)
        self.horizontalLayout_2.addWidget(self.send_widget)
        self.network_groupBox = QtWidgets.QGroupBox(self.top_panel_widget)
        self.network_groupBox.setObjectName("network_groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.network_groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.restart_button = QtWidgets.QPushButton(self.network_groupBox)
        self.restart_button.setObjectName("restart_button")
        self.gridLayout.addWidget(self.restart_button, 1, 0, 1, 2)
        self.downlink_button = QtWidgets.QPushButton(self.network_groupBox)
        self.downlink_button.setObjectName("downlink_button")
        self.gridLayout.addWidget(self.downlink_button, 0, 1, 1, 1)
        self.uplink_button = QtWidgets.QPushButton(self.network_groupBox)
        self.uplink_button.setStyleSheet("background-color: rgba(46, 204, 113)")
        self.uplink_button.setObjectName("uplink_button")
        self.gridLayout.addWidget(self.uplink_button, 0, 0, 1, 1)
        self.horizontalLayout_2.addWidget(self.network_groupBox)
        self.verticalLayout.addWidget(self.top_panel_widget)
        self.log_view = QtWidgets.QTextEdit(self.centralwidget)
        self.log_view.setStyleSheet("")
        self.log_view.setReadOnly(True)
        self.log_view.setObjectName("log_view")
        self.verticalLayout.addWidget(self.log_view)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.status_label.setText(_translate("MainWindow", "TextLabel"))
        self.send_button.setText(_translate("MainWindow", "Send!"))
        self.network_groupBox.setTitle(_translate("MainWindow", "Ростелеком"))
        self.restart_button.setText(_translate("MainWindow", "Restart in 3s"))
        self.downlink_button.setText(_translate("MainWindow", "Down"))
        self.uplink_button.setText(_translate("MainWindow", "Up"))
