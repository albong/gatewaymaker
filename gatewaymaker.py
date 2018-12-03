#!/usr/bin/python3

#################################################
# GATEWAYMAKER
# 
# A tool to generate random tests for gateway
# exams.  Outputs .tex files.
#
# This tool features a menu for editing its
# configuration, so if you aren't comfortable
# with JSON, please use that.
#
# There is also a help screen available from the
# menu.
#
# A. Bongiovanni 2018
# abongiov@kent.edu
#################################################

import json
import pathlib
import random
import os
import sys
import copy


TITLE = "\
                 _                                           _             \n\
      __ _  __ _| |_ _____      ____ _ _   _ _ __ ___   __ _| | _____ _ __ \n\
     / _` |/ _` | __/ _ \ \ /\ / / _` | | | | '_ ` _ \ / _` | |/ / _ \ '__|\n\
    | (_| | (_| | ||  __/\ V  V / (_| | |_| | | | | | | (_| |   <  __/ |   \n\
     \__, |\__,_|\__\___| \_/\_/ \__,_|\__, |_| |_| |_|\__,_|_|\_\___|_|   \n\
     |___/                             |___/                               \n"
DIVIDER = "\
--------------------------------------------------------------------------------"

CONFIG_FILE_PATH = pathlib.Path("configuration/configuration.json")
TEST_HEADER_FILE_PATH = pathlib.Path("configuration/test_header.tex")
ANSWER_KEY_HEADER_FILE_PATH = pathlib.Path("configuration/test_header.tex")
OUTPUT_DIR_PATH = pathlib.Path("tests")
QUESTION_FILES_DIR_PATH = pathlib.Path("question_files")

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

def createTests(config, numberOfTests):
    """
    Create the given number of tests and answer keys based on the current configuration.
    
    testConfig = config file for the program
    numberOfTests = number of tests to create
    """
    #its convenient to store the actual LaTeX with the configuration, but then we will write that to file if we edit the configuration after making a test
    testConfig = copy.deepcopy(config)
    
    #read in the latex headers
    testHeader = ""
    try:
        with open(TEST_HEADER_FILE_PATH, "r") as fin:
            testHeader = fin.read()
    except IOError:
        print("ERROR: Couldn't read the latex header file at " + str(TEST_HEADER_FILE_PATH))
        waitAndExit(1)
        
    answerHeader = ""
    try:
        with open(ANSWER_KEY_HEADER_FILE_PATH, "r") as fin:
            answerHeader = fin.read()
    except IOError:
        print("ERROR: Couldn't read the latex header file at " + str(ANSWER_KEY_HEADER_FILE_PATH))
        waitAndExit(1)
    
    #read in the question files
    for questionSet in testConfig["question sets"]:
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
                #TODO - improve comment symbol removal?
            questionFile["question tex"] = questionTex
            questionFile["answer tex"] = answerTex
            
        #verify that there is enough questions to make the test, error and exit if not
        if questionSet["number of questions"] > sum([len(qf["question tex"]) for qf in questionSet["question files"]]):
            print("ERROR: Insufficient number of questions in")
            for questionFile in questionSet["question files"]:
                print("\t" + questionFile["file path"])
            print("Expected at least " + str(questionSet["number of questions"]) + " questions total.")
            waitAndExit(1)

    for testCreatedCount in range(0,numberOfTests):
        #construct the test - this could of course be merged with the above loop, but the performance gain is negligible compared to the readability of separating data loading/validation and test construction
        totalQuestionsWritten = 0
        testTex = testHeader + "\n"
        answerTex = answerHeader + "\n"
        for questionSet in testConfig["question sets"]:
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
                    if totalQuestionsWritten in testConfig["page breaks after questions"]:
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
            answerTex = answerTex.replace("%%VERSION_NUMBER%%", str(testNumber) + " ANSWER KEY")
            (OUTPUT_DIR_PATH / ("test_" + str(testNumber) + ".tex")).write_text(testTex)
            (OUTPUT_DIR_PATH / ("test_" + str(testNumber) + "_answers.tex")).write_text(answerTex)
        except IOError as e:
            print("ERROR: could not write out the test file, please check write permissions.")
            waitAndExit(1)
        print("Created 'test_" + str(testNumber) + ".tex' and 'test_" + str(testNumber) + "_answers.tex'")

