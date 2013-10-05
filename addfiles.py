#! /usr/bin/python
# PyAddfiles - A utility to create HTML slide shows from photos written
# in Python
#
# This is free and unencumbered software released into the public domain.
# http://unlicense.org/
#
# Excuse me if my comments seem a bit verbose; I chose this project
# as an attempt to learn Python

# From the Tkinter package, which you may need to install separately
from Tkinter import *

# The Tkinter component to select files and directories
import tkFileDialog, tkColorChooser

# For simple dialogs: prompting the user for strings, etc
import tkSimpleDialog

# For message boxen
import tkMessageBox

# From the Python Image Library, which you need to install separately
import Image, ImageTk

# For manipulating directories:
import dircache

# Regular expressions, operating system and wildcard expansion modules
import re, os, fnmatch

# To copy files
import shutil

# For XML processing
import xml.dom.minidom
from xml.dom.minidom import getDOMImplementation

# In order to convert the Icons to .xbm files, I had to:
# >"c:\Program Files\ImageMagick-6.2.5-Q16\convert" down.GIF down.xbm

##############################################################################

version = 0.9
author = "Werner Stoop"
email = "wstoop@gmail.com"

# FIXME: Make these globals configurable through a Dialog, and save them in
# the XML file

RESIZE_WIDTH = 1024
RESIZE_HEIGHT = 900

HTML_IMG_MAX_WIDTH = 2000
HTML_IMG_MAX_HEIGHT = 2000

THUMB_WIDTH = 100
THUMB_HEIGHT = 100

THUMBS_PER_ROW = 10

HTML_BGCOLOR = "WHITE"
HTML_TEXT = "BLACK"
HTML_LINK = "GRAY" 
HTML_VLINK = "SILVER"

# The template for HTML output. Text between @ @ symbols are replaced by
# appropriate values
HTML_TEMPLATE = """
<HTML>
<HEAD>
<TITLE>@GROUPNAME@</TITLE>
<STYLE TYPE="text/css">
  BODY { font-family: sans-serif; background-color: @BGCOLOR@; color:@TEXT@}
  TABLE {border-style: none; border-width: 2px; padding: 5px; border-color: @TEXT@; width: 100%; }
  A:link { color: @LINK@ }
  A:visited { color: @VLINK@ }
  A:active { color: @TEXT@ }
#Header {	
	position  : fixed;	
	width : 100%;
	height : 30px;
	top : 0;
	left : 0;
	vertical-align: top;
}
#Content {	
	position : fixed;
	top : 35px;
	bottom : 35px;	
	left : 20px;
	right : 20px;
	overflow: none;	
	margin-left : 20px;
}
#Footer {
	position  : fixed;	
	width : 100%;
	height : 30px;
	top : auto;
	left : 0;
	bottom : 0; 
	vertical-align: bottom;	
}
</STYLE>
</HEAD>
<BODY>
	<DIV id="Header">
	<TABLE>
		<TR>
			<TD align="left"><A href="@PREVIOUSGROUP@">PREV GROUP</A></TD>
			<TD align="left"><A href="@PREVIOUS@">PREV</A></TD>
			<TD align="center"><A HREF="../../index.html#@ROWNAME@">INDEX</A></TD>
			<TD align="right"><A href="@NEXT@">NEXT</A></TD>
			<TD align="right"><A href="@NEXTGROUP@">NEXT GROUP</A></TD>
		</TR>
	</TABLE>
	</DIV>
	<DIV id="Content">
	<TABLE>
		<TR>
			<TD align="Center">
				<A href="@NEXT@"><IMG @IMAGESIZE@ src="@IMAGE@"></A>
			</TD>
		</TR>	
	</TABLE>	
	</DIV>
	<DIV id="Footer">
	<TABLE>
		<TR>
			<TD align="left"><A href="@PREVIOUSGROUP@">PREV GROUP</A></TD>
			<TD align="left"><A href="@PREVIOUS@">PREV</A></TD>
			<TD align="center"><A HREF="../../index.html#@ROWNAME@">INDEX</A></TD>
			<TD align="right"><A href="@NEXT@">NEXT</A></TD>
			<TD align="right"><A href="@NEXTGROUP@">NEXT GROUP</A></TD>
		</TR>
	</TABLE>
	</DIV>
</BODY>
</HTML>
"""

##############################################################################

def isImageFile(filename):
	"""Checks a file extension with a regular expression 
	to see whether it's a graphics file"""
	# FIXME: Is there a better way to do this?
	if re.compile(r"\.(bmp|jpe?g|gif)$").search(filename) != None:
		return True
	return False
	
def relpath(ffrom, fto):
	"""
	Returns the relative path from a file 'ffrom' to a file 'fto'
	For example:
		relpath('C:/temp/foo/a/c/foo.txt', 'C:/temp/foo/b/foo.txt')
	returns
		"..\..\b"
		
	It has a couple of known bugs. Both:
		relpath('C:/temp/foo/a/c/foo.txt', 'C:/tempx/foo/b/foo.txt')
	and 
		relpath('C:/temp/foo/a/c/foo.txt', 'D:/temp/foo/b/foo.txt')
	will return incorrect results
	"""
	x1 = ffrom.replace("\\", "/").split("/")
	x2 = fto.replace("\\", "/").split("/")
	del x1[-1]
	del x2[-1]
	while len(x1) > 0 and len(x2) > 0 and x1[0] == x2[0]:
		del x1[0]
		del x2[0]
	
	s = "../" * len(x1) + "/".join(x2)
	if len(x2) > 0:
		s = s + "/"
	if s.find("../") == 0:
		return s
	return "./" + s
	
def recdir(path, pattern="*"):
	"""
	Recursively runs down all the subdirectories in 'path' and returns a
	list of all the files that matches the specified 'pattern' (which is
	a fnmatch()-type pattern)
	"""
	dir = []
	for i in os.listdir(path):
		name = os.path.join(path,i)
		if os.path.isdir(name):
			dir.extend(recdir(name, pattern))
		elif fnmatch.fnmatch(i, pattern):
			dir.append(os.path.normpath(name))
	return dir

##############################################################################

class ImageItem:
	def __init__(self, name, path):
		self.name = name
		self.path = path

	def getName(self):
		return self.name
		
	def getPath(self):
		return self.path
		
##############################################################################

class Group:
	def __init__(self, name):
		self.images = []
		self.name = name
		self.thumbnail = None
		
	def getImages(self):
		return self.images	

	def getName(self):
		return self.name
		
	def setName(self, newName):
		self.name = newName
		
	def getThumbnail(self):
		return self.thumbnail
		
	def setThumbnail(self, tn):
		self.thumbnail = tn
		
	def addItem(self, name, path):
		self.images.append(ImageItem(name,path))		
		
	def addImageItem(self, item):
		self.images.append(item)
		
	def getItem(self, name):
		for i in self.images:
			if i.getName() == name:
				return i
		return None
	
	def getItemByIndex(self, index):
		return self.images[index]
		
	def removeItem(self, index):
		return self.images.pop(index)	
		
	def getFirst(self):
		if len(self.images) > 0:
			return self.images[0].getPath()
		return None
	
	def getItemNames(self):
		n = []
		for i in self.images:
			n.append(i.getName())
		return n
		
	def toXml(self, doc, element, filename):
		if self.thumbnail != None:
			(d,f) = os.path.split(self.thumbnail)
			tnpath = relpath(os.path.realpath(filename), os.path.realpath(self.thumbnail)) + f			
			tnpath = os.path.normpath(tnpath)
			element.setAttribute("thumbnail", tnpath)
			
		for i in self.images:
			ie = doc.createElement("image")
			ie.setAttribute("name", i.getName())
			path = i.getPath()
			ie.setAttribute("path", relpath(filename, path))
			element.appendChild(ie)
		
	def fromXML(self, element, relpath):
		if element.hasAttribute("thumbnail"):
			self.thumbnail = os.path.join(relpath, element.getAttribute("thumbnail"))
			
		for g in element.getElementsByTagName("image"):
			name = g.getAttribute("name")
			filepath = g.getAttribute("path") + name
			path = os.path.normpath(os.path.join(relpath, filepath))			
			self.addItem(name,path)
			
