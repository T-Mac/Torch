import wx
import threading
from tools import file
import time
import Queue
import wx.lib.newevent
from wx.lib.pubsub import Publisher as pub

MoveEvent, EVT_NOTE_MOVE = wx.lib.newevent.NewCommandEvent()
HideEvent, EVT_NOTE_HIDE = wx.lib.newevent.NewCommandEvent()
RemvEvent, EVT_NOTE_REMV = wx.lib.newevent.NewCommandEvent()
	
class Popup_Old(wx.Frame):
	"""notifier's popup window"""

	def __init__(self,text):
		wx.Frame.__init__(self, None, -1, style=wx.NO_BORDER|wx.FRAME_NO_TASKBAR)
		self.padding = 12 # padding between edge, icon and text
		self.popped = 0 # the time popup was opened
		self.delay = 4 # time to leave the popup opened
		self.message = text
		
		# platform specific hacks
		lines = 2
		lineHeight = wx.MemoryDC().GetTextExtent(" ")[1]
		if wx.Platform == "__WXGTK__":
			# use the popup window widget on gtk as the
			# frame widget can't animate outside the screen
			self.popup = wx.PopupWindow(self, -1)
		elif wx.Platform == "__WXMSW__":
			# decrement line height on windows as the text calc below is off otherwise
			self.popup = self
			lineHeight -= 3
		elif wx.Platform == "__WXMAC__":
			# untested
			self.popup = self

		self.popup.SetSize((250, (lineHeight * (lines + 1)) + (self.padding * 2)))
		self.panel = wx.Panel(self.popup, -1, size=self.popup.GetSize())

		# popup's click handler
		self.panel.Bind(wx.EVT_LEFT_DOWN, self.click)
		
		#popup's move handler
		#self.Bind(EVT_NOTE_MOVE, self.show)
		
		# popup's logo
		self.logo = wx.Bitmap(file("dat/reader_large.png", "p"))
		wx.StaticBitmap(self.panel, -1, pos=(self.padding, self.padding)).SetBitmap(self.logo)

		# main timer routine
		self.timer = wx.Timer(self, -1)
		self.Bind(wx.EVT_TIMER, self.main, self.timer)
		self.timer.Start(5)
		
		# create new text
		

	def main(self, event):
		print 'main'
		if self.focused():
			# maintain opened state if focused
			self.popped = time.time()
		elif self.opened() and self.popped + self.delay < time.time():
			# hide the popup once delay is reached
			self.hide()

	def click(self, event):
		"""handles popup click"""

		self.popped = 0
		self.hide()

	def show(self, event):
		popupSize = self.popup.GetSize()
		logoSize = self.logo.GetSize()
		self.text = wx.StaticText(self.panel, -1, self.message)
		self.text.Bind(wx.EVT_LEFT_DOWN, self.click)
		self.text.Move((logoSize.width + (self.padding * 2), self.padding))
		self.text.SetSize((
			popupSize.width - logoSize.width - (self.padding * 3),
			popupSize.height - (self.padding * 2)
		))
		"""shows the popup"""
		popupSize = self.popup.GetSize()
		# animate the popup
		screen = wx.GetClientDisplayRect()
		self.popup.Show()
		for i in range(1, popupSize.height + 1):
			self.popup.Move((screen.width - popupSize.width, screen.height - i))
			self.popup.SetTransparent(int(float(240) / popupSize.height * i))
			self.popup.Update()
			self.popup.Refresh()
			time.sleep(0.01)
		self.popped = time.time()

	def hide(self):
		"""hides the popup"""
		print 'hiding'
		self.popup.Hide()
		self.popped = 0

	def focused(self):
		"""returns true if popup has mouse focus"""

		mouse = wx.GetMousePosition()
		popup = self.popup.GetScreenRect()
		return (
			self.popped and
			mouse.x in range(popup.x, popup.x + popup.width)
			and mouse.y in range(popup.y, popup.y + popup.height)
		)

	def opened(self):
		"""returns true if popup is open"""

		return self.popped != 0