def promptUserChoice(description, choices):
    """
    Used to give the user a list of choices to choose from.
    Blocks till they choose.
    
    description = the text to display above the choices
    choices = a list of strings to display as numbered choices to the user
    """
    userChoice = None
    while userChoice is None:
        print(description)
        for i in range(0, len(choices)):
            print(" " + str(i+1) + ") " + choices[i])
        userInput = input("Type the number of your selection: ")
        try:
            userChoice = int(userInput)
            if userChoice < 1:
                userChoice = None
                print("Invalid input\n")
                print(DIVIDER)
        except ValueError:
            userChoice = None
            print("Invalid input\n")
            print(DIVIDER)
    return userChoice
    
def promptUserNumber(description):
    """
    Ask the user to input a number, blocks until they actually input a number.
    Input number must be at least 1.
    
    description = the text to display
    """
    userNumber = None
    while userNumber is None:
        userInput = input(description + " ")
        try:
            userNumber = int(userInput)
            if userNumber < 1:
                userNumber = None
                print("Invalid input\n")
        except ValueError:
            userNumber = None
            print("Invalid input\n")
    return userNumber
    
def displayMainMenu(config):
    """
    Displays the main menu for running the program.
    """
    #loop until the user asks to exit
    exitProgram = False
    while not exitProgram:
        userChoice = promptUserChoice("What would you like to do:", ["Make tests", "Display current configuration", "Edit configuration", "Help", "Exit"])
        print(DIVIDER)
        
        #make tests
        if userChoice == 1:
            numberOfTests = promptUserNumber("How many tests?")
            createTests(config, numberOfTests)
            print(DIVIDER)
            
        #display config
        elif userChoice == 2:
            displayConfig(config)
            print(DIVIDER)
        
        #edit config
        elif userChoice == 3:
            config = displayGeneralEditMenu(config)
            print(DIVIDER)
        
        #help
        elif userChoice == 4:
            displayHelp()
            print(DIVIDER)
            
        #exit
        else:
            exitProgram = True
            
def displayConfig(config):
    """
    As the name suggests, it displays the current configuration.
    """
    print("The sets of questions:")
    totalNumberOfQuestions = 0
    for i in range(0, len(config["question sets"])):
        print("Set " + str(i+1) + ":")
        print("\tNumber of questions to randomly choose: " + str(config["question sets"][i]["number of questions"]))
        totalNumberOfQuestions += config["question sets"][i]["number of questions"]
        print("\tQuestion files:")
        for qf in config["question sets"][i]["question files"]:
            print("\t\t" + str(pathlib.Path(qf["file path"])))
    
    print("")
    
    print("Total number of questions on each test: " + str(totalNumberOfQuestions))
    
    print("")
    
    print("Page breaks will be inserted after questions:")
    print("\t" + (", ".join(str(num) for num in config["page breaks after questions"])))
    
