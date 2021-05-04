import random, re, json, itertools, copy, time
import xml.etree.ElementTree as ET 

global sequence
tense_sets = {"P":["PRS","PRF"],"S":["IMP","PPF"]}
sequence = {"PRS":tense_sets["P"],"FUT":tense_sets["P"],"FPF":tense_sets["P"],"IMP":tense_sets["S"],"PRF":tense_sets["S"],"PPF":tense_sets["S"]}

class Entry:
	# All info for lexeme
	lemma = ""
	title = ""
	stem = ""
	pos = ""
	gender = ""
	pattern = ""
	tags = []
	gloss = []
	parts = []
	
	def __init__(self, i):
		self.stem = i[0]
		self.pos = i[1]

		if self.pos == "N":
			self.gender = i[2]
			self.pattern = i[3]
			self.tags = i[4].split(".")
			self.gloss = i[5].split(".")
			
		if self.pos == "V" or self.pos == "A":
			self.pattern = i[2].split(".")[0]
			self.parts = i[2].split(".")[1:]
			self.tags = i[3].split(".")
			self.gloss = i[4].split(".")
			
		if self.pos in ["P","I","D","C","R"]: #prepositions, interjections, adverbs, conjunctions, pronouns
			self.tags = i[2].split(".")
			self.gloss = i[3].split(".")
		
		if (self.pos == "N" and self.pattern in ["3","3n"]) or self.pattern == "3t": #separate stem from title for 3rd nouns and some adjectives
			self.stem = i[0].split(".")[1]
			self.title = i[0].split(".")[0]
			
			
	def satisfies(self, c): # Does this entry qualify to be chosen as a dependent
		if c == "":
			return True
		return eval(c.replace("dependent","self"))
		
			
	def inflect(self, params):		
		# returns a Word
		request = self.pos+"/pattern"+self.pattern
	
		
		if self.pos == "V": # Special verb handling
			# Illegal forms zone	
			if params[4] == "SUB" and params[2] in ["FUT","FPF"]:
				return Word(self.stem+str(params),self,params)
				
			if params[4] == "IMP":
				if params[2] not in ["PRS","FUT"]:
					return Word(self.stem+str(params),self,params)
				if params[0] == "FIR" or (params[0] == "THR" and params[2] != "FUT") or (params[0] == "SEC" and params[2] == "FUT" and params[3] == "PAS"):
					return Word(self.stem+str(params),self,params)
					
			if params[4] == "INF":
				if params[2] not in ["PRS","FUT","PRF"]:
					return Word(self.stem+str(params),self,params)
					
			if params[4] == "PRT":
				if params[2:4] not in [["PRS","ACT"],["FUT","ACT"],["PRF","PAS"],["FUT","PAS"]]:
					return Word(self.stem+str(params),self,params)
					
			# Illegal forms zone

			
			stem = self.stem
			
			if params[4] == "PRT": # Participle havoc
				if params[2:4] == ["PRS","ACT"]:
					stem = Entry([stem+inflection.find(request+"/PP").text+"ns."+stem+inflection.find(request+"/PP").text+"nt", "A", "3t","","PAP"]).inflect([params[5],params[1],params[6]]).text
				if params[2:4] == ["FUT","ACT"]:
					stem = Entry([self.parts[1]+"ur", "A", "1","","FAP"]).inflect([params[5],params[1],params[6]]).text
				if params[2:4] == ["PRF","PAS"]:
					stem = Entry([self.parts[1], "A", "1","","PPP"]).inflect([params[5],params[1],params[6]]).text
				if params[2:4] == ["FUT","PAS"]:
					stem = Entry([stem+inflection.find(request+"/PP").text+"nd", "A", "1","","FPP"]).inflect([params[5],params[1],params[6]]).text
				return Word(stem, self, params)
				
			if params[4] == "INF": # Infinitives
			
				participleparams = params[0:4]+["PRT"]+params[5:]
					
				if params[2:4] in [["FUT","ACT"],["PRF","PAS"]]:
					return Word(self.inflect(participleparams).text+" esse", self, params) # Future active infinitives use the word's FAP and Perfect passive infinitives use the word's PPP
				if params[2:4] == ["FUT","PAS"]:
					return Word(self.parts[1]+"um"+" iri", self, params)
				if params[2:4] == ["PRF","ACT"]:
					return Word(self.parts[0]+inflection.find(request+"/PRF/ACT/INF").text, self, params)
				else:
					return Word(stem+inflection.find(request+"/"+params[2]+"/"+params[3]+"/"+params[4]).text, self, params)
					
			for item in params[0:5]: # Ignore gender and case for now
				request += "/"+item
				
			if params[2] in ["PRF","PPF","FPF"]: # Perfect tense handling
				
				stem = self.parts[0] # Perfect active forms use the perfect stem
				
				if params[3] == "PAS":
					participleparams = params[0:2]+["PRF","PAS","PRT"]+params[5:]
					stem = self.inflect(participleparams).text # Perfect passive forms use the word's PPP
					linking_verb_params = copy.copy(params)
					linking_verb_params[2] = {"PRF":"PRS","PPF":"IMP","FPF":"FUT"}[linking_verb_params[2]] # Shift the tense for the copula
					linking_verb_params[3] = "ACT" # Change to active for the copula
					linking_verb = Entry(["","V","0","",""]).inflect(linking_verb_params).text
					return Word(stem + " " + linking_verb, self, params) # PPP + copula
				
		else: # For the regular forms
			stem = self.stem
			for item in params:
				request += "/"+item
							
		if self.pos == "C":
			return Word(self.stem,self,params)
			
		if self.pos == "R":
			if params[2] == "V":
				return Word(self.stem+str(params),self,params)
			
		ending = inflection.find(request).text

		if ending == "#L#":
			form = self.title
		elif ending is None: # XML path leads to empty string
			form = stem
		else:
			form = stem+ending

		return Word(form, self, params)
		
	def choose_inflect(self, constraints):

		options = {
		"N":[["S","P"],["N","G","D","A","B","V"]],
		"C":[["M","F","N"],["FIR","SEC","THR"],["S","P"]],
		"A":[["M","F","N"],["S","P"],["N","G","D","A","B","V"]],
		"R":[["M","F","N"],["S","P"],["N","G","D","A","B","V"]],
		"V":[["FIR","SEC","THR"],["S","P"],["PRS","IMP","FUT","PRF","PPF","FPF"],["ACT","PAS"],["IND","SUB","IMP","INF","PRT"],["M","F","N"],["N","G","D","A","B","V"]]
		}
		
		if self.pos == "V":
			constrainedoptions = []
			
			for ending in endings:
				okay = True
				
				for i in range(len(constraints)):
					if not (constraints[i] is None or ending[i] == constraints[i] or ending[i] in constraints[i]):
						okay = False
						
				# Lexical inflection constraints
				if "INT" in self.tags and ending[3] == "PAS":
					okay = False
				if "IMP" in self.tags and ending[4] == "IMP": # Impersonals cannot be imperative
					okay = False
				if "IMP" in self.tags and ending[0] != "THR": # Impersonals must be third person
					okay = False
				if "IMP" in self.tags and ending[1] != "S": # Impersonals must be singular
					okay = False
					
				if okay:
					constrainedoptions.append(ending)
					
			if constrainedoptions == []:
				return None

			constraints = random.choice(constrainedoptions)
		
		if self.pos in ["N","A","V","R","C"]:
			if constraints == []:
				constraints = [None]*len(options[self.pos])

			for i in range(len(options[self.pos])):
				if constraints[i] is None:
					constraints[i] = random.choice(options[self.pos][i])
				if type(constraints[i]) is list:
					constraints[i] = random.choice(constraints[i])
					
		return self.inflect(constraints)
				
		# returns a Word given incomplete information (a Template's constraints)
		
	def get_lemma(self):
		
		if self.pos == "N" :
			if self.pattern in ["1","2","2n","4","5"]:
				return self.inflect(["S","N"]).text+", -"+inflection.find("N/pattern"+self.pattern+"/S/G").text
			return self.inflect(["S","N"]).text+", "+self.inflect(["S","G"]).text
			
		if self.pos in ["A"]:
			if self.pattern == "3t":
				return self.inflect(["M","S","N"]).text+", "+self.inflect(["M","S","G"]).text
			return self.inflect(["M","S","N"]).text+", -"+inflection.find(self.pos+"/pattern"+self.pattern+"/F/S/N").text+", -"+inflection.find(self.pos+"/pattern"+self.pattern+"/N/S/N").text
			
		if self.pos == "V":
			return self.inflect(["FIR","S","PRS","ACT","IND"]).text+", -"+inflection.find("V/pattern"+self.pattern+"/PRS/ACT/INF").text
			
		if self.pos == "R":
			return self.inflect(["M","S","N"]).text+", "+inflection.find(self.pos+"/pattern"+self.pattern+"/F/S/N").text+", "+inflection.find(self.pos+"/pattern"+self.pattern+"/N/S/N").text
			
		else:
			return self.stem

