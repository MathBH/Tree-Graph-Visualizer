from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.scatter import Scatter
from kivy.graphics.transformation import Matrix
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from helper import zero_patch, there_is, brighten, color_complement, luminescence, color_instance, toggle_truth_value
from loader import load
from kivy.uix.bubble import Bubble
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.colorpicker import ColorPicker
from kivy.factory import Factory
from kivy.graphics import Color, Rectangle
from kivy.config import Config
import os

#import treelib
from treelib import Tree

#This is to make weight[] selection more legible
left = 0
right = 1

max_val = 128

menu_bar_height = 30

scale_treshold_a = 75
scale_treshold_b = 45

zoom_speed = 15
zoom_out_limit = 1
zoom_in_limit = 1500

highlight_val = 0.85
default_highlight_color = [(1,0.4,0.4,1),(0.6,0.87,1,1),(1.,0.76,0.42,1)]

popup_size = (400,400)

default_node_radius=40
default_border_size=100

class TreeHelper(): # Provides helper methods for tree data, in order to make the main code easier to read
	buffer = []

	@staticmethod
	def get_common_root(t,nid1,nid2):
	
		path_nid1 = reversed(list(t.rsearch(nid1)))
		path_nid2 = reversed(list(t.rsearch(nid2)))
		
		last_step = 0
		for step1, step2 in zip(path_nid1,path_nid2):
			if step1 != step2:
				return last_step
			last_step = step1
		
		return last_step
		
	@staticmethod
	def get_common_subtree(t,nid1,nid2):
	
		a = TreeHelper.get_common_root(t,nid1,nid2)
		return t.subtree(a)
		
	@staticmethod
	def get_at_depth(t, nid, depth):
		if nid == 0 and depth == 1:
			TreeHelper.buffer.append(nid)
			
		if depth <= 1:
			return nid
		
		for cid in t.get_node(nid).fpointer:
			TreeHelper.buffer.append(TreeHelper.get_at_depth(t,cid,depth-1))
			
	@staticmethod
	def dump_buffer():
		buff = TreeHelper.buffer
		TreeHelper.buffer = []
		return buff
		
	@staticmethod
	def distance_to_root(t, nid):
		return len(list(t.rsearch(nid)))
		
class ColorMenu(Popup):
	item_tools = None
	target = None
	
	def __init__(self, **kwargs):
		super(ColorMenu, self).__init__(**kwargs)

	def take_item_tools(self,item_tools):
		self.item_tools = item_tools
		
	def update_target(self, instance, value):
		if self.target != None:
			if type(self.target) is list:
				for item in self.target:
					if item != None: item.set_color(value)
			else:
				self.target.set_color(value)
		
		self.item_tools.get_ctrl().refresh_graph()
	
	def set_target(self,item):
		self.target = item
	
	def bind_functions(self):
		self.content.bind(color=self.update_target)
	
	def get_ctrl(self):
		return self.parent.get_ctrl()

class TagWidget(FloatLayout):
	def __init__(self, **kwargs):
		super(TagWidget, self).__init__(**kwargs)

class CircularButton(Button):
	def __init__(self, **kwargs):
		super(CircularButton, self).__init__(**kwargs)
		self.bind(on_press=self.interact)

	def interact(self, value):
		if self.get_ctrl().touch_button == 'left':
			self.background_color = brighten(self.color, highlight_val)

	def get_ctrl(self):
		return self.parent.get_ctrl()
		
class Leveler(FloatLayout):
	def __init__(self, y_anchor, color, **kwargs):
		super(Leveler,self).__init__(**kwargs)
		
		self.y_anchor = y_anchor
		
		self.color = color
		