class Popup(threading.Thread):
	def __init__(self, message, pic, show_lock):
		#define content
		self.message = message
		self.logo = wx.Bitmap(pic)
		self.move_event = threading.Event()
		self.show_lock = show_lock
		self.first_run = True
		#define window attributes
		self.padding = 12 # padding between edge, icon and text
		lines = 2
		lineHeight = wx.MemoryDC().GetTextExtent(" ")[1]
		lineHeight -= 3
		
		#create window
		self.popup =  wx.Frame(None, -1, style=wx.NO_BORDER|wx.FRAME_NO_TASKBAR)
		self.popup.SetSize((250, (lineHeight * (lines + 1)) + (self.padding * 2)))
		self.panel = wx.Panel(self.popup, -1, size=self.popup.GetSize())
		
		#Pic
		wx.StaticBitmap(self.panel, -1, pos=(self.padding, self.padding)).SetBitmap(self.logo)
		
		#Create Text
		popupSize = self.popup.GetSize()
		logoSize = self.logo.GetSize()
		self.text = wx.StaticText(self.panel, -1, self.message)
		self.text.Move((logoSize.width + (self.padding * 2), self.padding))
		self.text.SetSize((
			popupSize.width - logoSize.width - (self.padding * 3),
			popupSize.height - (self.padding * 2)
		))
		screen = wx.GetClientDisplayRect()
		self.position = screen.height
		#self.timeout = threading.Timer(5, self.hide, args=[self])
		
		#Bind Events
		pub.subscribe(self.move, 'note.move')
		
		#def show(self):
		self.popped = None
		#pub.sendMessage('note.move', 'blarg')
		#self.move()
		self.alive = threading.Event()
		self.alive.set()
		threading.Thread.__init__(self)
		
	def move(self, event):
		self.popup.Show()
		
		popupSize = self.popup.GetSize()
		screen = wx.GetClientDisplayRect()
		for i in range(1, popupSize.height + 1):
			self.position = self.position - 1
			#print 'pos:%s - i:%s'%(str(self.position),str(i))
			self.popup.Move((screen.width - popupSize.width, self.position))
			#self.popup.SetTransparent(int(float(240) / popupSize.height * i))
			self.popup.Update()
			self.popup.Refresh()
			time.sleep(0.005)
		print 'done'

	def hide(self):
		print 'hiding'
		for i in range(1,60):
			i = 240 - (i * 4)
			self.popup.SetTransparent(i)
			time.sleep(0.01)
		self.popup.Hide()
	
	def run(self):
		while self.alive.isSet():
			self.move_event.wait()
			if self.first_run == True:
				self.show_lock.acquire()
				self.popped = (time.time() + 5)
			self.move_event.clear()
			self.move('test')
			if self.first_run == True:
				self.show_lock.release()
				self.first_run = False
			
			
class Icon(wx.TaskBarIcon):
	"""notifier's taskbar icon"""

	def __init__(self, menu):

		wx.TaskBarIcon.__init__(self)

		# menu options
		self.menu = menu

		# event handlers
		self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.click)
		self.Bind(wx.EVT_TASKBAR_RIGHT_DOWN, self.click)
		self.Bind(wx.EVT_MENU, self.select)

		# icon state
		self.states = {
			"on": wx.Icon(file("dat/reader_new.png", "p"), wx.BITMAP_TYPE_PNG),
			"off": wx.Icon(file("dat/reader_empty.png", "p"), wx.BITMAP_TYPE_PNG)
		}
		self.setStatus("off")

	def click(self, event):
		"""shows the menu"""

		menu = wx.Menu()
		for id, item in enumerate(self.menu):
			menu.Append(id, item[0])
		self.PopupMenu(menu)

	def select(self, event):
		"""handles menu item selection"""

		self.menu[event.GetId()][1]()

	def setStatus(self, which):
		"""sets the icon status"""

		self.SetIcon(self.states[which])

	def close(self):
		"""destroys the icon"""

		self.Destroy()
		
class Gui(wx.App):
	def __init__(self):
		wx.App.__init__(self, redirect=0)
		self.popups = []
		menu = [
			("add", self.test_add),
			("add2", self.test2),
			("add3", self.test3),
		]
		self.NoteQ = Queue.Queue(maxsize=0)
		self.icon = Icon(menu)
		self.timer = wx.Timer(self, -1)
		self.Bind(wx.EVT_TIMER, self.main, self.timer)
		self.timer.Start(1)
		self.notes = ['test']
		self.testtimer = wx.Timer(self, -1)
		self.Bind(wx.EVT_TIMER, self.test_add, self.testtimer)
		#self.testtimer.Start(500)
		self.show_lock = threading.Lock()
		self.MainLoop()
		
		
	def main(self, event):
		if self.show_lock.acquire(False):
			self.show_lock.release()
			try:
				note = self.NoteQ.get_nowait()
			except Queue.Empty:
				pass
			else:
				note.start()
				for popup in self.popups:
					popup.move_event.set()
		self.remove()
	

		
	def add(self, text):
		#pub.sendMessage('note.move', 'blarg')
		newpopup = Popup(text,file("dat/reader_large.png", "p"),self.show_lock)
		print 'step 1'
		self.popups.append(newpopup)
		print 'step 2'
		#newpopup.start()
		self.NoteQ.put(newpopup)
		#newpopup.show()
		
		#newtimer = wx.Timer(self, -1)
		#event = MoveEvent(-1)
		
			#wx.PostEvent(popup.popup.GetEventHandler(),event)
			#popup.popup.GetEventHandler().ProcessEvent(event)
		#	pub.sendMessage('note.move', 'blarg')
		print 'added'
			
	def remove(self):
		for popup in self.popups:
			if popup.popped != None and popup.popped < time.time():
				popup.hide()
				self.popups.remove(popup)
				popup.alive.clear()
		
	def test_add(self):
		self.add('test')
		
	def test2(self):
		self.add('test')
		self.add('test')

	def test3(self):
		self.add('test')
		self.add('test')
		self.add('test')

app = Gui()

	
	
