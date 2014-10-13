meta_data = raw_input()
meta_data = map(lambda x: int(x),meta_data.split(" "))

num_topics = meta_data[0]
num_questions = meta_data[1]
num_queries = meta_data[2]

# Read the next T lines for topics
topics = {}
for i in range(num_topics):
	topic_line = raw_input()
	topic_line = topic_line.split(" ")
