'''
Use a prefix tree to quickly look up whether a query token string is part of our data. 
'''
class PrefixTrie():
	def __init__(self, root=None):
		self.root = root

	# Print level order traversal of the trie
	def __str__(self):
		if self.root == None:
			return ""

		trie_str = ""
		queue = []
		queue.append(self.root)
		while queue:
			node = queue.pop(0)
			trie_str += str(node.val) + " "
			for char, next_node in node.links.iteritems():
				queue.append(next_node)
		return trie_str

	def add_string(self, string, item_id):
		curr_node = self.root
		for i in range(len(string)):
			char = string[i]
			if curr_node.links.get(char, None) == None:
				# Create a node
				new_node = TrieNode(string[:i+1])
				curr_node.links[char] = new_node
				curr_node = new_node
			else:
				curr_node = curr_node.links[char]
			curr_node.item_ids.append(item_id)

	# An alternative version of is_prefix
	# Return an array of item_ids if string is in trie, else return false
	def get_item_ids(self, string):
		curr_node = self.root
		for char in string:
			if curr_node.links.get(char, None) == None:
				return False
			curr_node = curr_node.links.get(char)

		return curr_node.item_ids

	def remove_item_id(self, data_token, item_id):
		curr_node = self.root
		for char in data_token:
			curr_node = curr_node.links[char]
			curr_node.item_ids.remove(item_id)

class TrieNode():
	def __init__(self, val="", links=None, item_ids=None):
		self.val = val
		if links == None:
			self.links = {}
		else:
			self.links = links
		if item_ids == None:
			self.item_ids = []
		else:
			self.item_ids = item_ids

	def __str__(self):
		return str(self.val) + " "

class Item():
	def __init__(self, item_id, item_type, score, name, timestamp):
		self.id = item_id
		self.type = item_type
		self.score = score
		self.name = name
		self.timestamp = timestamp

''' TypeHeadSearch object to encapsulate all global variables, and methods to process each command '''
class TypeHeadSearch():
	def __init__(self):
		self.trie_root = TrieNode()
		self.prefix_trie = PrefixTrie(self.trie_root)
		self.all_items = {}
		self.curr_timestamp = 0

	def process_command(self, line):
		line = line.split(" ")
		command = line[0]
		command_data = line[1:]

		if command == "ADD":
			self.add(command_data)
		elif command == "DEL":
			self.delete(command_data)
		elif command == "QUERY":
			results = self.query(command_data)
			if results:
				print " ".join(results)
			else:
				print ""
		elif command == "WQUERY":
			results = self.wquery(command_data)
			if results:
				print " ".join(results)
			else:
				print ""
		self.curr_timestamp += 1

	def add(self, data):
		item_type = data[0]
		item_id = data[1]	
		item_score = float(data[2])
		name_tokens = data[3:]
		
		# Store the item by id, for constant time retrieval
		self.all_items[item_id] = Item(item_id, item_type, item_score, " ".join(name_tokens), self.curr_timestamp)

		# Insert each word into the trie dictionary
		for token in name_tokens:
			self.prefix_trie.add_string(token.lower(), item_id)

	def delete(self, data):
		item_id = data[0]
		if self.all_items.get(item_id, None) == None:
			return

		data_tokens = self.all_items[item_id].name.split(" ")
		del self.all_items[item_id]
		# Delete an item by removing from item_ids in the prefix trie for each data token
		for token in data_tokens:
			self.prefix_trie.remove_item_id(token.lower(), item_id)

	def query(self, data):
		num_results = int(data[0])
		query_tokens = data[1:]

		return self.execute_query(num_results, query_tokens)

	def wquery(self, data):
		num_results = int(data[0])
		num_boosts = int(data[1])
		boosts_input = data[2:2 + num_boosts]
		query_tokens = data[2 + num_boosts:]

		# Make a map containing boost factors for each type (if any), as well as for each id
		boosts_map = {}
		for boost in boosts_input:
			boost = boost.split(":")
			boosts_map[boost[0]] = boosts_map.get(boost[0], 1) * float(boost[1])

		return self.execute_query(num_results, query_tokens, boosts_map)

	def execute_query(self, num_results, query_tokens, boosts=None):
		if boosts == None:
			boosts = {}

		queried_item_ids = set()
		for query_token in query_tokens:
			item_ids = self.prefix_trie.get_item_ids(query_token.lower())
			if not item_ids:
				return []
			if not queried_item_ids:
				queried_item_ids = set(item_ids)
			else:
				queried_item_ids = queried_item_ids & set(item_ids)

		# Rank the items in descending order of score
		queried_items = map(lambda id: self.all_items[id], list(queried_item_ids))
		quick_sort(queried_items, 0, len(queried_items), boosts)

		# Return the ids of the sorted list of items
		queried_items_ids = map(lambda item: item.id, queried_items)
		return queried_items_ids[:num_results]

# Helper functions, to sort items by score, breaking ties by order of insert
def partition(items, left, right, boosts=None):
	if boosts == None:		# Use none instead of {} to prevent Python mutable default parameter behavior
		boosts = {}

	pivot_index = last_small = left
	pivot = items[pivot_index]

	for i in range(left, right):
		item_score = items[i].score
		pivot_score = pivot.score

		# Apply boosts
		item_score *= (boosts.get(items[i].type, 1) * boosts.get(items[i].id, 1))
		pivot_score *= (boosts.get(pivot.type, 1) * boosts.get(pivot.id, 1))

		if item_score == pivot_score:
			# New items should be ranked higher
			if items[i].timestamp > pivot.timestamp:
				last_small += 1
				items[last_small], items[i] = items[i], items[last_small]	
		elif item_score > pivot_score:
			last_small += 1
			items[last_small], items[i] = items[i], items[last_small]

	items[last_small], items[pivot_index] = items[pivot_index], items[last_small]
	pivot_index = last_small

	return pivot_index

def quick_sort(items, left, right, boosts=None):
	if boosts == None:		
		boosts = {}

	pivot_index = partition(items, left, right, boosts)
	if pivot_index > left:
		quick_sort(items, left, pivot_index, boosts)
	if pivot_index + 1 < right:
		quick_sort(items, pivot_index+1, right, boosts)

if __name__ == '__main__':
	app = TypeHeadSearch()
	N = int(raw_input())

	for i in range(N):
		line = raw_input()
		app.process_command(line)
	