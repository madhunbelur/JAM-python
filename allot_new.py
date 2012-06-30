#!/usr/bin/python

# this allot.py takes stu-data.csv (with student choices, and ranks) and also
# a bran-capacities.csv file which contains capacities, and then "allots".
# Output is currently coming to STDOUT
# program developed by FOSSEE team, IIT Bombay, in particular,
# Madhu, Parth, Prashant, Primal, Srikant. Comments to Madhu Belur
# This program is under the GPL license.
# Please see the readme.txt for running procedure but the 
# jam-allotment document for elaborate details. 

VERSIONDATE = 'June-30th-2012' # unallotted seats info and modified capacities suggestion

STUDENTDATAFILE =  'stu-template.csv'
COURSECAPACITIESFILE = 'capacities-template.csv'

from csv import reader
from collections import Counter
from operator import itemgetter, attrgetter
import time
# from copy import deepcopy
import copy

class Student():
    def __init__(self, SNo, RegNo, Name, Category, CategKey, isPD, NP, PaperCode, PaperCode2, 
                 Rank, Rank2,#mrk1,mrk2,
                 Choices, ChoicesIndx, ChoicesIter, Offered1, isOffered, canAvailFromOld, 
                 canAvailFrom, availedFrom, toConsiderNext_Ch, toConsiderNext_Cat,
                 twin2, got2, got2old, isLast, isTied, RegNoActual, PaperCodeSortBy):
        self.SNo = SNo; self.RegNo = RegNo; self.Name = Name; self.Category = Category
        self.CategKey=CategKey; self.isPD=isPD; self.NP=NP; self.PaperCode=PaperCode
        self.PaperCode2=PaperCode2; self.Rank=Rank; self.Rank2=Rank2; self.Choices=Choices
        self.ChoicesIndx = ChoicesIndx; self.ChoicesIter = ChoicesIter; self.Offered1 = Offered1
        self.isOffered = isOffered; self.canAvailFrom = canAvailFrom; self.canAvailFromOld = canAvailFromOld; self.availedFrom = availedFrom
        self.toConsiderNext_Ch = toConsiderNext_Ch; self.toConsiderNext_Cat = toConsiderNext_Cat
        self.twin2 = twin2; self.got2 = got2; self.got2old = got2old;
        self.isLast = isLast; self.isTied = isTied; self.RegNoActual = RegNoActual; 
        self.PaperCodeSortBy = PaperCodeSortBy
    def printData(self):
        print "S3" + "-" + str(self.PaperCode) + '-' + str(self.Rank) + " - " + \
            str(self.RegNo) + " : " + str(self.PaperCodeSortBy) + " : " + str(self.canAvailFrom) 
    def printDataSortBy(self):
        print "S7" + "-" + str(self.PaperCode) + '-' + str(self.Rank) + " - " + \
            str(self.RegNo) + " : " + str(self.PaperCodeSortBy) + " : " + str(self.PaperCode) 
    def printFormattedData(self): # student
        Name = str(self.Name)
        NameTitle = Name.title()
        print "S1" + "+" + str(self.PaperCode) + '+' + str(self.Rank) + " + " + \
           str(self.RegNo) + " + " + str(self.Offered1) + " in category: ", \
           str(self.availedFrom) + " : " + str(self.got2+1) + " : " \
           + ':' + str(self.isLast) + ':' + str(self.isTied) + ':' + str(self.ChoicesIndx) \
           + " - " + str(self.Choices) + NameTitle
    def printDataCompareCourseFirstLine(self): # student
        print "S9, 0RegNo, PaperCode, CourseCode, 0-ChoiceNumber, Rank, AltCategory, Name, 0-ChoiceNumber"
    def printDataCompareCourse(self): # student
        Name = str(self.Name)
        NameTitle = Name.title()
        print "S9, " + str(self.RegNoActual) + ", " + str(self.PaperCode) + ", " + str(self.Offered1) \
            + ", " + str(self.got2+1) + ", " + str(self.Rank) + ", " + str(self.availedFrom) \
            + ", " + NameTitle + ", " + str(self.got2+1)
    def GetRank(self):
        return self.Rank
    def GetName(self):
        Name = str(self.Name)
        NameTitle = Name.title()
        return NameTitle
    def setIsLastIsTied(self):
        if self.isOffered: 
            Course,lenobj = FindCourse(self.Offered1, self.PaperCode)
            if self.Rank == Course.RanksOfLastAllotted[self.availedFrom]:
                self.isLast = 'Last guy'
                if Course.ExpandedBy[self.availedFrom] > 0:
                    self.isTied = 'Tied and Last'
            else:
                self.isLast = 'not Last'
    def setCatAvail(self):
        if self.Category != 'G':
            if self.Category == 'M':
                self.canAvailFromOld.extend(['B', 'M'])
                self.canAvailFrom.extend(['B_pd_N', 'M_pd_N'])
            else: # for SC, ST and *plain* OBC
                toAppend = str(self.Category)+'_pd_N'
                self.canAvailFrom.append(toAppend)
                self.canAvailFromOld.append(self.Category)
        if self.isPD == 'Y':
            toExtend = [str(element)+'_pd_Y' for element in self.canAvailFromOld]
            self.canAvailFrom.extend(toExtend)
        self.CategKey = self.canAvailFrom[-1]
    def StudentOffer(self, CourseCode, chNum, availingIn):
        self.Offered1 = CourseCode
        self.isOffered = True
        self.availedFrom = availingIn
        self.toConsiderNext_Ch = False
        self.toConsiderNext_Cat = False
        self.got2old, self.got2 = self.got2, chNum
        if self.NP == 2: 
            self.twin2.got2old, self.twin2.got2 = self.twin2.got2, chNum
            if self.twin2.isOffered:
                RemoveFrom,lenObj = FindCourse(self.twin2.Offered1, self.twin2.PaperCode)
                RemoveFrom.RemoveStudent(self.twin2.RegNo, self.twin2.availedFrom, \
                                      'twin-removal')
                self.twin2.Offered1 = False
                self.twin2.isOffered = False
    def setSortBy(self):
        global SortByDict
        self.PaperCodeSortBy = SortByDict[self.PaperCode]
    
