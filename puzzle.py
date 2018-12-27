import re
from tkinter import *
import string
from pickle import Pickler, Unpickler

tk = Tk()
class Crossword(object):
	def __init__(self, cols, rows):
		self.cols = cols
		self.rows = rows
		self.grid = [[' ' for i in range(cols)] for k in range(rows)]
		self.across = {}
		self.down = {}

	def get_cell(self,row,col=None):
		if col == None:
			row,col = row
		return self.grid[row][col]

	def set_cell(self,row,col, value):
		self.grid[row][col] = value

	def getStart(self, rc, direction):
		direction = "Left" if direction == 'Right' else 'Up'
		while True:
			candidate = self.transition(rc,direction)
			if self.boundary(candidate):
				return rc
			if self.get_cell(candidate) == '.':
				return rc
			rc = candidate

	def getWord(self, rc, direction):
		start = self.getStart(rc,direction)
		if direction == 'Down':
			return self.down[start][0]
		else:
			return self.across[start][0]

	def transition(self, rc, direction):
		if direction == 'Down':
			return (rc[0]+1, rc[1])
		if direction == 'Up':
			return (rc[0]-1, rc[1])
		if direction == 'Right':
			return (rc[0], rc[1]+1)
		if direction == 'Left':
			return (rc[0], rc[1]-1)

	def boundary(self, rc):
		return rc == '.' or -1 in rc or self.rows in rc

	def getFixedMatches(self, rc, direction):
		fixedWord = []
		rotate = 'Right' if direction == 'Down' else 'Down'
		start = self.getWord(rc, direction)
		while True:
			if '.' in self.getWord(rc, rotate):
				fixedWord.append('.')
			else:
				fixedWord.append(self.get_cell(rc))
			rc = self.transition(rc,direction)
			if self.boundary(rc):
				print(fixedWord)
				return ''.join(fixedWord)


	def get_across(self):
		ret = {}
		for row in range(self.rows):
			i=0
			r = ''.join(self.grid[row]).split('.')
			for word in r:
				if word != '':
					ret[(row,i)] = (word.replace(' ','.')+'$', [])
					i += len(word)
				else:
					i += 1
		return ret

	def get_down(self):
		ret = {}
		grid = list(zip(*self.grid))
		for col in range(self.cols):
			r = ''.join(grid[col]).split('.')
			i = 0
			for word in r:
				if word != '':
					ret[(i,col)] = (word.replace(' ','.')+'$', [])
					i += len(word)
				else:
					i += 1
		return ret

	def scan(self):
		across = self.get_across()
		down = self.get_down()
		items = list(self.across.keys())
		for i in items:
			if i not in across or self.across[i][0] != across[i][0]:
				self.across.pop(i)
		for k,v in across.items():
			if k not in self.across:
				self.across[k] = (v[0], match(v[0]))
				items = self.across.keys()
		items = list(self.down.keys())
		for i in items:
			if i not in down or self.down[i][0] != down[i][0]:
				self.down.pop(i)
		for k,v in down.items():
			if k not in self.down:
				self.down[k] = (v[0], match(v[0]))

		return {"Acrosses": [len(v[1]) for v in self.across.values()],
				"Downs": [len(v[1]) for v in self.down.values()]}

class Bunch(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)


