import os
import re
import sys
import io
from stat import *


def convertContent(fileContents):

    replacement = re.sub(
        r'(\d\d:\d\d:\d\d).(\d\d\d) --> (\d\d:\d\d:\d\d).(\d\d\d)(?:[ \-\w]+:[\w\%\d:]+)*\n', r'\1,\2 --> \3,\4\n', fileContents)
    replacement = re.sub(
        r'(\d\d:\d\d).(\d\d\d) --> (\d\d:\d\d).(\d\d\d)(?:[ \-\w]+:[\w\%\d:]+)*\n', r'\1,\2 --> \3,\4\n', replacement)
    replacement = re.sub(
        r'(\d\d).(\d\d\d) --> (\d\d).(\d\d\d)(?:[ \-\w]+:[\w\%\d:]+)*\n', r'\1,\2 --> \3,\4\n', replacement)
    replacement = re.sub(r'WEBVTT\n\n', '', replacement)
    replacement = re.sub(r'Kind:[ \-\w]+\n', '', replacement)
    replacement = re.sub(r'Language:[ \-\w]+\n', '', replacement)
    # replacement = re.sub(r'^\d+\n', '', replacement)
    # replacement = re.sub(r'\n\d+\n', '\n', replacement)
    replacement = re.sub(r'<c[.\w\d]*>', '', replacement)
    replacement = re.sub(r'</c>', '', replacement)
    replacement = re.sub(r'<\d\d:\d\d:\d\d.\d\d\d>', '', replacement)
    replacement = re.sub(
        r'::[\-\w]+\([\-.\w\d]+\)[ ]*{[.,:;\(\) \-\w\d]+\n }\n', '', replacement)
    replacement = re.sub(r'Style:\n##\n', '', replacement)

    return replacement


def fileCreate(strNamaFile, strData):
    # --------------------------------
    # fileCreate(strNamaFile, strData)
    # create a text file
    #
    try:

        f = open(strNamaFile, "w", encoding='utf-8')
        f.writelines(str(strData))
        f.close()

    except IOError:

        strNamaFile = strNamaFile.split(os.sep)[-1]
        f = open(strNamaFile, "w", encoding='utf-8')
        f.writelines(str(strData))
        f.close()

    # print("file created: " + strNamaFile + "\n")


def readTextFile(strNamaFile):

    f = open(strNamaFile, mode='r', encoding='utf-8')

    # print("file being read: " + strNamaFile + "\n")

    return f.read()


def vtt_to_srt(strNamaFile):

    fileContents = readTextFile(strNamaFile)

    strData = ""

    strData = strData + convertContent(fileContents)

    strNamaFile = strNamaFile.replace(".vtt", ".srt")

    # print(strNamaFile)

    fileCreate(strNamaFile, strData)


def walktree(TopMostPath, callback):
    '''recursively descend the directory tree rooted at TopMostPath,
       calling the callback function for each regular file'''

    for f in os.listdir(TopMostPath):

        pathname = os.path.join(TopMostPath, f)
        mode = os.stat(pathname)[ST_MODE]

        if S_ISDIR(mode):

            # It's a directory, recurse into it
            walktree(pathname, callback)

        elif S_ISREG(mode):

            # It's a file, call the callback function
            callback(pathname)

        else:

            # Unknown file type, print a message
            print('Skipping %s' % pathname)


def walkdir(TopMostPath, callback):
    for f in os.listdir(TopMostPath):
        pathname = os.path.join(TopMostPath, f)
        if not os.path.isdir(pathname):
            # It's a file, call the callback function
            callback(pathname)


def convertVTTtoSRT(f):
    if '.vtt' in f:
        vtt_to_srt(f)


def vtts_to_srt(directory, rec=False):
    TopMostPath = directory
    if rec:
        walktree(TopMostPath, convertVTTtoSRT)
    else:
        walkdir(TopMostPath, convertVTTtoSRT)


if __name__ == '__main__':

    path = 'aaa.vtt'

    if os.path.isdir(path):
        vtts_to_srt(path)
    else:
        vtt_to_srt(path)
