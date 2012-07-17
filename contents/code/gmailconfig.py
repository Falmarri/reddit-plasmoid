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
from PyKDE4.kio import *
from PyKDE4.kdeui import *
from PyKDE4.kdecore import *

from gmailconfigaccount import GmailConfigAccount

class GmailConfig(QWidget):
    def __init__(self, parent, settings):
        QWidget.__init__(self)
        self.ui = uic.loadUi(parent.package().filePath('ui', 'gmailconfigform.ui'), self)
        self.addChildrenAsMembers(self.ui)
        
        self.parent = parent
        
        # Put icons on the buttons
        self.btnAdd.setIcon(KIcon("list-add"))
        self.btnRemove.setIcon(KIcon("list-remove"))
        self.btnMoveUp.setIcon(KIcon("arrow-up"))
        self.btnMoveDown.setIcon(KIcon("arrow-down"))
        
        # Put in icon colors
        self.cmbDefaultIconNone.addItem(i18n("Default"))
        self.cmbDefaultIconNone.insertSeparator(self.cmbDefaultIconNone.count())
        self.cmbDefaultIconNone.addItem(i18n("Default")+" ("+i18n("Red")+")")
        self.cmbDefaultIconNone.addItem(i18n("Default")+" ("+i18n("Blue")+")")
        self.cmbDefaultIconNone.addItem(i18n("Default")+" ("+i18n("Green")+")")
        self.cmbDefaultIconNone.addItem(i18n("Default")+" ("+i18n("Gray")+")")
        self.connect(self.cmbDefaultIconNone, SIGNAL("activated (int)"), self.commandDefaultIconNone)
        
        self.cmbDefaultIcon.addItem(i18n("Default"))
        self.cmbDefaultIcon.insertSeparator(self.cmbDefaultIcon.count())
        self.cmbDefaultIcon.addItem(i18n("Default")+" ("+i18n("Red")+")")
        self.cmbDefaultIcon.addItem(i18n("Default")+" ("+i18n("Blue")+")")
        self.cmbDefaultIcon.addItem(i18n("Default")+" ("+i18n("Green")+")")
        self.cmbDefaultIcon.addItem(i18n("Default")+" ("+i18n("Gray")+")")
        self.connect(self.cmbDefaultIcon, SIGNAL("activated (int)"), self.commandDefaultIcon)
        
        # Fetch Mechanism
        if settings["fetchmechanism"] == "python":
            self.cmbFetchMechanism.setCurrentIndex(0)
        else:
            self.cmbFetchMechanism.setCurrentIndex(1)
        
        # Initialize values
        i = 0
        self.accountlist = settings["accountlist"]
        for ac in self.accountlist:
            item = QListWidgetItem()
            item.setText(self.getDisplayName(ac))
            item.setData(Qt.UserRole, QVariant(i))
            i += 1
            self.listAccounts.addItem(item)
        
        self.intPollingInterval.setValue(settings["pollinterval"])
        self.txtCommand.setText(settings["command"])
        if settings["checknetwork"] == 1: self.chkNetwork.setChecked(True)
        if settings["debugoutput"] == 1: self.chkDebug.setChecked(True)
        self.fonTextFont.setCurrentFont(QFont(settings["textfont"]))
        self.intTextSize.setValue(settings["textsize"])
        self.colColor.setColor(QColor(settings["textcolor"]))
        self.icoIcon.setIcon(settings["icon"])
        self.icoIconNone.setIcon(settings["iconnone"])
        
        # Connect signals
        self.connect(self.btnCommandBrowse, SIGNAL("clicked()"), self.commandBrowse)
        self.connect(self.btnAdd, SIGNAL("clicked()"), self.commandAdd)
        self.connect(self.btnRemove, SIGNAL("clicked()"), self.commandRemove)
        self.connect(self.btnMoveUp, SIGNAL("clicked()"), self.commandMoveUp)
        self.connect(self.btnMoveDown, SIGNAL("clicked()"), self.commandMoveDown)
        self.connect(self.listAccounts, SIGNAL("doubleClicked(QListWidgetItem *, const QPoint)"), self.commandModify)
        self.connect(self.listAccounts, SIGNAL("itemSelectionChanged()"), self.commandSelectionChanged)
        
        self.updateButtonState()
        
    def addChildrenAsMembers(self, widget):
        for w in widget.children():
            if w.inherits('QWidget'):
                try:
                    if w.objectName() != '':
                        self.__dict__[str(w.objectName())] = self.ui.findChild(globals()[w.metaObject().className()], w.objectName())
                        self.addChildrenAsMembers(self.__dict__[str(w.objectName())])
                except:
                    print '[gmail-plasmoid] Not using ' + w.metaObject().className() + ':' + str(w.objectName()) + ' as child.'
        
    # ---- ListView ---- #
    
    def commandSelectionChanged(self):
        self.updateButtonState()
    
    # ---- Button Commands ---- #
    
    def updateButtonState(self):
        pos = self.listAccounts.currentRow()
        # Remove button
        if pos <> -1:
            self.btnRemove.setEnabled(True)
        else:
            self.btnRemove.setEnabled(False)
            
        # Move Up button
        if pos > 0:
            self.btnMoveUp.setEnabled(True)
        else:
            if self.btnMoveUp.hasFocus(): self.listAccounts.setFocus()
            self.btnMoveUp.setEnabled(False)
            
        # Move Down button
        if pos <> -1 and pos+1 < self.listAccounts.count():
            self.btnMoveDown.setEnabled(True)
        else:
            if self.btnMoveDown.hasFocus(): self.listAccounts.setFocus()
            self.btnMoveDown.setEnabled(False)
    
    def updateList(self):
        i = 0
        self.listAccounts.clear()
        for ac in self.accountlist:
            item = QListWidgetItem()
            item.setText(self.getDisplayName(ac))
            item.setData(Qt.UserRole, QVariant(i))
            i += 1
            self.listAccounts.addItem(item)
    
    def commandAdd(self):
        print "[gmail-plasmoid] Add account"
        dialog = GmailConfigAccount(self.parent, self)
        dialog.setModal(True)
        dialog.show()
    
    def commandRemove(self):
        print "[gmail-plasmoid] Remove account"
        pos = self.listAccounts.currentRow()
        if pos <> -1:
            # Fix actual account data
            self.accountlist.pop(pos)
            self.updateList()
        self.updateButtonState()
        
    def commandMoveUp(self):
        pos = self.listAccounts.currentRow();
        if pos > 0:
            self.accountlist.insert(pos-1, self.accountlist.pop(pos))
            self.updateList()
            self.listAccounts.setCurrentRow(pos-1)    
        self.updateButtonState()
    
    def commandMoveDown(self):
        pos = self.listAccounts.currentRow();
        if pos <> -1 and pos+1 < self.listAccounts.count():
            self.accountlist.insert(pos+1, self.accountlist.pop(pos))
            self.updateList()
            self.listAccounts.setCurrentRow(pos+1)
        self.updateButtonState()
    
    def commandModify(self, item):
        print "[gmail-plasmoid] Modify account"
        dialog = GmailConfigAccount(self.parent, self, self.listAccounts.currentRow(), self.convertAccount(self.accountlist[item.data(Qt.UserRole).toPyObject()]))
        dialog.setModal(True)
        dialog.show()
        self.updateButtonState()
        
    def saveAccount(self, pos, ac):
        if pos == None:
            print "[gmail-plasmoid] Adding account"
            self.accountlist.append(ac)
            item = QListWidgetItem()
            item.setText(self.getDisplayName(ac))
            item.setData(Qt.UserRole, QVariant(self.accountlist.index(ac)))
            self.listAccounts.addItem(item)
        else:
            print "[gmail-plasmoid] Modifying account"
            self.accountlist[pos] = ac
            self.listAccounts.item(pos).setText(self.getDisplayName(ac))
            self.listAccounts.item(pos).setData(Qt.UserRole, QVariant(pos))
        self.updateButtonState()
        
        # Check sanity of passwords (two accounts with the same username should not have different passwords)
        # Note: It is important to check for this because we only store the user:password combinations in KWallet
        #       and this could lead to confusing errors for the user.
        l = {}
        prob = []
        for i in range(0, len(self.accountlist)):
            item = self.accountlist[i]
            ac = self.convertAccount(item)
            if l.has_key(ac["username"]):
                if l[ac["username"]] <> ac["passwd"]:
                    prob.append(ac["username"])
            else:
                l[ac["username"]] = ac["passwd"]
        if len(prob) > 0:
            msg = "The following usernames are used in multiple accounts but with different passwords, which should be rectified to avoid strange authentication problems: "
            for p in prob:
                msg = msg + p + ", "
            msg = msg[:-2]
            KMessageBox.sorry(self, msg, "Warning")
    
    def commandBrowse(self):
        fn = KFileDialog.getOpenFileName(KUrl(), "application/x-executable")
        if fn <> "":
            self.txtCommand.setText(fn + " %u")
    
    def commandDefaultIconNone(self, s):
        if s == 2:
            self.icoIconNone.setIcon(self.parent.package().path() + "contents/icons/gmail-plasmoid.svg")
        elif  s == 3:
            self.icoIconNone.setIcon(self.parent.package().path() + "contents/icons/gmail-plasmoid-blue.svg")
        elif  s == 4:
            self.icoIconNone.setIcon(self.parent.package().path() + "contents/icons/gmail-plasmoid-green.svg")
        elif  s == 5:
            self.icoIconNone.setIcon(self.parent.package().path() + "contents/icons/gmail-plasmoid-gray.svg")
        else:
            self.icoIconNone.setIcon(self.parent.package().path() + "contents/icons/gmail-plasmoid-gray.svg")
        
    def commandDefaultIcon(self, s):
        if s == 2:
            self.icoIcon.setIcon(self.parent.package().path() + "contents/icons/gmail-plasmoid.svg")
        elif  s == 3:
            self.icoIcon.setIcon(self.parent.package().path() + "contents/icons/gmail-plasmoid-blue.svg")
        elif  s == 4:
            self.icoIcon.setIcon(self.parent.package().path() + "contents/icons/gmail-plasmoid-green.svg")
        elif  s == 5:
            self.icoIcon.setIcon(self.parent.package().path() + "contents/icons/gmail-plasmoid-gray.svg")
        else:
            self.icoIcon.setIcon(self.parent.package().path() + "contents/icons/gmail-plasmoid.svg")

    # ---- Account Commands ---- #
    
    def getDisplayName(self, ac):
        if ac["displayname"] == "":
            if ac["label"] == "":
                return ac["username"]
            else:
                return ac["username"]+"/"+ac["label"]
        else:
            return ac["displayname"]
    
    # ---- Export Commands ---- #
    
    def getItem(self, item, key):
        # FIXME: This is a hack is used by convertAccount to get around different versions of the
        # QT bindings returning different data types.
        if item.has_key(key):
            return item[key]
        elif item.has_key(QString(key)):
            return item[QString(key)]
        else:
            raise KeyError    
    
    def convertAccount(self, item):
        ac = {}
        ac["username"] = unicode(self.getItem(item, "username"))
        ac["passwd"] = unicode(self.getItem(item, "passwd"))
        ac["label"] = unicode(self.getItem(item, "label"))
        ac["displayname"] = unicode(self.getItem(item, "displayname"))
        ac["intotal"] = bool(self.getItem(item, "intotal"))
        return ac
    
    def exportSettings(self):
        settings = {}
        
        # General settings
        settings["pollinterval"] = self.intPollingInterval.value()
        settings["command"] = unicode(self.txtCommand.text())
        if self.chkNetwork.isChecked() == True:
            settings["checknetwork"] = 1
        else:
            settings["checknetwork"] = 0
        if self.chkDebug.isChecked() == True:
            settings["debugoutput"] = 1
        else:
            settings["debugoutput"] = 0
        settings["icon"] = unicode(self.icoIcon.icon())
        settings["iconnone"] = unicode(self.icoIconNone.icon())
        font = self.fonTextFont.currentFont()
        settings["textfont"] = unicode(font.family())
        settings["textsize"] = self.intTextSize.value()
        settings["textcolor"] = unicode(self.colColor.color().name())
        
        if self.cmbFetchMechanism.currentIndex() == 0:
            settings["fetchmechanism"] = "python"
        else:
            settings["fetchmechanism"] = "kio"
        
        settings["accounts"] = []
        settings["accountlist"] = self.accountlist
        return settings