class StudentManager():
    """ Reads in students csv file and also checks uniqueness of RegNo."""
    global CatKeysList
    applicants = [] 
    AllChoicesOfAll = []
    AllStudentsRegNos = []
    NumberOfStudents = 0
    StuPaperCodes = []
    def csvread(self):
        CsvData = reader(open(STUDENTDATAFILE, 'rb')) # csv.reader
        next(CsvData) # skips first line (*textual* explanation)
        PreChoices = 10 # Number of compulsorynon-choice fields.(for 1 or 2 papers)
        for x in CsvData:
            stu=Student(SNo=x[0],RegNo=x[1],Name=x[2].strip(), Category=x[3],isPD=x[4],
                   NP=int(x[5]), PaperCode=x[6].strip(), PaperCode2=x[7].strip(),
                   Rank=int(x[8]), Rank2=int(x[9]), 
                   Choices=[int(x[i]) for i in range(PreChoices,len(x))], 
                   ChoicesIndx = [], ChoicesIter = [], Offered1=False, isOffered=False, 
                   canAvailFromOld = ['G'], canAvailFrom = ['G_pd_N'], availedFrom = 'None', 
                   toConsiderNext_Ch = True, CategKey='None',
                   toConsiderNext_Cat = True, twin2='None', got2=0, got2old=-1, 
                   isLast = 'UnOffered', isTied='', RegNoActual=x[1], PaperCodeSortBy=0)
            if len(stu.Choices) != 0:
                self.applicants.append(stu) 
                self.AllStudentsRegNos.append(stu.RegNo)
            stu.setCatAvail()
            stu.got2 = len(stu.Choices)
            stu.got2old = stu.got2
            stu.ChoicesIndx = range(stu.got2)
            if int(x[5])==1: # single paper
                if len(stu.PaperCode)!=2:
                    stu.PaperCode=stu.PaperCode2
                    stu.Rank=stu.Rank2
                elif len(stu.PaperCode2)!=0:
                    print "Warning: (while paper re-allocation) some problem (paper code) for", stu.RegNo
            elif int(x[5])==2: # double paper
                stu2 = copy.deepcopy(stu)
                stu2.PaperCode = stu.PaperCode2; stu2.Rank = stu.Rank2
                stu2.PaperCode2 = stu.PaperCode; stu2.Rank2 = stu.Rank
                stu.RegNo = str(stu.RegNo) + "-" + str(stu.PaperCode)
                stu2.RegNo = str(stu2.RegNo) + "-" + str(stu2.PaperCode)
                stu2.twin2 = stu; stu.twin2 = stu2
                if len(stu.Choices) != 0:
                    self.applicants.append(stu2) 
                    self.AllStudentsRegNos.append(stu2.RegNo)
            else:
                print "Warning: number of papers is neither 1 nor 2", x[1]
            self.NumberOfStudents += 1
            if stu.PaperCode not in self.StuPaperCodes:
                self.StuPaperCodes.append(stu.PaperCode)
            if stu.NP==2:
                if stu.PaperCode2 not in self.StuPaperCodes:
                    self.StuPaperCodes.append(stu.PaperCode2)
            for ch in stu.Choices:
                if not(ch in self.AllChoicesOfAll):
                    self.AllChoicesOfAll.append(ch)