class Word:
	# Instance of lexeme
	text = ""
	entry = None
	params = []

	constraints = None # I'm not sure why this is here
	tags = []
	parent = None
	children = []
	position_number = 0
	dependencyname = ""
	punctuation = ""
	
	def __init__(self, t, e, p, d = "", ta = []):
		self.text = t
		self.entry = e
		self.params = p
		self.dependencyname = d
		self.tags = ta
		
	def satisfies(self, c): # Does this word qualify to be a parent
		if c == "":
			return True
		return eval(c.replace("parent","self"))
		
	def choose_constituents(self, complexity):
		re = []
		
		factor = 1 # Limits option additions
		if complexity < 1:
			factor = 0
			
		for item in grammar: # For each possible grammar relationship,
			itemname = item[1]
			iteminfo = item[0]
			for g in iteminfo: # For possible form,
				if self.satisfies(g[0]): # If the parent satisfies the rule
					if g[1] == "M" or (random.random() < factor*float(g[1])): # If the dependent is mandatory or chosen at random,
				
						constituent = Template(g[2],eval(g[3].replace("parent","self")).split(","),eval(g[4].replace("parent","self")),g[5], self, itemname).choose() # Find a dependent word that works
						
						if constituent is None: # If no adequate vocabulary is selected
							return None
						re.append(constituent)
						
					
						break

		return re
		# returns a list of consituents without specification
			
	def str(self):
		return self.text
	def __eq__(self, other):
		return self.text == other.text
	def __lt__(self, other):
		return self.text < other.text


