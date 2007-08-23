""" Defines the visual part of core: NodePanel and Arrow classes.

Here we're using OpenGL to draw nodes and connections between them. Note the source code is completely PEP8-incompatible; 
there's a desperate need to refactor the function names et al...

"""

from core import node
import core.node_draw as node_draw

from core.utils import *
from core.shared import *

import wx

try:
	from OpenGL.GL import *
except ImportError:
	print "The OpenGL extensions do not appear to be installed."
	print "This application cannot run."
	sys.exit(1)

class NodePanel(object):
	def __init__(self, parent, x=100, y=100, showParameters = True, showPreview = False, iconicMode = False):
		self.x = x
		self.y = y
		
		self.width = 100
		self.height = 150
		
		self.delta = (0,0)
		self.originalClick = (0, 0)
		self.node = None
		self.owner = parent
		
		self.showParameters = showParameters # this and following 3 might be a bit field; we'll see about it...
		self.showPreview = False
		self.iconicMode = iconicMode
		
	def assignNode(self, Node):
		self.node = Node
		Node.panel = self
		
		width, height, headerh, dh, col1, col2 = node_draw.CalcMinMaxSize(self.node, wx.ClientDC(self.owner))
		
		self.width = width
		self.height = height
		
	def __repr__(self):
		return """pnl = NodePanel(self, %d, %d, %s, %s, %s)\npanels.append(pnl)\npnl.assignNode(node%s)\n""" % (self.x, self.y,  str(self.showParameters), str(self.showPreview), str(self.iconicMode), self.node.id)
		
	def refreshFont(self):
		width, height, headerh, dh, col1, col2 = node_draw.CalcMinMaxSize(self.node, wx.ClientDC(self.owner))
		
		self.width = width
		self.height = height
		
	def inside(self, ax, ay):
		return (ax in range(self.x, self.x+self.width)) and ((ay in range(self.y, self.y+self.height)))
		
	def paint(self):
		GL_TEXTURE_RECTANGLE_ARB = 0x84F5
		mode = GL_TEXTURE_RECTANGLE_ARB # GL_TEXTURE_2D
		
		if self in self.owner.c.markedPanels:
		 	#glDisable(GL_TEXTURE_2D) # to ensure the image isn't "color corrected" by texture :)
			glDisable(mode)
			glColor4f( 248/255.0, 206/255.0, 36/255.0, 0.5 ) # hardcoded selection color
	
			selectionBorder = 5 # ... and size
			glBegin( GL_QUADS )
			
			glVertex2i( self.x-selectionBorder, self.y-selectionBorder )
			glVertex2i( self.x+self.width+selectionBorder, self.y-selectionBorder )
			glVertex2i( self.x+self.width+selectionBorder, self.y+self.height+selectionBorder )
			glVertex2i( self.x-selectionBorder, self.y+self.height+selectionBorder )
			
			glEnd()
		

	 	glEnable(mode)
		TextureBitmap = node_draw.PaintForm(self.node, 0, 0, wx.ClientDC(self.owner))
		image = wx.ImageFromBitmap(TextureBitmap).GetData()
			
		# Create Texture
		_textureName = 0
		_textureName = glGenTextures(1)
		
		glBindTexture(mode, _textureName)
			
		glPixelStorei(GL_UNPACK_ALIGNMENT,1)
		glTexImage2D(mode, 0, 3, TextureBitmap.GetWidth(), TextureBitmap.GetHeight(), 0, GL_RGB, GL_UNSIGNED_BYTE, image)
		glTexParameterf(mode, GL_TEXTURE_WRAP_S, GL_CLAMP)
		glTexParameterf(mode, GL_TEXTURE_WRAP_T, GL_CLAMP)
		glTexParameterf(mode, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		glTexParameterf(mode, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)
	
		glColor3f( 1, 1, 1 ) # to ensure the image isn't "color corrected" :)
	
		glBegin( GL_QUADS )
		
		glTexCoord2i(0, 0)
		glVertex2i( self.x, self.y )
		
		#glTexCoord2i(1, 0)
		glTexCoord2i(self.width, 0)
		glVertex2i( self.x+self.width, self.y )
		
		#glTexCoord2i(1, 1)
		glTexCoord2i(self.width, self.height)
		glVertex2i( self.x+self.width, self.y+self.height )
		
		#glTexCoord2i(0, 1)
		glTexCoord2i(0, self.height)
		glVertex2i( self.x, self.y+self.height )
		
		glEnd()
		
		glDeleteTextures(_textureName)
	
class Arrow(object):
	def __init__(self, parent):
		self.x1 = 0
		self.y1 = 0
		self.x2 = 0
		self.y2 = 0
		self.connection = None
		self.idx1 = -1
		self.idx2 = -1
		self.owner = parent
	
	def assignConnection(self, Connection):
		self.connection = Connection
		Connection.arrow = self
		
		inpn = self.connection.inputNode
		outn = self.connection.outputNode
		
		inname = self.connection.inputName
		outname = self.connection.outputName
		
		for i in range(len(outn.in_params)):
			param = outn.in_params[i]
			if param["name"] == outname:
				self.idx2 = i
		
		for i in range(len(inpn.out_params)):
			param = inpn.out_params[i]
			if param["name"] == inname:
				self.idx1 = i
		
		if ((self.idx1 == -1) or (self.idx2 == -1)):
			print "connection not found! something fatal!"
			
		self.refreshFont()
			
	def __repr__(self):
		return """arr = Arrow(self)\narrows.append(arr)\narr.assignConnection(connection%s)\n""" % (self.connection.id)
		
	def refreshFont(self):
		self.hoffset1 = node_draw.CalcArrowPosition(self.idx1, wx.ClientDC(self.owner), self.connection.inputNode)
		self.hoffset2 = node_draw.CalcArrowPosition(self.idx2, wx.ClientDC(self.owner), self.connection.outputNode)
	
	def paint(self):
		if self.connection != None:
			x1 = self.connection.inputNode.panel.x+self.connection.inputNode.panel.width
			y1 = self.connection.inputNode.panel.y+self.hoffset1
			
			x2 = self.connection.outputNode.panel.x
			y2 = self.connection.outputNode.panel.y+self.hoffset2
		else:
			x1 = self.owner.tax
			y1 = self.owner.tay
			x2 = self.owner.tax2
			y2 = self.owner.tay2
		
		bezscale = 20
		bezmiddle = abs(x2-x1)/1.5
		
		glEnable(GL_MAP1_VERTEX_3)
		ctrlpoints=[[x1, y1, 0.01], [x1+bezscale, y1, 0.01], [x1+bezmiddle, y1, 0.01], [x2-bezmiddle, y2, 0.01],[x2-bezscale, y2, 0.01], [x2, y2, 0.01]]
		glMap1f(GL_MAP1_VERTEX_3, 0.0, 1.0, ctrlpoints)
		glColor3f(0.4, 0.4, 0.4)        # grey
		glBegin(GL_LINE_STRIP)
		SEGS=20
		for p in range(0, SEGS+1): 
			glEvalCoord1f(float(p)/float(SEGS))
		glEnd()
		
		arrow_size = 5
		
		glBegin(GL_POLYGON)
		glVertex2i( x2, y2 )
		glVertex2i( x2-arrow_size, y2-arrow_size )
		glVertex2i( x2-arrow_size, y2+arrow_size )
		glEnd()
		
		
class Group(object):
	""" Group of panels """

	_instance_count = 0

	def __init__(self, parent):
		Group._instance_count += 1
		self.id = str(Group._instance_count)
		self.owner = parent

		self.panels = []

	def AddPanel(self, apanel):
		self.panels.append(apanel)

	def __repr__(self): # serialize the state into file
		s = """group%s = Group(self)\ngroups.append(group%s)\n""" % (self.id, self.id)
		for p in self.panels:
			s += "group%s.AddPanel(node%s.panel)\n" % (self.id, p.node.id)
		return s
		
	def paint(self):
		if len(self.panels):
			w, h, dh = node_draw.CalcGroupSize(self, wx.ClientDC(self.owner))
			#print gs
			
			minx = min([p.x for p in self.panels])
			maxx = max([(p.x+p.width) for p in self.panels])
			miny = min([p.y for p in self.panels])
			maxy = max([(p.y+p.height) for p in self.panels])
			
			GL_TEXTURE_RECTANGLE_ARB = 0x84F5
			mode = GL_TEXTURE_RECTANGLE_ARB # GL_TEXTURE_2D
			

			glDisable(mode)
			glColor4f( 161/255.0, 223/255.0, 149/255.0, 1 ) # hardcoded selection color

			selectionBorder = 5 # ... and size
			glBegin( GL_QUADS )

			# top
			glVertex2i( minx-selectionBorder, miny-h )
			glVertex2i( maxx+selectionBorder, miny-h )
			glVertex2i( maxx+selectionBorder, miny )
			glVertex2i( minx-selectionBorder, miny )

			# left
			glVertex2i( minx-selectionBorder, miny )
			glVertex2i( minx, miny )
			glVertex2i( minx, maxy+selectionBorder )
			glVertex2i( minx-selectionBorder, maxy+selectionBorder )

			# right
			glVertex2i( maxx, miny )
			glVertex2i( maxx+selectionBorder, miny )
			glVertex2i( maxx+selectionBorder, maxy+selectionBorder )
			glVertex2i( maxx, maxy+selectionBorder )			
			
			# bottom
			glVertex2i( minx, maxy )
			glVertex2i( maxx, maxy )
			glVertex2i( maxx, maxy+selectionBorder )
			glVertex2i( minx, maxy+selectionBorder )
			
			glEnd()
			
		 	glEnable(mode)
			TextureBitmap = node_draw.PaintGroup(self, wx.ClientDC(self.owner))
			image = wx.ImageFromBitmap(TextureBitmap).GetData()

			# Create Texture
			_textureName = 0
			_textureName = glGenTextures(1)

			glBindTexture(mode, _textureName)

			glPixelStorei(GL_UNPACK_ALIGNMENT,1)
			glTexImage2D(mode, 0, 3, TextureBitmap.GetWidth(), TextureBitmap.GetHeight(), 0, GL_RGB, GL_UNSIGNED_BYTE, image)
			glTexParameterf(mode, GL_TEXTURE_WRAP_S, GL_CLAMP)
			glTexParameterf(mode, GL_TEXTURE_WRAP_T, GL_CLAMP)
			glTexParameterf(mode, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
			glTexParameterf(mode, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
			glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

			glColor4f( 1, 1, 1, 1 ) # to ensure the image isn't "color corrected" :)

			glBegin( GL_QUADS )

			glTexCoord2i(0, 0)
			glVertex2i( minx, miny-h )

			glTexCoord2i(w, 0)
			glVertex2i( minx+w, miny-h )

			glTexCoord2i(w, h)
			glVertex2i( minx+w, miny )

			glTexCoord2i(0, h)
			glVertex2i( minx, miny )

			glEnd()

			glDeleteTextures(_textureName)
			