class Node(FloatLayout):

	i = None
	highlit = False
	truncate = False
	data = []
	
	tag_widget = None
	null_tag = None
	tag_index=0
	
	info_box = None
	info_text = ""
	
	tag_index=0

	def __init__(self, i, data=None, color=None, **kwargs):
		super(Node,self).__init__(**kwargs)
		self.i = i
		self.pos_x, self.pos_y = self.pos
		
		self.ids['handle'].bind(on_release=self.interact)
		
		if there_is(color):
			self.color = color
		if there_is(data):
			self.data = data
			
		self.ids['handle'].color = self.color
		
		#tag to be displayed if the node has no data
		self.null_tag = "node "+str(self.i)
		
		self.tag = self.data[self.tag_index] if (len(self.data)>0) else self.null_tag
		self.info_box=Popup(title=self.tag, content=Label(text='<data void>'), size_hint=(None,None), size=popup_size)
		
		#Size correcting in case the tag is of length 128
	
	def generate_tag(self):
		self.tag_widget = TagWidget(target_x=self.x,target_y=self.y,target_radius=self.radius,tag=self.tag)
		self.tag_widget = TagWidget(target_x=self.x,target_y=self.y,target_radius=self.radius,tag=self.tag)
	
	def show_tag(self):
		self.parent.add_widget(self.tag_widget)
	
	def hide_tag(self):
		self.parent.remove_widget(self.tag_widget)
		
	def generate_info_text(self):
		attrs = self.get_ctrl().graph_data.nodeAttrs
		if len(attrs) <= 0: return
		for attr, val in zip(attrs, self.data):
			self.info_text += str(attr) + ": " + str(val) + "\n"
		self.info_box.content.text = self.info_text
		
	def rotate_tag(self):
		#If there is no data, do not execute
		if len(self.data) <= 0: return
		
		#This mod formula increments the index by 1 but returns to 0 if it would pass the max index
		new_index = (self.tag_index + 1)%len(self.data)
		self.change_tag(new_index)
		
	def change_tag(self, idx):
		if idx < 0 or idx >= len(self.data):
			return
		self.tag_index = idx
		
		self.refresh_tag_data()
	
	def refresh_tag_data(self):
		if len(self.data) != 0:
			self.tag = self.data[self.tag_index]
		else:
			self.tag = self.null_tag
			
		self.info_box.title = self.tag

		if self.truncate:
			self._truncate_tag()
		self.tag_widget.tag = self.tag
		
	def interact(self, value):
		if self.get_ctrl().touch_button == 'left':
			if self.get_ctrl().double_click:
				self.info_box.open()
			self.get_ctrl().select(self)
			
	def select(self):
		if not self.selected:
			self.selected = 1
		
	def deselect(self):
		if self.selected:
			self.selected = 0
				
	def highlight(self, color):
		self.glow_color = color
		self.glow_active = 1
		
	def unlight(self):
		self.glow_active = 0
		
	def dye(self, color):
		self.ids['handle'].color = color

	def undye(self):
		self.ids['handle'].color = self.color

	def set_color(self, col):
		self.color = color_instance(col)
		
		if not self.highlit:
			self.refresh_handle()
			
	def refresh_handle(self):
		self.ids['handle'].color = self.color
		
	def _truncate_tag(self):				#under the hood method
		if len(self.tag) > 5:
			self.tag = self.tag[:5] + "..."
		
	def truncate_tag(self):				#actual method
		self.truncate = True
		self.refresh_tag_data()
		
	def extend_tag(self):				#actual method
		self.truncate = False
		self.refresh_tag_data()
		
	def get_ctrl(self):
		return self.parent.get_ctrl()
		

class Edge(FloatLayout):

	i = None
	highlit = False
	truncate = False
	data = []
	
	tag_widget = None
	null_tag = None
	tag_index=0
	
	info_box = None
	info_text = ""
	
	def __init__(self, i, tail=None, head=None, data=None, color=None, **kwargs):
		super(Edge, self).__init__(**kwargs)
		
		if there_is(tail):
			self.tail_x, self.tail_y = tail
		if there_is(head):
			self.head_x, self.head_y = head
		if there_is(color):
			self.normal_color = color
		if there_is(data):
			self.data = data
			
		self.ids['handle'].color = self.normal_color
		
		self.x_mod = zero_patch(self.head_x, self.tail_x)
		self.y_mod = zero_patch(self.head_y, self.tail_y)
		self.i = i
		
		#tag to be displayed if the edge has no data
		self.null_tag = "edge "+str(self.i)
		
		self.tag = self.data[self.tag_index] if (len(self.data)>0) else self.null_tag
		self.info_box=Popup(title=self.tag, content=Label(text='<data void>'), size_hint=(None,None), size=popup_size)
		
		self.ids['handle'].bind(on_release=self.interact)
	
	def generate_tag(self):
		handle_x, handle_y = (self.head_x + self.tail_x)*0.5, (self.head_y + self.tail_y)*0.5
		self.tag_widget = TagWidget(target_x=handle_x,target_y=handle_y,target_radius=self.handle_size,tag=self.tag)
		self.tag_widget = TagWidget(target_x=handle_x,target_y=handle_y,target_radius=self.handle_size,tag=self.tag)
		
	def show_tag(self):
		self.parent.add_widget(self.tag_widget)
	
	def hide_tag(self):
		self.parent.remove_widget(self.tag_widget)
		
	def generate_info_text(self):
		attrs = self.get_ctrl().graph_data.edgeAttrs
		if len(attrs) <= 0: return
		for attr, val in zip(attrs, self.data):
			self.info_text += str(attr) + ": " + str(val) + "\n"
		self.info_box.content.text = self.info_text
		
	def rotate_tag(self):
		if len(self.data) <= 0: return
		new_index = (self.tag_index + 1)%len(self.data)
		self.change_tag(new_index)
		
	def change_tag(self, idx):
		if idx < 0 or idx >= len(self.data):
			return
		self.tag_index = idx
		
		self.refresh_tag_data()
	
	def refresh_tag_data(self):
	
		if len(self.data) != 0:
			self.tag = self.data[self.tag_index]
		else:
			self.tag = self.null_tag
		
		if self.truncate: self._truncate_tag()
		self.tag_widget.tag = self.tag
		self.info_box.title = self.tag
	
	def interact(self, value):
		if self.get_ctrl().touch_button == 'left':
			if self.get_ctrl().double_click:
				self.info_box.open()
			self.get_ctrl().select(self)
			
	def select(self):
		if not self.selected:
			self.selected = 1
		
	def deselect(self):
		if self.selected:
			self.selected = 0
				
	def highlight(self, color):
		self.glow_color = color
		self.glow_active = 1
		
	def unlight(self):
		self.glow_active = 0
			
	def dye(self, color):
		self.ids['handle'].color = color
			
	def undye(self):
		self.ids['handle'].color = self.normal_color

	def set_color(self, col):
		self.normal_color = color_instance(col)
		
		if not self.highlit:
			self.refresh_handle()
		return
			
	def refresh_handle(self):
		self.ids['handle'].color = self.color
		
	def _truncate_tag(self):				#under the hood method
		if len(self.tag) > 5:
			self.tag = self.tag[:5] + "..."
		
	def truncate_tag(self):				#actual method
		self.truncate = True
		self.refresh_tag_data()
		
	def extend_tag(self):				#actual method
		self.truncate = False
		self.refresh_tag_data()
		
	def get_ctrl(self):
		return self.parent.get_ctrl()
		
