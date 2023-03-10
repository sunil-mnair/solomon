def find_vowels(word,vowels):
    for letter in word:
        if letter in vowels:
            vowels[letter] += 1
    return vowels

def find_words(lettersinput,wordlist):

    letters = [letterinput for letterinput in lettersinput]
    answers=[]
    max_length = ""
    word_cookies=[{}]

    def checkword(word):
        localletters=letters.copy()
        wordanswer = True
        for letter in word:
            if letter in localletters:
                localletters.remove(letter)
            else:
                wordanswer=False
                break
        if wordanswer == True:
            answers.append(word)

    #with app.open_resource('static/engmix.txt') as file:
    #with open('engmix.txt','r') as file:
        #wordlist = file.readlines()

    for word in wordlist:
        word = word.decode()
        word = word.rstrip("\n")
        checkword(word)

    finalanswers = []
    longestword=0
    for answer in answers:
        length = len(answer)
        if length > longestword:
            longestword=length


    for x in range(longestword+1):
        finalanswers.append([])

    for answer in answers:
        finalanswers[len(answer)-1].append(answer)

    max_length += f"The max length of words possible is {longestword} letters long"

    for index, list in enumerate(finalanswers,1):
        if index != len(finalanswers):
            if list:
                word_cookies[0][index] = []
                list.sort()
                for word in list:
                    word_cookies[0][index].append(f'{word}')

    print(word_cookies)
    #word_cookies = word_cookies.split('\n')
    return max_length,word_cookies