class Course():
    def __init__(self, SrNo, CourseCode,
               forPaperCode, Capacities, RanksOfLastAllotted, 
               ExpandedBy, Allotted, AllottedCount, SortBy, CatFirstRank):
        self.SrNo = SrNo; self.CourseCode = CourseCode; self.forPaperCode = forPaperCode
        self.Capacities = Capacities # seats
        self.RanksOfLastAllotted = RanksOfLastAllotted # 8: GN, OBC,.., GN-PD,etc
        self.ExpandedBy = ExpandedBy # only stretching is counted
        self.Allotted = Allotted; self.AllottedCount = AllottedCount; self.SortBy = SortBy
        self.CatFirstRank = CatFirstRank
    def CourseOffer(self, RegNo, availingIn): # first sort rank wise
        #print "Z9,", RegNo, availingIn, self.Allotted[availingIn]
        if RegNo not in self.Allotted[availingIn]: 
            self.Allotted[availingIn].append(RegNo)
        else:
            print "Warning: appending double! for (regNo, CourseCode, category)", 
            print RegNo, self.CourseCode, availingIn
        ListOfAllottedStudents = [FindStudent(stuRegNo) for stuRegNo in self.Allotted[availingIn]]
        ListOfAllottedStudents.sort(key = lambda stu: Student.GetRank(FindStudent(stu.RegNo)))
        self.Allotted[availingIn] = [stu.RegNo for stu in ListOfAllottedStudents]
        self.RanksOfLastAllotted[availingIn] = Student.GetRank(FindStudent(self.Allotted[availingIn][-1]))
    def RemoveStudent(self, RegNo, availedIn, flag):
        self.Allotted[availedIn].remove(RegNo)
        stud = FindStudent(RegNo)
        stud.Offered1 = False
        stud.isOffered = False
        stud.availedFrom = 'None'
        global totalRemoved
        totalRemoved += 1
        print "Removing", RegNo, "from", self.CourseCode, availedIn, flag
    def setExpandedBy(self):
        global CatKeysReAllocateDict
        for k in CatKeysList:
            self.ExpandedBy[k] = len(self.Allotted[k])-self.Capacities[k]
            if self.ExpandedBy[k] > 0:
                print "C5,", self.CourseCode, self.forPaperCode, "Expanded by", \
                    self.ExpandedBy[k], "in", k
            elif self.ExpandedBy[k] < 0:
                print "C8," + str(self.forPaperCode) + str(",") + str(self.CourseCode), k, \
                    "Unallotted_seats:", -self.ExpandedBy[k], "Allotted_just:", len(self.Allotted[k])
                if k in CatKeysReAllocateDict.keys(): # ReAllocate: from_where:to_where
                   to_where = CatKeysReAllocateDict[k]
                   print "C3," + str(self.forPaperCode) + str(",") + str(self.CourseCode), \
                     ": Modified_Capacities of", to_where, "and", k, "(post addition, subtraction):", \
                     self.Capacities[to_where]-self.ExpandedBy[k], len(self.Allotted[k]), \
                     "(due to", -self.ExpandedBy[k], "unallotted in", k + str(")")

    def setCatFirstRank(self):
        global CatKeysList
        for k in CatKeysList:
            if len(self.Allotted[k]) != 0:
                self.CatFirstRank[k]  = Student.GetRank(FindStudent(self.Allotted[k][0]))
    def printStudentWiseData(self): # for course C9
        global CatKeysList
        for k in CatKeysList:
            for stuRegNo in self.Allotted[k]:
                stName = Student.GetName(FindStudent(stuRegNo))
                print "C9, " + str(self.CourseCode) + ", " + k + ", " + str(stuRegNo) \
                    + ", " + str(self.CourseCode) + ", " + str(self.forPaperCode) \
                    + ", " + k + ", " + stName
    def printFormattedData(self):
        global CatKeysList
        global stulist
        all_closing_ranks = ' '
        all_opening_ranks = ' '
        #for k, v in self.Allotted.iteritems():
        for k in CatKeysList:
             if len(self.Allotted[k]) != 0:
                LastStudent = FindStudent(self.Allotted[k][-1])
                LastStudentRank = LastStudent.Rank
                FirstStudent = FindStudent(self.Allotted[k][0])
                FirstStudentRank = FirstStudent.Rank
             else:
                LastStudentRank = 9999
                FirstStudentRank = 9999
             print "C1,  " + str(self.CourseCode) + ", " + str(self.forPaperCode) + ", " \
                + str(k), self.Allotted[k]
             print "C2,  " + str(self.CourseCode) + ", " + str(self.forPaperCode) + ", " \
                + str(LastStudentRank) + ", " + str(k) + ", " + str(self.Capacities[k]) + \
                ", " + str(len(self.Allotted[k])) + ', ' + str(self.ExpandedBy[k]),
             print  " (Last Student's rank, Category, capacity, actual-allotted, Expanded-By)" 
             all_closing_ranks = all_closing_ranks + ', ' + k + ':' + str(LastStudentRank) 
             all_opening_ranks = all_opening_ranks + ', ' + k + ':' + str(FirstStudentRank) 
        print "C6, Opening ranks:", all_opening_ranks, self.CourseCode, self.forPaperCode
        print "C4, Closing ranks:", all_closing_ranks, self.CourseCode, self.forPaperCode

