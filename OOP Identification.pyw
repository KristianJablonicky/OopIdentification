from fileinput import filename
from itertools import filterfalse
import os
from sqlite3 import InterfaceError
import sys
import re
from anytree import Node, RenderTree
#https://stackoverflow.com/questions/2358045/how-can-i-implement-a-tree-in-python

from tkinter import *
from tkinter import filedialog

#https://stackoverflow.com/questions/18262293/how-to-open-every-file-in-a-folder

# executable file export:
# pyinstaller --onefile --windowed --add-data "Logo.png;." --add-data "appIcon.ico;." --icon="appIcon.ico" "OOP Identification.pyw"

debug = False # True if you want to print extra debug outputs to the console

parents = [] # list of all hierarchies represented by a triple(parentNode, isDeclaredByAuthor, typeOfHierarchy)
             # typeOfHierarchy: 0 - inheritance hierarchy; 1 - interface hierarchy
orphans = [] # list of all child classes that currently don't have a
             # parent class saved in the parents list (represented by tuples (child, parent) )
classContent = [] # list [className, depth, linesOfCode<(depth, line)>, methods,
                  # objectAttributes<(objectName, parentClass)>, bool isClass(False when Interface)]
                  # used to detect aggregation, composition, nested classes etc.
listOfClasses = []
listOfInterfaces = []
listOfParents = []

singletonList = []
designPattern = [] # list of lists; [singleton[], ], each design pattern is represented by a touple
                   # class name, and method name which implements said design pattern

bannedStrings = [] # to avoid outputting the same line multiple times, we forbit these lines from being printed on the screen

designPattern.append(singletonList)

commentLocation = 0
fullLine = "//"

isString = False # True means that our currently processed line is value of a String variable/argument

printFilename = True # we want to print file name only once per file
currentDepth = 1 # how many nested blocks are there currently: class outerClass{ innerClass{int depth=2} }
depthOfClass = 0 # save the depth at which we declared the current class


outputLines = ([], [], [], [], []) # 0: hierarchies, 1: encapsulations, 2: associations, 3: polymorphisms, 4: design patterns
summaryLines = []

javaFiles = 0

inheritances = 0
interfaces = 0

polymorphisms = 0
objPolymorphisms = 0
aggregations = 0
compositions = 0
encapsulations = 0

rootDirectory = os.getcwd()
path = rootDirectory


def printLine(string, index=0):
    outputLines[index].append(string)

def printSummary(string):
    summaryLines.append(string)

def addToHierarchy (childClass, parentClass, typeOfHierarchy):

    if not (parentClass in listOfParents): # list of all classes that are inherited from (useful for polymorphism in function)
        listOfParents.append(parentClass)

    #for currentParent in parents:
    for parentNode in parents:
        if parentNode[2] == typeOfHierarchy:
            for pre, fill, currentParent in RenderTree(parentNode[0]): # check all the classes in all hierarchies
                if currentParent.name == parentClass:
                    
                    newParent = Node(childClass, parent=currentParent) # add class to hierarchy
                    checkOrphans(newParent, typeOfHierarchy) # check if current class isn't a parent
                    return
            
    orphans.append((childClass, parentClass, typeOfHierarchy)) # current class' parent isn't in the Node tree yet

def printHierarchies(typeOfHierarchy):

    i = 1
    localInheritances = 0
    for parentClass in parents:
        if parentClass[2] == typeOfHierarchy and parentClass[0].children: # prints hierarchies only if a class doesn't have a child
            
            stringAuthour = "---"
            if not parentClass[1]:
                stringAuthour = " (Parent not declared in the input files)---"
                if parentClass[0].name in listOfInterfaces: # the parent is declared, but happens to be an interface
                    continue
            if typeOfHierarchy == 1: #typeOfHierarchy == 0 and parentClass[0].name in listOfInterfaces or typeOfHierarchy == 1:
                hierarchyType = "\n---Interface hierarchy "

            elif typeOfHierarchy == 0:
                hierarchyType = "\n---Inheritance hierarchy "
            
            elif typeOfHierarchy == 2:
                hierarchyType = "\n---Nested type hierarchy "
                    
            printLine(hierarchyType + str(i) + stringAuthour) # then no other class extends that class
            for pre, fill, node in RenderTree(parentClass[0]):
                printLine("%s%s" % (pre, node.name))
            i += 1

        if typeOfHierarchy == 0:
            localInheritances = i - 1

        elif typeOfHierarchy == 1:
            global interfaces
            interfaces = i - 1
            
    global inheritances
    inheritances += localInheritances
        
def checkOrphans(parentNode, typeOfHierarchy):
    for node in orphans:
        if node[2] == typeOfHierarchy and node[1] == parentNode.name:
            newParent = Node(node[0], parent=parentNode)
            orphans.remove(node)
            checkOrphans(parentNode, typeOfHierarchy) # first we check, whether there aren't multiple child nodes
            # that share a parent with current node
            checkOrphans(newParent, typeOfHierarchy) # then we check if current child node doesn't have children
            return

def addParent(parentClass, isDeclaredByAuthor, typeOfHierarchy):
    if not isDeclaredByAuthor and parentClass in listOfInterfaces: # we would output interface hierarchies twice as class hierarchies otherwise
        return

    parentNode = Node(parentClass)
    parents.append((parentNode, isDeclaredByAuthor, typeOfHierarchy))
    checkOrphans(parentNode, typeOfHierarchy)