class treeData(): #Object holding relevant data for visualizing the tree

	t = None
	treeVis = None
	axis = [0,0]
	offset = []
	
	graph_width = 0
	graph_height = 0
	
	graph_rightmost = 0
	graph_leftmost = 0
	graph_bottommost = 0
		
	border = default_border_size
	node_radius= default_node_radius

	def __init__(self, tree):

		#Load tree
		self.t = tree
		
		#By definition a tree graph has a number of edges equivalent to the number of nodes - 1
		self.treeVis = TreeVisualizer(num_nodes=self.t.size(), num_edges=self.t.size()-1, node_radius=self.node_radius, scale_index=50) #tree visualizer is initialized with correct node number
		#TODO: also get correct edge number
		
		#Weight will be used to keep track of how many nodes there are on each side of
		#A given node. Offset is the offset between a node and its parent.
		weight = [None] * self.t.size()
		self.offset = [0] * self.t.size()
	
		#Itterate by Depth First Search in reverse to move from the leaves up to the root node.
		nodeIds = self.t.expand_tree(0,Tree.DEPTH)
		
		#For each node, calculate its weight, based on its children, and re-arrange its
		#children according to their weight.
		for nid in reversed(list(nodeIds)):
			node = self.t.get_node(nid)
			
			weight[nid] = [0,0]
		
			if not node.is_leaf():
				midPoint = len(node.fpointer)/2
			
				#For every child, determine if it is left or right from the parent by
				#comparing its index to the midPoint
				for idx, cid in enumerate(node.fpointer):
					if idx < midPoint:
						#LEFT OF PARENT
						self.offset[cid] = idx - midPoint - weight[cid][right]
						weight[nid][left] += self.offset[cid]
					
					if idx >= midPoint:
						#RIGHT TO PARENT
						self.offset[cid] = idx - midPoint + 1 - weight[cid][left]
						weight[nid][right] += self.offset[cid]
		
	def build_items(self, pid=None, nid=0, altroot_pos=None):
		#Draws a single node and the edge leading up to it (unless is a root), and then
		#calls it's self on its children.
	
		#If no value was passed to the optional arguments nid and altroot_pos, 
		#we are starting from the root of the tree.
		root_pos = self.axis if (altroot_pos == None) else altroot_pos
		
		#Function variables for the sake of clarity
		offset = self.offset
		t = self.t
		root_x, root_y = root_pos
		
		#Add the offset of the node under consideration
		pos = [root_x + offset[nid], root_y]
		#Get node
		node = t.get_node(nid)
		input_data = node.data
		
		if pos[0] < self.graph_leftmost:
			self.graph_leftmost = pos[0]
			
		if pos[0] > self.graph_rightmost:
			self.graph_rightmost = pos[0]
		
		#If not root, move the node down by the scale value
		if nid != 0: pos[1] -= 1
		
		if pos[1] < self.graph_bottommost: self.graph_bottommost = pos[1]
		
		#paint the node and the edge leading up to it
		self.treeVis.add_node(nid, pos, input_data)
		
		'''
		For the edge id, since this is a tree, each child only has one parent. Thus, we will use the child the
		edge is leading up to as the edge's index, since we know this will always be a unique value for edges.
		'''
		
		if nid != 0: self.treeVis.add_edge((pid, nid),root_pos,pos)
		
		for cid in t.get_node(nid).fpointer:
			self.build_items(nid, cid, pos) #call build_items on children
			
	def load_tree(self):
		
		self.build_items()
		
		self.treeVis.generate_tree()
		
		self.graph_width = self.graph_rightmost - self.graph_leftmost
		self.graph_height = -self.graph_bottommost
		
		self.treeVis.graph_width = self.graph_width
		self.treeVis.graph_height = self.graph_height
		
		self.treeVis.item_pos = -self.graph_leftmost, -self.graph_bottommost
		
		self.treeVis.ids['graph'].bounding_box = self.treeVis.graph_size[0], self.treeVis.graph_size[1]
		
		#Scale graph to fit in window#
		graph_window_height = Window.height-menu_bar_height

		if self.treeVis.graph_width*graph_window_height > self.treeVis.graph_height*Window.width:
			self.treeVis.scale_index = (Window.width - self.border*2)/self.treeVis.graph_width	
		else:
			self.treeVis.scale_index = (graph_window_height - self.border*2)/self.treeVis.graph_height
		
		self.treeVis.graph.refresh()
		
		#Center graph items#
		self.treeVis.graph.center= Window.width/2, graph_window_height/2

