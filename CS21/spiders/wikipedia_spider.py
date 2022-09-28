# CS021E, Jordan Bourdeau Final Project
# This program will take user input for a text file to read from as a submission file
# The program will also take user input for the wikipedia page of the paper's topic
# The program will scrape the text from the wikipedia page into a string, compared the submission file's sentences line by line, and track how many sentences matches there are as well as which sentences it is which match
# The program will iterate through the first 50 links on the wikipedia page's reference text section and repeat this process, incrementing the number of sentence matches and the matched sentences for every source
# Using the number of matches, the program will assign the paper a raw score equivalent to the number of matches, run it through a function which scales it so if 20% or more of the sentences are matches it will give a 10, and display a corresponding text message based on the score.
# The program will also provide the user with the list of matched sentences so they can manually review them to see if they were intentional matches or poor citation

import scrapy

from scrapy.crawler import CrawlerProcess

import os

MAX_PLAGIARISM_SCORE = 10
ARBITRARY_PLAGIARISM_WORD_COUNT_NUMBER = 7
PLAGIARISM_NUM_TO_SCALE_TWENTY_PERCENT = 50
NO_PLAGIARISM_LOWER_BOUND = 0
LOW_PLAGIARISM_LOWER_BOUND = 3
MODERATE_PLAGIARISM_LOWER_BOUND = 5
HIGH_PLAGIARISM_LOWER_BOUND = 7
MAX_PLAGIARISM_LOWER_BOUND = 9

# The code setting up the scrapy class is copied from the scrapy tutorial site since we didn't go over classes in this class
# Source 1: https://docs.scrapy.org/en/latest/intro/tutorial.html
# Source 2: https://www.youtube.com/watch?v=ve_0h4Y8nuI&list=PLhTjy8cBISEqkN-5Ku_kXG4QW33sxQo0t&ab_channel=buildwithpython
# Some specific portions are cited above the code if it was copied over or inspired from the sources



def main():

    # Gets the name for the submission file to check against
    submissionFile = take_submission()

    # Barring the numPages and items variables, the class definition was set up in the buildwithpython youtube tutorial
    class searchSpider(scrapy.Spider):

        numPages = get_num_pages()

        items = {"Matches": 0, "Sentences": []}

        name = "wikipedia"
        print("Please enter the wikipedia page for the topic of the paper.")
        start_urls = [
            get_url()
        ]
        custom_settings = {
            'DEPTH_LIMIT': 1,
            'DEPTH_PRIORITY': 1,
            'DNS_TIMEOUT': 5
        }

        def parse(self, response):

            # Figured out how to get the variables from class scope to go in here during emails with professor
            numPages = self.numPages

            items = self.items

            pageCount = 0

            # This was inspired from the buildwithpython youtube tutorial (adapted for this purpose)
            # This extracts all the text in paragraph elements from the webpage as a bunch of list items
            paragraphs = response.css('p *::text').extract()

            # This iterates through the paragraphs list and builds one comprehensive string for the source from it
            paragraphsString = ""
            for line in paragraphs:
                paragraphsString += line

            # This will run the detection algorithm to see if each line is also in the scraped text
            numMatches, plagiarizedSentences = sentence_match(submissionFile, paragraphsString)

            # There were some instances where the same thing might be flagged multiple times
            # This code only will append items to the items["Matches"] list is they aren't in it
            # Additionally, for every sentence which was already in the list, it will subtract 1 from the number of matches
            for sentence in plagiarizedSentences:
                if sentence not in items["Sentences"]:
                    items["Sentences"].append(sentence)
                else:
                    numMatches -= 1
            items["Matches"] += numMatches

            # This code is inspired buildwithpython youtube tutorial (adapted to this specific scraper)
            citations = response.css('div.reflist > ol > li > span.reference-text > cite > a ::attr(href)').extract()

            # This code is for troubleshooting, uncomment it if you would like to see this step
            # check_plagiarism(items["Matches"], submissionFile, items["Sentences"])

            # This code is in part from the buildwithpython youtube tutorial (iterating through links, the if statement is made by me)
            for link in citations:
                # This controls how many pages it scrapes through
                if pageCount < numPages:
                    pageCount += 1
                    yield response.follow(link, callback=self.parse)

            yield items

    # Learned how to run python script from scrapy here:
    # https://www.youtube.com/watch?v=Z9tFRznPAS8&ab_channel=CodeMonkeyKing
    # runs the spider from the script.
    process = CrawlerProcess()
    process.crawl(searchSpider)
    process.start()

    # This code is for troubleshooting, uncomment it if you would like to see this step
    # print(items["Matches"])
    # Figured out how to get the items variable from within the class during TA office hours
    items = searchSpider.items
    check_plagiarism(items["Matches"], submissionFile, items["Sentences"])

