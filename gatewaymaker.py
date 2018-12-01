#!/usr/bin/python3

#################################################
# GATEWAYMAKER
# 
# A tool to generate random tests for gateway
# exams.  Outputs .tex files.
#
# A. Bongiovanni 2018
# abongiov@kent.edu
#################################################

import json
import pathlib
import random
import os
import sys


CONFIG_FILE_PATH = pathlib.Path("configuration/configuration.json")
OUTPUT_DIR_PATH = pathlib.Path("tests")

TEX_ANSWERBOX_HEIGHT = "1.6cm"
TEX_ANSWERBOX_WIDTH = "3cm"
TEX_SPACING = "    "
TEX_BEGIN_QUESTIONS = "\\begin{questions}"
TEX_END_QUESTIONS = "\\end{questions}"
TEX_ANSWER_BOX_EMPTY = "%\\\\[.3in] \\vspace*{-10ex} \n" + TEX_SPACING + "\\begin{flushright} \\fbox{\\rule[0cm]{0cm}{" + TEX_ANSWERBOX_HEIGHT + "} \\hspace{" + TEX_ANSWERBOX_WIDTH + "} } \\end{flushright} "
TEX_ANSWER_BOX_FULL_START = "%\\\\[.3in] \\vspace*{-10ex} \n" + TEX_SPACING + "\\begin{flushright} \\fbox{\\rule[0cm]{0cm}{0cm} \\begin{minipage}[0pt][" + TEX_ANSWERBOX_HEIGHT + "][c]{" + TEX_ANSWERBOX_WIDTH + "} \\begin{center}"
TEX_ANSWER_BOX_FULL_END = "\end{center} \\end{minipage}} \\end{flushright}"
TEX_ITEM = "\\item "
TEX_END_DOCUMENT = "\\end{document}"
TEX_INSTRUCTION_START = "\\noindent \\bf{"
TEX_INSTRUCTION_END = "}"
TEX_NEWPAGE = "\\newpage"


def waitAndExit(exitCode):
    """
    Called to wait for the user to press enter, then exits with exitCode.
    Good for users who double click to run the program, and may not see
    any error messages if the program doesn't wait.
    """
    input("Press the 'Enter' key to exit...")
    exit(exitCode)


#################################################
# Script start
#################################################
#change to the directory that the script lives in
os.chdir(sys.path[0])

#read the config file
config = None
try:
    with open(CONFIG_FILE_PATH, "r") as fin:
        config = json.load(fin)
except IOError:
    print("ERROR: The configuration file at " + str(CONFIG_FILE_PATH) + " could not be read.")
    waitAndExit(1)
except json.decoder.JSONDecodeError as e:
    print("ERROR: Configuration file has an error on line " + str(e.lineno) + ".  Check that the file is valid JSON.")
    waitAndExit(1)
    
#read in the latex header
testHeaderPath = pathlib.Path(config["test header file path"])
testHeader = ""
try:
    with open(testHeaderPath, "r") as fin:
        testHeader = fin.read()
except IOError:
    print("ERROR: Couldn't read the latex header file at " + str(testHeaderPath))
    waitAndExit(1)

#read in the question files - store them in config, cause why not? PIZZA rename config
for questionSet in config["question sets"]:
    for questionFile in questionSet["question files"]:
        #first, extract the raw tex from the files
        questionPath = pathlib.Path(questionFile["file path"])
        rawTex = ""
        try:
            with open(questionPath, "r") as fin:
                rawTex = fin.read()
        except IOError:
            print("ERROR: Problem reading question file at " + str(questionPath) + ".")
            waitAndExit(1)
    
        #now remove whitespace and try to decide what lines are answers and what are questions
        questionTex = []
        answerTex = []
        texLines = rawTex.splitlines()
        for i in range(0, len(texLines)):
            #get the question, skipping empty lines or commented lines
            cleanLine = texLines[i].strip()
            if cleanLine == "" or cleanLine[0] == "%":
                continue
            questionTex.append(cleanLine)
            
            #check if the next line is an answer, skipping empty lines or lines not starting with "%%"
            if i+1 >= len(texLines):
                continue #well, break actually
            cleanLine = texLines[i+1].strip()
            if cleanLine == "" or cleanLine[0:2] != "%%":
                answerTex.append("")
            else:
                answerTex.append(cleanLine[2:])
                i+=1
            #PIZZA - improve comment symbol removal?
        questionFile["question tex"] = questionTex
        questionFile["answer tex"] = answerTex
        
    #verify that there is enough questions to make the test, error and exit if not
    if questionSet["number of questions"] > sum([len(qf["question tex"]) for qf in questionSet["question files"]]):
        print("ERROR: Insufficient number of questions in")
        for questionFile in questionSet["question files"]:
            print("\t" + questionFile["file path"])
        print("Expected at least " + str(questionSet["number of questions"]) + " questions total.")
        waitAndExit(1)