groups = []
		
def addGroup(name):
	g = Group(name)
	groups.append(g)
	return g
	
def removeGroup(index):
	return groups.pop(index)
	
def renameGroup(index, newname):
	groups[index].setName(newname)	

def getGroup(name):
	for group in groups:
		if group.getName() == name:
			return group
	return None
	
def getGroupnames():
	"""Returns a list of all the groups' names"""
	x = []
	for i in groups:
		x.append(i.getName())
	return x
	
def groupExist(name):
	for i in groups:
		if i.getName() == name:
			return True
	return False

##############################################################################

# The configuration dialog extends the class tkSimpleDialog.Dialog and
# overloads its body() and apply() methods:
# body() is used to layout the dialog
# apply gets called when the user clicks OK
class ConfigDialog(tkSimpleDialog.Dialog):

	def body(self, top):
		row_num = 0
		Label(top,text="Resize").grid(row=row_num,column=0,columnspan=2,sticky=E+W)
		row_num = row_num + 1
		Label(top,text="Width").grid(row=row_num,column=0)
		self.resize_w = Entry(top)
		self.resize_w.insert(END,RESIZE_WIDTH)
		self.resize_w.grid(row=row_num,column=1)
		row_num = row_num + 1
		Label(top,text="Height").grid(row=row_num,column=0)
		self.resize_h = Entry(top)
		self.resize_h.insert(END,RESIZE_HEIGHT)
		self.resize_h.grid(row=row_num,column=1)
		row_num = row_num + 1
		
		Label(top,text="HTML imagesize").grid(row=row_num,column=0,columnspan=2,sticky=E+W)
		row_num = row_num + 1
		Label(top,text="Width").grid(row=row_num,column=0)
		self.html_img_w = Entry(top)
		self.html_img_w.insert(END,HTML_IMG_MAX_WIDTH)
		self.html_img_w.grid(row=row_num,column=1)
		row_num = row_num + 1
		Label(top,text="Height").grid(row=row_num,column=0)
		self.html_img_h = Entry(top)
		self.html_img_h.insert(END,HTML_IMG_MAX_HEIGHT)
		self.html_img_h.grid(row=row_num,column=1)
		row_num = row_num + 1
		
		Label(top,text="Thumbnails").grid(row=row_num,column=0,columnspan=2,sticky=E+W)
		row_num = row_num + 1
		Label(top,text="Width").grid(row=row_num,column=0)
		self.thumbnail_w = Entry(top)
		self.thumbnail_w.insert(END,THUMB_WIDTH)
		self.thumbnail_w.grid(row=row_num,column=1)
		row_num = row_num + 1
		Label(top,text="Height").grid(row=row_num,column=0)
		self.thumbnail_h = Entry(top)
		self.thumbnail_h.insert(END,THUMB_HEIGHT)
		self.thumbnail_h.grid(row=row_num,column=1)		
		row_num = row_num + 1
		Label(top,text="Columns").grid(row=row_num,column=0)
		self.thumbnail_cols = Entry(top)
		self.thumbnail_cols.insert(END,THUMBS_PER_ROW)
		self.thumbnail_cols.grid(row=row_num,column=1)
		row_num = row_num + 1
		
		Label(top,text="HTML Colours").grid(row=row_num,column=0,columnspan=2,sticky=E+W)
		row_num = row_num + 1
		Label(top,text="BGCOLOR").grid(row=row_num,column=0)
		self.bgcolor = Entry(top)
		self.bgcolor.insert(END,HTML_BGCOLOR)
		self.bgcolor.grid(row=row_num,column=1)
		Button(top,text="...",command=self.setBgColor).grid(row=row_num,column=2)
		row_num = row_num + 1
		Label(top,text="TEXT").grid(row=row_num,column=0)
		self.text = Entry(top)
		self.text.insert(END,HTML_TEXT)
		self.text.grid(row=row_num,column=1)
		Button(top,text="...",command=self.setText).grid(row=row_num,column=2)
		row_num = row_num + 1
		Label(top,text="LINK").grid(row=row_num,column=0)
		self.link = Entry(top)
		self.link.insert(END,HTML_LINK)
		self.link.grid(row=row_num,column=1)
		Button(top,text="...",command=self.setLink).grid(row=row_num,column=2)
		row_num = row_num + 1
		Label(top,text="VLINK").grid(row=row_num,column=0)
		self.vlink = Entry(top)
		self.vlink.insert(END,HTML_VLINK)
		self.vlink.grid(row=row_num,column=1)
		Button(top,text="...",command=self.setVlink).grid(row=row_num,column=2)
		row_num = row_num + 1
				
		return self.resize_w
		
	def setBgColor(self):
		(col, HTML) = tkColorChooser.askcolor()
		if HTML == None:
			return
		self.bgcolor.delete(0,END)
		self.bgcolor.insert(END,HTML)
		
	def setText(self):
		(col, HTML) = tkColorChooser.askcolor()
		if HTML == None:
			return
		self.text.delete(0,END)
		self.text.insert(END,HTML)
		
	def setLink(self):
		(col, HTML) = tkColorChooser.askcolor()
		if HTML == None:
			return
		self.link.delete(0,END)
		self.link.insert(END,HTML)
		
	def setVlink(self):
		(col, HTML) = tkColorChooser.askcolor()
		if HTML == None:
			return
		self.vlink.delete(0,END)
		self.vlink.insert(END,HTML)
		
	def apply(self): 
		
		# These variables must be declared global in order to assign to them
		global RESIZE_WIDTH, RESIZE_HEIGHT, THUMB_WIDTH, THUMB_HEIGHT, \
			HTML_BGCOLOR, HTML_TEXT, HTML_LINK, HTML_VLINK, THUMBS_PER_ROW, \
			HTML_IMG_MAX_WIDTH, HTML_IMG_MAX_HEIGHT
		
		RESIZE_WIDTH = int(self.resize_w.get())
		RESIZE_HEIGHT = int(self.resize_h.get())
		
		HTML_IMG_MAX_WIDTH = int(self.html_img_w.get())
		HTML_IMG_MAX_HEIGHT = int(self.html_img_h.get())
		
		THUMB_WIDTH = int(self.thumbnail_w.get())
		THUMB_HEIGHT = int(self.thumbnail_h.get())
		THUMBS_PER_ROW = int(self.thumbnail_cols.get())
		
		HTML_BGCOLOR = self.bgcolor.get()
		HTML_TEXT = self.text.get()
		HTML_LINK = self.link.get()
		HTML_VLINK = self.vlink.get()
		
##############################################################################

