import random
import os

def jumble(sentence):


  sentence = sentence.split()

  new_sentence = []

  for word in sentence:

    positions = list(range(1,len(word)-1))

    jumble = ''

    if len(word) == 3:
        jumble += word[0]
        jumble += word[2]
        jumble += word[1]

        new_sentence.append(jumble)

    elif len(word) == 4:
        jumble += word[0]
        jumble += word[2]
        jumble += word[1]
        jumble += word[3]

        new_sentence.append(jumble)

    elif len(word) > 4:
        jumble += word[0]
        for _ in word[1:-1]:
            index = random.choice(positions)
            jumble += word[index]
            positions.remove(index)

        jumble += word[-1]

        if jumble == word:
            jumble(word)
        else:
            new_sentence.append(jumble)
    else:
        new_sentence.append(word)

    file_path = os.getcwd()+'/mysite/text_files/'

    with open(file_path+"typoglycemia.txt","a") as f:
        f.write(" ".join(sentence) + '\n')
        f.write(" ".join(new_sentence) + '\n')

  return " ".join(new_sentence)
