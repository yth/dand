# Standard imports
import xml.etree.cElementTree as ET
import re

# For validation phase
# import cerberus
# import schema

# My imports
from pprint import pprint
from collections import defaultdict
from collections import Counter
from time import time
from csv import DictWriter
import string

# CONSTANTS

MIN_LAT = 42.3409
MAX_LAT = 42.4162
MIN_LON = -71.1995
MAX_LON = -71.0251
TAGS =  ("node", "way") # 'relation' for added spiciness
# SCHEMA = schema.schema # For validation phase

# PATH CONSTANTS
XML_PATH = "Data\\cambridge.xml"
NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

# FIELD CONSTANTS
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid',
			'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

# RE "CONSTANTS"

LOWER = re.compile(r'^([a-z]|_)*$')
LOWER_COLON = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
STREET_TYPE = re.compile(r'\b\S+\.?$', re.IGNORECASE)

# Street Ending Data

safe_words = [	"Lane", "Road", "Way", "Park", "Mall", "Row", "Main",
				"East", "West", "Elm", "Silk", "odd", "estimate",
				"even", "actual", "A", "Bay", "O'Brien", "F.", "Bow",
				"1/2", "One", "DeWolfe", "D", "6", "floor", "DMSE,",
				"(Physics,", ",", "40A-F", "1-B", "W20-557", "33,",
				"S-1155", "-"
]

addr_values = Counter()
questionable_words = Counter()

word_transforms = {
	"MA" : "Massachusetts",
	"US" : "United States",
	"MA-" : "Massachusetts",
	"MASSACHUSETTS" : "Massachusetts",
	"St" : "Street",
	"ST" : "Street",
	"St." : "Street",
	"st" : "Street",
	"St," : "Street",
	"Ave" : "Avenue",
	"Ave." : "Avenue",
	"Rd" : "Road",
	"Dr" : "Drive",
	"Pkwy" : "Parkway",
	"Pl" : "Plaza",
	"Sq" : "Square",
	"Sq." : "Square",
	"Ct" : "Court",
	"Hwy" : "Highway",
	"ma" : "Massachusetts",
	"Arlington." : "Arlington,",
	"WAY," : "Way,",
	"LOMASNEY" : "Lomasney",
	"ROOF" : "Roof",
	"LEVEL" : "Level"
}

# Helper Functions

def get_element(file_name, tags=TAGS):
	"""Yield element if it is the right type of tag"""

	context = ET.iterparse(file_name, events=('start', 'end'))
	_, root = next(context)
	for event, element in context:
		if event == 'end' and element.tag in tags:
			yield element
			root.clear()

