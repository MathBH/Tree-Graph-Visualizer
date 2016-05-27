#!/usr/bin/env python

from pygraph.classes.digraph import digraph
import sys
import treelib
from treelib import Tree
from treelib import Node

def isInt(val):
	try:
		int(val)
		return True
	except ValueError:
		return False

def isFloat(val):
	try:
		float(val)
		return True
	except ValueError:
		return False

def load(path):

	gtype = None
	graph = None
	nodes = []

	#TEMP: LOAD FILE FROM PATH#
	file = open(path,"r",0)
	#TEMP#

	gtype = file.next()
	gtype = int(gtype)

	if (gtype == 0):
		graph = Tree()
		nodes = []

	if (gtype == 1):
		graph = digraph()		

	graph.nodeAttrs = []
	graph.edgeAttrs = []
	
	for linenum,line in enumerate(file):
		if (linenum == 0): 
			parts = line.split()

			nodeAttrs = parts[1].split(';')
			numNodeAttrs = nodeAttrs.pop(0)
			graph.nodeAttrs = nodeAttrs
			continue

		if (linenum == 1):
			for node in line.split():
				tokens = node.split(';')
				index = tokens.pop(0)
				if (isInt(index)):
					index = int(index)
					if (gtype == 0):
						nodes.append(Node(identifier=index,data=tokens))
						if (index == 0):
							graph.add_node(nodes[0])
					if (gtype == 1):
						graph.add_node(index, attrs=tokens)
					continue

		if (linenum == 2):
			if (gtype == 0):
				numEdges = int(line)
			if (gtype == 1):
				parts = line.split()

				lineAttrs = parts[1].split(';')
				numLineAttrs = lineAttrs.pop(0)
				continue

		if (linenum > 2):
			#CHECK THAT PARTS ARE INT
			parts = line.split()
			tail = int(parts[0])
			head = int(parts[1])

			if (gtype == 0):
				graph.add_node(nodes[head],tail)

			if (gtype == 1):
				attributes = parts[2].split(';')
				weight = attributes.pop(0)
				graph.add_edge((tail,head),weight,attrs=attributes)
	return graph