class GraphWidget(FloatLayout):
	
	def __init__(self, scale_index=None, **kwargs):
		super(GraphWidget,self).__init__(**kwargs)
		
		if there_is(scale_index):
		
			self.scale_index = scale_index
	
	def zoom_in(self, focus_pos):
		
		if self.scale_index + zoom_speed > zoom_in_limit:
			return
		
		focus_x, focus_y = focus_pos
		
		x_correction = ((focus_x - self.x)/self.width)*self.x_units*zoom_speed
		y_correction = ((focus_y - self.y)/self.height)*self.y_units*zoom_speed
		
		self.x -= x_correction
		self.y -= y_correction
		
		self.scale_index += zoom_speed
		
		if self.scale_index > scale_treshold_a and not self.parent.tags_hidden:
		
			self.parent.extend_tags()
			
		elif self.scale_index > scale_treshold_b and self.parent.tags_hidden:
		
			self.parent.show_tags()
		
	def zoom_out(self, focus_pos):
	
		if self.scale_index - zoom_speed < zoom_out_limit:
			return
		
		focus_x, focus_y = focus_pos
		
		x_correction = ((focus_x - self.x)/self.width)*self.x_units*zoom_speed
		y_correction = ((focus_y - self.y)/self.height)*self.y_units*zoom_speed
		
		self.x += x_correction
		self.y += y_correction
		
		self.scale_index -= zoom_speed
		
		self.refresh()
			
	def refresh(self):
	
		if self.scale_index < scale_treshold_b and not self.parent.tags_hidden:
		
			self.parent.hide_tags()
			
		if self.scale_index < scale_treshold_a:
		
			self.parent.truncate_tags()
		
	def move(self, transform_vector):
		delta_x, delta_y = transform_vector
		
		self.center_x += delta_x
		self.center_y += delta_y
		
	def get_ctrl(self):
		return self.parent.get_ctrl()
	
class GraphItems(FloatLayout):

	def __init__(self, scale_index=None, **kwargs):
		super(GraphItems,self).__init__(**kwargs)
		
		if there_is(scale_index):
			self.scale_index = scale_index
			
	def get_ctrl(self):
		return self.parent.get_ctrl()
		
