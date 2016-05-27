
					README
					------
------------------------------------------------------------------------------------

===========
DESCRIPTION:
===========

The following is a program that takes a tree graph and makes a visual representation
and gives the user tools to help discuss and evaluate said graph.

Files for testing are located in the "graph" folder in this repository

============
REQUIREMENTS:
============

You will need python 2.7.11 and kivy installed in order to run this program.

Kivy can be found at https://kivy.org/#download
Python can be found at https://www.python.org/

============
INSTALLATION:
============

Do you have the folder on your computer? Then it's already installed! Whoo!

==========
HOW TO RUN:
==========

Double click on graph_visualizer.py or open it with python to activate it.

================
GRAPH VISUALIZER:
================

Basic Commands:
---------------

"Open file" button is situated in the upper left corner.

-	Hold down the middle mouse button and drag to move the camera.
-	Use the mouse wheel to zoom in or out.
-	Use left click to select a node/edge.
-	To select a second node/edge, hold down ctrl and left click the other.
-	To display a node/edge's data list, double click on it.

Each node/edge holds a list of data. The tag of the node can be any of these data
members. By default, the first data member is set as the tag though this can be
changed.

Tag Commands:
-------------
-	e: hide/unhide edge tags 
-	ctrl+e: swap edge tag
-	n: hide/unhide node tags 
-	ctrl+n: swap node tag
-	t: swap selected node/edge’s tag

There are also commands for visual answers to certain questions one might have
in regards to a tree such as the path to root, or what subtree do two nodes share.

Visualizer Commands:
--------------------
-	1: highlight path from node to tree root
-	2: draw line through nodes at same depth
-	3: highlight common subtree of two selected nodes

Aesthetics Command:
-------------------

-	c: set graph color
-	ctrl+c: set selected edge/node color

------------------------------------------------------------------------------------

========
CREDITS:
========

- treelib-1.3.1 - by Xiaming Chen (https://github.com/caesar0301/treelib)

- python-graph-master - by this lovely band of people -> https://github.com/pmatiello/python-graph

------------------------------------------------------------------------------------