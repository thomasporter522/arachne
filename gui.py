import tkinter as tk
from tkinter import *
from tkinter.ttk import Separator, Style
import itertools

global MAX_RESULTS 
MAX_RESULTS = 30
global DISPLAY_SIZE
DISPLAY_SIZE = 8

global sentences
sentences = []

global position
position = 0

global demomode
demomode = False

def run(vocabulary_file, grammar_file, message_file, sentence_maker, inflection_table):
	
	dictionary = sentence_maker.ingest_vocab(vocabulary_file, inflection_table)
	grammar = sentence_maker.ingest_grammar(grammar_file)
	grammars = [i[0][0] for i in grammar]
	
	root = tk.Tk()
	root.title("Arachne Latin")
	root.geometry('{}x{}'.format(1000, 800))
	
	frame0 = tk.Frame(root, width=400, height=100) #Title
	frame1 = tk.Frame(root, width=600, height=100) #Instructions
	frame2 = tk.Frame(root, width=400, height=400) #Results
	frame3 = tk.Frame(root, width=400, height=300) #Initiator space
	frame4 = tk.Frame(root, width=400, height=700) #Vocabulary selection
	frame5 = tk.Frame(root, width=400, height=300) #Ending selection
	frame6 = tk.Frame(root, width=400, height=400) #Grammar selection
	
	# 0 ------------------------------------------------
	
	Label(frame0, text="Arachne", font=("Helvetica", 26)).grid()
	
	# 1 ------------------------------------------------
	
	Label(frame1, text="".join(message_file.read()), font=("Helvetica", 10)).grid()

	# 2 ------------------------------------------------
	
	
	def scrolling(a):
		
		global position
		position += int(a)
		if position < 0:
			position = 0
			
		display_results()

	bar0 = Scrollbar(frame2)
	bar0.pack()
	
	results = []
	for i in range(DISPLAY_SIZE):
		var = StringVar()
		var.set("")
		results.append(var)
		Label(frame2, textvariable = var, wraplength = 195).pack()
	
	bar0.config(command=scrolling)
		
	# 3 ------------------------------------------------

	def display_results():
		global position
		
		for i in range(DISPLAY_SIZE):
			results[i].set("")
			
		for i in range(position,position + DISPLAY_SIZE):
			if i < len(sentences):
				sentence = sentences[i]
				if sentence is None:
					sentence = "Error: you have not selected sufficient vocabulary items to construct a sentence with this grammar."
				results[i-position].set("\n"+str(i+1)+". "+sentence)
			elif (position + DISPLAY_SIZE > len(sentences) and len(sentences) >  DISPLAY_SIZE) or (len(sentences) < DISPLAY_SIZE and position > 0):
				position = position-1
				display_results()
		
	def go():
		selected_vocab = [dictionary[i] for i in [0]+[int(a+1) for a in vocab.curselection()]] #The offset and adding [0] is to ensure that ROOT is included
		selected_grammar = []
		for i in [int(a) for a in grambox.curselection()]:
			selected_grammar.extend(grammar[i])
				
		if len(grambox.curselection()) == 0 or grambox.curselection()[0] != 0:
			results[0].set("Please select 'Sentence' if you want a sentence.")
			for i in range(1,MAX_RESULTS):
				results[i].set("")
			root.update_idletasks()
			return 

		clear_illegal_forms(endings)
		selected_endings = []
		for i,j,k in itertools.product(range(6),range(5),range(2)):
			if i in endings[j+5*k].curselection():
				selected_endings.append([i,k,j]) # Tense, Voice, Mood
		
		if t.get() == "":
			number = 0
		else:
			number = min(MAX_RESULTS, abs(round(float(t.get()))) )
			
		if s.get == "":
			length = 0
		else:
			length = min(10, abs(round(float(s.get()))) )
			
		rs = []
		
		for i in range(number):
			rs.append(sentence_maker.run(selected_vocab, selected_grammar, selected_endings, inflection_table, length, demomode))
		if demomode:
			input("\nFinished")
			
		global sentences
		sentences = rs
		global position
		position = 0
		
		if len(sentences) > 0:
			display_results()
		
		root.update_idletasks()
		
	def toggle():
		global demomode
		demomode = not demomode
		demobutton.config(text = {True:"Demo: On", False:"Demo: Off"}[demomode])
		
	Label(frame3, text = "Number of sentences to generate: ").grid()
	t = Entry(frame3)
	t.insert(END, "1")
	t.grid()
	Label(frame3, text = "Length Limitation: ").grid()
	s = Entry(frame3)
	s.insert(END, "10")
	s.grid()
	Button(frame3, text="Go", command=go).grid()

	demobutton = Button(frame3, text = "Demo: Off", command=toggle)
	demobutton.grid()

	# 4 ------------------------------------------------
	bar1 = Scrollbar(frame4)
	bar1.pack(side=RIGHT, fill=Y)
	
	words = [w.get_lemma() for w in dictionary[1:]]

	vocab = Listbox(frame4, yscrollcommand=bar1.set, selectmode=MULTIPLE, width = 30, height = 30, exportselection = FALSE)
	for w in words:
		vocab.insert(END, w)
	[vocab.select_set(i) for i in range(0,len(words))]
	vocab.pack()

	bar1.config(command=vocab.yview)

	# 5 ------------------------------------------------
	toplabels = "Indicative,Imperative,Infinitive,Participle,Subjunctive".split(",")
	sidelabels = "Present,Imperfect,Future,Perfect,Pluperfect,Future Perfect".split(",")
	#Button(frame5, "SELECT-ALL BUTTON").grid(row=0,column=0)
	Label(frame5, text = "Active").grid(row=0,column=1,columnspan=5)
	Label(frame5, text = "Passive").grid(row=0,column=6,columnspan=5)

	for i,j in itertools.product(range(1,8),range(11)):
		if i == 1 and j > 0:
			Label(frame5, text = toplabels[(j-1)%len(toplabels)] ).grid(row=i,column=j)
		elif j == 0 and i > 1:
			Label(frame5, text = sidelabels[(i-2)%len(sidelabels)] ).grid(row=i,column=j)
			
	endings = []
	for j in range(1,11):
		endings.append( Listbox(frame5, selectmode=MULTIPLE, exportselection = FALSE, width = 5, height = 6, font = (30)) )
		for i in range(6):
			endings[-1].insert(END,"_______")
		endings[-1].grid(row=2,column=j,rowspan=6)
		
	[ [l.select_set(i) for i in range(0,l.size())] for l in endings]
	
	clear_illegal_forms(endings)
	
	Separator(frame5, orient = "vertical").grid(row=0,column=6,rowspan=8,sticky=("W","NS"))
	Style(root).configure("TSeparator",background="BLACK")

	# 6 ------------------------------------------------
	bar2 = Scrollbar(frame6)
	bar2.pack(side=RIGHT, fill=Y)

	grambox = Listbox(frame6, yscrollcommand=bar2.set, selectmode=MULTIPLE, width = 30, height = 30, exportselection = FALSE)
	for i in grammars:
		grambox.insert(END, i)
	[grambox.select_set(i) for i in range(0,len(grammars))]
	grambox.pack()
	
	bar2.config(command=grambox.yview)


	# Configuration
	frame0.grid(row=0,column=0,columnspan=1)
	frame1.grid(row=0,column=1,columnspan=2)
	frame2.grid(row=2,column=0)
	frame3.grid(row=1,column=0)
	frame4.grid(row=2,column=1)
	frame5.grid(row=1,column=1,columnspan=2)
	frame6.grid(row=2,column=2)

	root.mainloop()

def clear_illegal_forms(endings):

	for j in range(0,10):
		legal = [0,1,2,3,4,5]
		if j in [1,6,3]: #imp or active participle
			legal = [0,2]
		if j in [2,7]: #Inf
			legal = [0,2,3]	
		if j == 8:
			legal = [2,3]
		if j in [4,9]: #subj
			legal = [0,1,3,4]
		
		for l in {0,1,2,3,4,5} - set(legal):
			endings[j].selection_clear(l)