class Template:
	requirements = "" # Requirements for the Entry of the dependent
	tags = [] # Tags added to the dependent upon inflection
	constraints = [] # Rules for inflecting the dependent
	position_number = 0
	punctuation = ""
	parent = None
	dependencyname = ""
	
	def __init__(self, r = "", t = [], c = [], n = "0", p = None, g=""):
		self.requirements = r
		self.tags = t
		self.constraints = c
		self.dependencyname = g
		if "." in list(n):
			self.position_number = int(n.split(".")[0])
			self.punctuation = n.split(".")[1]
		else:
			self.position_number = int(n)
			self.punctuation = ""
			
		self.parent = p
		
	def satisfies(self, e):
		statement = self.requirements.replace("dependent","e").replace("parent","self.parent")
		return eval(statement)
		
	def choose(self): # returns Word meeting the criteria
		options = []
		for e in dictionary:
			if self.satisfies(e):
				options.append(e)		
		if options == []:
			return None
		
		random.shuffle(options)
		
		for option in options:
			word = option.choose_inflect(self.constraints)
			if word is not None:
				word.tags = self.tags
				word.position_number = self.position_number
				word.punctuation = self.punctuation
				word.dependencyname = self.dependencyname
				return word
		return None

def initiate_phrases():
	pass
	
def display_tree(root, n):
	if n == 0:
		print(root.text+" (Main Verb)")
	if n > 0:
		print(n*"\t"+"> "+root.text+" ("+root.dependencyname+")")
		
	for child in root.children:
		display_tree(child, n+1)
	
