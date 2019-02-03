# embedding_in_qt5.py --- Simple Qt5 application embedding matplotlib canvases
#
# Copyright (C) 2005 Florent Rougon
#               2006 Darren Dale
#               2015 Jens H Nielsen
#               2019 Toby M Potter
#
# Adapted for use in plotting 1D and 2D slices of arrays
# by Toby M Potter of Pelagos Consulting and Education, 2019
# https://www.pelagos-consulting.com

# Complete courses in Python available at
# https://learn.pelagos-consulting.com

from __future__ import unicode_literals
import sys
import os
import random
import matplotlib

# Make sure that we are using QT5
matplotlib.use('Qt5Agg')
from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtCore import Qt

# Import Numpy
import numpy as np

# Get the Matplotlib Navigation toolbar from Qt5 backend
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

progname = os.path.basename(sys.argv[0])
progversion = "0.1"

class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        self.compute_initial_figure()

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass

class ArrayMplCanvas(MyMplCanvas):
    """Canvas to show portions of a multidimensional array"""
    def __init__(self, array, **kwargs):
        MyMplCanvas.__init__(self, **kwargs)
        self.array=array
        self.ndim=self.array.ndim
        self.create_slices(array)

    def set_array(self, array):
        self.array=array.copy()
        self.ndim=self.array.ndim
        self.create_slices(self.array)

    def get_array(self):
        return(self.array)
        
    def create_slices(self, array):
        """Create default view of slices into the array"""
        self.slices=[]
        for n in range(0,self.array.ndim):
            self.slices.append(slice(None,None,None))
        self.slices=tuple(self.slices)

    def set_slices(self, slices):
        assert(len(slices)==self.array.ndim)
        self.slices=tuple(slices)

    def get_slices(self):
        return(self.slices)

    def compute_initial_figure(self):
        pass

    def update_figure(self):
        """Regenerate the plot"""
        sliced_arr=self.array[self.slices]

        #find out which axes have length greater than 1
        trial_arr=np.squeeze(sliced_arr)
        axis_no=[]

        for n in range(0, len(self.slices)):
            if sliced_arr.shape[n]>1:
                axis_no.append(n)  

        if len(axis_no)==2:
            self.axes.cla()
            self.axes.imshow(trial_arr, interpolation=None, aspect="auto")
            self.axes.set_ylabel("Axis {}".format(axis_no[0]))
            self.axes.set_xlabel("Axis {}".format(axis_no[1]))
            self.draw()
            
        elif len(axis_no)==1:
            self.axes.cla()
            self.axes.imshow(trial_arr[np.newaxis,:], interpolation=None, aspect="auto")
            self.axes.set_xlabel("Axis {} (0-based)".format(axis_no[0]))
            self.draw()

class ApplicationWindow(QtWidgets.QMainWindow):
    """Create the application"""
    def __init__(self, array):
        QtWidgets.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")

        # Menus
        self.file_menu = QtWidgets.QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.help_menu = QtWidgets.QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

        self.help_menu.addAction('&About', self.about)

        # Main widget
        self.main_widget = QtWidgets.QWidget(self)

        # Grid layout to keep everything organised
        self.layout = QtWidgets.QGridLayout(self.main_widget)

        # Main plot canvas
        self.arr_canvas = ArrayMplCanvas(array, parent=self.main_widget,  width=5, height=4, dpi=100)

        # Add the Matplotlib toolbar
        self.addToolBar(NavigationToolbar(self.arr_canvas, self))

        # Add a layout to the canvas
        self.layout.addWidget(self.arr_canvas, 0, 0, 1, 3)

        self.naxes=self.arr_canvas.ndim

        # Create sliders, checkboxes, and labels
        self.sliders =  [QtWidgets.QSlider(orientation=Qt.Horizontal) for n in range(0,self.naxes)]
        self.checkboxes=[QtWidgets.QCheckBox("Slice along Axis {}".format(a)) for a in range(0,self.naxes)]
        self.labels=[QtWidgets.QLabel() for n in range(0, self.naxes)]

        # Initial setup for sliders
        start_row=1
        for n in range(0, self.naxes):
            slider=self.sliders[n]
            slider.setPageStep(1)
            slider.valueChanged.connect(self.update_plot)
            slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
            slider.setEnabled(False)

            checkbox=self.checkboxes[n]
            checkbox.stateChanged.connect(self.update_plot)

            label=self.labels[n]

            self.layout.addWidget(checkbox, start_row+n,1,1,1)
            self.layout.addWidget(slider, start_row+n,0,1,1)
            self.layout.addWidget(label, start_row+n,2,1,1)
            
        # Update the slider ranges
        self.update_slider_ranges()

        # Add the layout to the image
        self.main_widget.setLayout(self.layout)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

    def update_plot(self):
        """Go through all valid sliders and checkboxes and update the plot with new parameters"""

        # Create new slices object
        new_slices=[slice(None,None,None) for n in range(0, self.arr_canvas.ndim)]
        for n in range(0, self.arr_canvas.ndim):
            slider=self.sliders[n]
            checkbox=self.checkboxes[n]
            label=self.labels[n]
            label.setText("Index: {:6d}, N{}: {:6d}".format(slider.value(),n,slider.maximum()+1))

            if checkbox.isChecked():
                slider.setEnabled(True)
                new_slices[n]=slice(slider.value(),slider.value()+1,1)
            else:
                slider.setEnabled(False)
        
        # Set the new slices
        self.arr_canvas.set_slices(new_slices)

        # Tell the array canvas to update the Figure
        self.arr_canvas.update_figure()

    def update_slider_ranges(self):
        # Modify slider ranges to fit a new array
        for n in range(0, self.naxes):
            slider=self.sliders[n]
            label=self.labels[n]
            if n<self.arr_canvas.ndim:
                slider.setMinimum(0)
                slider.setMaximum(self.arr_canvas.array.shape[n]-1)

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QtWidgets.QMessageBox.about(self, "About",
                                    """Slicer, 

Copyright 2005 Florent Rougon, 2006 Darren Dale, 2015 Jens H Nielsen, 2019 Toby Potter

This program is a simple program to display a 1D or 2D slice of a multidimensional Numpy array.

It may be used and modified with no restriction; raw copies as well as
modified versions may be distributed without limitation.""")

def slicer(array):
    qApp = QtWidgets.QApplication(sys.argv)
    aw = ApplicationWindow(array)
    aw.setWindowTitle("%s" % progname)
    aw.show()
    qApp.exec_()

if __name__=="__main__":
    array=np.random.random((256,128,64))