def printDesignPatterns():
    #singletons
    for singleton in designPattern[0]:
        if singleton[1] != "":
            printLine(singleton[0] + "'s method " + singleton[1] + " implements the design pattern Singleton.", 4)
        else:
            printLine(singleton[0] + " implements the design pattern Singleton.", 4)
def detectClass(line, lineNumber, fullLine, keyWord, fileName, isClass, replaced): # detects classes and inheritances
    global printFilename
    if line.find(" class ") >= 0 and line.find(" " + keyWord + " ") >= 0: # class X extends/implements Y {
        if printFilename:
            printLine("\n" + fileName + ":")
            printFilename = False
        if keyWord == "extends" and not replaced:
            printLine("Inheritance found at line " + str(lineNumber) + ":\n\"" + fullLine[:-1] + '"')
        elif keyWord == "implements":
            printLine("Implementation of an interface found at line " + str(lineNumber) + ":\n\"" + fullLine[:-1] + '"')
        classIndex = line.find(" class ")
        keyWordIndex = line.find(" " + keyWord + " ")
        offset = len(keyWord) + 2
        className = line[classIndex + 7: classIndex + 7 + line[classIndex + 7:].find(" ")]
        parentName = line[keyWordIndex + offset: keyWordIndex + offset + line[keyWordIndex + offset:].find(" ")]
        
        if not isClass:
            addParent(className, True, 1) # interface type of hierarchy is no longer a thing
            listOfInterfaces.append(className)

        if keyWord == "extends":
            addToHierarchy(className, parentName, 0)
        elif keyWord == "implements":
            addToHierarchy(className, parentName, 1)
        
        if not className in listOfClasses: # avoid adding the same className to the list (possible when a class implements / extends a class / multiple interfaces)
            listOfClasses.append(className)
            classContent.append([className, 0, [], [], [], isClass])

        extendsIndex = line.rfind(" extends ")
        if line.find(" extends ") < extendsIndex:
            line = line[:extendsIndex] + " , " + line[extendsIndex+9:]

        if line.find(",") > -1:
            detectClass(line.replace(" " + parentName + " , ", " "), lineNumber, fullLine, keyWord, fileName, isClass, replaced)

    # class A { -> add class to our list of classes
    elif line.find(" class ") > -1 and keyWord == "extends": # checking the keyWord just secures that we don't print this twice

        if line.find(". class") > -1 or line.find("class .") > -1: # this.class.(...) gets translated to -> this . class . 
            return
        classIndex = line.find(" class ")
        className = line[classIndex + 7: classIndex + 7 + line[classIndex + 7:].find(" ")]
        
        if not isClass:
            addParent(className, True, 1)
            listOfInterfaces.append(className)
        else:
            addParent(className, True, 0)
        classContent.append([className, 0, [], [], [], isClass])
        listOfClasses.append(className)
        
def updateDepth(line):
    
    global currentDepth
    
    if line.find("{") > -1:
        currentDepth += 1
    elif line.find("}") > -1:
        currentDepth -= 1
    
    # update contents of class bodies
    for classUpdate in classContent:
        if classUpdate[1] == 0: # following lines will be appended to this class' body
            classUpdate[1] = currentDepth-1
        
        elif classUpdate[1] > 0 and currentDepth > classUpdate[1]: # append line to body

            if line.find(" class ") > -1 and line.find(". class") == -1 and line.find("class .") == -1:
                # nested class, do not append following lines
                classUpdate[1] = ( classUpdate[1] * -1) -1 # negative value means we're going thru inner class content
                classUpdate[2].append((currentDepth, line)) # append class declaration

            elif not re.search("^ *$", line): # the line isn't just white spaces
                classUpdate[2].append((currentDepth, line))

                minDepth = classUpdate[2][0][0]
                if classUpdate[2][0][1].find("{") > -1:
                    minDepth -= 1
                if classUpdate[5]:
                    if currentDepth == minDepth + 1: # +1 since methods contain the { character that increases currentDepth by one
                        if line.find("{") > 0 and line.find("=") == -1 and line.find(" ( ") > -1:
                            methodEnd = line.find(" ( ")
                            methodStart = line[:methodEnd].rfind(" ") + 1
                            classUpdate[3].append(line[methodStart:methodEnd])
                else:
                    if currentDepth == minDepth: # +1 since methods contain the { character that increases currentDepth by one
                        if line.find("(") > 0 and line.find("=") == -1:
                            methodEnd = line.find(" ( ")
                            methodStart = line[:methodEnd].rfind(" ") + 1
                            classUpdate[3].append(line[methodStart:methodEnd])
        
        elif classUpdate[1] < 0: # inner class' body is closed off, invert classUpdate depth
            if line == " } " and (currentDepth * -1)  == classUpdate[1]:
                classUpdate[1] = (classUpdate[1] * -1) -1
                classUpdate[2].append((currentDepth, " } "))

        elif classUpdate[1] > 0 and currentDepth == classUpdate[1]: # current class is completed
            classUpdate[1] = -1000 # the code will run into issues at 1k nested blocks

def outputAssociation(mainClass, doesWhat, otherClass):

    string = "The \"" + mainClass + "\" type " + doesWhat + " the \"" + otherClass + "\" type."
    if string in bannedStrings:
        return
    bannedStrings.append(string)
    if doesWhat.find("nested") == -1:
        printLine(string, 2)
    else:
        printLine(string) # nested class hierarchy
    
    if doesWhat == "aggregates":
        global aggregations
        aggregations += 1
    elif doesWhat == "composites":
        global compositions
        compositions += 1