#construct the test - this could of course be merged with the above loop, but the performance gain is negligible compared to the readability of separating data loading/validation and test construction
totalQuestionsWritten = 0
testTex = testHeader + "\n"
answerTex = testHeader + "\n"
for questionSet in config["question sets"]:
    #throw all the questions in a big list to make random sampling from multiple files easier
    taggedQuestions = []
    for i in range(0, len(questionSet["question files"])):
        for j in range(0, len(questionSet["question files"][i]["question tex"])):
            taggedQuestions.append((i, questionSet["question files"][i]["question tex"][j], questionSet["question files"][i]["answer tex"][j]))
    
    #sample the questions and then sort based on what file they came from - makes it easier to group when printing instructions
    chosenQuestions = random.sample(taggedQuestions, questionSet["number of questions"])
    chosenQuestions.sort(key=lambda q: q[0])
    
    #loop over each question file, and print instructions and questions chosen from that file
    startIndex = 0
    for j in range(0, len(questionSet["question files"])):
        environmentTexWritten = False
        for i in range(startIndex, len(chosenQuestions)):
            fileIndex, questionTex, questionAnswerTex = chosenQuestions[i]
            
            #check that this question belongs to this file; if not, break so we can move on to the next set, which has different instructions
            if fileIndex != j:
                startIndex = i
                break
    
            #add the instructions and environment "begin" if it hasn't already been
            if not environmentTexWritten:
                testTex += TEX_INSTRUCTION_START
                testTex += questionSet["question files"][j]["instructions"]
                testTex += TEX_INSTRUCTION_END + "\n"
                testTex += TEX_BEGIN_QUESTIONS + "\n"
                
                answerTex += TEX_INSTRUCTION_START
                answerTex += questionSet["question files"][j]["instructions"]
                answerTex += TEX_INSTRUCTION_END + "\n"
                answerTex += TEX_BEGIN_QUESTIONS + "\n"
                
                environmentTexWritten = True
            
            #add the question and answer box
            testTex += TEX_SPACING + TEX_ITEM
            testTex += questionTex + "\n"
            testTex += TEX_SPACING + TEX_ANSWER_BOX_EMPTY + "\n"
            
            answerTex += TEX_SPACING + TEX_ITEM
            answerTex += questionTex + "\n"
            answerTex += TEX_SPACING + TEX_ANSWER_BOX_FULL_START
            answerTex += "\n" + TEX_SPACING*2 + questionAnswerTex + "\n" #we do a bad job of sanitizing comments, so sometimes putting things on the same line broke stuff
            answerTex += TEX_SPACING + TEX_ANSWER_BOX_FULL_END + "\n"
            
            #check to add the page breaks
            totalQuestionsWritten += 1
            if totalQuestionsWritten in config["page breaks after questions"]:
                testTex += TEX_SPACING + TEX_NEWPAGE + "\n"
                answerTex += TEX_SPACING + TEX_NEWPAGE + "\n"
    
        #if we actually added questions from this file, add the end of the questions environment
        if environmentTexWritten:
            testTex += TEX_END_QUESTIONS + "\n\n"
            answerTex += TEX_END_QUESTIONS + "\n\n"
            
testTex += TEX_END_DOCUMENT
answerTex += TEX_END_DOCUMENT

#make the directory for the tests if it doesn't already exist
try:
    OUTPUT_DIR_PATH.mkdir(exist_ok=True)
except FileExistsError:
    print("ERROR: problem with the output directory at: " + str(OUTPUT_DIR_PATH))
    print("Check permissions or that there isn't a file with the same name")
    waitAndExit(1)

#decide what file to use and then write out
#probably more efficient to just walk the directory and find the name but yolo
testNumber = 1
while (OUTPUT_DIR_PATH / ("test_" + str(testNumber) + ".tex")).exists() or (OUTPUT_DIR_PATH / ("test_" + str(testNumber) + "_answers.tex")).exists():
    testNumber += 1
try:
    testTex = testTex.replace("%%VERSION_NUMBER%%", str(testNumber))
    answerTex = answerTex.replace("%%VERSION_NUMBER%%", str(testNumber) + "ANSWER KEY")
    (OUTPUT_DIR_PATH / ("test_" + str(testNumber) + ".tex")).write_text(testTex)
    (OUTPUT_DIR_PATH / ("test_" + str(testNumber) + "_answers.tex")).write_text(answerTex)
except IOError as e:
    print("ERROR: could not write out the test file, please check write permissions.")
    waitAndExit(1)




#PIZZA - answer keys aren't written.  Probably need to check for existence of answer keys and test files to determine the correct index