class CourseManager():
    """ Reads in all branches csv file and checks uniqueness of branch code."""
    CourseList=[]
    AllCourseCodes = []
    CoursePaperCodes = []
    def csvread(self):
        CsvData = reader(open(COURSECAPACITIESFILE, 'r')) # csv.reader
        next(CsvData) # skips first line (*textual* explanation)
        global CatKeysList
        for x in CsvData:
            course=Course(SrNo=x[0], forPaperCode = x[1], CourseCode = int(x[2]), 
                      Capacities={key:int(x[3+CatKeysList.index(key)]) for key in CatKeysList},
                      RanksOfLastAllotted = {key:0 for key in CatKeysList}, 
                      ExpandedBy = {key:0 for key in CatKeysList},
                      Allotted = {key:[] for key in CatKeysList},
                      #isOpen = {key:"Open" for key in CatKeysList}, 
                      AllottedCount = 0, SortBy = 0,
                      CatFirstRank = {key:9999 for key in CatKeysList})
            self.CourseList.append(course)
            self.AllCourseCodes.append(course.CourseCode)
            if course.forPaperCode not in self.CoursePaperCodes:
                self.CoursePaperCodes.append(course.forPaperCode)
        y = Counter(self.AllCourseCodes) # collections.Counter
        NonUniqueCourseCodes = [i for i in y if y[i]>1]