def getObject(lineString, className):
    
    lineString = lineString.replace(" var ", " " + className + " ")
    objectLocation = lineString.find(" " + className + " ") + 2 + len(className)
    
    objectEnd = lineString[objectLocation:].find(" ") + objectLocation
                        
    objectName = lineString[objectLocation:objectEnd]
    
    if objectName.find("(") == -1:  # ClassName ObjectName = -> ObjectName is the name of a ClassName object
                                    # new ClassName ( ) -> ( isn't, so it gets ignored
       
        if lineString.find(" " + className + " " + objectName + " ( ") == -1: # Singleton getInstance ( ... getInstance is a method name, not an object
            if objectName != ">" and objectName != "=" and objectName != ")" and objectName != "." and len(objectName) > 0 and objectName != className:
                lineString = lineString[:lineString.find(" " + className + " ")] + lineString[objectEnd:]
                return (lineString, objectName)

    return False

def scanObjects():
    regexStart = r'[^A-z0-9"]{1}'
    firstLine = True
    minDepth = -1

    for classBody in classContent:
        firstLine = True
        for line in classBody[2]:
            if firstLine: # get on the first line only
                minDepth = line[0]
                if line[1].find("{") > -1:
                    minDepth -= 1
            firstLine = False

            for className in listOfClasses:
                if re.search(regexStart + className + regexStart, line[1]): # we are using another class
                    if line[1].find(" class ") == -1: # not a nested class
                        if line[0] == minDepth: # object is an attribute, and has't been appended yet
                            multipleObjects = True
                            objectString = line[1]
                            while multipleObjects:
                                multipleObjects = False
                                objectTuple = getObject(objectString, className)
                                if objectTuple != False:
                                    if ((objectTuple[1], className)) not in classBody[4]:
                                        classBody[4].append((objectTuple[1], className))
                                
                                    if objectString.find(objectTuple[1] + " , ") > -1 and objectString.find(" new ") == -1: # C1 o1, o2; -but not- C1 o1 = new C1 (par1, par2)
                                        objectString = objectString.replace(" " + objectTuple[1] + " ,", "")
                                        multipleObjects = True

def getClassIndex(className):

    index = 0
    for readClass in classContent:
        if readClass[0] == className:
            return index
        index += 1

    print("FATAL ERROR")
    exit()