def shape_element(element,
				node_attr_fields=NODE_FIELDS,
				way_attr_fields=WAY_FIELDS,
				problem_chars=PROBLEMCHARS,
				default_tag_type="regular"):
	"""Clean and shape node or way XML element to Python dict"""

	node_attribs = {}
	way_attribs = {}
	way_nodes = []
	tags = []  # Handle secondary tags the same way for both node and way elements

	# YOUR CODE HERE
	if element.tag == 'node':
		node_attribs['changeset'] = element.attrib['changeset']
		node_attribs['id'] = element.attrib['id']
		node_attribs['lat'] = element.attrib['lat']
		node_attribs['lon'] = element.attrib['lon']
		node_attribs['timestamp'] = element.attrib['timestamp']
		node_attribs['uid'] = element.attrib['uid']
		node_attribs['user'] = element.attrib['user']
		node_attribs['version'] = element.attrib['version']

		for i in element.iter():
			if i.tag == 'tag':
				tag_dict = {}
				tag_dict["id"] = node_attribs['id']
				tag_dict["value"] = i.attrib['v']

				if problem_chars.match(i.attrib['k']):
					print(i.attrib['k'])
					continue

				if ':' in i.attrib['k']:
					n = i.attrib['k'].find(':')
					tag_dict['type'] = i.attrib['k'][:n]
					tag_dict['key'] = i.attrib['k'][n+1:]

				else:
					tag_dict['key'] = i.attrib['k']
					tag_dict['type'] = default_tag_type

				tags.append(tag_dict)

		return ({'node': node_attribs, 'node_tags': tags})

	elif element.tag == 'way':
		way_attribs['changeset'] = element.attrib['changeset']
		way_attribs['id'] = element.attrib['id']
		way_attribs['timestamp'] = element.attrib['timestamp']
		way_attribs['uid'] = element.attrib['uid']
		way_attribs['user'] = element.attrib['user']
		way_attribs['version'] = element.attrib['version']

		n = 0
		for i in element.iter():
			if i.tag == 'tag':
				tag_dict = {}
				tag_dict["id"] = way_attribs['id']
				tag_dict["value"] = i.attrib['v']

				if problem_chars.match(i.attrib['k']):
					print(i.attrib['k'])
					continue

				if ':' in i.attrib['k']:
					n = i.attrib['k'].find(':')
					tag_dict['type'] = i.attrib['k'][:n]
					tag_dict['key'] = i.attrib['k'][n+1:]
				else:
					tag_dict['key'] = i.attrib['k']
					tag_dict['type'] = default_tag_type

				tags.append(tag_dict)

			elif i.tag == 'nd':
				node_dict = {}
				node_dict['id'] = element.attrib['id']
				node_dict['node_id'] = i.attrib['ref']
				node_dict['position'] = n

				n += 1

				way_nodes.append(node_dict)

		return ({'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags})

"""Validation Phase
def validate_element(element, validator, schema=SCHEMA):
	# Raise ValidationError if element does not match schema
	if validator.validate(element, schema) is not True:
		field, errors = next(validator.errors.iteritems())
		message_string = "\nElement of type '{0}' has the following errors:\n{1}"
		error_string = pprint.pformat(errors)

		raise Exception(message_string.format(field, error_string))
"""

# Exploration Tests // Filters

def in_box(lat, lon):
	return lat <= MAX_LAT and lat >= MIN_LAT and \
		lon <= MAX_LON and lon >= MIN_LON

def bad_zip(num_str):
	# Bad zip are likely 4 digits (missing leading 0) 
	# or has more than 5 digit

	# Cambridge Zip Code Include: 
	# 02114, 02138, 02140, 02142, 02238, 02134, 02139, 02141, 02163
	potential_zips = ["2114", "2138", "2140", "2142", "2238", "2134", 
					  "2139", "2141", "2163"]

	if num_str in potential_zips:
		return True

	return len(num_str) > 5

def good_word(word):
	# Filter out words that are likely not needed to be checked manually
	# Abbreviation longer than 3 letters are very rare
	# No punctual
	# Is in title form (istitle() returns true)
	return len(word) > 3 and word.istitle() and word.isalpha() \
		   and word.lower() != "pkwy"

def long_zip(zip):
	return len(zip) == 10 and zip[:5].isdigit() and zip[6:].isdigit \
		   and zip[5] == '-'

def door_number(word):
	return word.isdigit() or word[:-1].isdigit()

def multi_door(word):
	nums = ""
	if "," in word:
		nums = [x.strip() for x in word.split(",")]

	elif "-" in word:
		nums = [x.strip() for x in word.split("-")]

	for num in nums:
		if not num.isdigit():
			return False
	return True

# Main

def main():
	"""
	Validation phase is removed due to shape_element pass validation for
	the whole dataset passed into it. It's removed thereafter to improve
	performance and simply code.
	"""

	# Counters for keeping track of useful information in the data
	node_type = Counter()
	node_users = Counter()
	way_users = Counter()
	key_cntr = Counter()
	boxed_out = defaultdict(int)
	years = Counter()
	node_tags = Counter()
	node_tag_types = Counter()
	way_tags = Counter()
	way_tag_types = Counter()
	total_node_edits = 0
	total_way_edits = 0

	# Initiate csv writers for creating csv files for different data
	with open(NODES_PATH, 'w') as nodes_file, \
		open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
		open(WAYS_PATH, 'w') as ways_file, \
		open(WAY_NODES_PATH, 'w') as way_nodes_file, \
		open(WAY_TAGS_PATH, 'w') as way_tags_file:

		nodes_writer = DictWriter(nodes_file, NODE_FIELDS)
		node_tags_writer = DictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
		ways_writer = DictWriter(ways_file, WAY_FIELDS)
		way_nodes_writer = DictWriter(way_nodes_file, WAY_NODES_FIELDS)
		way_tags_writer = DictWriter(way_tags_file, WAY_TAGS_FIELDS)

		nodes_writer.writeheader()
		node_tags_writer.writeheader()
		ways_writer.writeheader()
		way_nodes_writer.writeheader()
		way_tags_writer.writeheader()

		for element in get_element(XML_PATH):
			type = element.tag

			element = shape_element(element)

			# both node and way information
			years[element[type]["timestamp"][0:4]] += 1

			# Correct addr information
			for e in element[type+"_tags"]:
				if e["type"] == "addr":
					if e["value"].isdigit():
						if not bad_zip(e["value"]):
							continue
						else:
							questionable_words[e["value"]] += 1

					if long_zip(e["value"]):
						e["value"] = e["value"][:5]
						continue

					if multi_door(e["value"]):
						continue

					words = e["value"].split()

					for word in words:
						if word not in safe_words:
							if good_word(word) or \
								(word[-1] == "," and good_word(word[:-1])):
								continue
							if multi_door(word):
								continue

							if word in word_transforms.keys():
								word = word_transforms[word]
							elif "," in word:
								sub_words = word.split(",")
								for sub_word in sub_words:
									sub_word.strip()

									if door_number(sub_word):
										continue

									if sub_word in word_transforms.keys():
										sub_word = word_transforms[sub_word]
									else:
										questionable_words[word] += 1
										addr_values[e["value"]] += 1
								# use Oxford comma
								word = ", ".join(sub_words) 
							else:
								questionable_words[word] += 1
								addr_values[e["value"]] += 1

					e["value"] = " ".join(words)

			# node information
			if type == "node":
				if not in_box(float(element[type]["lat"]),
							  float(element[type]["lon"])):
					boxed_out["node"] += 1
					continue

				node_type[type] += 1
				node_users[element[type]["user"]] += 1
				total_node_edits += int(element[type]["version"])

				""" # Analyze node tag information
				for e in element["node_tags"]:
					for key in e.keys():
						# id, value, key, type

						# id = numerical id
						# value = description of item
						# key = summary of item, type
						# type - regular, addr, various other types
						node_tags[key] += 1

						if key == "type":
							node_tag_types[e[key]] += 1
				"""

				# Write to CSV
				try:
					nodes_writer.writerow(element['node'])
					node_tags_writer.writerows(element['node_tags'])
				except:
					pass

			# way information
			if type == "way":

				node_type[type] += 1
				way_users[element[type]["user"]] += 1
				total_way_edits += int(element[type]["version"])

				""" # Analyze way tag information
				# 'way_tags'
				for e in element["way_tags"]:
					for key in e.keys():
						# id, value, key, type

						# id = numeric id
						# value = Descriptions, or ways to find more info
						# key = type information
						# type = type information - regular, massgis, addr
						way_tags[key] += 1

						if key == "type":
							way_tag_types[e[key]] += 1
				"""

				try:
					ways_writer.writerow(element['way'])
					way_nodes_writer.writerows(element['way_nodes'])
					way_tags_writer.writerows(element['way_tags'])
				except:
					pass

	# Printing Information about the data
	print("Total Number of Nodes: {}".format(node_type["node"] + node_type["way"]))
	print("Individual Node Types and Quantity:")
	pprint(node_type)

	print()

	print("Number of nodes outside of map box:")
	pprint(boxed_out)

	print()

	print("Changes made to information in Year:")
	for key in sorted(years.keys()):
		print("{}: {}".format(key, years[key]))

	print()

	print("Node tags:")
	pprint(node_tags)
	pprint(node_tag_types)

	print()

	print("Way tags:")
	pprint(way_tags)
	pprint(way_tag_types)

	print()

	print("Node Users:")
	pprint(node_users.most_common(10))
	print(len(node_users.keys()))

	node_singles = 0
	node_edits = 0
	for key in node_users.keys():
		n = node_users[key]
		node_edits += n
		if n == 1:
			node_singles += 1

	print("Only One Edit: {}".format(node_singles))	
	print("Total Node Edits: {}".format(total_node_edits))

	print()

	print("Way Users:")
	pprint(way_users.most_common(10))
	print(len(way_users.keys()))

	way_singles = 0
	way_edits = 0
	for key in way_users.keys():
		n = way_users[key]
		way_edits += n
		if n == 1:
			way_singles += 1

	print("Only One Edit: {}".format(way_singles))	
	print("Total Way Edits: {}".format(total_way_edits))

	print()

	# pprint(questionable_words.most_common(10))
	# pprint(questionable_words)
	# print(len(questionable_words))

	# pprint(addr_values.most_common(10))
	# pprint(addr_values)
	# print(len(addr_values))


# Start Execution
if __name__ == "__main__":
	main()