def displayGeneralEditMenu(config):
    """
    Edits and saves the current configuration.  Returns a new configuration object.
    """
    #loop until the user is done editing
    doneEditing = False
    while not doneEditing:
        userChoice = promptUserChoice("What would you like to edit?", ["Question sets", "Page breaks", "Done editing"])
        
        #question sets
        if userChoice == 1:
            print(DIVIDER)
            addOrEditOrRemove = promptUserChoice("What would you like to do?", ["Add new question set", "Edit existing question set", "Remove existing question set"])
            print(DIVIDER)
            
            #add new set
            if addOrEditOrRemove == 1:
                newQuestionSet = {}

                #depending if there are existing sets or not, decide where to add the new set of questions
                if len(config["question sets"]) > 0:
                    currentNumberOfSets = len(config["question sets"])
                    choices = ["Before set 1"]
                    for i in range(0, currentNumberOfSets-1):
                        choices.append("Between set " + str(i+1) + " and set " + str(i+2))
                    choices.append("After set " + str(currentNumberOfSets))
                    newSetLocation = promptUserChoice("Where in the test do you want to add the new set?", choices)-1
                    print(DIVIDER)
                else:
                    newSetLocation = 0 #interpreted as the start of the list
                    
                #decide how many questions to use
                newQuestionSet["number of questions"] = promptUserNumber("How many questions should be randomly pulled from this set?")
                
                #add files and directions to the set
                newQuestionSet["question files"] = []
                sortedFiles = [str(f) for f in QUESTION_FILES_DIR_PATH.glob("*")]
                sortedFiles.sort()
                filesInQuestionDir = sortedFiles + ["Done choosing files"]
                doneAddingFiles = False
                while not doneAddingFiles:
                    fileToAdd = promptUserChoice("What file do you want to pull questions from?", filesInQuestionDir)
                    if fileToAdd != len(filesInQuestionDir):
                        print("Type the LaTeX you want to use for the instructions for the questions from this file:")
                        instructions = input("")
                        newQuestionSet["question files"].append({ "file path":filesInQuestionDir[fileToAdd-1], "instructions":instructions })
                    else:
                        doneAddingFiles = True
                    print(DIVIDER)
                
                #change and save the config
                config["question sets"].insert(newSetLocation, newQuestionSet)
                saveConfig(config)
                
            #edit existing set
            elif addOrEditOrRemove == 2:
                #if there are no sets, skip
                if len(config["question sets"]) == 0:
                    print("There are no sets to edit.")
                    print(DIVIDER)
                    continue
                
                setsToChooseFrom = []
                for i in range(0, len(config["question sets"])):
                    setsToChooseFrom.append("Set " + str(i+1))
                setToEditNumber = promptUserChoice("What set do you want to edit?", setsToChooseFrom) - 1
                setToEdit = config["question sets"][setToEditNumber]
                print(DIVIDER)
                
                #ask to change number of questions
                print("Currently " + str(setToEdit["number of questions"]) + " questions will be chosen from this set.")
                newNumberOfQuestions = input("How many questions should be chosen? ")
                try:
                    setToEdit["number of questions"] = int(newNumberOfQuestions)
                except ValueError:
                    print("Invalid input")
                    continue
                print(DIVIDER)
                
                #ask for files to remove with loop
                doneRemovingFiles = False
                while not doneRemovingFiles and len(setToEdit["question files"]) > 0:
                    removalChoices = []
                    for qf in setToEdit["question files"]:
                        removalChoices.append(qf["file path"] + "\n\t" + qf["instructions"])
                    removalChoices.append("Done removing files")
                    
                    fileToBeRemoved = promptUserChoice("These are the files and instructions currently in this set.\nWhich should be removed?", removalChoices)
                    if fileToBeRemoved != len(removalChoices):
                        setToEdit["question files"].pop(fileToBeRemoved-1)
                    else:
                        doneRemovingFiles = True
                    print(DIVIDER)
                
                #ask for files to add with loop
                sortedFiles = [str(f) for f in QUESTION_FILES_DIR_PATH.glob("*")]
                sortedFiles.sort()
                filesInQuestionDir = sortedFiles + ["Done choosing files"]
                doneAddingFiles = False
                while not doneAddingFiles:
                    fileToAdd = promptUserChoice("What file do you want to pull questions from?", filesInQuestionDir)
                    if fileToAdd != len(filesInQuestionDir):
                        print("Type the LaTeX you want to use for the instructions for the questions from this file:")
                        instructions = input("")
                        setToEdit["question files"].append({ "file path":filesInQuestionDir[fileToAdd-1], "instructions":instructions })
                    else:
                        doneAddingFiles = True
                    print(DIVIDER)
                
                #save the changes
                saveConfig(config)
            
            #remove sets
            else:
                #if there are no sets, skip
                if len(config["question sets"]) == 0:
                    print("There are no sets to remove.")
                    print(DIVIDER)
                    continue
                    
                #loop until done removing or no more sets
                doneRemovingSets = False
                while not doneRemovingSets and len(config["question sets"]) > 0:
                    setsToChooseFrom = []
                    for i in range(0, len(config["question sets"])):
                        setsToChooseFrom.append("Set " + str(i+1))
                    setsToChooseFrom.append("Done removing sets")
                                        
                    setToRemove = promptUserChoice("What set do you want to remove?", setsToChooseFrom)
                    if setToRemove != len(setsToChooseFrom):
                        config["question sets"].pop(setToRemove-1)
                    else:
                        doneRemovingSets = True
                    print(DIVIDER)
                
                saveConfig(config)
                            
        #page breaks
        elif userChoice == 2:
            print(DIVIDER)
            print("Page breaks will currently be inserted after questions: ")
            print("\t" + (", ".join(str(num) for num in config["page breaks after questions"])))
            print("Please enter a comma separated list of question numbers (spaces are okay):")
            
            userInput = input("")
            try:
                newPageBreaks = [int(token.strip()) for token in userInput.split(",")]
                config["page breaks after questions"] = newPageBreaks
                saveConfig(config)
            except ValueError:
                print("Error in input, page breaks not changed.")
            print(DIVIDER)
            
        #done editing
        else:
            doneEditing = True
        
    return config
    