class TreeVisualizer(Widget):
	graph = None
	graph_items = None
	screen = None
	tags_hidden = True
	tags_truncated = False
	
	node_widgets = []
	edge_widgets = []
	
	highlighters = None
	leveler = None
	
	class highlighter():
		color = None
		id = None
		parent = None
	
		def __init__(self, color, parent, id):
			self.parent = parent
			self.id = id
			self.set_color(color)
		
		def set_color(self, color):
			self.color = color_instance(color)
			
		def get_ctrl(self):
			return self.parent.get_ctrl()
	
	def __init__(self, num_nodes=max_val, num_edges=max_val, node_radius=default_node_radius, **kwargs):
		super(TreeVisualizer, self).__init__(**kwargs)
		
		self.node_radius = node_radius
		
		#Node widget list and edge list are initialized with a given size so to allow us to insert items
		#using their id as an index
		self.node_widgets=[None]*num_nodes
		self.edge_widgets=[None]*num_edges
		
		self.graph = self.ids['graph']
		self.graph_items = self.ids['graph_items']
		self.screen = self.ids['screen']
		
	def add_node(self, i, input_position, input_data=None, input_color=None):
		new_node = Node(i, data=input_data, color=input_color, pos=input_position, radius=self.node_radius)
		new_node = Node(i, data=input_data, color=input_color, pos=input_position, radius=self.node_radius)
		self.node_widgets[i] = new_node
	
	def hash_edge_key(self,key):
		if len(key) == 2:
			return (key[1] - 1)
		print "ERROR, TRIED TO HASH ", key, " AS EDGE KEY"
		return -1
	
	def add_edge(self, key, input_tail, input_head, input_data=None, input_color=None):
		new_edge = Edge(key, data=input_data, color=input_color, tail=input_tail, head=input_head)
		new_edge = Edge(key, data=input_data, color=input_color, tail=input_tail, head=input_head)
		self.edge_widgets[self.hash_edge_key(key)]=new_edge
		
	def build_leveler(self,y_level,color):
		self.remove_leveler()
		self.leveler = Leveler(y_level,color)
		self.ids['back_drop'].add_widget(self.leveler)
		
	def remove_leveler(self):
		if there_is(self.leveler):
			self.ids['back_drop'].remove_widget(self.leveler)
		
	def generate_tree(self):
		for part in (self.edge_widgets + self.node_widgets):
			if part != None:
				self.graph_items.add_widget(part)
				part.generate_info_text()
				part.generate_tag()
		self.show_tags()
		
		#By default, edge info is hidden for trees since all the data is in the nodes.
		if type(self.get_ctrl().graph_data) == Tree:
			self.get_ctrl().hide_etags()
	
	def show_tags(self):
		if self.tags_hidden:
			if not self.get_ctrl().ntags_hidden:
				for node in self.node_widgets:
					node.show_tag()
			if not self.get_ctrl().etags_hidden:
				for part in self.edge_widgets:
					if part != None:
						part.show_tag()
			self.tags_hidden = False
				
	def hide_tags(self):
		if not self.tags_hidden:
			for part in (self.edge_widgets + self.node_widgets):
				if part != None:
					part.hide_tag()
			self.tags_hidden = True
			
	def truncate_tags(self):
		if not self.tags_truncated:
			for part in (self.edge_widgets + self.node_widgets):
				if part != None:
					part.truncate_tag()
			self.tags_truncated = True
			
	def extend_tags(self):
		if self.tags_truncated:
			for part in (self.edge_widgets + self.node_widgets):
				if part != None:
					part.extend_tag()
			self.tags_truncated = False
			
	def build_highlighters(self):###Move highlighters to another class perhaps
		self.highlighters = [self.highlighter(default_highlight_color[0], self, 0),self.highlighter(default_highlight_color[1], self, 1),self.highlighter(default_highlight_color[2], self, 2)]
				
	def edge_to_node(self,nid):
		return self.edge_widgets[nid - 1]
				
	def get_ctrl(self):
		return self.parent.get_ctrl()

class ScreenWidget(Widget):
	def on_touch_down(self,touch):
		self.get_ctrl().touch_button = touch.button
		self.get_ctrl().double_click = touch.is_double_tap
		if touch.button == 'middle':
			touch.grab(self)
		elif touch.button == 'scrollup':
			self.parent.graph.zoom_in(touch.pos)
		elif touch.button == 'scrolldown':
			self.parent.graph.zoom_out(touch.pos)
		elif touch.button == 'left':
			if not self.get_ctrl().ctrl_down:
				if touch.y < Window.height - menu_bar_height:
					self.get_ctrl().clear_selection()
			
	def on_touch_move(self, touch):
		if touch.grab_current is self:
			x, y = touch.pos
			x0, y0 = touch.ppos
			transform_vector = (x-x0, y-y0)
			self.parent.graph.move(transform_vector)
			
	def on_touch_up(self, touch):
		if touch.y < Window.height - menu_bar_height:
			if touch.grab_current is self:
				touch.ungrab(self)
			
			if touch.button == 'left':
				self.get_ctrl().graph_tools.clear()

			
	def get_ctrl(self):
		return self.parent.get_ctrl()

