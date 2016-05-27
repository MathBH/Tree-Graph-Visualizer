#!/usr/bin/env python
#Helper Methods

#import load method and treelib
from loader import load

def loadTree(path):
	
	return load(path)

def there_is(item):
	if (item == None):
		return False
	else:
		return True

def zero_patch(n1, n2):
	if n1 == n2:
		return 0
	return 1
	
def brighten(col, amount):
	lum = 0
	for i in range(3):
		new_lum = 1-col[i]
		if new_lum > lum: lum = new_lum
		
	lum = lum*amount
	
	if len(col) == 3:
		r, g, b = col
		return r + lum, g + lum, b + lum
	if len(col) == 4:
		r, g, b, a = col
		return r + lum, g + lum, b + lum, a
	
def color_complement(col):
	if len(col) == 3:
		r, g, b = col
		return 1 - r, 1 - g, 1 - b
	if len(col) == 4:
		r, g, b, a = col
		return 1 - r, 1 - g, 1 - b, a
		
def luminescence(col):
	luminescence = 0
	for i in range(0,3):
		luminescence += col[i]
		luminescence *= 0.33
	return luminescence
	
def color_instance(col):
	if len(col) == 3:
		r, g, b = col
		return r, g, b
	if len(col) == 4:
		r, g, b, a = col
		return r, g, b, a
		
def toggle_truth_value(val):
	return not val