class CellEntry(Entry):
	def __init__(self, master, row, col, crossword, **kwargs):
		self._variable = StringVar()
		self._variable.trace("w",self._callback)
		self._crossword = crossword
		self.row = row
		self.col = col
		self.old_value = ' '
		vcmd = (master.register(self.validate),
				'%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
		font = "Times 32 bold"
		super().__init__(master, textvariable=self._variable, bd=1,
			highlightthickness=1, highlightcolor="orange", validate="key", validatecommand=vcmd,
			font=font, width=2, highlightbackground="white", **kwargs)
		self.bind('<BackSpace>', self._goBack)
		self.bind('<Button1-ButtonRelease>', App.static.click)
		self.bind('<FocusIn>', self._focus)


	def set(self, letter):
		self._variable.set(letter)

	def get(self):
		return self._variable.get()

	def validate(self, action, index, value_if_allowed,
					   prior_value, text, validation_type, trigger_type, widget_name):
		return text in string.ascii_letters + '. '

	def _goBack(self, *args):
		self.set(' ')
		App.static.previousLetter()

	def _callback(self, *args):
		value = self._variable.get()
		value = value.replace(' ','')
		self._variable.set(' ' if not value else value[-1].upper())
		self._crossword.set_cell(self.row,self.col,self._variable.get())
		self['bg']= 'black' if '.' in self._variable.get() else 'white'
		self.old_value = self._variable.get()
		if value != '' and value != ' ':
			App.static.nextLetter()

	def _focus(self, *args):
		App.static.selected = (self.row,self.col)

class App:
	def __init__(self, crossword):
		App.static = self
		self.root = tk
		self._crossword = crossword
		self._grid = Frame(self.root)
		self._grid.pack()
		self.selected = (0,0)
		self.direction = 'Right'
		self._hl = False
		self._tabi = 0
		self.root.bind('<Key>', self.arrow)

		self._cells = {}
		for col in range(crossword.cols):
			for row in range(crossword.rows):
				entry = CellEntry(self._grid, row, col, crossword, justify=CENTER)
				entry.grid(row=row,column=col)
				self._cells[(row,col)] = entry

	def click(self, *args):
		if self.direction == "Right":
			self.direction = "Down"
		else:
			self.direction = "Right"
		self.select()

	def nextLetter(self):
		return self.arrow(Bunch(keysym=self.direction))

	def previousLetter(self):
		if self.direction == 'Right':
			return self.arrow(Bunch(keysym='Left'))
		elif self.direction == 'Down':
			return self.arrow(Bunch(keysym='Up'))

	def goToStart(self):
		while self._cells[self.selected]._variable.get() != '.':
			if not self.previousLetter():
				return
		# Hit a black square, go forward one
		self.nextLetter()

	def getSelection(self):
		if self._hl:
			return
		self._hl = True
		r,c = self.selected # keep track of original position
		cs = []
		self.goToStart()
		while self._cells[self.selected]._variable.get() != '.':
			cs.append(self.selected)
			if not self.nextLetter():
				break
		self.selected = (r,c)
		self.select()
		self._hl = False
		return cs

	def shadeSelection(self, cs, color):
		for c,entry in self._cells.items():
			if c in cs:
				entry['bg'] = color

	def showTrouble(self):
		selected = self.selected
		for c,entry in self._cells.items():
			if entry['bg'] != 'black':
				entry['bg'] = 'white'
		for r,c in self._crossword.across:
			self.selected = (r,c)
			if len(self._crossword.across[(r,c)][1]) == 0:
				self.shadeSelection(self.getSelection(), 'yellow')
		for r,c in self._crossword.down:
			self.selected = (r,c)
			if len(self._crossword.down[(r,c)][1]) == 0:
				self.shadeSelection(self.getSelection(), 'yellow')
		self.selected = selected

	def highlightSelection(self, cs):
		for c,entry in self._cells.items():
			if c in cs:
				entry['highlightbackground'] = 'red'
			else:
				entry['highlightbackground'] = 'white'

	def select(self):
		self._cells[self.selected].focus()
		if not self._hl:
			self.highlightSelection(self.getSelection())

	def tab(self):
		pos = self.selected
		self._crossword.scan()
		self.showTrouble()
		cs = self.getSelection()
		choices = self._crossword.getFixedMatches(self.selected, self.direction)
		print(choices)
		try:
			self._tabi = self._tabi + 1 % len(choices)
		except ZeroDivisionError:
			self._tabi = 0
		try:
			wd = choices[self._tabi]
			s = self._crossword.getStart(self.selected,self.direction)
			for i in wd:
				self._cells[s].set(i)
				s = self._crossword.transition(s, self.direction)
		except IndexError:
			print("Ran out of choices")
			pass
		#self.selected = pos
		#self.select()

	def arrow(self, event):
		r,c = self.selected
		keys = {"Left": (r,c-1, "Right"),
				"Right": (r,c+1, "Right"),
				"Up": (r-1,c, "Down"),
				"Down": (r+1,c, "Down")}
		if event.keysym in keys:
			r,c,self.direction = keys[event.keysym]
			r,c = max(0,min(self._crossword.rows-1,r)), max(0,min(self._crossword.cols-1,c))
			ret = self.selected != (r,c)
			self.selected = (r,c)
			self.select()
			return ret
		elif event.keysym == 'Tab':
			self.tab()
			return 'break'

	def run(self):
		self.root.mainloop()


dict = []
DICTIONARY="WL-SP.txt"

with open(DICTIONARY) as f:
	for line in f.read().split('\n'):
		dict.append(line)

def pprint(l):
	for w in l:
		print(w)

def hamming(w1,w2):
	d=0
	if len(w1) != len(w2):
		return 10000
	for x,y in zip(w1,w2):
		if x != y:
			d += 1
	return d

def match(r,dict=dict):
	r = re.compile(r)
	words = [w for w in dict if r.match(w)]
	return words

def match_ham(b1,b2,ham):
	cb1 = match(b1,dict)
	cb2 = match(b2,dict)

	res = {}
	for w in cb1:
		resw = [y for y in cb2 if hamming(w,y) == ham]
		if len(resw) > 0:
			res[w] = resw

	for k,v in res.items():
		print("{}: {}".format(k,v))
	return res

def match_box(b1,b2,dict=dict,length=None):
	#b1 = 's..o...'
	#b2 = 's..a...'
	cb1 = match(b1,dict)
	cb2 = match(b2,dict)

	difs = []
	for i in range(len(b1)):
		if b1[i] != b2[i]:
			difs.append(i)
	res = []
	for w in cb2:
		k = w
		for i in difs:
			k = k[:i]+b1[i] + k[i+1:]
		if k in cb1:
			res.append((k, w))
	if length:
		res = [(k,v) for (k,v) in res if len(k) == length]
	return res

def save():
	with open('cw.pickle','wb') as f:
		Pickler(f).dump(cw)

def load():
	with open('cw.pickle','rb') as f:
		cw = Unpickler(f).load()
	App(cw).run()

def run():
	cw = Crossword(15,15)
	App(cw).run()

run()