def scanClasses():
    # check, if a different class' object isn't used in the body of a class
    
    global encapsulations
    global objPolymorphisms
    global polymorphisms
    isConstructor = False
    constructorDepth = -1

    lineNumber = 0
    classNumber = -1

    regexStart = r'[^A-z0-9"]{1}'
    minDepth = 0
    attributes = []
    association = [] # list of all classes associated with the current class
    objects = [] # tuples (className, objectName)
    upcastObjects = [] # tuples (objectName, upcastClassName)
    
    keywords = [" protected ", " private "]
    privateAttributes = [] # list of all private / protected attributes

    encapsulated = True # ensure that each class gets counted just once
    addPolymorphism = True # False when a method is being declared
    lineString = "edited line of code"

    globalObjects = []
    globalUpcastObjects = []
    for classBodyObjects in classContent: # get all the globally "upcast" objects
        for uObj in classBodyObjects[4]:
            globalUpcastObjects.append(uObj)
            globalObjects.append((uObj[1], uObj[0]))

    isSingleton = 0
    staticInstance = False

    for classBody in classContent:
        for depth in classBody[2]: # depth at which class atributes are defined
            minDepth = depth[0]
            if depth[1].find("{") > -1:
                minDepth -= 1 # the first line is a method - methods have depth 1 higher than they should
            break

        classNumber += 1
        association.clear()
        attributes.clear()

        privateAttributes.clear()
        encapsulated = True
        addPolymorphism = True

        isConstructor = False
        constructorDepth = -1
        
        lineNumber = 0
        
        objects.clear()
        upcastObjects.clear()
        isSingleton = 0
        staticInstance = False

        objects += globalObjects
        upcastObjects += globalUpcastObjects

        #redefinedObjects = globalObjects
        redefinedUpcasts = []
        for line in classBody[2]:
            lineString = line[1]
            replaceLineString = lineString
            for className in listOfClasses:
                # check for nested classes, aggregation, composition or association
                if re.search(regexStart + className + regexStart, lineString): # another class is being used
                    if lineString.find(" class ") > -1 and lineString.find(". class ") == -1 and lineString.find(" class .") == -1: # nested class defined at classDepth (shallowest depth possible)
                        if line[0] == (minDepth + 1):
                            outputAssociation(className, "is nested in", classBody[0])
                            addParent(classBody[0], True, 2)
                            addToHierarchy(className, classBody[0], 2)
                        continue # otherwise we would output "className is associated with ... " and mess up the object to class conversion, which is unnecessary
                                 # move on to the next line
                    else:
                        if lineString.find(" " + className + " ") > -1: # a new object is being defined (being defined but not used [eg. object.method ( param ) ])
                            if lineString.find(" ( ") > -1 and lineString.find(" ) ") > -1 and lineString.find(" {") > -1: # method parameters
                                objectTuple = True
                                gracePeriod = 3 # allow 3 repeats before considering something an infinite loop (good for debugging)
                                objectString = lineString.replace(" , ", " ")
                                previousString = ""
                                while objectTuple != False and re.search(regexStart + className + regexStart, objectString):
                                    if previousString == objectString or (len(previousString) > 0 and (len(previousString) < len(objectString))):
                                        # make sure that a bug doesn't cause infinite loop
                                        if gracePeriod > 0:
                                            gracePeriod -= 1
                                            previousString = objectString
                                        else:
                                            printSummary("(1) Fatal error at line: " + objectString + "\nClass: " + className)
                                            printSummary(classBody[0] + " " + lineString + "\n")
                                            return
                                    else:
                                        previousString = objectString

                                    objectTuple = getObject(objectString, className)
                                    if objectTuple != False:
                                        if ((className, objectTuple[1])) not in objects:
                                            objects.append((className, objectTuple[1]))
                                        for upcastObject in upcastObjects:
                                            if upcastObject[0] == objectTuple[1] and upcastObject in upcastObjects:
                                                upcastObjects.remove(upcastObject)
                                                continue
                                        if lineString.find(" for ") > -1:
                                            upcastObjects.append((objectTuple[1], className))
                                            redefinedUpcasts.append((objectTuple[1], className))
                                        objectString = objectTuple[0]
                                        if line[0] == (minDepth + 1): # +1, since methods have their depth increased by one ({)
                                            if className in listOfParents: # current object's class is extended, thus may be upcast and implement polymorphism
                                                append = True
                                                for i in range(len(upcastObjects)):
                                                    if upcastObjects[i][0] == objectTuple[1]:
                                                        append = False
                                                        upcastObjects[i] = (objectTuple[1], className)
                                                        break
                                                if append:
                                                    upcastObjects.append((objectTuple[1], className))
                                                    redefinedUpcasts.append((objectTuple[1], className))
                            else:
                                multipleObjects = True
                                objectString = lineString
                                while multipleObjects:
                                    multipleObjects = False
                                    objectTuple = getObject(objectString, className)
                                    if objectTuple != False:

                                        if lineString.find(" " + classBody[0] + " ") > -1 and lineString.find(" static ") > -1 and lineString.find(" for ") == -1:
                                            staticInstance = True
                                            
                                        if lineString.find(" for ") > -1:
                                            objects.append((className, objectTuple[1]))
                                            upcastObjects.append((objectTuple[1], className))
                                            redefinedUpcasts.append((objectTuple[1], className))
                                        elif ((className, objectTuple[1])) not in objects:
                                            objects.append((className, objectTuple[1]))
                                        else:
                                            for upcastObject in upcastObjects:
                                                if upcastObject[0] == objectTuple[1] and upcastObject in upcastObjects:
                                                    upcastObjects.remove(upcastObject)
                                                    continue

                                        if objectString.find(objectTuple[1] + " , ") > -1 and objectString.find(" new ") == -1: # C1 o1, o2; -but not- C1 o1 = new C1 (par1, par2)
                                            objectString = objectString.replace(" " + objectTuple[1] + " ,", "")
                                            multipleObjects = True
                        if line[0] == minDepth and not className in attributes:
                            attributes.append(className)

                if re.search(regexStart + className + regexStart, lineString):
                    
                    if re.search(" return[ (]{1}", lineString):
                        if lineString.find(" new ") == -1:
                            outputAssociation(classBody[0], "aggregates", className)
                            if debug:
                                printLine("1 " + lineString)
                        else:
                            outputAssociation(classBody[0], "is associeted with", className)
                            if debug:
                                printLine("1.5 " + lineString)
                        if className in association:
                            association.remove(className)
                        
                    elif not className in association and className != classBody[0]:
                        association.append(className)

            # translate all object names to class names
            # but first check for potential object upcasting
            replacedLineString = lineString
            for objectName in objects:
                reSult = re.search(regexStart + objectName[1] + regexStart, lineString)
                if reSult:
                    upcastString = " " + objectName[1] + " = new "
                    upcastIndex = lineString.find(upcastString)
                    if upcastIndex > -1: # an object is potentially being upcast
                        upcastClassStart = upcastIndex + len(upcastString)
                        upcastClassEnd = lineString[upcastClassStart:].find(" ") + upcastClassStart
                        upcastClass = lineString[upcastClassStart:upcastClassEnd]
                        if upcastClass != objectName[0]: # current object is being upcast to a different class' type
                            append = True # do we need to append this object to our list, or just update the class of this object?
                            for i in range(len(upcastObjects)):
                                if upcastObjects[i][0] == objectName[1]:
                                    append = False
                                    upcastObjects[i] = (objectName[1], upcastClass)
                                    break
                            if append:
                                upcastObjects.append((objectName[1], upcastClass))
                                redefinedUpcasts.append((objectName[1], className))

                    methodString = " " + objectName[1] + " . "
                    methodIndex = lineString.find(methodString)
                    if methodIndex > -1:
                        methodIndex += len(methodString)
                        methodEndIndex = lineString[methodIndex:].find(" ") + methodIndex
                        utilisedMethod = lineString[methodIndex:methodEndIndex]
                        keepLooping = True
                        for uObj in upcastObjects: # was this method used by an upcast object?
                            if keepLooping and objectName[1] == uObj[0]: # yes, it was. however was the method overriden? (or is it a method at all, and not an attribute)
                                for obj in objects:
                                    if keepLooping and obj[1] == uObj[0]: # find the former type of the upcast object
                                        for method in classContent[getClassIndex(obj[0])][3]: # check, if the called method is overriden
                                            if method == utilisedMethod: # we just detected polymorphism
                                                # if the object is globally upcast: objA.objB.m(); is ok, but just objB.m(); is not
                                                if not uObj in globalUpcastObjects or uObj in redefinedUpcasts or lineString.find(" . " + uObj[0] + " . ") > -1: 
                                                    if addPolymorphism:
                                                        printLine("Class " + classBody[0] + ":", 3)

                                                    printLine(" The \"" + uObj[0] + "\" object implements polymorphism.", 3)
                                                    objPolymorphisms += 1
                                                    if addPolymorphism:
                                                        polymorphisms += 1
                                                        addPolymorphism = False

                                                    if uObj in upcastObjects: # just in case, removing elements while iterrating could lead to issues
                                                        if not uObj in globalUpcastObjects:
                                                            upcastObjects.remove(uObj) # avoid outputting the same object multiple times
                                                    keepLooping = False

                    replacedLineString = replacedLineString.replace(reSult[0][0] + objectName[1] + reSult[0][-1],
                                                                    reSult[0][0] + objectName[0] + reSult[0][-1])

                    # translate all object names to class names, keep the first and last char untouched (vectors lists etc.)
                    classContent[classNumber][2][lineNumber] = (line[0], replacedLineString)

                if className == classBody[0]: # we did this in an if(), so let's make sure that all the lines skip the following
                    continue

                # objects are translated to class name, let's look for associations
                # we worked with current class' name until this point to detect objects of current class' type
                # from now on we will take a look at associations, those require a strictly different class
                
                lineString = replaceLineString
            
            if line[1].find("}") == -1 and line[0] == minDepth and\
                (line[1].find("(")== -1 or line[1].find("=") > -1): # ignore definitions of private/protected methods
                                                                    # and abstract class methods
                privateLine = line[1]
                privateAttAmount = len(privateAttributes)
                for keyword in keywords:
                    multipleAttributes = True
                    if privateLine.find(keyword) > -1:
                        startIndex = 0
                        while multipleAttributes: # detect all private attributes on current line
                            endIndex = privateLine.rfind(" = ") # private int var_name1, var_name2 = 2;
                            if endIndex > -1:
                                startIndex = privateLine[:endIndex].rfind(" ") + 1
                                privateAttributes.append(privateLine[startIndex:endIndex])
                                if privateLine.find(",") == -1:
                                    multipleAttributes = False
                                privateLine = privateLine[:startIndex -2]

                            else:
                                endIndex = privateLine.rfind(" ") # private int var_name;
                                startIndex = privateLine[:endIndex].rfind(" ") + 1
                                privateAttributes.append(privateLine[startIndex:endIndex])
                                if privateLine.find(",") == -1:
                                    multipleAttributes = False
                                privateLine = privateLine[:startIndex -2]

                if privateAttAmount == len(privateAttributes) and classBody[5]: # the newly declared attribute isn't encapsulated
                    encapsulated = False
                                
            for attribute in privateAttributes:
                if re.search(regexStart + attribute + regexStart, line[1]):
                    if line[1].find(" return ") > -1:
                        printLine('"' + classBody[0] + '" class encapsulates the "' + attribute + '" attribute.', 1)
                        privateAttributes.remove(attribute)
                        continue
                    elif line[0] != minDepth and line[1].find(" = ") > -1:
                        if line[1].find (" if ") == -1 or line[1].rfind(" = ") > line[1].rfind(" = = "): # there is either no if,
                                                                                                         # or the if statement is followed by attribute value setting
                            printLine('"' + classBody[0] + '" class encapsulates the "' + attribute + '" attribute.', 1)
                            privateAttributes.remove(attribute)
                            continue
            lineNumber += 1
            
        if debug:
            print("---" + classBody[0] + "---")
            print("objects: " + str(objects))
            print("Private Attributes: " + str(privateAttributes))
            print("upcastObjects: " + str(upcastObjects))

        # find the class' constructor
        # https://stackoverflow.com/questions/1281752/accessing-elements-with-offsets-in-pythons-for-in-loops
        # we'll use enumerate to send line offset to function checkSimpleton()
        for lineNumberOffset, line in enumerate(classBody[2]):
            lineString = line[1]
            if lineString.find(" " + classBody[0] + " ") > -1 and lineString.find(" new ") == -1 \
            and lineString.find("(") > -1: # return type of the method is current class
                isConstructor = True
                constructorDepth = line[0]

                if attributes:
                    for attribute in attributes:
                        if attribute != classBody[0] and  re.search("[ ,(]+" + attribute + " ", lineString):
                            outputAssociation(classBody[0], "aggregates", attribute)
                            if debug:
                                printLine("2 " + lineString)
                            if attribute in association:
                                association.remove(attribute)
                            attributes.remove(attribute)
                
                if lineString.find(" class ") == -1 and lineString.find(" if ") == -1 and lineString[-2] == "{": # run max once per class, not an IF statement nor class declaration
                    #check, if current class is singleton
                    singletonResult = checkSingleton(classBody[2], lineNumberOffset, line[0])
                    if singletonResult == 1:
                        tempLineString = lineString[lineString.find(" " + classBody[0] + " ") + 2 + len(classBody[0]):]
                        methodEnd = tempLineString.find(" ")
                        methodName = tempLineString[:methodEnd]
                        singletonList.append((classBody[0], methodName))
                        isSingleton = -1 # we don't need to output this twice
                    elif singletonResult == 0:
                        isSingleton = -1
                    elif singletonResult == 2 and isSingleton != -1: # unless a method creates a new instance and does not implement the
                        isSingleton = 1                              # singleton pattern, this class can be considered a singleton
                        
            
            if line[0] < constructorDepth:
                isConstructor = False
                constructorDepth = -1

            if isConstructor:
                #for className in listCopy:
                for className in listOfClasses:
                    if className != classBody[0] and lineString.find(" new " + className + " ") != -1:
                        # we create a new object belonging only to current class
                        outputAssociation(classBody[0], "composites", className)
                        if className in association:
                            association.remove(className)
                        if className in attributes:
                            attributes.remove(className) # avoid the same class being considered as aggregated

        if attributes:
            while len(attributes) > 0:
                if classBody[0] != attributes[0]:
                    outputAssociation(classBody[0], "aggregates", attributes[0])
                    if attributes[0] in association:
                            association.remove(attributes[0])
                attributes.remove(attributes[0])
        
        if association:
            for associatedClass in association:
                if classBody[0] != associatedClass:
                    outputAssociation(classBody[0], "is associated with", associatedClass)

        if debug:
            for o in objects:
                printLine(str(o))

        if encapsulated:
            encapsulations += 1
        else:
            printLine("The \"" + classBody[0] + "\" class doesn't encapsulate all of its attributes!", 1)

        if isSingleton == 1 and staticInstance:
            singletonList.append((classBody[0], ""))

