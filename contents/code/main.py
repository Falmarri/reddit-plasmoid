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
from PyKDE4.kdecore import *
from PyKDE4.kdeui import *
from PyKDE4.plasma import *
from PyKDE4 import plasmascript
from PyKDE4.kio import *
from PyKDE4.solid import *

import sys, os, commands, glob, time, pickle
#sys.stdout = open("/home/dknapp/reddit.log", "w")
from redditconfig import RedditConfig
from reddit_api import Reddit


class redditplasmoid(plasmascript.Applet):
    def __init__(self,parent,args=None):
        plasmascript.Applet.__init__(self,parent)
    
    def init(self):
        self.debug = True
        self.OldRect = None
        self.setHasConfigurationInterface(True)
        self.setAspectRatioMode(Plasma.Square)
        self.theme = Plasma.Svg(self)
        self.theme.setImagePath("widgets/background")
        self.setBackgroundHints(Plasma.Applet.TranslucentBackground)
        self.layout = QGraphicsLinearLayout(self.applet)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setOrientation(Qt.Horizontal)
        self.icon = Plasma.IconWidget()
        self.layout.addItem(self.icon)
        self.resize(128,128)
        
        # File versions
        vers = {}
        vers["reddit-plasmoid.notifyrc"] = "10"
        
        # Setup configuration
        self.settings = {}
        gc = self.config()
        
        # General settings
        self.settings["pollinterval"] = int(self.fixType(gc.readEntry("pollinterval", "5")))
        self.settings["checknetwork"] = int(self.fixType(gc.readEntry("checknetwork", "1")))
        self.settings["fetchmechanism"] = self.fixType(gc.readEntry("fetchmechanism", "python"))
        self.settings["debugoutput"] = int(self.fixType(gc.readEntry("debugoutput", "1")))
        self.settings["command"] = self.fixType(gc.readEntry("command", 'firefox %u'))
        self.settings["textfont"] = self.fixType(gc.readEntry("textfont", ""))
        self.settings["textsize"] = int(self.fixType(gc.readEntry("textsize", "60")))
        self.settings["textcolor"] = self.fixType(gc.readEntry("textcolor", "blue"))
        self.settings["icon"] = self.fixType(gc.readEntry("icon", self.package().path() + "contents/icons/reddit-plasmoid.svg"))
        self.settings["iconnone"] = self.fixType(gc.readEntry("iconnone", self.package().path() + "contents/icons/reddit-plasmoid-gray.svg"))
        if self.settings["debugoutput"] == 1: self.debug = True
        
        # Create notifyrc file if required
        kdehome = unicode(KGlobal.dirs().localkdedir())
        if not os.path.exists(kdehome+"share/apps/reddit-plasmoid/reddit-plasmoid.notifyrc"):
            if os.path.exists(kdehome+"share/apps"):
                self.createNotifyrc(kdehome, vers)
        else:
            # Update if the version string does not match
            ver = self.fixType(gc.readEntry("reddit-plasmoid.notifyrc", "0"))
            if ver != vers["reddit-plasmoid.notifyrc"]:
                if self.debug: print "[reddit-plasmoid] Update .notifyrc file..."
                self.createNotifyrc(kdehome, vers)
                
        # Get default font if font not set
        if self.settings["textfont"] == "":
            # FIXME: There must be a better way to get the default font.
            paint = QPainter()
            font = paint.font()
            self.settings["textfont"] = unicode(font.family())
            paint = None
        
        
        # Create the gmailaccount objects
        
        # Initialize variables
        self.fetching = False
        self.paused = False
        self.error = False
        
        # Set initial tooltip
        self.setUserMessage("reddit-plasmoid", "")
        
        # Check the status of the network connection
        self.disconnected = False
        if self.settings["checknetwork"] == 1 and Solid.Networking.status() == Solid.Networking.Unconnected:
            self.disconnected = True
            self.setUserMessage(i18n("Error"), i18n("Network connection appears to be down."))
        
        # Paint the icon
        self.updateIcon()
        
        # Connect icon
        self.connect(self.icon, SIGNAL("clicked()"), self.iconClicked)
        
        # Connect to Solid network state signals
        self.connect(Solid.Networking.notifier(), SIGNAL("shouldConnect()"), self.networkConnected)
        self.connect(Solid.Networking.notifier(), SIGNAL("shouldDisconnect()"), self.networkDisconnected)
        
        # Create timer
        self.timer = QTimer()
        self.connect(self.timer, SIGNAL("timeout()"), self.checkMail)        
        
        # Get password from kwallet (async to avoid blocking)
        # NOTE: The wid and the value for async opening should be done better
        self.wallet = KWallet.Wallet.openWallet(KWallet.Wallet.LocalWallet(), 0, KWallet.Wallet.Asynchronous)
        if self.wallet is not None:
            self.connect(self.wallet, SIGNAL("walletOpened(bool)"), self.walletOpened)
        else:
            # KWallet service is disabled, start checking for emails if connected
            if self.debug: print "[reddit-plasmoid] KWallet disabled"
            if self.disconnected == False:
                self.checkMail()
   
    def networkConnected(self):
        if self.debug: print "[reddit-plasmoid] Network connection up"
        if self.settings["checknetwork"] == 1:
            self.disconnected = False
            self.timer.start(5000) # Start checking again after 5 seconds
        
    def networkDisconnected(self):
        if self.debug: print "[reddit-plasmoid] Network connection down"
        if self.settings["checknetwork"] == 1:
            self.timer.stop()
            self.disconnected = True
            self.setUserMessage(i18n("Error"), i18n("Network connection appears to be down."))
            self.updateIcon()
    
    def fixType(self, val):
        # FIXME: This is needed to take care of problems with KDE 4.3 bindings, but it should be removed
        # when things are fixed.
        if type(val) == QVariant:
            return str(val.toString())
        else:
            return val
        
    def paintInterface(self, painter, option, rect):
        if self.OldRect <> None:
            if self.OldRect <> rect:
                self.updateIcon()
        self.OldRect = QRect(rect.x(), rect.y(), rect.width(), rect.height())
            
    def setUserMessage(self, s1, s2=""):
        # Update the tooltip to give user information
        self.data = Plasma.ToolTipContent()
        self.data.setMainText(s1)
        self.data.setSubText(s2)
        self.data.setAutohide(False)
        Plasma.ToolTipManager.self().setContent(self.applet, self.data)
    
    def updateIcon(self):
        # Note: I'm not sure why, but the font shows up much nicer at small sizes when the size is set to larger than the
        #       plasmoid (using a multiple of 2 here)
        loader = KIconLoader()
        size = min(self.icon.size().width(),self.icon.size().height())*2
        if self.TotalCount == 0:
            pix = KIconLoader.loadIcon(loader, self.settings["iconnone"], KIconLoader.NoGroup, size)
        else:
            pix = KIconLoader.loadIcon(loader, self.settings["icon"], KIconLoader.NoGroup, size)
        
        paint = QPainter(pix)
        paint.setRenderHint(QPainter.SmoothPixmapTransform)
        paint.setRenderHint(QPainter.Antialiasing)
        
        # Add indicators
        if self.error:
            over = KIconLoader.loadIcon(loader, self.package().path() + "contents/icons/errors.svg", KIconLoader.NoGroup, size/3, KIconLoader.DefaultState, "", "", True)
            paint.drawPixmap(size*0.66,size*0.66,over)
        elif self.disconnected:
            over = KIconLoader.loadIcon(loader, self.package().path() + "contents/icons/disconnected.svg", KIconLoader.NoGroup, size/3, KIconLoader.DefaultState, "", "", True)
            paint.drawPixmap(size*0.66,size*0.66,over)
        elif self.paused:
            over = KIconLoader.loadIcon(loader, self.package().path() + "contents/icons/paused.svg", KIconLoader.NoGroup, size/3, KIconLoader.DefaultState, "", "", True)
            paint.drawPixmap(size*0.66,size*0.66,over)
        
        if self.TotalCount is not None and self.TotalCount != 0:
            # Set the font
            font = QFont(self.settings["textfont"])
            size = (pix.width() * self.settings["textsize"]) / 100
            font.setPixelSize(size)
            font.setBold(True)
            
            # Check if the font is too big
            fm = QFontMetrics(font)
            if fm.width(str(self.TotalCount)) > pix.width():
                if self.debug: print "[reddit-plasmoid] Resizing font"
                while fm.width(str(self.TotalCount)) > pix.width() and size > 0:
                    size = size - 1
                    font.setPointSize(size)
                    fm = QFontMetrics(font)
            
            paint.setFont(font)
            
            # Write the message count
            paint.setPen(QColor(self.settings["textcolor"]))
            paint.drawText(pix.rect(), Qt.AlignVCenter | Qt.AlignHCenter, str(self.TotalCount))
        
        paint.end()
        
        # Update the icon
        self.icon.setIcon(QIcon(pix))
        self.icon.update()
        
        if self.debug: print "[reddit-plasmoid] Done updateIcon"
    
    
    #
    # ---------- Actions ----------
    #
    
    def walletOpened(self, status):
        if self.debug: print "[reddit-plasmoid] Wallet opened"
            
        if status:
            # We first open the wallet again in a synchronous manner to avoid a bug in some distributions
            self.wallet = KWallet.Wallet.openWallet(KWallet.Wallet.LocalWallet(), 0, KWallet.Wallet.Synchronous)
            # Get passwords from wallet
            self.wallet.setFolder("reddit-plasmoid")
            for i in range(0, len(self.settings["accounts"])):
                passwd = QString()
                # FIXME: readPassword call changed in KDE 4.4
                try:
                    # New KDE 4.4 version
                    passwd = self.wallet.readPassword(self.settings["accounts"][i].username)[1]
                except:
                    self.wallet.readPassword(self.settings["accounts"][i].username, passwd)
                    
                self.settings["accounts"][i].setPasswd(unicode(passwd))
                self.settings["accountlist"][i]["passwd"] = unicode(passwd)
        
        # Now start checking for emails (if connected)
        if self.disconnected == False:
            self.checkMail()
    
    def iconClicked(self):
        if self.debug: print "[reddit-plasmoid] iconClicked"
        
        if len(self.settings["accounts"]) > 0:
            if self.settings["accounts"][0].data <> None and len(self.settings["accounts"][0].data) > 0:
                url = self.settings["accounts"][0].data[0].permalink
            else:
                url = "http://www.reddit.com"
        else:
            url = "http://www.reddit.com"
        
        # Replace '%u' with url
        cmd = unicode(self.settings["command"])
        cmd = cmd.replace("%u", url)
        if self.debug: print "[reddit-plasmoid] Run command: "+cmd
        KRun.runCommand(cmd, None)

    def contextualActions(self):
        # Add custom context menus
        newActions = []
        
        # Check Now action
        checkNow = QAction(KIcon("mail-receive"), i18n("Check email now"), self)
        self.connect(checkNow, SIGNAL("triggered()"), self.forceCheck)
        newActions.append(checkNow)
        
        # Pause checking
        if self.paused:
            pauseChecking = QAction(KIcon(self.package().path() + "contents/icons/play.svg"), i18n("Resume email checking"), self)
        else:
            pauseChecking = QAction(KIcon(self.package().path() + "contents/icons/paused.svg"), i18n("Pause email checking"), self)
        self.connect(pauseChecking, SIGNAL("triggered()"), self.pauseChecking)
        newActions.append(pauseChecking)
        
        
        # Show threads action
        # FIXME: Self.obj is a bit of a hack. QMenu needs a parent QWidget or the object gets destroyed.
        self.obj = QWidget()
        threadsAction = QAction(KIcon("zoom-in"), i18n("Threads..."), self)
        #threadsAction = QAction(KIcon(self.package().path() + "contents/icons/threads.svg"), "Threads...", self)
        threadsMenu = QMenu(self.obj)
        
        newActions.append(threadsAction)
        return newActions

    def forceCheck(self):
        # Check for mail then reset the timer
        self.checkMail()
    
    def pauseChecking(self):
        self.paused = not self.paused
        if self.paused:
            if self.debug: print "[reddit-plasmoid] Pausing email checking"
            self.timer.stop()
            self.updateIcon()
        else:
            if self.debug: print "[reddit-plasmoid] Resuming email checking"
            self.updateIcon()
            self.checkMail()
    
    #
    # ---------- Check Mail ----------
    #
    
    def sOut(self, s):
        # This is a helper function
        # NOTE: This function is only temporary and will be removed when
        #       a better method for diplaying the data is implemented.
        return unicode(s).replace(" ","&nbsp;")
    
    def checkMail(self):
        if self.debug: print "[reddit-plasmoid] Checking mail..."
        
        # Reset status indicators
        self.error = False
        #self.disconnected = False # %%% do we want to reset this here?
        
        # Output message if no accounts setup
        if len(self.settings["accounts"]) == 0:
            self.error = True
            self.setUserMessage(i18n("No Accounts"), i18n("Please configure some accounts to check."))
            if self.debug: print "[reddit-plasmoid] No accounts configured"
            self.updateIcon()
            
        # See if any accounts are still fetching
        fetching = False
        for ac in self.settings["accounts"]:
            if ac.fetching == True:
                if self.debug: print "[reddit-plasmoid] Account "+ac.username+" still fetching"
                fetching = True
        
        # Tell all accounts to fetch
        if not fetching:
            for ac in self.settings["accounts"]:
                ac.checkMail()
                # Reset the timer
                if self.paused == False:
                    self.timer.start(self.settings["pollinterval"] * 60000)
        
    def readAccountData(self, ac):
        # Check to see if other accounts are still fetching
        fetching = False
        for ac in self.settings["accounts"]:
            if ac.fetching == True:
                fetching = True
        
        if fetching:
            if self.debug: print "[reddit-plasmoid] At least one account is still fetching emails"
        else:
            # All accounts are done fetching
            if self.debug: print "[reddit-plasmoid] All fetching is complete"
            
            # Aggregate data from all accounts
            fullcount = 0
            newentries = []
            disp = ""
            msg = ""
            # Fire notification if there are new emails
            if len(newentries) <> 0:
                if len(newentries) == 1:
                    message = "<table><tr><td><b>"+i18n("From")+"</b>: </td><td>"+newentries[0]["authorname"]+"</td></tr><tr><td><b>"+i18n("Subject")+"</b>: </td><td>"+newentries[0]["subject"]+"</td></tr></table>"
                else:
                    message = i18np("You have <b>%1</b> new message.", "You have <b>%1</b> new messages.", len(newentries))
                if self.debug: print "[reddit-plasmoid] Fire new-mail-arrived notification"
                self.fireNotification("new-mail-arrived", message)
            
            # Fire notification if there were messages before, but now there are not
            if self.TotalCount <> None:
                if fullcount == 0 and self.TotalCount > 0:
                    if self.debug: print "[reddit-plasmoid] Fire no-unread-mail notification"
                    self.fireNotification("no-unread-mail", "No unread messages.")
                    

                # If there is only one account dispay the threads
                # FIXME: This display should be modified to look better
            disp = "<table>"
            ac = self.settings["accounts"][0]
            if ac.data <> None and len(ac.data) > 0:
                for entry in ac.data:
                    
                    disp += '<tr><td><p style="margin-left: 50px ; text-indent: -50px;">'+str(entry)+'</p></td></tr>'
            disp += "</table>"
            self.setUserMessage(i18n("Threads"), disp+msg)
            if len(msg) <> 0: self.error = True
            self.updateIcon()
            
    #
    # ---------- Notification ----------
    #
    
    def fireNotification(self, strType, strMessage=""):
        KNotification.event(strType,
                strMessage,
                QPixmap(self.settings["icon"]),
                None,
                KNotification.CloseOnTimeout,
                KComponentData("reddit-plasmoid", "reddit-plasmoid", KComponentData.SkipMainComponentRegistration)
                )
    
    #
    # ---------- Configuration ----------
    #
        
    def createConfigurationInterface(self, parent):
        # Settings page
        self.redditconfig = RedditConfig(self, self.settings)        
        p = parent.addPage(self.redditconfig, i18n("Accounts"))
        p.setIcon( KIcon(self.settings["icon"]) )
        
        self.connect(parent, SIGNAL("okClicked()"), self.configAccepted)
        self.connect(parent, SIGNAL("cancelClicked()"), self.configDenied)
        
        # Notifications page
        # FIXME: Find a way to load the notification configuration widget
        #notifyWidget = KNotifyConfigWidget()
        
            
    def isKDEVersion(self, a, b, c):
        return (version() >= (a << 16) + (b << 8) + c)
    
    def showConfigurationInterface(self):
        # KDE 4.4 and above
        if self.isKDEVersion(4,3,74):
            plasmascript.Applet.showConfigurationInterface(self)
            return
        
        # KDE 4.3
        cfgId = QString('%1settings%2script').arg(self.applet.id()).arg(self.applet.name())
        if KConfigDialog.showDialog(cfgId):
            return
        self.nullManager = KConfigSkeleton()
        self.dlg = KConfigDialog(None, cfgId, self.nullManager)
        self.dlg.setFaceType(KPageDialog.Auto)
        self.dlg.setWindowTitle(i18nc('@title:window', '%1 Settings', self.applet.name()))
        self.dlg.setAttribute(Qt.WA_DeleteOnClose, True)
        self.dlg.showButton(KDialog.Apply, False)
        self.connect(self.dlg, SIGNAL('finished()'), self.nullManager, SLOT('deleteLater()'))
        
        self.createConfigurationInterface(self.dlg)
        self.dlg.show() 
    
    def configAccepted(self):
        self.settings = self.redditconfig.exportSettings()
        if self.settings["debugoutput"] == 1:
            self.debug = True
        else:
            self.debug = False
            
        gc = self.config()
        
        # Write general items
        gc.writeEntry("icon", self.settings["icon"])
        gc.writeEntry("iconnone", self.settings["iconnone"])
        gc.writeEntry("pollinterval", str(self.settings["pollinterval"]))
        gc.writeEntry("checknetwork", str(self.settings["checknetwork"]))
        gc.writeEntry("fetchmechanism", self.settings["fetchmechanism"])
        gc.writeEntry("debugoutput", str(self.settings["debugoutput"]))
        gc.writeEntry("command", self.settings["command"])
        gc.writeEntry("textfont", self.settings["textfont"])
        gc.writeEntry("textsize", str(self.settings["textsize"]))
        gc.writeEntry("textcolor", self.settings["textcolor"])
                
        # Open kwallet (synchronous style)
        # NOTE: As above, the wid sent to the wallet is not correct.
        wallet = KWallet.Wallet.openWallet(KWallet.Wallet.LocalWallet(), 0)
        if wallet is not None:
            if not wallet.hasFolder("reddit-plasmoid"):
                wallet.createFolder("reddit-plasmoid")
            wallet.setFolder("reddit-plasmoid")
            
            # Create account array without passwords and save it to file

            ac = self.settings["account"]
            tmpac = ac.copy()
            tmpac["passwd"] = ""
            # Write passwords to wallet while going through list
            wallet.writePassword(ac["username"], ac["passwd"])
            gc.writeEntry("accountlist", pickle.dumps(tmpac))
        else:
            # KWallet disabled, save passwords to config file
            gc.writeEntry("accountlist", pickle.dumps(self.settings["accountlist"]))
        
        # Clean up
        wallet = None
        self.configDenied()
        
        # Convert accounts array into account objects
        self.createAccountObjects()
        
        # Reset the timer and check mail (if not paused)
        if not self.paused:
            self.checkMail()
        
        self.updateIcon()

    def configDenied(self):
        self.redditconfig.deleteLater()
        
    def createAccountObjects(self):
        if self.debug: print "[reddit-plasmoid] create account"
        acobj = Reddit(user_agent="reddit-plasmoid")
        self.settings["account"] = acobj
        # Note: Always connect when account object is created.
        #self.connect(acobj.getSingalObject(), SIGNAL("checkMailDone"), self.readAccountData)
        
    #
    # ---------- End Configuration ----------
    #
    
    def createDirectory(self, d):
        if not os.path.isdir(d):
            try:
                os.mkdir(d)
            except:
                print "[reddit-plasmoid] Problem creating directory: "+d
                
    
    def createNotifyrc(self, kdehome, vers):
        # Output the notifyrc file to the correct location
        print "[reddit-plasmoid] Outputting notifyrc file"
        
        # Create reddit-plasmoid directory if required
        self.createDirectory(kdehome+"share/apps/reddit-plasmoid")
        
        # File to create
        fn = kdehome+"share/apps/reddit-plasmoid/reddit-plasmoid.notifyrc"
        
        # File contents
        c = []
        c.append("[Global]\n")
        c.append("IconName=reddit-plasmoid\n")
        c.append("Comment=reddit plasmoid\n")
        c.append("Name=Reddit\n")
        c.append("\n")
        c.append("[Event/new-mail-arrived]\n")
        c.append("Name=New Mail Arrived\n")
        c.append("Name[fr]=Un nouveau message est arrivé\n")
        c.append("Name[pl]=Nowe wiadomości\n")
        c.append("Name[ru]=Пришла почта\n")
        c.append("Name[el]=Νέο μήνυμα προσήλθε\n")
        c.append("Name[sr]=Имате нову е-поруку\n")
        c.append("Name[de]=Neue Nachricht erhalten\n")
        c.append("Name[zh_TW]=新郵件抵達\n")
        c.append("Name[bg]=Имате нова поща\n")
        c.append("Name[es]=Tiene correo nuevo\n")
        c.append("Name[it]=Arrivo di un Nuovo Messaggio\n")
        c.append("Name[cs]=Přijmutí Nového Emailu\n")
        c.append("Name[uk]=Отримано нова пошта\n")
        c.append("Name[nl]=U heeft nieuwe mail\n")
        c.append("Name[pt_BR]=Novos e-mails disponíveis\n")
        c.append("Sound=KDE-Im-New-Mail.ogg\n")
        c.append("Action=Popup|Sound\n")
        c.append("\n")
        c.append("[Event/no-unread-mail]\n")
        c.append("Name=No Unread Mail\n")
        c.append("Name[fr]=Pas de messages non-lu\n")
        c.append("Name[pl]=Brak nieprzeczytanych wiadomości\n")
        c.append("Name[ru]=Нет новых писем\n")
        c.append("Name[el]=Κανένα Νέο Μήνυμα\n")
        c.append("Name[sr]=Нема непрочитаних е-порука\n")
        c.append("Name[de]=Keine ungelesenen Nachrichten\n")
        c.append("Name[zh_TW]=沒有未讀郵件\n")
        c.append("Name[bg]=Няма непрочетена поща\n")
        c.append("Name[es]=No tiene correo sin leer\n")
        c.append("Name[it]=Nessun Nuovo Messaggio\n")
        c.append("Name[cs]=Žádný Nepřečtený Email\n")
        c.append("Name[uk]=Нет не прочитаних повідомлень\n")
        c.append("Name[nl]=Geen Nieuwe Berichten\n")
        c.append("Name[pt_BR]=Sem e-mails não lidos\n")
        c.append("Action=None\n")
        
        # Write file
        try:
            f = open(fn,"w")
            f.writelines(c)
            f.close()
            # Update saved version
            gc = self.config()
            gc.writeEntry("reddit-plasmoid.notifyrc", vers["reddit-plasmoid.notifyrc"])
        except:
            print "[reddit-plasmoid] Problem writing to file: "+fn
            
 
def CreateApplet(parent):
    return redditplasmoid(parent)