class Control(Widget):
	touch_button = ""
	double_click = False
	selection_1, selection_2 = None, None
	auto_function = [None,None,None]
	
	graph_tools = []
	
	node_tools = []
	edge_tools = []
	ntags_hidden = False
	etags_hidden = False
	
	ctrl_down = False
	
	graph_data = None
	node_numAttrs = 0
	edge_numAttrs = 0
	
	graph_type = None
	
	graph_tools = None
	item_tools = None
	
	def __init__(self, **kwargs):
		super(Control,self).__init__(**kwargs)
		
		self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
		self._keyboard.bind(on_key_down=self._on_keyboard_down)
		self._keyboard.bind(on_key_up=self._on_keyboard_up)
	
	def reset(self):
		self.touch_button = ""
		self.double_click = False
		self.selection_1, selection_2 = None, None
		self.auto_function = [None,None,None]
	
		self.graph_tools = []
	
		self.node_tools = []
		self.edge_tools = []
		self.ntags_hidden = False
		self.etags_hidden = False
	
		self.ctrl_down = False
	
		self.graph_data = None
		self.node_numAttrs = 0
		self.edge_numAttrs = 0
	
		self.graph_type = None
	
		self.graph_tools = None
		self.item_tools = None
		
	def _keyboard_closed(self):
		self._keyboard.unbind(on_key_down=self._on_keyboard_down)
		self._keyboard = None
		
	def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
		if keycode[1] == 'lctrl':
			if self.ctrl_down == False:
				self.ctrl_down = True
		if keycode[1] == 'n':
			if self.ctrl_down:
				self.item_tools.rotate_ntags()
			else:
				self.toggle_ntag_visibility()
				
		if keycode[1] == 'e':
			if self.ctrl_down:
				self.item_tools.rotate_etags()
			else:
				self.toggle_etag_visibility()
		if keycode[1] == '1':
			if self.ctrl_down:
				self.graph_tools.set_highlighter_color(0)
			else:
				self.graph_tools.toggle_active(0)
				
		if keycode[1] == '2':
			if self.ctrl_down:
				self.graph_tools.set_highlighter_color(1)
			else:
				self.graph_tools.toggle_active(1)
				
		if keycode[1] == '3':
			if self.ctrl_down:
				self.graph_tools.set_highlighter_color(2)
			else:
				self.graph_tools.toggle_active(2)
			
		if keycode[1] == 't':
			self.item_tools.switch_tag()
			
		if keycode[1] == 'c':
			if self.ctrl_down:
				self.item_tools.set_color()
			else:
				self.item_tools.set_colors()

			'''
		if keycode[1] == '1':
			for item in self.get_visualizer().node_widgets + self.get_visualizer().edge_widgets:
				if item != None: item.set_color((1,0.2,0.25,1))
		if keycode[1] == '2':
			for item in self.get_visualizer().node_widgets + self.get_visualizer().edge_widgets:
				if item != None: item.set_color((0.2,0.8,0.5,1))
				'''
		return True
		
	def _on_keyboard_up(self, keyboard, keycode):
		if keycode[1] == 'lctrl':
			self.ctrl_down = False
		return True
	
	#GRAPH MANAGEMENT
	
	def take_graph_data(self, g):
		self.graph_data = g
		self.graph_type = type(g)
	
	def get_graph_node(self,i):
		return self.parent.visualizer.node_widgets[i]
		
	def get_graph_edge(self,i):
		graph_vis = self.parent.visualizer
		return graph_vis.edge_widgets[graph_vis.hash_edge_key(i)]
	
	def hide_ntags(self):
		if not self.get_visualizer().tags_hidden:
			if not self.ntags_hidden:
				self.ntags_hidden = True
				for node in self.get_visualizer().node_widgets:
					node.hide_tag()
				
	def show_ntags(self):
		if not self.get_visualizer().tags_hidden:
			if self.ntags_hidden:
				self.ntags_hidden = False
				for node in self.get_visualizer().node_widgets:
					node.show_tag()
				
	def toggle_ntag_visibility(self):
		if self.ntags_hidden:
			self.show_ntags()
		else:
			self.hide_ntags()
	
	def hide_etags(self):
		if not self.get_visualizer().tags_hidden:
			if not self.etags_hidden:
				self.etags_hidden = True
				for edge in self.get_visualizer().edge_widgets:
					if edge != None: edge.hide_tag()
		
	def show_etags(self):
		if not self.get_visualizer().tags_hidden:
			if self.etags_hidden:
				self.etags_hidden = False
				for edge in self.get_visualizer().edge_widgets:
					if edge != None: edge.show_tag()
		
	def toggle_etag_visibility(self):
		if self.etags_hidden:
			self.show_etags()
		else:
			self.hide_etags()
		
	def rotate_ntags(self):
		for node in self.get_visualizer().node_widgets:
			node.rotate_tag()
		'''
		The tags weren't updating their position until the graph was moved. As a quick fix
		I've opted to 'nudge' the graph after rotating tags. This ought to only be temporary though.
		'''
		
		self.get_visualizer().graph.move((0.000000000001,0.000000000001))
		
	def rotate_etags(self):
		for edge in self.get_visualizer().edge_widgets:
			if edge != None: edge.rotate_tag()
		'''
		The tags weren't updating their position until the graph was moved. As a quick fix
		I've opted to 'nudge' the graph after rotating tags. This ought to only be temporary though.
		'''
		
		self.get_visualizer().graph.move((0.000000000001,0.000000000001))
		
	def select(self,item):
		if item.i in (self.selection_1, self.selection_2):
			return
		elif self.selection_1 == None:
			item.select()
			self.selection_1 = item.i
		elif self.selection_2 == None:
			item.select()
			self.selection_2 = self.selection_1
			self.selection_1 = item.i
		else:
			self.clear_selection()
			item.select()
			self.selection_1 = item.i
		self.run_auto()
			
	def clear_selection(self):
		if there_is(self.selection_1):
			if type(self.selection_1) is int:
				self.get_graph_node(self.selection_1).deselect()
			elif type(self.selection_1) is tuple:
				self.get_graph_edge(self.selection_1).deselect()
				
		if there_is(self.selection_2):
			if type(self.selection_2) is int:
				self.get_graph_node(self.selection_2).deselect()
			elif type(self.selection_2) is tuple:
				self.get_graph_edge(self.selection_2).deselect()
		
		self.selection_1, self.selection_2 = None, None

		
	def toggle_active(self, id):
		if there_is(self.auto_function[id]):
			self.auto_function[id] = None
		else:
			self.auto_function[id] = self.graph_tools.index[id]
		
		self.refresh_graph()
		
	def run_auto(self):
		for function in self.auto_function:
			if there_is(function): function(self.selection_1,self.selection_2)
		
	def refresh_graph(self):
		self.graph_tools.clear()
		self.run_auto()
		
	def get_visualizer(self):
		return self.parent.visualizer
		
	def get_window(self):
		return self.parent
	
