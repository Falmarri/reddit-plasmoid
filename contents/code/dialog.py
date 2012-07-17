# -*- coding: utf-8 -*-

# Copyright (C) 2009  Mark McCans <mjmccans@gmail.com>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyKDE4.plasma import *

class PopupDialog(Plasma.Dialog):
    def init(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setStyleSheet("padding-left:0;color: %s;" % Plasma.Theme.defaultTheme().color(Plasma.Theme.TextColor).name())
        
        layout = QVBoxLayout(self)
        self.title = QLabel()
        self.title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title)
        self.body = QLabel()
        layout.addWidget(self.body)
        
        self.setLayout(layout)
    
    def setTitle(self, s):
        if s == "":
            self.title.setText("")
        else:
            self.title.setText("<b>"+s+"</b>")
        
    def setBody(self, s):
        self.body.setText(s)
        
    def showDialog(self):
        if self.title.text() == "" and self.body.text() == "":
           pass
        else:
            self.show()
            