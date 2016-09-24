import sys, nltk, re, random, string
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet as wn
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import brown

# set maximum number of blanks (per sentence), desired number of answer
# choices (per exercise), and preference for possible 'null' option here
MAX_BLANKS = 3
NUM_CHOICES = 4 # will warn/decrease if exceeds number of possible distractors
NULL_OPTION = False

tagged_sents = []
# if provided, import file passed as parameter, split sentences, and tag Parts of Speech
if len(sys.argv) > 1:
    with open(sys.argv[1], 'r') as my_file:
        sents = nltk.sent_tokenize(my_file.read())
    for sent in sents:
        tagged_sents.append(nltk.pos_tag(word_tokenize(sent)))
# else randomly intake 100 (tagged) Brown corpus sentences of certain categories
else:
    tagged_sents = random.sample(brown.tagged_sents(categories=['news','government']),100)

rpins = set()
rpin_sents = set()
in_occurrences = []
null_candidates = []
selected_null_candidates = []
lmtzr = WordNetLemmatizer()

# add 'null' option if global Boolean set to True
if NULL_OPTION:
    rpins.add('null')

for sent in tagged_sents:
    # import phrasal verb list acquired from http://www.usingenglish.com/reference/phrasal-verbs/list.html
    f = open('PhrasalVerbsComplete.txt','r')
    for w, word in enumerate(sent):
        # store phrasal verb particles (RPs) and respective sentences
        if word[1] == 'RP' and w != 0:
            rpins.add(word[0])
            rpin_sents.add(tuple(sent))
        # store phrasal verb prepositions (INs) and respective sentences
        elif re.match(r'VB.*', word[1]) and len(sent) > w+1 and sent[w+1][1] == 'IN':
            # valid occurrence if lemmatized verb and IN combination appear in list of possible phrasal verbs
            for line in (x for x in f if x.lower().strip() == lmtzr.lemmatize(word[0], wn.VERB) + " " + sent[w+1][0]):
                # keep track of prepositional verb sentences and indices of occurrences
                in_occurrences.append([tuple(sent),w])
                rpins.add(sent[w+1][0])
                rpin_sents.add(tuple(sent))
        # store phrase candidates for null option if enabled globally
        elif re.match(r'VB.*', word[1]) and NULL_OPTION:
            found_cand = False
            phrase = word[0] + " "
            wordcount = 1
            # scan the rest of current sentence
            for i in range(w+1, len(sent)):
                # keep up with current phrase candidate
                phrase += sent[i][0] + " "
                # increment word count only if non-punctuation
                if not re.match(r'\.|\,|\!|\?|\;|\:', sent[i][0]):
                    wordcount += 1
                # weed out poor candidates for null option
                if (re.match(r'VB.*|PRP|JJ|RB', sent[i][1]) and i == w+1) or re.match(r'RP|IN|TO', sent[i][1]):
                    break
                # if reach another verb or end of sentence, found null candidate
                elif re.match(r'VB.*', sent[i][1]) or i == len(sent)-1:
                    found_cand = True                    
                    break
            # further scrutinize null candidates by setting minimum number of words
            if found_cand and wordcount > 2:
                # keep track of null phrase candidate(s) and indices of locations
                null_candidates.append([tuple(sent),w])
    f.close()

# randomly select one to three null candidates, taking into consideration number of phrasal verb occurrences
if null_candidates and NULL_OPTION:
    selected_null_candidates = random.sample(null_candidates,random.sample(xrange(1,min((len(rpin_sents)//10)+2,4)),1)[0])
    for null_candidate in selected_null_candidates:
        rpin_sents.add(tuple(null_candidate[0]))

# generate key (exercises and correct answers), writing sentences and leaving RP/IN/null blank(s)
key = open('Key.txt','w')
for x, rp_sent in enumerate(rpin_sents):
    correct = ''
    numBlanks = 0
    verbs = set()
    # write exercise numbers
    key.write(str(x+1) + '.')
    for i, word in enumerate(rp_sent):
        # do not write space before punctuation
        if re.match(r'\.|\,|\!|\?|\;|\:', word[0]):
            key.write(word[0])
        elif numBlanks < MAX_BLANKS and ((word[1] == 'RP' and i != 0) or (word[1] == 'IN' and [rp_sent,i-1] in in_occurrences)):
            numBlanks += 1
            key.write(' ___')
            correct += word[0] + ', '
        elif numBlanks < MAX_BLANKS and NULL_OPTION and [rp_sent,i] in selected_null_candidates:
            numBlanks += 1
            key.write(' ' + word[0] + ' ___')
            correct += 'null, '
        else:
            key.write(' ' + word[0])
        # store lemmatized verbs to look up possible phrasal verb combos for distractor generation
        if re.match(r'VB.*', word[1]):
            verbs.add(lmtzr.lemmatize(word[0], wn.VERB))
    key.write('\n')
    
    # add possible RP/IN options for stored verbs from a given sentence via WordNet
    for verb in verbs:
        for synset in wn.synsets(verb, pos=wn.VERB):
            for lemma in (x for x in synset.lemmas() if '_' in x.name()):
                lem = nltk.pos_tag(word_tokenize(lemma.name().replace('_', ' ')))
                if verb == lem[0][0] and re.match(r'RP|IN', lem[1][1]):
                    rpins.add(lem[1][0])
                    # lower ambiguity by accepting only one phrasal verb per synset
                    break
    
    # initalize set of answer choices with correct choice
    choices = {correct}
    # randomly create and write answer choices
    num_choices = NUM_CHOICES
    while len(choices) < num_choices:
        # warn/decrease NUM_CHOICES if exceeds number of possible distractors for an exercise
        if num_choices > len(rpins) * numBlanks:
            while num_choices > len(rpins) * numBlanks:
                num_choices -= 1
            print "\nNUM_CHOICES exceeds number of possible distractors;"
            print "automatically decreased to " + str(num_choices) + " for Exercise " + str(x+1) + "."
        choice = ''
        # create and add random distractor for given number of blanks
        for i in range(numBlanks):
            choice += str(random.sample(rpins,1)[0]) + ', '
        choices.add(choice)
    choiceNum = 0
    # write choice letters and distractors in random order
    for choice in random.sample(choices, num_choices):
        key.write('     ' + string.ascii_uppercase[choiceNum] + ". " + choice[:-2])
        # indicate correct choice in printout
        if choice == correct:
            key.write('*')
        choiceNum += 1
    key.write('\n\n')
key.close()

# show output in terminal and generate exercise list (w/out correct answers) from key
with open('Exercises.txt', 'w') as exercises, open('Key.txt', 'r') as key:
    print('\n' + key.read())
    key.seek(0)
    for line in key:
        exercises.write(line.replace('*',''))