def FindStudent(regno): 
    global stulist
    stu = [s for s in stulist if s.RegNo == regno]
    return stu[0]
 
def FindCourse(CourseCode, papercode): 
    global CourseList 
    Obj = [ob for ob in CourseList if (ob.CourseCode == CourseCode and \
           ob.forPaperCode == papercode)]
    if len(Obj) == 1:
        return  Obj[0], len(Obj)
    elif len(Obj) == 0:
        return Obj, len(Obj)
    else:
        print "Some genuine problem!", len(Obj)
        return "junk", "junk"


def CheckForOffering(stu):
    global CourseList 
    stu.toConsiderNext_Ch = True
    global iterationCount 
    while stu.toConsiderNext_Ch:  # choice while loop
        stu.toConsiderNext_Cat = True
        doubleEntry_defFalse = False
        TryGot2inG_def_false = False
        multiLoopUnfairFlag2DefaultTrue = True
        try:
            chNum = stu.ChoicesIter.next()
            Course,lenObj = FindCourse(stu.Choices[chNum], stu.PaperCode)
            if lenObj == 0: stu.toConsiderNext_Cat = False
        except StopIteration:
            stu.toConsiderNext_Ch = False
            stu.toConsiderNext_Cat = False
            if stu.NP ==2 and stu.twin2.isOffered: 
                 Course,lenObj = FindCourse(stu.twin2.Offered1, stu.PaperCode)
                 if lenObj == 1:
                    doubleEntry_defFalse = True # means the twin's Offer (THIS round) is eligible to stu too.
                    print "Double offer? for", stu.RegNo, "(and twin:", stu.twin2.RegNo, 
                    print ") who got", stu.twin2.Offered1
                    print "Twin: doubleEntry_defFalse for (POSSIBLY to decide)", stu.RegNo, iterationCount
                    stu.toConsiderNext_Cat = True # change back to True from False
                    chNum = stu.got2
            if stu.isOffered: 
                # relevant only for upgradation of previous offer to GN (..) category.
                if stu.availedFrom != 'G_pd_N':
                    chNum = stu.got2
                    stu.toConsiderNext_Cat = True
                    Course,lenObj = FindCourse(stu.Offered1, stu.PaperCode)
                    TryGot2inG_def_false = True 
                    #print "Fairness to reservation", stu.RegNo, iterationCount, TryGot2inG_def_false
        avNum = 0
        while stu.toConsiderNext_Cat: # category while loop
            avail = stu.canAvailFrom[avNum]
            if TryGot2inG_def_false:# for upgradation of category at last choice if stu.availedFrom != avail:
                if stu.availedFrom == avail:
                   multiLoopUnfairFlag2DefaultTrue = False # for upgradation of category at last choice
            isAvailable = len(Course.Allotted[avail]) < Course.Capacities[avail]
            isTiedWithLastAllotted = Course.RanksOfLastAllotted[avail] == stu.Rank
            canAllot = isAvailable or isTiedWithLastAllotted
            if canAllot and multiLoopUnfairFlag2DefaultTrue and not(doubleEntry_defFalse):
               # due to multiple loops, upgradation of category allowed except current cat
                if TryGot2inG_def_false: # stu is offered already
                    # !! sequence here is important (first remove then offer while upgrading)
                    Course.RemoveStudent(stu.RegNo, stu.availedFrom, 'same choice, but category upgrade') 
                    stu.isOffered = False
                if stu.isOffered: # was already offered a *different* (worse) choice
                    courseToRemoveFrom, lenObj = FindCourse(stu.Offered1, stu.PaperCode)
                    courseToRemoveFrom.RemoveStudent(stu.RegNo, stu.availedFrom, \
                          'Choice upgrade')
                    stu.isOffered = False
                Course.CourseOffer(stu.RegNo,avail) 
                stu.StudentOffer(Course.CourseCode, chNum, avail)# set got2, got2old, availedFrom 
            if doubleEntry_defFalse and canAllot: # has a twin who already got same course from another paper
               print "doubleEntry_defFalse activated the deductFromWhere"
               deductFromWhere(stu, stu.twin2, avail, 
                               stu.twin2.availedFrom, Course.CourseCode, chNum)
            avNum += 1
            if avNum >= len(stu.canAvailFrom): stu.toConsiderNext_Cat = False 
        global got2diff
        got2diff += stu.got2old - stu.got2

