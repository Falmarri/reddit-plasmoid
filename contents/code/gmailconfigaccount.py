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
from PyQt4 import uic
from PyKDE4.kdeui import *

class GmailConfigAccount(QDialog):
    def __init__(self, applet, parent=None, pos=None, ac=None):
        QWidget.__init__(self, parent)
        self.ui = uic.loadUi(applet.package().filePath('ui', 'gmailconfigaccountform.ui'), self)
        self.addChildrenAsMembers(self.ui)
        
        self.pos = pos
        self.p = parent
        
        # Initialize values
        if ac <> None:
            self.txtUsername.setText(ac["username"])
            self.txtPasswd.setText(ac["passwd"])
            self.txtLabel.setText(ac["label"])
            self.txtDisplayName.setText(ac["displayname"])
            self.chkInTotal.setChecked(ac["intotal"])
            
        # Connect button signals
        self.connect(self.btnSave, SIGNAL("clicked()"), self.commandSave)
        self.connect(self.btnCancel, SIGNAL("clicked()"), self.commandCancel)
        
    def addChildrenAsMembers(self, widget):
        for w in widget.children():
            if w.inherits('QWidget'):
                try:
                    if w.objectName() != '':
                        self.__dict__[str(w.objectName())] = self.ui.findChild(globals()[w.metaObject().className()], w.objectName())
                        self.addChildrenAsMembers(self.__dict__[str(w.objectName())])
                except:
                    print '[gmail-plasmoid] Not using ' + w.metaObject().className() + ':' + str(w.objectName()) + ' as child.'
        
    def commandSave(self):
        print "[gmail-plasmoid] Save account details"
        
        if unicode(self.txtUsername.text()) == "" or unicode(self.txtPasswd.text()) == "":
            KMessageBox.sorry(self, "In order to save you must enter a username and password.", "Error")
        else:
            # Gather account data
            ac = {}
            ac["username"] = unicode(self.txtUsername.text())
            ac["passwd"] = unicode(self.txtPasswd.text())
            ac["label"] = unicode(self.txtLabel.text())
            ac["displayname"] = unicode(self.txtDisplayName.text())
            ac["intotal"] = bool(self.chkInTotal.isChecked())
                    
            self.p.saveAccount(self.pos, ac)
            self.close()
        
    def commandCancel(self):
        self.close()