def take_submission():
    validInput = False
    while validInput is False:
        fileName = input("What is the name of the file you are looking to check for plagiarism? (Include .txt file extension) ")
        # Learned how to validate a file exists here:
        # https://www.pythontutorial.net/python-basics/python-check-if-file-exists/
        if os.path.exists(fileName):
            validInput = True
        else:
            print("Submission file not located in the same folder as spider")
    inFile = open(fileName, "r")
    submissionFile = inFile.read()
    inFile.close()
    return submissionFile

# This function takes no inputs for the function call but will take a text file name as user input for the name of the file with all the scraped data
def write_submission():
    fileName = input("What would you like to save the file with scraped results as? (Don't include the file extension) ")
    return fileName

# This function takes no inputs, asks the user for a starting url and then returns the entered url
def get_url():
    url = input("Please enter the full url of the website you want to crawl from:  ")
    return url

def get_num_pages():
    validInput = False
    print("Please enter a valid integer")
    numPages = input("What is the maximum number of pages you would like to scrape?  ")
    while validInput is False:
        try:
            numPages = int(numPages)
            if numPages <= 0:
                print("Input must be a positive integer number")
                numPages = input("What is the maximum number of pages you would like to scrape?  ")
            elif numPages >= 0:
                validInput = True
        except:
            print("Input must be a positive integer number")
            numPages = input("What is the maximum number of pages you would like to scrape?  ")
            validInput = False

    return numPages

# This function takes the number of matches determined by sentence_match, the submission file text, and the plagiarized sentence list
# The function will use the scale_score function to determine a score for how plagiarized the submission file is based on how many matches there were relative to the number of total lines
# If 20% or more of the lines contained plagiarism, the function will give it a 10
# Finally, the function prints output to the user with the determine plagiarism function and also will give the user output of the sentences to review if the list is not empty
def check_plagiarism(number_sentence_matches, submission_file, plagiarized_sentences):
    rawPlagiarismScore = number_sentence_matches
    scaledPlagiarismScore = scale_score(rawPlagiarismScore, submission_file)
    if scaledPlagiarismScore >MAX_PLAGIARISM_SCORE:
        scaledPlagiarismScore = MAX_PLAGIARISM_SCORE
    determine_plagiarism(scaledPlagiarismScore)
    if len(plagiarized_sentences) > 0:
        print("Here are a list of sentences flagged for plagiarism. Please manually review these to determine if they were plagiarized or if they were cited correctly.")
        for sentence in plagiarized_sentences:
            print(f"\t{sentence}")

# This function takes a sentence as input, strips all newline characters, whitespace, periods, exclamation marks, and question marks then returns the sentence as just text
def clean_sentence(sentence):
    sentence = sentence.strip()
    sentence = sentence.strip(".")
    sentence = sentence.strip("!")
    sentence = sentence.strip("?")
    return sentence