def deductFromWhere(stu, twin, avail, # Note: stu is TO BE availed, twin ALREADY got paper2
                    twinAvailed, CourseCode, chNum):
  paper1, paper2 = stu.PaperCode, twin.PaperCode
  print "   Iteration count:", iterationCount, stu.RegNo, "and his/her twin with paper codes", stu.PaperCode, stu.twin2.PaperCode,
  print "with ranks respectively:", stu.Rank, twin.Rank, "get through into", CourseCode
  CourseTwin, lenobjTwin = FindCourse(twin.Offered1, twin.PaperCode)
  if stu.isOffered:
      removeStuPerhaps, lenObj = FindCourse(stu.Offered1, stu.PaperCode)
  Course, lenobj = FindCourse(CourseCode, stu.PaperCode)
  if lenobj == 1: 
      print Course.Allotted[avail], Course.Allotted[twinAvailed]
  else:
      print "Warning"
  stringRawInput = 'Enter either ' + paper1 + ' or ' + paper2 + ' to *allot* him/her: '
  while True:
    paper0 = raw_input(stringRawInput)
    print "You typed", paper0
    if paper0 == paper1:
       stu.StudentOffer(CourseCode, stu.got2, avail)
       Course, lenObj = FindCourse(CourseCode, paper0)
       Course.CourseOffer(stu.RegNo, avail)
       break
    elif paper0 == paper2:
       twin.StudentOffer(CourseCode, twin.got2, twinAvailed)
       Course, lenObj = FindCourse(CourseCode, paper0)
       Course.CourseOffer(twin.RegNo, twinAvailed)
       break
    else:
       print "  Only one of the two mentioned, please."
       print " "
  stu.got2old, stu.got2 = stu.got2, chNum
  stu.twin2.got2old, stu.twin2.got2 = stu.twin2.got2, chNum
  

def Complain(stu, course): # student tries complaining rank unfairness
  rankUnfair = stu.Rank <= course.RanksOfLastAllotted[stu.CategKey]
  unFilled = course.Capacities[stu.CategKey] > len(course.Allotted[stu.CategKey])
  if (rankUnfair or unFilled):
     print "Z5,", stu.RegNo, "has valid complaint for his choice", course.CourseCode
  else:
     pass
     #print "Z6, checked for: RegNo, offered? offered-coursecode in cat?", stu.RegNo, stu.isOffered, stu.Offered1, stu.availedFrom, "for course", course.CourseCode


def CheckCourseLastRanker(course,k):
  list1 = [FindStudent(stuRegNo) for stuRegNo in course.Allotted[k]]
  newlist = sorted(list1, key = lambda stu: Student.GetRank(FindStudent(stu.RegNo)))
  if len(newlist) != 0:
    if newlist[-1].Rank != course.RanksOfLastAllotted[k]:
      print "Z9, Warning: RanksOfLastAllotted is not right", course.CourseCode, k, newlist[-1].Rank, course.RanksOfLastAllotted[k]
      ranksOfStudents1 = [Student.GetRank(stu) for stu in newlist]
      ranksOfStudents2 = [Student.GetRank(stu) for stu in list1]
      print "Z3,", course.CourseCode, k, ranksOfStudents1, ranksOfStudents2
    if (k != 'G_pd_N' and len(course.Allotted['G_pd_N']) != 0):
      if course.RanksOfLastAllotted['G_pd_N'] > course.CatFirstRank[k]:
        print "Z4, Warning: category:", k, "started BEFORE GN closed! for", course.CourseCode, course.forPaperCode, course.CatFirstRank[k]
        kFirstRank = Student.GetRank(FindStudent(course.Allotted[k][0]))
      if (k == 'M' and len(course.Allotted['B']) != 0):
         if course.RanksOfLastAllotted['B'] > course.CatFirstRank['M']:
           print "Z4, Warning: category: OBC-M started BEFORE OBC closed! for", course.CourseCode, course.forPaperCode, course.CatFirstRank['M']