class WindowWidget(AnchorLayout):
	control = None
	visualizer = None
	popup_menu = None
	
	def __init__(self, **kwargs):
		super(WindowWidget,self).__init__(**kwargs)
		
		self.control = Control()
		self.add_widget(self.control)
		
	def take_visualizer(self,v):
		self.visualizer = v
		
		self.add_widget(self.visualizer)
		
		self.get_ctrl().item_tools = ItemTools(self.visualizer)
		self.get_ctrl().item_tools.connect_to_graph(self.visualizer, self.get_ctrl())
		
		if self.get_ctrl().graph_type is Tree:
			self.get_ctrl().graph_tools = TreeTools(self.visualizer, self.get_ctrl())
		
	def take_graph_data(self,g):
		self.control.take_graph_data(g)
	
	def get_ctrl(self):
		return self.control
		
	def reset(self):
		if not self.visualizer is None:
			self.remove_widget(self.visualizer)
			
			visualizer = None
			self.get_ctrl().item_tools = None
		
		self.control.reset()
		
			
class ItemTools():
	disabled = ObjectProperty(None)
	control = None
	visualizer = None
	color_picker = ColorMenu(title='<tag>', content=ColorPicker(), size_hint=(None,None), size=popup_size)
	color_picker.bind_functions()
	color_picker_shown = False
	
	def __init__(self, visualizer):
		self.visualizer = visualizer
		
	def connect_to_graph(self,visualizer,control):
		self.visualizer = visualizer
		self.control = control
		self.color_picker.take_item_tools(self)
		
	def enable(self):
		self.disabled = False
		
	def disable(self):
		self.disabled = True
		
	def set_color(self):
		target = None
		
		id = self.get_ctrl().selection_1		
		if type(id) is int:
			target = self.visualizer.node_widgets[id]
		elif type(id) is tuple:
			target = self.visualizer.edge_widgets[self.visualizer.hash_edge_key(id)]
		if target is None:
			print "ERROR: tried to set the color of None type object"
			return
		
		self.color_picker.set_target(target)
		self.color_picker.title="Color Chooser"
		self.color_picker.open()
		
	def switch_tag(self):
		id = self.get_ctrl().selection_1
		target = None
		if type(id) is int:
			target = self.visualizer.node_widgets[id]
		elif type(id) is tuple:
			target = self.visualizer.edge_widgets[self.visualizer.hash_edge_key(id)]
		if target is None:
			print "ERROR: edge/node "+str(id)+" not found"
			return
		target.rotate_tag()
		self.visualizer.graph.move((0.000000000001,0.000000000001))

	def set_colors(self):
		target = self.visualizer.edge_widgets + self.visualizer.node_widgets
		
		self.color_picker.set_target(target)
		self.color_picker.title="Color Chooser"
		self.color_picker.open()
		
	def rotate_ntags(self):
		self.get_ctrl().rotate_ntags()
		
	def rotate_etags(self):
		self.get_ctrl().rotate_etags()
		
	def toggle_ntag_visibility(self):
		self.get_ctrl().toggle_ntag_visibility()
	
	def toggle_etag_visibility(self):
		if self.etags_hidden:
			self.show_etags()
		else:
			self.hide_etags()
		
	def show_color_picker(self):
		self.visualizer.graph.add_widget(self.color_picker)
		self.color_picker_shown = True
		
	def hide_color_picker(self):
		self.visualizer.graph.remove_widget(self.color_picker)
		self.color_picker_shown = False
		
	def get_ctrl(self):
		return self.control
		
