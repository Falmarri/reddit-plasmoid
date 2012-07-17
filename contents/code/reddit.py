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
from PyKDE4.kio import * 
from PyKDE4.kdecore import *
from reddit_api import Reddit
import urllib2

class redditaccount(QObject):
    def __init__(self, fetchmechanism="python", username="", passwd="", label="", displayname="", intotal=True, debug=True):
        QObject.__init__(self)
        
        # Store data
        self.fetchmechanism = fetchmechanism
        self.username = username
        self.passwd = passwd
        self.label = label
        self.displayname = displayname
        self.intotal = intotal
        self.debug = debug
        
        self.red = Reddit(user_agent="reddit-plasmoid")
        self.red.login(username=username, password=passwd)
        # Status
        self.fetching = False
        
        # Initialize variables
        self.first = True
        self.data = None
        self.newMessages = False
        self.msg = ""
        
        # Note: The use of the SignalObject variable for emitting signals seems
        #       like a hack, but this has been done because the underlying c++
        #       object was desroyed when trying to use the self.emit variable. If
        #       there is a better way to do this please let me know.
        self.SignalObject = QObject()
        
    # --- Check Mail --- #
    
    def getSingalObject(self):
        return self.SignalObject
        
    def addMsg(self, s):
        self.msg = self.msg + s
        
    def checkMail(self):
        if self.debug: print "[reddit-plasmoid] ["+self.getDisplayName()+"] Checking mail..."
        
        # Clear any pending messages if not currently fetching
        if not self.fetching:
            self.msg = ""
        
        if self.username == "" or self.passwd == "":
            # Do not check email if there is no username or password set
            # NOTE: should send message back
            if self.debug: print "[reddit-plasmoid] ["+self.getDisplayName()+"] Blank username or password"
            self.addMsg("["+self.getDisplayName()+"] Blank username or password")
            self.SignalObject.emit(SIGNAL("checkMailDone"), self)
        elif not self.fetching:
            # Determine if we have a hosted domain
            self.fetching = True
            # Fetching using python
            if self.debug: print "[reddit-plasmoid] ["+self.getDisplayName()+"] Fetching feed using python..."
            
            # Get the atom feed

            self.data = self.unread = list(self.red.user.get_unread())
            
            self.fetching = False
            if self.debug: print self.data
            self.SignalObject.emit(SIGNAL("checkMailDone"), self)
            self.first = False
        
    
    # --- Get/Set Functions --- #
    
    def getDisplayName(self):
        if self.displayname == "":
            if self.label == "":
                return self.username
            else:
                return self.username+"/"+self.label
        else:
            return self.displayname
    
    def setPasswd(self, passwd):
        self.passwd = passwd
        
    def fetching(self):
        return self.fetching
    
    
    
if __name__ == '__main__':
    r = redditaccount(username = "falmarri" , passwd = "", debug=True)
    r.checkMail()