def checkSingleton(classBody, lineOffset, startingDepth): # returns 0 when class doesn't implement singleton pattern, 1 if does, 2 if it is not ruled out yet.

    lineOffset += 1 # we don't need to check the first line of the method
    maxRowsLeft = len(classBody) # last index of a line in classBody
    objectStart = -1
    objectEnd = -1
    returnObject = -1
    ifDepth = 0
    isIf = False
    objects = []
    ifObjects = []
    
    conditionNewObject = False # is there an object declared in an IF statement? 
    conditionPredeclared = False # does the method return a pre-declared object otherwise?
    
    calledNew = False # True when the class' type variable gets instantiated
                      # if True and all other conditions are false, the class does not implement the singleton pattern.

    for index in range(lineOffset, maxRowsLeft):
        if classBody[index][0] < startingDepth: # end of method
            break
        if classBody[index][0] < ifDepth and isIf: # if function body ended
            isIf = False
        if classBody[index][1].find(" if ") > -1: # start of if function body
            ifDepth = classBody[index][0]
            isIf = True
        objectEnd = classBody[index][1].find(" = new ")
        if objectEnd > -1: # we found an object which will most likely be returned by the method
            calledNew = True
            objectStart = classBody[index][1][:objectEnd].rfind(" ") + 1
            objectName = classBody[index][1][objectStart:objectEnd]
            if isIf:
                ifObjects.append(objectName)
            else:
                objects.append(objectName)
        returnObject = classBody[index][1].find(" return ")
        if returnObject > -1:
            returnedObj = classBody[index][1][returnObject+8:]
            returnedObj = returnedObj[:returnedObj.find(" ")]
           
            if not isIf:
                for tempObj in ifObjects: # the new object in if statement was pre-declared
                    if tempObj == returnedObj:
                        conditionNewObject = True
                        conditionPredeclared = True
                        if debug:
                            print("3")
    
    if debug:
        print(classBody[0][1])
        print("\nconditionNewObject: " + str(conditionNewObject) + "\nconditionPredeclared: " + str(conditionPredeclared))
        print("\n")
    if conditionNewObject and conditionPredeclared:
        return 1
    if not calledNew:
        return 2
    return 0