def compress_tree(root):
	worditems = []
	sequence = [(child.position_number, child) for child in root.children]+[(0,root)]
	for item in [x[1] for x in sorted(sequence)]:
		if item == root:
			worditems.append(item.text)
		else:
			if item.punctuation == "C":
				worditems.append(",")
				worditems.extend(compress_tree(item))
				worditems.append(",")
			else:
				worditems.extend(compress_tree(item))	
	return worditems

def get_sentence(length, demo):
	current = [] # stack of tuples (Word, its parent)
	root = Template("dependent.pos == 'ROOT'").choose()
	sentence = (root,None,0)
	current.append(sentence)
	complexity = length

	while len(current) > 0:
		node, parent, depth = current.pop()

		if parent is not None:
			parent.children = parent.children + [node]
			if demo:
				input("\nEnter for next:\n")
				display_tree(root,-1)

		constituents = node.choose_constituents(complexity)
		if constituents is None:
			return None
		
		for constituent in constituents:
			current.append( (constituent, node, depth + 1) )
			
		complexity -= 1
	
		if depth >= 14:
			if demo:
				print("\nMaximum depth reached. Sentence cancelled.")
			return None
		
	if demo:
		input("\nEnter to finish sentence:")
		
	worditems = compress_tree(root)
	text = ""
	i = 0
	while i < len(worditems):
		if set(worditems[i:]) == {","}:
			break
			
		if worditems[i] in [",",""]:
			while worditems[i+1] == ",":
				worditems.pop(i+1)
			text += worditems[i]
		else:
			text += (" "+worditems[i])
		i += 1
	
	return text.strip().capitalize()+"."
	
#---------------------------------#
	
def ingest_vocab(f, i):
	global inflection
	inflection = ET.parse(i).getroot()
	
	lines = f.readlines()
	dictionary = []
	for line in lines:
		if line != "" and line[0] != "#":
			line = re.sub(r"[\n\t\s]*", "", line)
			dictionary.append(Entry(line.split(",")))
	return dictionary
	
def ingest_grammar(f):
	re = []
	for line in f.readlines():
		if line[0] == "+":
			item = [i.strip() for i in line[1:].split("@")]
			re[-1].append(item)
		elif line != "" and line[0] != "#":
			item = [i.strip() for i in line.split("@")]
			re.append([item])
	return re
	
def define_endings(selections):
	global endings
	
	options1 = [["PRS","IMP","FUT","PRF","PPF","FPF"],["ACT","PAS"],["IND","IMP","INF","PRT","SUB"]]
	options2 = [["FIR","SEC","THR"],["S","P"],["M","F","N"],["N","G","D","A","B","V"]]	
	endings = []

	for selection in selections:
		params = [None]*7
		params[2] = options1[0][selection[0]]
		params[3] = options1[1][selection[1]]
		params[4] = options1[2][selection[2]]
		
		for option in itertools.product(*options2):
			params[0] = option[0]
			params[1] = option[1]
			params[5] = option[2]
			params[6] = option[3]
			
			legal = True
			if params[4] == "SUB" and params[2] in ["FUT","FPF"]:
					legal = False
			if params[4] == "IMP":
				if params[2] not in ["PRS","FUT"]:
					legal = False
				if params[0] == "FIR" or (params[0] == "THR" and params[2] != "FUT") or (params[0] == "SEC" and params[2] == "FUT" and params[3] == "PAS"):
					legal = False	
			if params[4] == "INF":
				if params[2] not in ["PRS","FUT","PRF"]:
					legal = False
			if params[4] == "PRT":
				if params[2:4] not in [["PRS","ACT"],["FUT","ACT"],["PRF","PAS"],["FUT","PAS"]]:
					legal = False
			if legal:
				endings.append(copy.copy(params))
	
def run(d, g, e, i, l, dem):
	global dictionary
	dictionary = d
	global grammar
	grammar = [([i[a].split("|") for a in range(1,len(i))],i[0]) for i in g] 
	define_endings(e)
	global inflection
	inflection = ET.parse(i).getroot()
	
	return get_sentence(l, dem)