class ExtendedTools():
	pass	#this will incorporate set_color_theme or set theme (where 
			#you pick a color and all the highlighters auto generate)
	
class TreeTools():

	control = None
	tree_widget = None
	tree_data = None
	index = []
		
	def __init__(self, tree_widget, control):
		self.control = control
		self.tree_widget = tree_widget
		self.tree_data = self.control.graph_data
		self.index = [self.path_to_root, self.at_same_depth, self.subtree]
		
	def set_highlighter_color(self, num):
		color_picker = self.get_ctrl().item_tools.color_picker
		
		color_picker.set_target(self.tree_widget.highlighters[num])
		color_picker.title="Color Chooser"
		color_picker.open()
		
	def path_to_root(self, nid1, nid2):	#[0]#
		nid = None
		color = self.tree_widget.highlighters[0].color
		
		if type(nid1) is int:
		
			nid = nid1
			
		elif type(nid2) is int:
		
			nid = nid2

		if nid == None:
			return
		
		path_gen = self.tree_data.rsearch(nid)
		
		for step_id in path_gen:
		
			self.tree_widget.node_widgets[step_id].highlight(color)
			
			if step_id != self.tree_data.root:
			
				self.tree_widget.edge_to_node(step_id).highlight(color)

	def at_same_depth(self, nid1, nid2):	#[1]#
		nid = None
		color = self.tree_widget.highlighters[1].color
		
		if type(nid1) is int:
		
			nid = nid1
			
		elif type(nid2) is int:
		
			nid = nid2
		
		if nid == None:
			return
		
		target_node = self.tree_widget.node_widgets[nid]
		
		self.tree_widget.build_leveler(target_node.pos_y,color)

	def subtree(self, nid1, nid2):	#[2]#
		color = self.tree_widget.highlighters[2].color
		
		if not (type(nid1) == int) or not (type(nid2) == int):
			return
		
		subtree = TreeHelper.get_common_subtree(self.tree_data, nid1, nid2)
		
		for node in subtree.all_nodes():
		
			nid = node.identifier
			self.tree_widget.node_widgets[nid].dye(color)
			
			if nid != subtree.root:
			
				self.tree_widget.edge_to_node(nid).dye(color)

	def toggle_active(self, num):
		self.get_ctrl().toggle_active(num)
				
	def clear(self):
		for item in self.tree_widget.edge_widgets + self.tree_widget.node_widgets:
			if item != None: 
				item.unlight()
				item.undye()
		self.tree_widget.remove_leveler()
			
	def get_ctrl(self):
		return self.control
			
class LoadDialog(FloatLayout):
	load = ObjectProperty(None)
	cancel = ObjectProperty(None)

class Root(FloatLayout):
	loadfile = ObjectProperty(None)
	text_input = ObjectProperty(None)

	def dismiss_popup(self):
		self._popup.dismiss()

	def show_load(self):
		if there_is(self.ids['window'].get_ctrl().item_tools):
			self.ids['window'].get_ctrl().refresh_graph()
		content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
		self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
		self._popup.open()

	def load(self, path, filename):
		window = self.ids['window']
		
		window.reset()
		
		tree = load(os.path.join(path, filename[0]))
		tdata = treeData(tree)
		
		window.take_graph_data(tdata.t)
		window.take_visualizer(tdata.treeVis)
		
		tdata.load_tree()
		
		window.visualizer.build_highlighters()

		self.dismiss_popup()

			
class Graph_VisualizerApp(App):
	Config.set('graphics','window_state','maximized')
	Config.write()
	'''
    def build(self):
		
		t = load("BigTGraph.txt")
		td = treeData(t)
		parent = WindowWidget()
		parent.take_graph_data(td.t)
		parent.take_visualizer(td.treeVis)
		td.load_tree()
		
		return parent
	'''	

Factory.register('Root', cls=Root)
Factory.register('LoadDialog', cls=LoadDialog)

if __name__ == '__main__':
    Graph_VisualizerApp().run()

	
'''
How the program works:
---------------------

hierarchy:

	WindowWidget:
		
		relevant instance vars
		-------------
			popup_menu:
		
		children
		--------
			Control:
			TreeVisualizer:
				children
				--------
					ScreenWidget: #think of this not as the screen on which stuff is dislayed, more like a 
								  screen in front of a zoo exhibit. Its purpose is to track touch commands 
								  "over" all the rest of the widgets.#
					GraphWidget:
						children
						--------
							graph_items(GraphItems): #Node layer#
				
As aforementioned, from just about any widget, the command "get_ctrl()" is available and returns Control.
'''

#TODO: edit to use ObjectProperty to make classes cleaner (especially their initializers) clean stuff up and set load dialog to icons update dialog box