def addSpaces(line):
    replaceChars = "(),=.+-*/"
    index = 0
    length = len(replaceChars)
    char = "("
    
    # remove // comments
    if line.find("//") > -1:
        if line.find("/*") > -1 and line.find("//") > line.find("/*"):
            line = line.replace("//", "")
        else:
            line = line[:line.find("//")]

    while index < length:
        char = replaceChars[index]

        if char == "/":
            line = line.replace("//", ";;") # replace comment markers with ";;" (;; doesn't make sense)
                                           # so we can rely on a ";;" symbol being a temporary replacement of "//"
            line = line.replace("/ *", ";COMMENTSTART;") # very low chance that this would actually be in the inputted files
            line = line.replace("* /", ";COMMENTEND;") # with a space in between since we just added spaces ahead and afer the "*" character
            line = line.replace(char, " " + char + " ") # slashes that are division, not comments
            line = line.replace(";;", "//") # return the comment markers
            line = line.replace(";COMMENTSTART;", "/*")
            line = line.replace(";COMMENTEND;", "*/")
        else:
            line = line.replace(char, " " + char + " ")
        
        index += 1
    
    return line

def detectInFolder(path): #returns true if succeeded, false if input path does not exist
    global javaFiles
    if not os.path.exists(path):
        printLine("Specified path does not exist.")
        if len(path) < 3:
            return -1 # change the path window value to default path
        return 0 # keep the current path window value

    for fileName in os.listdir(path): # open every file in current directory folder
        if os.path.isdir(path + "\\" + fileName):
            if fileName.find("ignore") == -1:
                detectInFolder(path + '\\' + fileName)
        global printFilename
        printFilename = True
        if (fileName.rfind(".java") != -1 and fileName.rfind(".java") + 5 == len(fileName)) \
            or (fileName.rfind(".aj") != -1 and fileName.rfind(".aj") + 3 == len(fileName)):
            # we found a .java / aspectJ file (name.java.txt does't count as a java file)
            javaFiles += 1
            try:
                file = open(os.path.join(path, fileName), 'r', encoding="utf-8") # can read wilder letters
                lines = file.readlines()
            except:
                try:
                    file = open(os.path.join(path, fileName), 'r') # can read accents
                    lines = file.readlines()
                except:
                    printSummary("Unable to decode at least one character in the " + fileName + " file!")
                    return 0
            
            lineNumber = 0
            lineStart = ""
            for classBody in classContent:
                classBody[1] = -1000 # in case a class' body hasn't been closed off }
        
            for fullLine in lines:
                lineFromCode = fullLine
                if len(lineStart) > 0:
                    lineStart += lineFromCode
                    lineFromCode = lineStart
                    lineStart = ""
                lineNumber += 1
                outputLine = lineFromCode
                # remove string definitions " "
                commentLocation = lineFromCode.find('"')
                if commentLocation > -1:
                    isString = False
                    stringStart = 0
                    stringEnd = 0
                    while commentLocation != -1:
                        if lineFromCode[commentLocation-1] != "\\":
                            # quotation mark we found isn't a part of the string's value
                            if not isString: # start of string declaration
                                stringStart = commentLocation
                            else: # end of string declaration
                                stringEnd = commentLocation
                                lineFromCode = lineFromCode[:stringStart] + lineFromCode[stringEnd+1:] # crop out the string
                                commentLocation = -1
                        else:
                            commentLocation += lineFromCode[commentLocation+1:].find('"') + 1
                            continue
                        if isString:
                            commentLocation = lineFromCode[commentLocation+1:].find('"')
                        else:
                            commentLocation += lineFromCode[commentLocation+1:].find('"') + 1
                    
                        isString = not isString
            
                isString = False
                lineFromCode = lineFromCode.replace("{", "{;") # we want to split string on {,
                # but we also want to keep the { symbol in the 1st substring
            
                lineFromCode = lineFromCode.replace("}", "};") # "} catch(exception) {" would cause issues otherwise
                                                               # (2 depth changes in one line)
            
                lineFromCode = addSpaces(lineFromCode) # add spaces around select characters
            
                lineFromCode = re.sub(r"\[(.*?)\]", "", lineFromCode) # "array[i]" -> "array"
                                                                      # arrays aren't important for our purpouses
            
                multipleComments = True
                while multipleComments:
                    multipleComments = False
                    if lineFromCode.find("/*") > -1: # the following special symbols are a part of a comment, we must keep looking for "*/"
                        if lineFromCode.find("*/") > -1: # we found the end of the commnet
                            lineFromCode = lineFromCode[:lineFromCode.find("/*")] + lineFromCode[lineFromCode.find("*/")+3:] # crop out the comment
                            multipleComments = True
                        # int x = /* ....... */ 5 /* ... */ + 4 ; -> int x = 5 + 4 ;
                        else:
                            lineFromCode = lineFromCode[:lineFromCode.find("/*")+2]

                # remove comments //
                commentLocation = lineFromCode.find("//")                
                if commentLocation > -1:
                    if commentLocation == 0: # the whole line was just a comment
                        continue
                    else:
                        lineFromCode = lineFromCode[:commentLocation-1]
                
                # a line got split into two lines in source code (doesn't apply to comments)
                if not lineFromCode.isspace() and len(lineFromCode) > 0 and lineFromCode.find(";") == -1:
                    lineStart = lineFromCode
                else:
                    splitLines = lineFromCode.split(";") # split line on ; or {
                    i = 0
                    for line in splitLines:
                        i += 1
                        

                
                        if line.find("{") > -1:
                            line = line.replace("{", " { ") # add an extra space before { character in case there wasn't one
                            line = " ".join(line.split()) # squeeze whitespaces
                            line = " " + line
                            #https://stackoverflow.com/questions/1546226/is-there-a-simple-way-to-remove-multiple-spaces-in-a-string
                        else:
                            line = " ".join(line.split()) # squeeze whitespaces
                            line = " " + line + " " # add an extra empty space to find out name of a class more easily
                            # " class ourClass "
                
                        if line.isspace():
                            continue
                        
                        if line.find(" Map<") > -1 or line.find(" Map <") > -1: # private Map <..., ...> map_name; -> private Map map_name;
                            startIndex1 = line.find(" Map<")
                            startIndex2 = line.find(" Map <")
                            startIndex1 = max(startIndex1, startIndex2)
                            startIndex1 += line[startIndex1:].find("<")
                            line = line[:startIndex1] +  line[line.rfind(">")+1:]

                        line = line.replace(" ArrayList ", " ")
                        line = line.replace(" ArrayList<", " ")
                        line = line.replace(" List ", " ")
                        line = line.replace(" List<", " ")
                        line = line.replace("<", " ")
                        line = line.replace(">", " ")

                        line = " ".join(line.split()) # squeeze whitespaces
                        line = " " + line + " "
                        

                        # ---detection of individual OOP mechanisms---
                        if isString == False and line.find(" class ") > -1 or line.find(" interface ") > -1:
                            
                            isClass = True
                            if line.find(" interface ") > -1:
                                isClass = False
                            else:
                                detectClass(line, lineNumber, outputLine, "implements", fileName, isClass, False)
                            replaced = False
                            if line.find(" implements ") > -1:
                                replaced = True
                                line = line.replace(" implements ", " extends ")
                            if line.find(".") == -1:
                                line = line.replace(" interface ", " class ")
                            detectClass(line, lineNumber, outputLine, "extends", fileName, isClass, replaced)
                        updateDepth(line)
            file.close()
    return 1