# This function takes in the submission file and scraped webpage file text
# The function iterates through every sentence in the submission file as list items split on periods, exclamation marks, and question marks
# Then, the function checks to see if they are in the scraped text and are less than 7 words in length to prevent accidental matches on common phrases
# If these conditions are fulfilled, the function will then increment the number of matches and append the matched sentence to the list to display to the user at the end
def sentence_match(submission_file, scraped_text):
    numSentenceMatches = 0
    plagiarizedSentences = []
    for sentence in submission_file.split("."):
        sentence = clean_sentence(sentence)
        # This code is for troubleshooting, uncomment it if you would like to see this step
        # print(sentence)
        if sentence in scraped_text:
            # This check prevents any single number from randomly being selected based off how a page was structured
            # print(sentence)
            if len(sentence.split()) > ARBITRARY_PLAGIARISM_WORD_COUNT_NUMBER:
                # This code is for troubleshooting, uncomment it if you would like to see this step
                # print("This sentence is in the source")
                numSentenceMatches += 1
                # This code is for troubleshooting, uncomment it if you would like to see this step
                # print(numSentenceMatches)
                plagiarizedSentences.append(sentence)
                # This code is for troubleshooting, uncomment it if you would like to see this step
                # print(plagiarizedSentences)
    for sentence in submission_file.split("!"):
        sentence = clean_sentence(sentence)
        # This code is for troubleshooting, uncomment it if you would like to see this step
        # print(sentence)
        if sentence in scraped_text:
            # This check prevents any single number from randomly being selected based off how a page was structured
            # print(sentence)
            if len(sentence.split()) > ARBITRARY_PLAGIARISM_WORD_COUNT_NUMBER:
                # This code is for troubleshooting, uncomment it if you would like to see this step
                # print("This sentence is in the source")
                numSentenceMatches += 1
                # This code is for troubleshooting, uncomment it if you would like to see this step
                # print(numSentenceMatches)
                plagiarizedSentences.append(sentence)
                # This code is for troubleshooting, uncomment it if you would like to see this step
                # print(plagiarizedSentences)
    for sentence in submission_file.split("?"):
        sentence = clean_sentence(sentence)
        # This code is for troubleshooting, uncomment it if you would like to see this step
        # print(sentence)
        if sentence in scraped_text:
            # This check prevents any single number from randomly being selected based off how a page was structured
            # print(sentence)
            if len(sentence.split()) > ARBITRARY_PLAGIARISM_WORD_COUNT_NUMBER:
                # This code is for troubleshooting, uncomment it if you would like to see this step
                # print("This sentence is in the source")
                numSentenceMatches += 1
                # This code is for troubleshooting, uncomment it if you would like to see this step
                # print(numSentenceMatches)
                plagiarizedSentences.append(sentence)
                # This code is for troubleshooting, uncomment it if you would like to see this step
                # print(plagiarizedSentences)
    #print(numSentenceMatches)
    #print(plagiarizedSentences)
    return numSentenceMatches, plagiarizedSentences

# This function will take the raw number of points given for the plagiarism score based on the number of times something bore similarity and scale it based on the number of sentences in the paper
# If over 20% of the paper's sentences have similar elements, the paper will get a 10 as a final score
# The mathematical formula for scaling this score will be: (numPoints / numSentences) * 50
def scale_score(raw_plagiarism_score, submission_file):
    numSubmissionFileSentences = 0
    for line in submission_file.split(". "):
        numSubmissionFileSentences += 1
    for line in submission_file.split("! "):
        numSubmissionFileSentences += 1
    for line in submission_file.split("? "):
        numSubmissionFileSentences += 1
    scaledScore = ((raw_plagiarism_score / numSubmissionFileSentences) * PLAGIARISM_NUM_TO_SCALE_TWENTY_PERCENT)
    return scaledScore

# This function will take in a score and output varying degrees of similarity to related websites and papers
# The function will return a print statement giving the numerical score and a writeup to accompany it
def determine_plagiarism(plagiarism_score):
    textMessage = ""
    if plagiarism_score == NO_PLAGIARISM_LOWER_BOUND:
        textMessage = "There were no similarities found between this paper and other online sources."
    elif plagiarism_score > NO_PLAGIARISM_LOWER_BOUND and plagiarism_score < LOW_PLAGIARISM_LOWER_BOUND:
        textMessage = "There was some similarities found between this paper and other online sources but it is unlikely to have been due to cheating or plagiarism."
    elif plagiarism_score > LOW_PLAGIARISM_LOWER_BOUND and plagiarism_score < MODERATE_PLAGIARISM_LOWER_BOUND:
        textMessage = "There was a moderate amount of similarities found between this paper and other online sources and, while there is a chance it is due to plagiarism, it is unlikely."
    elif plagiarism_score > MODERATE_PLAGIARISM_LOWER_BOUND and plagiarism_score < HIGH_PLAGIARISM_LOWER_BOUND:
        textMessage = "There was quite a bit of similarity found between this paper and other online sources. There is a decent chance part of the content was plagiarized or incorrectly cited."
    elif plagiarism_score > HIGH_PLAGIARISM_LOWER_BOUND and plagiarism_score < MAX_PLAGIARISM_LOWER_BOUND:
        textMessage = "There was a lot of similarity found between this paper and other online sources. There is a high likelihood of plagiarism or incorrect citations."
    elif plagiarism_score > MAX_PLAGIARISM_LOWER_BOUND:
        textMessage = "A majority of this paper has similarities to other online sources. It is very likely this paper was plagiarized."
    print(f"This paper was found to have a plagiarism score of {plagiarism_score:.2f} on a 1-10 scale. {textMessage}")

main()