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
from feedparser import feedparser # Load load local copy to avoid installation issues

import urllib2

class gmailaccount(QObject):
    def __init__(self, fetchmechanism="python", username="", passwd="", label="", displayname="", intotal=True, debug=False):
        QObject.__init__(self)
        
        # Store data
        self.fetchmechanism = fetchmechanism
        self.username = username
        self.passwd = passwd
        self.label = label
        self.displayname = displayname
        self.intotal = intotal
        self.debug = debug
        
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
        if self.debug: print "[gmail-plasmoid] ["+self.getDisplayName()+"] Checking mail..."
        
        # Clear any pending messages if not currently fetching
        if not self.fetching:
            self.msg = ""
        
        if self.username == "" or self.passwd == "":
            # Do not check email if there is no username or password set
            # NOTE: should send message back
            if self.debug: print "[gmail-plasmoid] ["+self.getDisplayName()+"] Blank username or password"
            self.addMsg("["+self.getDisplayName()+"] Blank username or password")
            self.SignalObject.emit(SIGNAL("checkMailDone"), self)
        elif not self.fetching:
            # Determine if we have a hosted domain
            atomurl = "https://mail.google.com/mail/feed/atom/"
            if self.username.find("@") <> -1:
                domain = self.username[self.username.find("@")+1:]
                if domain <> "gmail.com" and domain <> "googlemail.com" and len(domain) > 0:
                    atomurl = "https://mail.google.com/a/"+domain+"/feed/atom/"
                    if self.debug: print "[gmail-plasmoid] ["+self.getDisplayName()+"] Hosted account "+atomurl
            
            # Add label (if applicable)
            if self.label <> "":
                atomurl = atomurl + self.label
            
            if self.fetchmechanism == "kio":
                # Fetching done through KIO
                if self.debug: print "[gmail-plasmoid] ["+self.getDisplayName()+"] Fetching feed using KIO..."
                url = KUrl(atomurl)
                url.setUser(self.username)
                url.setPass(self.passwd)
                self.fetching = True
                self.job = KIO.storedGet(url, KIO.Reload, KIO.HideProgressInfo)
                self.connect(self.job, SIGNAL("result(KJob*)"), self.resultData)
            else:
                # Fetching using python
                if self.debug: print "[gmail-plasmoid] ["+self.getDisplayName()+"] Fetching feed using python..."
                
                # Get the atom feed
                auth_handler = urllib2.HTTPBasicAuthHandler()
                auth_handler.add_password(realm='New mail feed', uri=atomurl, user=self.username, passwd=self.passwd)
                opener = urllib2.build_opener(auth_handler)
                try:
                    f = opener.open(atomurl)
                except urllib2.URLError:
                    # FIXME: This code is a hack to deal with a special case where python fetching does not work if the
                    #        network is disconnected when the plasmoid is first run.
                    if self.debug: print "[gmail-plasmoid] ["+self.getDisplayName()+"] Performing KIO test fetch..."
                    self.job = KIO.storedGet(KUrl("http://www.google.com"), KIO.Reload, KIO.HideProgressInfo)
                    raise
                
                self.parsefeed(f.read())
                
                self.fetching = False
                self.SignalObject.emit(SIGNAL("checkMailDone"), self)
                self.first = False
            
    def resultData(self, job):
        if self.debug: print "[gmail-plasmoid] ["+self.getDisplayName()+"] Process results"
        
        # Reset the new email list
        if self.data <> None:
            self.data["newentries"] == []
        
        # Process atom feed
        if job.error() <> 0:
            if self.debug: print "[gmail-plasmoid] ["+self.getDisplayName()+"] Error getting atom feed:", job.error(), unicode(job.errorText())
            self.addMsg("["+self.getDisplayName()+"] Error getting atom feed")
        else:
            if self.debug: print "[gmail-plasmoid] ["+self.getDisplayName()+"] Atom feed received"
            
            self.parsefeed(str(job.data()))
        
        # Clean up
        self.job = None
        self.fetching = False
        self.SignalObject.emit(SIGNAL("checkMailDone"), self)
        self.first = False
        
    def parsefeed(self, data):
        if self.debug: print "[gmail-plasmoid] ["+self.getDisplayName()+"] Parsing results"
        
        # Reset the new email list
        if self.data <> None:
            self.data["newentries"] == []
        
        # Feed data to the parser
        gf = gmailfeed()
        data = gf.parseFeed(data)
        
        if data == None:
            if self.debug: print "[gmail-plasmoid] ["+self.getDisplayName()+"] An error has occured parsing the list of emails."
            self.addMsg("["+self.getDisplayName()+"] An error has occured parsing the list of emails.")
        else:
            # See if there are any new messages
            data["newentries"] = []
            if self.data <> None:
                for entry in data["entries"]:
                    if self.data["entries"].__contains__(entry) == False: data["newentries"].append(entry)
            else:
                # If this is the first run then all messages are new
                data["newentries"] = data["entries"]
                
            # Set flag if there are new emails
            if len(data["newentries"]) <> 0:
                self.newMessages = True
            else:
                self.newMessages = False
            
            # Store newest mails
            self.data = data
            
    
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
    

class gmailfeed:
    def parseFeed(self, feed):
        # Grab the gmail atom feed
        mail = {}
        atom = feedparser.parse(feed)
        
        if atom.bozo <> 0:
            if self.debug: print "[gmail-plasmoid] Error parsing feed:", atom.bozo_exception
            mail = None
        else:
            mail["fullcount"] = int(atom.feed.fullcount)
            mail["url"] = atom.feed.link
            
            mail["entries"] = []
            for i in xrange(len(atom.entries)):
                entry = {}
                
                if atom.entries[i].has_key("title"):
                    entry["subject"] = atom.entries[i].title
                else:
                    entry["subject"] = ""
                
                if atom.entries[i].has_key("author_detail"):
                    if atom.entries[i].author_detail.has_key("name"):
                        entry["authorname"] = atom.entries[i].author_detail.name
                    else:
                        entry["authorname"] = ""
                    
                    if atom.entries[i].author_detail.has_key("email"):
                        entry["authoremail"] = atom.entries[i].author_detail.email
                    else:
                        entry["authoremail"] = ""
                else:
                    entry["authorname"] = ""
                    entry["authoremail"] = ""
                    
                #if atom.entries[i].has_key("link"):
                    #entry["link"] = atom.entries[i].link
                #else:
                    #entry["link"] = ""
                    
                mail["entries"].append(entry)
            
        return mail