def finalOutputs():
    # add parent classes that are not declared in input files but are extended in them
    # for example "ourClass extends thread {"
    for assumedParent in orphans.copy():
        addParent(assumedParent[1], False, 0)

    printHierarchies(0) # class hierarchy
    printHierarchies(1) # interface hierarchy
    
    scanObjects() # get objects of all classes (but not objects declared in methods)
    scanClasses()
    printDesignPatterns()

    printHierarchies(2) # nested class hierarchy
    
    classString = " classes; "
    if polymorphisms == 1:
        classString = " class; "

    objString = " objects"
    if objPolymorphisms == 1:
        objString = " object"
    
    printSummary("Total amount of class inheritance hierarchies: " + str(inheritances))
    printSummary("Total amount of interface inheritance hierarchies: " + str(interfaces))
    printSummary("Total amount of polymorphisms: " + str(polymorphisms) + classString + str(objPolymorphisms) + objString)
    printSummary("Total amount of aggregations: " + str(aggregations))
    printSummary("Total amount of compositions: " + str(compositions))
    printSummary("Total amount of encapsulated classes: " + str(encapsulations) + " out of " + str(len(listOfClasses)))
    if len(listOfClasses) > 0:
        listOfClassesString = "\nList of types: "
        for className in listOfClasses:
            listOfClassesString += className + ", "
        printSummary(listOfClassesString[:-2])

    if javaFiles == 0:
        printLine("No Java source code files were found in the specified path.")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