def displayHelp():
    print("\
gatewaymaker is a tool for generating the .tex files for random tests.  It pulls\n\
from a variety of .tex files located in the directory 'question_files'.  The\n\
configuration of gatewaymaker is contained in a JSON file in the 'configuration'\n\
directory, however, it is possible to edit the configuration from inside of\n\
gatewaymaker.  There are also .tex files in the 'configuration' directory that\n\
are used when generating the tests, they contain the preamble and beginning of\n\
the document through the title.  They will not compile as is - gatewaymaker will\n\
complete them during the process of test generation.\n\
\n\
A test is composed of 'sets' of questions.  A fixed number of questions will be\n\
chosen at random from each set to make the test.  A set of questions may be\n\
composed of multiple source files, each with different instructions.  In this\n\
way, collections of questions with common themes may be pooled into one group\n\
from which to choose questions at random.\n\
\n\
For example, if you want to have five questions about factoring, you could have\n\
one file with simple factoring questions and the instructions 'Factor\n\
completely', and another file with factor by grouping questions and the\n\
directions 'Factor by grouping'.  If configured as one set, gatewaymaker will\n\
randomly choose five questions from between these two files, and correctly\n\
insert the instructions depending on what questions were chosen.\n\
\n\
If, in your source question files, the line following a question starts with\n\
some amount of spaces and then '%%', that line will be interpreted as an answer\n\
to the previous line's question.  This will then be inserted into an answer key\n\
that is also generated along with the test.\
\n\
Finally, if your questions have consistent amounts of spacing, gatewaymaker can\n\
also be configured to add '\\newpage' where you want - otherwise you will have\n\
to manually adjust the page breaks in the output tests as needed.\
    ")
    
def saveConfig(config):
    with open(CONFIG_FILE_PATH, "w") as fout:
        config = json.dump(config, fout, indent=4)
    

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
    
#welcome the user - this may seem silly, but my users are generally used to graphical interfaces
print(TITLE)
print(DIVIDER)

#start the menu
try:
    displayMainMenu(config)
except KeyboardInterrupt:
    print("") #its overwhelmingly probable they exit at an "input(...)", so newline to move the terminal cursor


