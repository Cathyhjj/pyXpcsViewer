from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QFileSystemModel
from PyQt5.QtCore import QAbstractItemModel
from PyQt5.QtCore import QObject, pyqtSlot, QDir
import sys
import os
from pyqtgraph import PlotWidget, ImageWindow
import matplotlib.pyplot as plt
import matplotlib
import pyqtgraph as pg
from matplot_qt import MplCanvas
from data_loader import DataLoader
from file_locator import FileLocator
import numpy as np
import time
# from xpcs_ui import


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('xpcs.ui', self)
        self.show()
        self.dl = None
        self.cache = None
        self.load_path()
        self.g2_cache = {}

    def load_data(self):
        if (len(self.dl.target_list)) == 0:
            return
        # self.plot_g2()
        self.plot_saxs_2D()
        self.plot_saxs_1D()
        self.update_hdf_list()
        # self.plot_g2()
        # self.plot_stability_iq()
        self.btn_load_data.setEnabled(False)

    def update_hdf_list(self):
        self.hdf_list.clear()
        self.hdf_list.addItems(self.dl.target_list)

    def show_hdf_info(self):
        fname = self.hdf_list.currentText()
        msg = self.dl.get_hdf_info(fname)

        filter_str = self.hdf_key_filter.text()
        fstr = filter_str.split()
        if len(fstr) > 0:
            msg2 = []
            for x in fstr:
                for n, y in enumerate(msg):
                    if n == len(msg) - 1:
                        break
                    if x in y:
                        msg2 += [msg[n], msg[n + 1]]
            msg = msg2
        self.hdf_info.clear()
        self.hdf_info.setText('\n'.join(msg))

    def plot_saxs_2D(self):
        kwargs = {
            'plot_type': self.cb_saxs2D_type.currentText(),
            'cmap': self.cb_saxs2D_cmap.currentText(),
            'autorotate': self.saxs2d_autorotate.isChecked()}
        self.dl.plot_saxs_2d(pg_hdl=self.pg_saxs, **kwargs)

    def plot_saxs_1D(self):
        kwargs = {
            'plot_type': ('log', 'linear')[self.cb_saxs_type.currentIndex()],
            'plot_offset': self.sb_saxs_offset.value(),
            'plot_norm': self.cb_saxs_norm.currentIndex()}
        self.dl.plot_saxs_1d(self.mp_saxs, **kwargs)

    def plot_stability_iq(self):
        kwargs = {
            'plot_type': ('log', 'linear')[self.cb_stab_type.currentIndex()],
            'plot_norm': self.cb_stab_norm.currentIndex()}
        self.dl.plot_stability(self.mp_stab, **kwargs)

    def plot_tauq(self):
        kwargs = {
            'max_q': self.sb_tauq_qmax.value(),
            'offset': self.sb_tauq_offset.value()}
        msg = self.dl.plot_tauq(hdl=self.mp_tauq, **kwargs)
        self.tauq_msg.clear()
        self.tauq_msg.setText('\n'.join(msg))

    def plot_g2(self, max_points=3):
        kwargs = {
            'offset': self.sb_g2_offset.value(),
            'max_tel': 10 ** self.sb_g2_tmax.value(),
            'max_q': self.sb_g2_qmax.value()
        }
        bounds = self.check_number()
        err_msg = self.dl.plot_g2(handler=self.mp_g2, bounds=bounds, **kwargs)
        self.g2_err_msg.clear()
        if err_msg is None:
            self.g2_err_msg.insertPlainText('None')
        else:
            self.g2_err_msg.insertPlainText('\n'.join(err_msg))

    def load_path(self):
        # f = QFileDialog.getExistingDirectory(self, 'Open directory',
        #                                      '/User/mqichu',
        #                                      QFileDialog.ShowDirsOnly)
        # if not os.path.isdir(f):
        #     return
        f = './data/files2.txt'
        self.work_dir.setText(f)
        self.dl = DataLoader(f)
        self.update_box(self.dl.source_list, mode='source')

        # for debug
        # self.list_view_source.selectAll()
        # self.add_target()

    def show_error(self, msg):
        error_dialog = QtWidgets.QErrorMessage()
        error_dialog.showMessage('\n'.join(msg))

    def update_box(self, file_list, mode='source'):
        if mode == 'source':
            self.list_view_source.clear()
            self.list_view_source.addItems(file_list)
            self.box_source.setTitle('Source: %5d' % len(file_list))
        elif mode == 'target':
            self.list_view_target.clear()
            self.list_view_target.addItems(file_list)
            self.box_target.setTitle('Target: %5d' % len(file_list))
        return

    def add_target(self):
        target = []
        prev_hash = self.dl.hash(-1)
        for x in self.list_view_source.selectedIndexes():
            target.append(x.data())

        self.dl.add_target(target)
        self.update_box(self.dl.target_list, mode='target')

        curr_hash = self.dl.hash(-1)
        if prev_hash != curr_hash:
            self.btn_load_data.setEnabled(True)

        self.list_view_source.clearSelection()

    def remove_target(self):
        prev_hash = self.dl.hash(-1)
        rmv_list = []
        for x in self.list_view_target.selectedIndexes():
            rmv_list.append(x.data())

        self.dl.remove_target(rmv_list)
        self.update_box(self.dl.target_list, mode='target')

        curr_hash = self.dl.hash(-1)
        if prev_hash != curr_hash:
            if len(self.dl.target_list) >= 1:
                self.btn_load_data.setEnabled(True)

    def trie_search(self):
        val = self.filter_str.text()
        if len(val) == 0:
            self.update_box(self.dl.source_list, mode='source')
            return
        num, self.cache = self.dl.search(val)
        self.update_box(self.cache, mode='source')
        self.list_view_source.selectAll()

    def check_number(self, default_val=(1e-6, 1e-2, 0.01, 0.20, 0.95, 1.05)):
        keys = (self.tau_min, self.tau_max,
                self.bkg_min, self.bkg_max,
                self.cts_min, self.cts_max)
        vals = [None] * len(keys)
        for n, key in enumerate(keys):
            try:
                val = float(key.text())
            except:
                key.setText(str(default_val[n]))
                return
            else:
                vals[n] = val

        def swap_min_max(id1, id2, fun=str):
            if vals[id1] > vals[id2]:
                keys[id1].setText(fun(vals[id2]))
                keys[id2].setText(fun(vals[id1]))
                vals[id1], vals[id2] = vals[id2], vals[id1]

        swap_min_max(0, 1, lambda x: '%.2e' % x)
        swap_min_max(2, 3)
        swap_min_max(4, 5)
        vals = np.array(vals).reshape(len(keys) // 2, 2)
        return (tuple(vals[:, 0]), tuple(vals[:, 1]))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()