def ManagedToGet(stu, coursecode):# checks that every offered student has rank at most the closing rank
   course,lenobj = FindCourse(coursecode, stu.PaperCode)
   if lenobj == 1:
     if stu.Rank  > course.RanksOfLastAllotted[stu.availedFrom]:
      print "Z8, allotted student's rank is worse than last rank!", stu.RegNo, stu.Offered1, stu.Choices[stu.got2]
   else:
      print "Z0, Something strange due to lenobj not 1 inside ManagedToGet "

def main():
 global CatKeysList
 global CatKeysReAllocateDict
 global iterationCount
 global stulist
 global PaperCodesKeysList
 global CourseList
 global totalRemoved
 global got2diff
 CatKeysList = ['G_pd_N', 'B_pd_N', 'M_pd_N', 'C_pd_N', 'T_pd_N', 'G_pd_Y', 'B_pd_Y', 'M_pd_Y', 'C_pd_Y', 'T_pd_Y']
 CatKeysListFullForms = ['Gen', 'OBC_NCL', 'OBC_NCL_M', 'SC', 'ST', 'Gen_PD', 'OBC_NCL_PD', \
                         'OBC_NCL_M_PD', 'SC_PD', 'ST_PD']
 # ReAllocate: from_where:to_where
 CatKeysReAllocateDict = {'B_pd_N':'G_pd_N', 'G_pd_Y':'G_pd_N', 'B_pd_Y':'B_pd_N', \
                         'M_pd_Y':'M_pd_N', 'C_pd_Y':'C_pd_N', 'T_pd_N':'T_pd_N'}
 Stud = StudentManager()   
 Stud.csvread()
 c = CourseManager()
 c.csvread()
 stulist = Stud.applicants
 for stu in stulist:
    stu.setSortBy()
 stulist.sort(key = attrgetter('Rank'))
 stulist.sort(key = attrgetter('PaperCodeSortBy'))
 print "Student data that has been read in: sorted paper-wise, then rank-wise"
 for stu in stulist:
    stu.printData()
 print " "
 print "Allotment begins now"
 print " "
 iterationCount = 0
 CourseList = c.CourseList
 totalRemoved = -1
 totalRemovedOld = -1
 totalRemovedOldOld = -1
 while iterationCount < 7 and totalRemovedOldOld != 0:# and totalRemovedOld !=0 and totalRemoved != 0:
    print "       "
    print "        Round ", iterationCount, "begins (starts at 0)"
    print "       "
    got2diff = 0
    totalRemovedOldOld, totalRemovedOld, totalRemoved = totalRemovedOld, totalRemoved, 0
    for stu in stulist: 
        stu.ChoicesIndx = range(min(stu.got2,len(stu.Choices)))
        stu.ChoicesIter = iter(stu.ChoicesIndx)
        CheckForOffering(stu)
    iterationCount += 1
    totalAllotted = 0
    for course in CourseList:
       for key in CatKeysList:
         totalAllotted += len(course.Allotted[key])
    print "Iteration, totalAllotted, totalRemoved, totalRemovedOld, totalRemovedOldOld and got2diff Counts", 
    print iterationCount, totalAllotted, totalRemoved, totalRemovedOld, totalRemovedOldOld, got2diff
 print "        Allotment completed"
 print "       "
 print "Student-wise list of course allotments"
 print "     " 
 print "     Course-wise list of allotted students" 
 for course in CourseList:
   course.setExpandedBy()
   course.setCatFirstRank()
   course.printFormattedData()
   course.printStudentWiseData() # C9
 stulist[0].printDataCompareCourseFirstLine()
 for stu in stulist:
    stu.setIsLastIsTied()
    stu.printFormattedData()
    if stu.NP == 2:
       if stu.isOffered and stu.twin2.isOffered:
         print "Warning: Both twins", stu.RegNo, stu.twin2.RegNo, "have offers:", stu.Offered1, stu.twin2.Offered1
    stu.printDataCompareCourse() # S9
 print "Complaint-check starts"
 for stu in stulist:
   for chnum in range(stu.got2):
     ch = stu.Choices[chnum] 
     course,lenobj = FindCourse(ch, stu.PaperCode)
     if lenobj == 1:
        Complain(stu, course)
     elif lenobj == 0:
        if stu.NP == 2:
          course,lenobj = FindCourse(ch, stu.PaperCode2)
          if lenobj == 1:
            Complain(stu.twin2, course)
          else:
            print "Warning: course ineligible for BOTH twins"
        else :
          print "Warning: Student", stu.RegNo, "chose ineligible coursecodes (he/she is SINGLE paper)"
     elif lenobj > 1:
        print "Warning: some problem in multiple courses matching coursecodes and eligible papercodes"
   if stu.isOffered: 
     ManagedToGet(stu, stu.Offered1)
 for course in CourseList:
   for k in CatKeysList: 
     CheckCourseLastRanker(course,k)
 print "Printing closing ranks"
 first_line = "C7, Consolidated closing ranks, for various categories"
 second_line = "C7, PaperCode, CourseCode"
 for k in CatKeysList:
   first_line = first_line + ", " + k + ", " + str(CatKeysListFullForms[CatKeysList.index(k)]) + \
                    " (" + k + "), " + k
   second_line = second_line + ", Sanctioned, Allotted, Closing Rank"
 print first_line
 print second_line
 for course in CourseList:
   course_line = "C7, " + str(course.forPaperCode) + ", " + str(course.CourseCode)
   for k in CatKeysList:
     course_line = course_line + ", " + str(course.Capacities[k]) + ", " + \
          str(len(course.Allotted[k])) + ", " + str(course.RanksOfLastAllotted[k])
   print course_line
 #st = FindStudent('3022139')
 #print st.Rank, st.Name, st.RegNo, Student.GiveRank(st)
 print "Warning: check whether obc-m data file and new/old category (in py code), and closing ranks"
 print "Warning: Choices 113 and 114 were repeated sometimes but not all times"
 tim = time.localtime()
 print "Allotment py code version used is dated:", VERSIONDATE
 print "Student data file:", STUDENTDATAFILE, "and Course capacity file:", COURSECAPACITIESFILE
 TimeNow = str(tim.tm_hour) + ':' + str(tim.tm_min) + ':' + str(tim.tm_sec)
 DateToday = str(tim.tm_mday) + '-' + str(tim.tm_mon) + '-' + str(tim.tm_year)
 print "Data generated on (dd-mm-yyyy):", DateToday, "and time (24 hour form) (hh:min:sec):", TimeNow

if __name__ == '__main__':  
    PaperCodesList = ['BT', 'CA', 'CY', 'GG', 'GP', 'MA', 'MS', 'PH']
    IntegersList = [1,5,3,2,4,0,7,6]
    global SortByDict
    SortByDict = {key:IntegersList[PaperCodesList.index(key)] for key in PaperCodesList}
    main()

# issues. while *removing* a guy, modify lastshared Rank, expanded by also (if tied, then check)...
# reduce course.allottedCount while removing. 

# end of deductFromWhere: twin info to be pushed into stu.StudentOffer

#Course: C: C1: allotments, C2: closing ranks per category, 
# C5 expanded by
# C4, closing ranks across categories
# C8, unallotted seats
# C3, unallotted seats in PD and OBC with re-calculated seats
# C6 opening ranks  across categories
# C9, course-wise student-wise allotment (for comparison with student-wise.) # C9
# warnings: Z4: opening category BEFORE closing GN
# S1: final student allotments
# S9: final student for comparison with course-wise allotments
# S3: pre-allotment student's some data
# 

