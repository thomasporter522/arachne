import gui, sentences

def run():
	gui.run(vocabulary_file = open("vocab.txt","r"), grammar_file = open("grammar.txt","r"), message_file = open("message.txt","r"), sentence_maker = sentences, inflection_table = "inflection.xml")

if __name__ == "__main__":
	run()
