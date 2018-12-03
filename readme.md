# gatewaymaker.py

## Overview
gatewaymaker.py is a tool for generating LaTeX files for random tests.  It is named after the "gateway" tests it was written to generate: students are given a very long list of problems in advance, and then take tests where the questions are randomly pulled from the list (subject to some constraints).  If students fail the test, they keep retaking it until they pass, with each retest having different random questions.

gatewaymaker is mildly configurable with respect to how it chooses questions.  The configuration is stored in a JSON file, however, since  the intended users are not comfortable with editing such files and it is unknown how long this tool may be used for (it is replacing a Perl script from a decade ago written by an author long disappeared), the program has a built-in menu for editing the configuration.  The menu is far from optimal from a UX point of view, but it gets the job done.

## Configuration
As noted, configuration can be done from within gatewaymaker.

It pulls from a variety of .tex files located in the directory 'question_files'.  The configuration of gatewaymaker is contained in a JSON file in the 'configuration' directory.  There are also .tex files in the 'configuration' directory that are used when generating the tests, they contain the preamble and beginning of the document through the title.  They will not compile as is - gatewaymaker will complete them during the process of test generation.

A test is composed of 'sets' of questions.  A fixed number of questions will be chosen at random from each set to make the test.  A set of questions may be composed of multiple source files, each with different instructions.  In this way, collections of questions with common themes may be pooled into one group from which to choose questions at random.

For example, if you want to have five questions about factoring, you could have one file with simple factoring questions and the instructions 'Factor completely', and another file with factor by grouping questions and the directions 'Factor by grouping'.  If configured as one set, gatewaymaker will randomly choose five questions from between these two files, and correctly insert the instructions depending on what questions were chosen.

If, in your source question files, the line following a question starts with some amount of spaces and then `%%`, that line will be interpreted as an answer to the previous line's question.  This will then be inserted into an answer key that is also generated along with the test.

Finally, if your questions have consistent amounts of spacing, gatewaymaker can also be configured to add `\newpage` where you want - otherwise you will have to manually adjust the page breaks in the output tests as needed.