root = Tk()

root.iconbitmap(resource_path("appIcon.ico"))

canvas = Canvas(root, width=50, height=50)
canvas.place(x=3, y=70, in_=root)
img = PhotoImage(file=resource_path("Logo.png"))
canvas.create_image(27, 27, image = img)

textFont = ("Cascadia Mono", 13)
textWidth = 75

inputTextField = Text(root, height = 1, width = 61, font=textFont)
inputTextField.place(x=60, y=19, in_=root)
inputTextField.insert(END, path)

def runProgram():
    parents.clear()
    orphans.clear()
    classContent.clear()
    listOfClasses.clear()
    listOfInterfaces.clear()
    listOfParents.clear()
    singletonList.clear()
    designPattern[0].clear() # clear singletons
    bannedStrings.clear()
    for i in range(len(outputLines)):
        outputLines[i].clear()
    summaryLines.clear()

    global javaFiles
    javaFiles = 0

    global inheritances
    inheritances = 0

    global interfaces
    interfaces = 0

    global polymorphisms
    polymorphisms = 0

    global objPolymorphisms
    objPolymorphisms = 0

    global aggregations
    aggregations = 0

    global compositions
    compositions = 0

    global encapsulations
    encapsulations = 0
    global path
    returnVal = detectInFolder(path)
    
    if returnVal == 1:
        finalOutputs()
    elif returnVal == -1:
        path = rootDirectory
        inputTextField.delete('1.0', END)
        inputTextField.insert(END, path)


runProgram()

root.title("Object-oriented mechanisms identification")
root.geometry('824x650')
root.resizable(False,False)

maxHeight = 19

outputTextField = Text(root, height=maxHeight, width=textWidth, font=textFont)
outputTextField.place(x=60, y=200, in_=root)
outputTextField.config(state=DISABLED)

summaryTextField = Text(root, height=6, width=textWidth, font=textFont)
summaryTextField.place(x=60, y=55, in_=root)
summaryTextField.config(state=DISABLED)

versionLabel = Label(root, text="version: 1.0.0", font=textFont).place(x=10, y=622)

def updateText(textField, lines, indexes = False):
    textField.config(state=NORMAL)
    textField.delete('1.0', END)
    if indexes:
        for i in range(len(lines)):
            if len(lines[i]) > 0:
                if i == 0 and lines[0][0] != "No Java source code files were found in the specified path." and lines[0][0] != "Specified path does not exist.":
                    textField.insert(END, '-Hierarchies:')
                elif i == 1:
                    textField.insert(END, '\n-Encapsulations:\n')
                elif i == 2:
                    textField.insert(END, '\n-Associations:\n')
                elif i == 3:
                    textField.insert(END, '\n-Polymorphisms:\n')
                elif i == 4:
                    textField.insert(END, '\n-Design patterns:\n')

            for line in lines[i]:
                textField.insert(END, line + '\n')

    else:
        for line in lines:
            textField.insert(END, line + '\n')
    textField.config(state=DISABLED)


def runFunction():
    global path
    path = inputTextField.get(1.0, "end-1c").rstrip()
    runProgram()
    
    updateText(outputTextField, outputLines, True)
    updateText(summaryTextField, summaryLines)

# https://stackoverflow.com/a/55099951/18908257
def getFilePath ():
    global path
    tempdir = filedialog.askdirectory(parent=root, initialdir=path, title='Please select a directory')
    tempdir = tempdir.replace("/", "\\") # keep the slashes consistent for Windows (both would work though)
    if len(tempdir) > 0:
        path = tempdir
        inputTextField.delete('1.0', END)
        inputTextField.insert(END, path)
        
runButton = Button(root, text="Run", command=runFunction, padx=10, pady=10).place(x=5,y=10)
pathButton = Button(root, text="Browse for directory", command=getFilePath, padx=10, pady=10).place(x=680,y=10)
updateText(outputTextField, outputLines, True)
updateText(summaryTextField, summaryLines)
mainloop()