class HelpDialog:

	def __init__(self, parent):
		top = self.top = Toplevel(parent)
		
		scrollbar = Scrollbar(top)
		scrollbar.pack(side=RIGHT, fill=Y)
		
		self.t = Text(top,yscrollcommand=scrollbar.set,wrap=WORD)
		self.t.pack(padx=5,pady=5)
		
		scrollbar.config(command=self.t.yview)
		
		b = Button(top, text="OK", command=self.ok)
		b.pack(pady=5)

		width = int(self.t.cget('width'))
		
		f = open(os.path.join(appPath,'help.txt'), 'r')			
		txt = f.read()
		
		self.t.insert(END, txt)		
		self.t.config(state=DISABLED)
		
	def ok(self):		
		self.top.destroy()
		
##############################################################################

class Application(Frame):
	def __init__(self, master=None):
		"""Constructor for the application"""
		Frame.__init__(self, master)
		
		# This sets the Application to sticky within the top-level window
		# (if the sticky=N+S+E+W is not specified, the window will not 
		# resize correctly)
		self.grid(sticky=N+S+E+W)
		
		self.createWidgets()
		self.canvas_item = None
		
		# There must always be a default group
		addGroup("Default")		
		
		# Set the working directory - We must use absolute paths internally
		self.setDir(os.getcwd())
		
		# The name of the file we're working with (from Open and SaveAs)
		self.currentFileName = None
		
		# The name of the file being displayed in th
		self.displayedFile = None
		
		# The currently selected Group object
		self.selectedGroup = None
		
		# These are used to track the user's selection in the various list boxes
		self.currentFile = None
		self.oldFiles = None
		self.oldGroupFiles = None		
		self.currentGroupFile = None
		self.currentGroup = None
		
		self.poll() # Start polling the Listboxes (see Lundh's Tkinter tutorial)
		
		self.lastFileIndex = None
		
		self.refreshGroupList()	
		self.grouplist.select_set(0) # Select the "Default" group
		
		self.generating = False
		
		self.filterOn = False
		
		self.allFiles = dict()
				
	def createWidgets(self):		
		"""Lays ou the Widgets"""

		self.dirButton = Button(self, text=os.getcwd(),command=self.changeDir,takefocus=0)
		self.dirButton.grid(row=0,column=0,columnspan=4,sticky=E+W)
		
		scrollbar = Scrollbar(self)
		scrollbar.grid(row=1,rowspan=5,column=3,sticky=N+S+W)
		# The yscrollcommand=scrollbar.set below makes the Listbox use the scrollbar when it changes
		self.filelist = Listbox(self, yscrollcommand=scrollbar.set,exportselection=0,selectmode=EXTENDED)
		self.filelist.grid(row=1,rowspan=5,column=0,columnspan=3,sticky=E+W+N+S)
		
		# The "sticky=E+W+N+S" causes the widget ('filelist') to span the entire cell
		# Tell the scrollbar to call self.filelist.yview when it changes
		scrollbar.config(command=self.filelist.yview)
		
		Label(self, text="Rotate").grid(row=0,column=4,sticky=E+W)
		Button(self, bitmap="@%s" % os.path.join(appPath, "back.xbm"),command=self.fileLeft,takefocus=0).grid(row=1,column=4,sticky=N+E+W)
		Button(self, bitmap="@%s" % os.path.join(appPath, "forward.xbm"),command=self.fileRight,takefocus=0).grid(row=2,column=4,sticky=N+E+W)
		
		Button(self, text="Add",command=self.addFile,takefocus=0).grid(row=6,column=0,columnspan=2,sticky=E+W)
		Button(self, text="Remove",command=self.remFile,takefocus=0).grid(row=6,column=2,columnspan=2,sticky=E+W)
		
		Label(self, text="Group").grid(row=7,column=0,columnspan=3,sticky=W)
		scrollbar = Scrollbar(self)
		scrollbar.grid(row=8,rowspan=4,column=3,sticky=N+S+W)
		self.groupfilelist = Listbox(self, yscrollcommand=scrollbar.set,exportselection=0,selectmode=EXTENDED)
		self.groupfilelist.grid(row=8,rowspan=4,column=0,columnspan=3,sticky=E+W+N+S)
		scrollbar.config(command=self.groupfilelist.yview)
				
		Button(self, bitmap="@%s" % os.path.join(appPath, "up.xbm"),command=self.itemUp,takefocus=0).grid(row=8,column=4,sticky=N+E+W)
		Button(self, bitmap="@%s" % os.path.join(appPath, "down.xbm"),command=self.itemDown,takefocus=0).grid(row=9,column=4,sticky=N+E+W)		
		
		Label(self, text="Thumbnail").grid(row=12,column=0,sticky=W)		
		self.thumbnailButton = Button(self, text="None",command=self.setThumbnail,takefocus=0)
		self.thumbnailButton.grid(row=12,column=2,sticky=E+W)
		Button(self, text="Clear",command=self.delThumbnail,takefocus=0).grid(row=12,column=3,sticky=E+W)
		
		Label(self, text="Groups").grid(row=7,column=6,columnspan=3,sticky=W)
		scrollbar = Scrollbar(self)
		scrollbar.grid(row=8,rowspan=4,column=9,sticky=N+S+W)
		self.grouplist = Listbox(self, yscrollcommand=scrollbar.set,exportselection=0,selectmode=EXTENDED)
		self.grouplist.grid(row=8,rowspan=4,column=6,columnspan=3,sticky=E+W+N+S)
		scrollbar.config(command=self.grouplist.yview)
				
		Button(self, bitmap="@%s" % os.path.join(appPath, "up.xbm"),command=self.groupUp,takefocus=0).grid(row=8,column=5,sticky=N+E+W)
		Button(self, bitmap="@%s" % os.path.join(appPath, "down.xbm"),command=self.groupDown,takefocus=0).grid(row=9,column=5,sticky=N+E+W)
		
		Button(self, text="Add",command=self.groupAdd,takefocus=0).grid(row=8,column=10,sticky=N+E+W)
		Button(self, text="Remove",command=self.groupRemove,takefocus=0).grid(row=9,column=10,sticky=N+E+W)		
		Button(self, text="Rename",command=self.groupRename,takefocus=0).grid(row=10,column=10,sticky=N+E+W)		
		
		self.sizeLabel = Label(self, text="?x?",width=10)
		self.sizeLabel.grid(row=6,column=6,sticky=W)
		self.resizeButton=Button(self, text="Resize To Fit",command=self.fileResize)
		self.resizeButton.grid(row=6,column=7,sticky=E+W)
		self.resizeWidth = Entry(self,width=5)
		self.resizeWidth.grid(row=6,column=8,sticky=E+W)
		self.resizeWidth.insert(END,RESIZE_WIDTH)
		self.resizeHeight = Entry(self,width=5)
		self.resizeHeight.grid(row=6,column=9,sticky=E+W)		
		self.resizeHeight.insert(END,RESIZE_HEIGHT)
				
		# The canvas where the results are displayed.
		self.canvas = Canvas(self,borderwidth=2,relief=SUNKEN)
		self.canvas.grid(row=0,rowspan=6,column=5,columnspan=6,sticky=E+W+N+S)
		
		self.progressLabel = Label(self, text="Ready")
		self.progressLabel.grid(row=12,column=10,sticky=E+W)
		self.progress = Label(self, bitmap="@%s" % os.path.join(appPath, "pie0.xbm"))
		self.progress.grid(row=12,column=9,sticky=N+E+W)
		
		self.restoreButton = Button(self, text="Restore",command=self.restoreBackup)
		self.restoreButton.grid(row=6,column=10,sticky=E+W)
						
		# Add a menubar with "File", "Tools" and "Help" menus, each with 
		# their own submenus
		menubar = Menu(self)
		filemenu = Menu(menubar,tearoff=0)
		filemenu.add_command(label="New", command=self.new)
		filemenu.add_separator()
		filemenu.add_command(label="Open", command=self.open)
		filemenu.add_command(label="Save", command=self.save)
		filemenu.add_command(label="Save As", command=self.saveAs)
		filemenu.add_separator()
		filemenu.add_command(label="Generate HTML", command=self.generateHTML)
		filemenu.add_command(label="Configuration", command=self.configure)		
		filemenu.add_separator()
		filemenu.add_command(label="Exit", command=self.quit)
		menubar.add_cascade(label="File", menu=filemenu)				
		extramenu = Menu(menubar,tearoff=0)		
		extramenu.add_command(label="Filter", command=self.filter)
		extramenu.add_command(label="unFilter", command=self.unFilter)	
		extramenu.add_separator()		
		extramenu.add_command(label="Merge Groups", command=self.mergeGroups)
		extramenu.add_separator()		
		extramenu.add_command(label="Remove Backups", command=self.removeBackups)		
		extramenu.add_command(label="Wipe Groups", command=self.wipeGroups)
		extramenu.add_separator()
		extramenu.add_command(label="Statistics", command=self.statistics)
		menubar.add_cascade(label="Tools", menu=extramenu)
		helpmenu = Menu(menubar,tearoff=0)
		helpmenu.add_command(label="Help", command=self.help)
		helpmenu.add_command(label="About", command=self.about)
		menubar.add_cascade(label="Help", menu=helpmenu)
		self.master.config(menu=menubar)
		
		# This is my attempt to get it stretching properly
		top=self.winfo_toplevel()
		top.rowconfigure(0, weight=1)
		top.columnconfigure(0, weight=1)
		for i in range(11):
			self.columnconfigure(i, weight=1)
			self.rowconfigure(i, weight=1)
		
	def poll(self):
		"""Checks the Listboxes for changes - ask Lundh"""	
		x = self.filelist.curselection()
		if x != self.currentFile:
			self.fileSelected(x)
			self.currentFile = x
			self.filelist.focus_set()
			
		x = self.grouplist.curselection()
		if x != self.currentGroup:
			self.groupSelected(x)
			self.currentGroup = x
			self.grouplist.focus_set()		
			
		x = self.groupfilelist.curselection()
		if x != self.currentGroupFile:
			self.groupFileSelected(x)
			self.currentGroupFile = x
			self.groupfilelist.focus_set()
							
		self.after(250, self.poll)

	def fileSelected(self, selectedfiles):	
		"""Action for when a File is selected"""
		delta = []
		
		# Determine which files are in the new selection that were not in
		# the old one
		if self.oldFiles != None:
			delta = list(set(selectedfiles) - set(self.oldFiles))		
			
			if len(delta) == 0:
				# This happens when several files are selected and
				# the user then clicks on a file in the selection
				delta = list(selectedfiles)
				
			delta.sort(lambda x,y: int(x) - int(y))			
			
		self.oldFiles = selectedfiles	
		
		last = None
		for i in delta:
			last = self.filelist.get(i)	
			self.lastFileIndex = i
		
		if last == None:
			return
			
		self.showImage(self.currentDir + last)
					
	def groupSelected(self, selectedgroup):
		"""Action for when a group is selected"""
				
		if len(selectedgroup) > 1:
			return
		elif len(selectedgroup) < 1:
			print "No groups selected"
			return
		i = list(selectedgroup)[0]
		name = self.grouplist.get(i)	
				
		self.selectedGroup = getGroup(name)
		if self.selectedGroup == None:
			return
		
		first = self.selectedGroup.getFirst()
		if first != None:
			self.showImage(first)
		else:
			self.clearCanvas()
		
		self.refreshGroupView()
		
		if self.selectedGroup.getThumbnail() != None:
			(d,f) = os.path.split(self.selectedGroup.getThumbnail())
			self.thumbnailButton.config(text=f)
		else:
			self.thumbnailButton.config(text="None")
	
	def groupFileSelected(self, selectedgroupfile):
		"""Action for when a file in a group is selected"""
		if self.currentGroup == None:
			print "No group"
			return
			
		delta = []
		
		# Determine which files are in the new selection that were not in
		# the old one
		if self.oldGroupFiles != None:
			delta = list(set(selectedgroupfile) - set(self.oldGroupFiles))		
			
			if len(delta) == 0:
				# This happens when several files are selected and
				# the user then clicks on a file in the selection
				delta = list(selectedgroupfile)
				
			delta.sort(lambda x,y: int(x) - int(y))			
			
		self.oldGroupFiles = selectedgroupfile	
		
		last = -1
		for i in delta:
			last = int(i)
		
		if last == -1:
			return	
			
		if self.selectedGroup != None:
			item = self.selectedGroup.getItemByIndex(last)
			self.showImage(item.getPath())
		else:
			self.clearCanvas()
			
	def configure(self):
	
		# Don't allow configuration while we're generating HTML
		if self.generating:
			print "Already generating"
			return
		# Show the configuration dialog
		d = ConfigDialog(self)

	def help(self):
		d = HelpDialog(self)
		self.wait_window(d.top)
		
	def about(self):
		tkMessageBox.showinfo("About", "PyAddfiles %.2f\nAuthor: %s\nEmail: %s" % (version, author, email))
		
	def changeDir(self):
		dirname = tkFileDialog.askdirectory(parent=self,initialdir=".",title='Please select a directory')
		if len(dirname) <= 0:
			return
			
		dirname = os.path.realpath(dirname)
			
		self.setDir(dirname)
		
		self.currentFile = None
		self.oldFiles = None
		
		self.filter()
		
	def setDir(self, dirname):	
	
		dirname = os.path.realpath(dirname)
		
		self.listdir = dircache.listdir(dirname)
		self.filelist.delete(0, END) # Delete all items in the list
		for item in self.listdir:
			if isImageFile(item):
				self.filelist.insert(END, item) 
		self.currentDir = dirname + '/'		
		os.chdir(dirname)
		self.dirButton.config(text=dirname)
	
	def removeBackups(self):
		if not tkMessageBox.askyesno("Continue","This operation cannot be undone.\nAre you sure?"):
			return
		files = recdir(self.currentDir, "*~")
		for f in files:			
			print "Deleting %s" % (f,)
			os.remove(f)
		print "DONE"
			
	def statistics(self):
		count = 0
		for gr in groups:
			for it in gr.images:
				count = count + 1
		tkMessageBox.showinfo("Statistics", "%d items in %d groups" % (count, len(groups)))		
	
	def clear(self):	
		del groups[:]		
		self.groupfilelist.delete(0, END)
		self.clearCanvas()
		
		# Reset the working file
		self.currentFileName = None
		
		# Unselect anything that may be selected
		self.currentFile = None
		self.oldFiles = None
		self.oldGroupFiles = None		
		self.currentGroupFile = None
		self.currentGroup = None			
			
	def new(self):
		self.clear()
		addGroup("Default")
		self.refreshGroupList()	
		self.grouplist.select_set(0)
		
	def open(self):		
		
		# Note that askopenfile() returns the opened file, but
		# tkFileDialog has an askopenfilename() method as well
		file = tkFileDialog.askopenfile(parent=self,mode='r',title='Choose a file',filetypes=[('XML files','*.xml'),('All files','*.*')])
		self.openFile(file)
		
	def openFile(self, file):
		# These variables must be declared global in order to assign to them
		global RESIZE_WIDTH, RESIZE_HEIGHT, THUMB_WIDTH, THUMB_HEIGHT, \
			HTML_BGCOLOR, HTML_TEXT, HTML_LINK, HTML_VLINK, THUMBS_PER_ROW, \
			HTML_IMG_MAX_WIDTH, HTML_IMG_MAX_HEIGHT
		
		if file != None:
			try:
				relpath = os.path.dirname(os.path.realpath(file.name))
				self.clear()
				dom = xml.dom.minidom.parse(file)
				
				print "OPEN A: %s %s %s" % (file.name, os.path.realpath(file.name), relpath)
				print "OPEN B: %s %s %s" % (file.name, os.path.abspath(file.name), os.path.dirname(os.path.abspath(file.name)))
				
				el = dom.getElementsByTagName("AddFiles")[0]
				
				if len(el.getElementsByTagName("resize")) > 0:				
					params = el.getElementsByTagName("resize")[0]
					RESIZE_WIDTH = int(params.getAttribute("width"))
					self.resizeWidth.delete(0,END)
					self.resizeWidth.insert(END,RESIZE_WIDTH)
					RESIZE_HEIGHT = int(params.getAttribute("height"))
					self.resizeHeight.delete(0,END)				
					self.resizeHeight.insert(END,RESIZE_HEIGHT)
				else:
					print("No <resize/> parameters")					
					
				if len(el.getElementsByTagName("img_size")) > 0:				
					params = el.getElementsByTagName("img_size")[0]
					HTML_IMG_MAX_WIDTH = int(params.getAttribute("width"))
					HTML_IMG_MAX_HEIGHT = int(params.getAttribute("height"))
				else:
					print("No <img_size/> parameters")
					
				if len(el.getElementsByTagName("thumbnails")) > 0:				
					params = el.getElementsByTagName("thumbnails")[0]
					THUMB_WIDTH = int(params.getAttribute("width"))
					THUMB_HEIGHT = int(params.getAttribute("height"))
					THUMBS_PER_ROW = int(params.getAttribute("thumbs_per_row"))
				else:
					print("No <thumbnail/> parameters")
					
				if len(el.getElementsByTagName("html")) > 0:				
					params = el.getElementsByTagName("html")[0]
					HTML_BGCOLOR = params.getAttribute("bgcolor")
					HTML_TEXT = params.getAttribute("text")
					HTML_LINK = params.getAttribute("link")
					HTML_VLINK = params.getAttribute("vlink")
				else:
					print("No <html/> parameters")				
				
				for g in el.getElementsByTagName("group"):
					name = g.getAttribute("name")
					gp = addGroup(name)
					gp.fromXML(g, relpath)				
				self.currentFileName = file.name
				file.close()
				self.refreshGroupList()
				self.setDir(relpath)
				
				self.allFiles = dict()
				for g in groups:		
					for item in g.getImages():
						self.trackFile(item.getPath())
				#print "@@ OPEN: self.allFiles: %s" % (self.allFiles.keys(),)
				
			except IOError:
				tkMessageBox.showerror("Error", "Unable to load %s" % (file.name,))
		else:
			print "No file selected"
	
	def trackFile(self, name):
		if name in self.allFiles:
			self.allFiles[name] = self.allFiles[name] + 1
		else:
			self.allFiles[name] = 1
	
	def untrackFile(self, name):
		if name not in self.allFiles:
			print "Assertion failure: %s not in self.allFiles" % (name,)
			return 
		self.allFiles[name] = self.allFiles[name] - 1
		if self.allFiles[name] == 0:
			self.allFiles.pop(name)
				
	def save(self):		
		if self.currentFileName == None:
			self.saveAs()
		else:
			self.saveXML(self.currentFileName)
			
	def saveAs(self):
		fileName = tkFileDialog.asksaveasfilename(filetypes=[('XML files','*.xml'),('All files','*.*')])
		if len(fileName ) > 0:
			self.saveXML(fileName)
		
	def saveXML(self, filename):
		impl = getDOMImplementation()
		newdoc = impl.createDocument(None, "AddFiles", None)
		top_element = newdoc.documentElement
		
		comment = newdoc.createComment(' This file was generated by the PyAddfiles tool ')		
		top_element.appendChild(comment)
		
		el = newdoc.createElement("resize")
		el.setAttribute("width", str(RESIZE_WIDTH))
		el.setAttribute("height", str(RESIZE_HEIGHT))
		top_element.appendChild(el)
		
		el = newdoc.createElement("img_size")
		el.setAttribute("width", str(HTML_IMG_MAX_WIDTH))
		el.setAttribute("height", str(HTML_IMG_MAX_HEIGHT))
		top_element.appendChild(el)
		
		el = newdoc.createElement("thumbnails")
		el.setAttribute("width", str(THUMB_WIDTH))
		el.setAttribute("height", str(THUMB_HEIGHT))
		el.setAttribute("thumbs_per_row", str(THUMBS_PER_ROW))
		top_element.appendChild(el)
		
		el = newdoc.createElement("html")
		el.setAttribute("bgcolor", str(HTML_BGCOLOR))
		el.setAttribute("text", str(HTML_TEXT))
		el.setAttribute("link", str(HTML_LINK))
		el.setAttribute("vlink", str(HTML_VLINK))
		top_element.appendChild(el)
		
		for g in groups:
			ge = newdoc.createElement("group")
			ge.setAttribute("name", g.getName())
			
			g.toXml(newdoc, ge, filename)
			top_element.appendChild(ge)
		
		file = open(filename, 'w')
		file.write(newdoc.toprettyxml())
		file.close()
		self.currentFileName = filename
		
	def generateHTML(self):
	
		if self.generating:
			print "Already generating"
			return
		
		self.progressLabel.configure(text="Starting")	
		self.progress.configure(bitmap="@%s" % os.path.join(appPath, "pie0.xbm"))
			
		dirname = tkFileDialog.askdirectory(parent=self,initialdir=".",title='Please select a output directory')
		if len(dirname) <= 0:
			return			
		mydir = os.getcwd()
		
		dirname = os.path.realpath(dirname)
		os.chdir(dirname)
		
		self.generating = True
		
		count = 0
		for g in groups:
			for item in g.getImages():
				count = count + 1					
				
		ihtml = """<HTML>\n<HEAD>\n\t<TITLE>Index</TITLE>
	<STYLE TYPE="text/css">
	DIV.Overall{ text-align:center; margin: 0 auto; padding:0}
	DIV.RowDiv { border: none; margin: 5px; vertical-align: middle; display: inline-block; }
	DIV.ImgDiv { display: inline-block;width: %dpx} 
	IMG { border:none; padding: 5px 15px 5px 15px;}
	</STYLE>\n</HEAD>\n""" % (THUMB_WIDTH + 10,)
		ihtml = ihtml + "<BODY BGCOLOR=\"%s\" TEXT=\"%s\" LINK=\"%s\" VLINK=\"%s\">\n" % (HTML_BGCOLOR, HTML_TEXT, HTML_LINK, HTML_VLINK)
		
		c = 0
		i = 0
		
		rownum=1;
		
		lastg = len(groups)-1
		
		ihtml = ihtml + "<DIV class=\"Overall\">\n"
		ihtml = ihtml + "\t<DIV class=\"RowDiv\"><A name=\"Row_%d\"/>\n" % (rownum,)
		for g in groups:		
			
			groupdir = "%d" % (int(i/1000))
			groupsubdir = "%d" % (int((i%1000) / 100))
			
			if not os.path.exists(groupdir):
				os.mkdir(groupdir)
			grouppath = os.path.join(groupdir, groupsubdir)
			if not os.path.exists(grouppath):
				os.mkdir(grouppath)
		
			link = "%s/%s/g%d_p0.html" % (groupdir, groupsubdir, i)
								
			items = g.getImages()
			if len(items) == 0:
				print "Skipping group %s; no contents" % (g.getName(),)
				continue
			
			last = len(items) - 1
		
			if i == lastg:
				nextg = "g0_p0.html"
			else:
				nextg = "g%d_p0.html" % (i+1,)
			if i == 0:
				prevg = "g%d_p0.html" % (lastg,)
			else:
				prevg = "g%d_p0.html" % (i-1,)
				
			prevgroupprefix = "../../%d/%d/" % (int((i-1)/1000), int(((i-1)%1000) / 100))
			nextgroupprefix = "../../%d/%d/" % (int((i+1)/1000), int(((i+1)%1000) / 100))
					
			nextg = nextgroupprefix + nextg
			prevg = prevgroupprefix + prevg
			
			j = 0
			for item in items:
				groupname = g.getName()
				image = relpath(dirname + '/index.html', item.getPath()) + "/" + item.getName()
				if j == last:
					next = "g%d_p0.html" % (i,)
				else:
					next = "g%d_p%d.html" % (i,j+1)
				if j == 0:
					prev = "g%d_p%d.html" % (i,last)
				else:
					prev = "g%d_p%d.html" % (i,j-1)
								
				imagesize = ""
				
				# FIXME: There should be a toggle button for this...
				# Loading the images seems to slow down the process a lot,
				# so you ought to be able to disable this if you're in a hurry
				if True:
					try:		
						im = Image.open(image, mode='r') # mode='r' because we only want the size
						(w,h) = im.size
						if HTML_IMG_MAX_WIDTH > 0 and HTML_IMG_MAX_HEIGHT > 0:
							if w > HTML_IMG_MAX_WIDTH or h > HTML_IMG_MAX_HEIGHT:
								if w > h:
									ratio = float(HTML_IMG_MAX_WIDTH)/w
									rswh = int(h * ratio)
									if rswh < HTML_IMG_MAX_HEIGHT:
										imagesize = "width=\"%d\"" % (HTML_IMG_MAX_WIDTH,)
									else:
										imagesize = "height=\"%d\"" % (HTML_IMG_MAX_HEIGHT,)
								else:		
									ratio = float(HTML_IMG_MAX_HEIGHT)/h	
									rsww = int(w * ratio)	
									if rsww < HTML_IMG_MAX_WIDTH:				
										imagesize = "height=\"%d\"" % (HTML_IMG_MAX_HEIGHT,)
									else:
										imagesize = "width=\"%d\"" % (HTML_IMG_MAX_WIDTH,)	
					
					except IOError:
						print "File %s couldn't be opened (group: %s)" % (image,g.getName())
					
				rowname = "Row_%d" % (rownum,)	
				
				html = HTML_TEMPLATE.replace("@GROUPNAME@",groupname).replace("@IMAGE@", "../../" + image)
				html = html.replace("@BGCOLOR@", HTML_BGCOLOR)
				html = html.replace("@TEXT@", HTML_TEXT)
				html = html.replace("@LINK@", HTML_LINK)
				html = html.replace("@VLINK@", HTML_VLINK)
				html = html.replace("@NEXT@", next)
				html = html.replace("@PREVIOUS@", prev)
				html = html.replace("@NEXTGROUP@", nextg)
				html = html.replace("@PREVIOUSGROUP@", prevg)
				html = html.replace("@IMAGESIZE@", imagesize)
				html = html.replace("@ROWNAME@", rowname)
								
				htmlfile = open('%s/%s/g%d_p%d.html' % (groupdir, groupsubdir,i,j), 'w')
				htmlfile.write(html)
				htmlfile.close()				
				j = j + 1
				
				c = c + 1
				perc = float(c)/count * 100
				#print "%.2f%% %d" % (perc,int(perc*8/100))
				self.progress.configure(bitmap=os.path.normpath("@%s" % os.path.join(appPath, "pie%d.xbm" % (int(perc*8/100),))))	
			
				self.update()
				
			# Update progress indicator
			self.progressLabel.configure(text="%.2f%%" % (float(c)/count * 100))
			
			# Generate a thumbnail, and update index.html
			ihtml = ihtml + "\t\t<DIV class=\"ImgDiv\">"
			
			if g.getThumbnail() != None:
				try:
					path = g.getThumbnail()
					(d,f) = os.path.split(path)				
					thumb = "%s/%s/tn_%03d_%s" % (groupdir, groupsubdir, i,f)
					if self.makeThumb(path, thumb):
						ihtml = ihtml + "<A HREF=\"%s\"><IMG TITLE=\"%s\" src=\"%s\"></A>" % (link, g.getName().replace("\"",""), thumb)
					else:
						print "Thumbnail couldn't be generated for group %s (file: %s)" % (g.getName(), path)
						ihtml = ihtml + "<A HREF=\"%s\">%s</A>" % (link, g.getName().replace("\"",""))
				except IOError:
					print "Thumbnail couldn't be generated for group %s (file: %s)" % (g.getName(), path)
					ihtml = ihtml + "<A HREF=\"%s\">%s</A>" % (link, g.getName().replace("\"",""))
			else:
				ihtml = ihtml + "<A HREF=\"%s\">%s</A>" % (link, g.getName().replace("\"",""))
			
			
			ihtml = ihtml + "</DIV>\n"
			
			# Next group...
			i = i + 1
			if i % THUMBS_PER_ROW == 0:
				rownum = rownum + 1
				ihtml = ihtml + "\t</div>\n\t<div class=\"RowDiv\"><A name=\"Row_%d\"/>\n" % (rownum,)		
			
		# The last row's DIV
		ihtml = ihtml + "\t</div>\n"
		
		# The Overall DIV
		ihtml = ihtml + "</DIV>"
		
		# Finish the HTML
		ihtml = ihtml + "\n</BODY>\n</HTML>"		
		indexfile = open('index.html', 'w')
		indexfile.write(ihtml)
		indexfile.close()
			
		os.chdir(mydir)
		
		self.generating = False
		tkMessageBox.showinfo("Done", "HTML generated in\n%s" % (dirname,))	
		self.progressLabel.configure(text="Ready")
		
	def makeThumb(self, infile, outfile):			
		try:
			im = Image.open(infile)
		except IOError:
			return False
			
		(w,h) = im.size
		tw = THUMB_WIDTH
		th = THUMB_HEIGHT
		if w > h:			
			ratio = float(tw)/w
			th = int(h * ratio)
		else:		
			ratio = float(th)/h
			tw = int(w * ratio)			
		im2 = im.resize((tw,th),Image.BILINEAR)
		im2.save(outfile)
		
		return True
		
	def refreshGroupView(self):
		self.groupfilelist.delete(0, END)
		if self.selectedGroup == None:			
			return
		for item in self.selectedGroup.getItemNames():
			self.groupfilelist.insert(END, item)
		
	def addFile(self):
		if self.selectedGroup == None:			
			print "No group selected"
			return
		
		indices = list(self.filelist.curselection())
		if len(indices) < 1:
			print "No files selected"
			return
		
		# For each selected item, remove it and place it before the item above it
		for index in indices:
			name = self.filelist.get(index)
			self.selectedGroup.addItem(name, self.currentDir + name)
			
			self.trackFile(self.currentDir + name)
			
		#print "@@ ADD: self.allFiles: %s" % (self.allFiles.keys(),)
			
		self.refreshGroupView()
		
		print "filterOn: %s" % (self.filterOn,)
		if self.filterOn:
			#self.filter()
			indices.reverse() # guess why...
			for index in indices:
				self.filelist.delete(index)
		
	def remFile(self):
		if self.selectedGroup == None:			
			print "No group selected"
			return
		
		indices = list(self.groupfilelist.curselection())
		if len(indices) < 1:
			print "no files selected"
			return
		
		adj = 0
		for index in indices:
			i = int(index)
			item = self.selectedGroup.removeItem(i + adj)
			self.untrackFile(item.getPath())
			adj = adj-1			
		#print "@@ REMOVE: self.allFiles: %s" % (self.allFiles.keys(),)
		
		self.refreshGroupView()
		if self.filterOn:
			self.filter()
		
	def itemUp(self):
		if self.selectedGroup == None:			
			print "No group selected"
			return
		
		indices = list(self.groupfilelist.curselection())
		if len(indices) < 1:
			print "no selection"
			return
		
		items = self.selectedGroup.getImages()
			
		# For each selected item, remove it and place it before the item above it
		for index in indices:
			i = int(index)		
			if i > 0:
				g = items.pop(i)
				items.insert(i-1,g)	
		
		self.refreshGroupView()
		
		# Reselect the items that were selected
		for index in indices:
			i = int(index)	
			if i > 0:
				self.groupfilelist.select_set(i-1)
				last = i-1
			else:
				self.groupfilelist.select_set(0)
				last = 0
				
		# Scroll the list to ensure that the last item is visible
		self.groupfilelist.see(last)
		
		
	def itemDown(self):
		if self.selectedGroup == None:			
			print "No group selected"
			return
		
		indices = list(self.groupfilelist.curselection())
		if len(indices) < 1:
			print "no selection"
			return
			
		items = self.selectedGroup.getImages()
		
		# For each selected item, remove it and place it below the item below it
		indices.reverse()
		for index in indices:
			i = int(index)	
			g = items.pop(i)
			items.insert(i+1,g)
			
		self.refreshGroupView()	
		
		# Reselect the items that were selected
		for index in indices:
			i = int(index)
			self.groupfilelist.select_set(i+1)	
				
		self.groupfilelist.see(i+1)	
		
	def setThumbnail(self):
		if self.selectedGroup == None or self.displayedFile == None:			
			print "No image selected"
			return
		self.selectedGroup.setThumbnail(self.displayedFile)
		(d,f) = os.path.split(self.displayedFile)
		self.thumbnailButton.config(text=f)
		
	def delThumbnail(self):		
		if self.selectedGroup == None:			
			print "No group selected"
			return
		self.selectedGroup.setThumbnail(None)
		self.thumbnailButton.config(text="None")
		
	def groupUp(self):
		indices = list(self.grouplist.curselection())
		if len(indices) < 1:
			print "no selection"
			return
		
		# For each selected item, remove it and place it before the item above it
		for index in indices:
			i = int(index)		
			if i > 0:
				g = groups.pop(i)
				groups.insert(i-1,g)		
		self.refreshGroupList()
		
		# Reselect the items that were selected
		for index in indices:
			i = int(index)	
			if i > 0:
				self.grouplist.select_set(i-1)
				last = i-1
			else:
				self.grouplist.select_set(0)
				last = 0
		self.grouplist.see(last)
						
	def groupDown(self):
		indices = list(self.grouplist.curselection())
		if len(indices) < 1:
			print "no selection"
			return
		
		# For each selected item, remove it and place it before the item above it
		indices.reverse()
		for index in indices:
			i = int(index)	
			g = groups.pop(i)
			groups.insert(i+1,g)
			
		self.refreshGroupList()
		
		# Reselect the items that were selected
		for index in indices:
			i = int(index)
			self.grouplist.select_set(i+1)
			
		self.grouplist.see(i+1)
		
	def refreshGroupList(self):
		self.grouplist.delete(0,END)
		for item in getGroupnames():
			self.grouplist.insert(END, item)
		
	def groupAdd(self):
		gname = tkSimpleDialog.askstring("New Group", "Please enter a name for this group")
		if gname == None:
			return
			
		while groupExist(gname):
			tkMessageBox.showerror("Error", "A group named %s already exists" %(gname,))
			gname = tkSimpleDialog.askstring("New Group", "Please enter a name for this group", initialvalue=gname)
			if gname == None:
				return
		
		addGroup(gname)
		self.refreshGroupList()
		self.grouplist.select_clear(0,END)
		self.grouplist.select_set(self.grouplist.size()-1)
	
		# Scroll the list to ensure that the last item is visible
		self.grouplist.see(self.grouplist.size()-1)
		
	def groupRemove(self):
		indices = list(self.grouplist.curselection())
		if len(indices) < 1:
			print "no selection"
			return
		
		adj = 0 # Trick to remove the correct indices
		for index in indices:
			print "Remove " + self.grouplist.get(index)		
			g = removeGroup(int(index) + adj)
			
			for item in g.getImages():
				self.untrackFile(item.getPath())
			
			adj = adj - 1
		self.refreshGroupList()
		
		#print "@@ REMOVE GROUP: self.allFiles: %s" % (self.allFiles.keys(),)
		
		# Select and display the next group
		if int(index) < self.grouplist.size():
			self.grouplist.select_set(int(index))		
			self.grouplist.see(int(index))
		else:
			self.grouplist.select_set(self.grouplist.size()-1)
			self.grouplist.see(self.grouplist.size()-1)
			
		name = self.grouplist.get(int(index))
		self.selectedGroup = getGroup(name)
			
		if self.filterOn:
			self.filter()
			
		if self.selectedGroup == None:
			self.clearCanvas()
		else:			
			first = self.selectedGroup.getFirst()
			if first != None:
				self.showImage(first)
				
		self.refreshGroupView()
		
	def groupRename(self):
		indices = list(self.grouplist.curselection())
		if len(indices) < 1:
			print "no selection"
			return
		index = int(indices[0])
		group = self.grouplist.get(index)
		gname = tkSimpleDialog.askstring("Rename Group", "Please enter a new name for this group", initialvalue=group)
 		if gname != None:
 			if groupExist(gname):
				tkMessageBox.showerror("Error", "A group named %s already exists" %(gname,))
			else:
				renameGroup(index, gname)			
		self.refreshGroupList()
		
		self.grouplist.select_set(index)
		self.grouplist.see(index)
		
	def wipeGroups(self):
		indices = list(self.grouplist.curselection())
		if len(indices) < 1:
			print "no selection"
			return
		
		adj = 0 # Trick to remove the correct indices
		for index in indices:			
			g = getGroup(self.grouplist.get(index))
			for im in g.getImages():				
				src = im.getPath()
				dest = "%s~" %(src,)
				if os.path.exists(dest):
					print "Backup %s exists" % (dest,)
				else:
					shutil.move(src,dest)
					
				self.untrackFile(im.getPath())
						
			removeGroup(int(index) + adj)
			adj = adj - 1
			
		self.refreshGroupList()
		
		#print "@@ WIPE GROUPS: self.allFiles: %s" % (self.allFiles.keys(),)
		
		# Select and display the next group
		if int(index) < self.grouplist.size():
			self.grouplist.select_set(int(index))		
			self.grouplist.see(int(index))
		else:
			self.grouplist.select_set(self.grouplist.size()-1)
			self.grouplist.see(self.grouplist.size()-1)
		name = self.grouplist.get(int(index))
		self.selectedGroup = getGroup(name)
		if self.selectedGroup == None:
			return		
		first = self.selectedGroup.getFirst()
		if first != None:
			self.showImage(first)
			
	def mergeGroups(self):
		indices = list(self.grouplist.curselection())
		if len(indices) < 2:
			print "Needs at least 2 groups to merge"
			return
			
		index0 = indices[0]
		g_to = getGroup(self.grouplist.get(index0))
		indices = indices[1:]
		
		print "MERGE TO: %s" % (g_to.getName(),);
		
		adj = 0
		for index in indices:			
			g = getGroup(self.grouplist.get(index))
			print "MERGE FROM: %s" % (g.getName(),);
			for im in g.getImages():	
				g_to.addImageItem(im)
						
			removeGroup(int(index) + adj)
			adj = adj - 1
					
		self.refreshGroupList()
		self.refreshGroupView()
		
		self.grouplist.select_set(index0)
		self.grouplist.see(index0)
		
	def fileLeft(self):
		if self.displayedFile == None:
			print "No file"
			return
		
		try:
			img = Image.open(self.displayedFile)
			img2 = img.transpose(Image.ROTATE_90)
			img2.save(self.displayedFile)				
			self.showImage(self.displayedFile)
		except IOError:
			tkMessageBox.showerror("Error", "Unable to save the file; Is it read-only?")
		
	def fileRight(self):
		if self.displayedFile == None:
			print "No file"
			return
		
		try:
			img = Image.open(self.displayedFile)
			img2 = img.transpose(Image.ROTATE_270)
			img2.save(self.displayedFile)				
			self.showImage(self.displayedFile)
		except IOError:
			tkMessageBox.showerror("Error", "Unable to save the file; Is it read-only?")
		
	def fileResize(self):		
		indices = list(self.groupfilelist.curselection())
		if len(indices) < 1:
			print "no selection"
			return
			
		try:
			tw = int(self.resizeWidth.get())
			th = int(self.resizeHeight.get())
		except ValueError:
			tkMessageBox.showerror("Error", "Invalid resize dimension")
			return			
			
		items = self.selectedGroup.getImages()
		for i in indices:
			self.showImage(items[int(i)].path)
			
			(w,h) = self.im.size			
			
			if w > h:			
				ratio = float(tw)/w
				rswh = int(h * ratio)
				rsww = tw
			else:		
				ratio = float(th)/h
				rsww = int(w * ratio)			
				rswh = th				
				
			backname = self.displayedFile + "~"
				
			if os.path.exists(backname):
				print "Backup " + backname + " exists"
			else:
				shutil.copyfile(self.displayedFile, backname)
				print "Backup " + backname + " created"
			
			newim = self.im.resize((rsww,rswh),Image.BILINEAR)
			try:
				newim.save(self.displayedFile)				
			except IOError:
				tkMessageBox.showerror("Error", "Unable to save the file; Is it read-only?")
				
			self.showImage(self.displayedFile)
		
	def showImage(self, fname):
		"""Displays an image in the canvas"""
		
		self.clearCanvas()
		self.displayedFile = fname		
		try:		
			self.im = Image.open(fname)
		except IOError:
			self.canvas.create_text((self.canvas.winfo_width()/2, self.canvas.winfo_height()/2 -20), fill="red", 
				text="Unable to open %s" % (fname,))
			self.canvas.create_line(0, 0, self.canvas.winfo_width(), self.canvas.winfo_height(), fill="red")
			self.canvas.create_line(self.canvas.winfo_width(), 0, 0, self.canvas.winfo_height(), fill="red")
			
			return
		
		(w,h) = self.im.size
		
		(cw,ch) = (self.canvas.winfo_width(), self.canvas.winfo_height())
		if w > h:			
			ratio = float(cw)/w
			rswh = int(h * ratio)
			if rswh < ch:
				ch = int(h * ratio)
			else:
				ratio = float(ch)/h
				cw = int(w * ratio)					
		else:		
			ratio = float(ch)/h
			rsww = int(w * ratio)
			if rsww < cw:
				cw = int(w * ratio)		
			else:
				ratio = float(cw)/w
				ch = int(h * ratio)		
			
		try:
			tw = int(self.resizeWidth.get())
			th = int(self.resizeHeight.get())
			if w > tw or h > th:
				self.resizeButton.config(fg="red")
			else:
				self.resizeButton.config(fg="black")
		except ValueError:
			self.resizeButton.config(fg="black")
		
		self.sizeLabel.config(text="%4dx%4d" % (w,h))
		
		try:
			self.imt = ImageTk.PhotoImage(self.im.resize((cw,ch),Image.BILINEAR))
			if self.canvas_item != None:
				self.canvas.delete(self.canvas_item)
			self.canvas_item = self.canvas.create_image(0,0,anchor=NW, image=self.imt)		
		except IOError:
			self.clearCanvas()			
			self.canvas.create_text((self.canvas.winfo_width()/2, self.canvas.winfo_height()/2 -20), fill="red", 
				text="Unable to open %s" % (fname,))
			self.canvas.create_line(0, 0, self.canvas.winfo_width(), self.canvas.winfo_height(), fill="red")
			self.canvas.create_line(self.canvas.winfo_width(), 0, 0, self.canvas.winfo_height(), fill="red")
			
		# If a backup exists, allow the user to restore it:
		if os.path.exists(fname + "~"):
			self.restoreButton.config(fg="red")
		else:
			self.restoreButton.config(fg="black")
			
	def clearCanvas(self):		
		self.canvas.delete(ALL)

	def restoreBackup(self):
		indices = list(self.groupfilelist.curselection())
		if len(indices) < 1:
			print "no selection"
			return
					
		items = self.selectedGroup.getImages()
		for i in indices:
			self.showImage(items[int(i)].path)
			
			if not os.path.exists(self.displayedFile + "~"):
				print "No backup"
				continue
			
			dest = self.displayedFile
			src = dest + "~"
			shutil.move(src,dest)
			
			print "Restore backup %s to %s " % (src, dest)
			
			self.showImage(dest)
		
	def filter(self):
		dircache.reset( )

		listdir = dircache.listdir(self.currentDir)	
		
		self.listdir = []
		for filename in listdir:
			fullname = self.currentDir + filename
			#print "FILE: %s" % (fullname,)
			if fullname not in self.allFiles:
				self.listdir.append(filename)
				
		self.filelist.delete(0, END) # Delete all items in the list
		for item in self.listdir:
			if isImageFile(item):
				self.filelist.insert(END, item) 
				
		self.filterOn = True
		
	def unFilter(self):
		dircache.reset( )
		self.listdir = dircache.listdir(self.currentDir)		
		self.filelist.delete(0, END) # Delete all items in the list
		for item in self.listdir:
			if isImageFile(item):
				self.filelist.insert(END, item) 
		self.filterOn = False

###############################################################################
# The main application starts here
		
appPath = os.path.dirname(os.path.abspath(sys.argv[0]))

app = Application()
app.master.title("PyAddfiles")

if len(sys.argv) > 1:
	if os.path.isdir(sys.argv[1]):
		app.setDir(os.path.realpath(sys.argv[1]))
	else:
		topen = file(sys.argv[1])
		app.setDir(os.path.realpath(os.path.dirname(topen.name)))	
		app.openFile(topen)

app.mainloop()
