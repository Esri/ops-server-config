#!/usr/bin/env python
#------------------------------------------------------------------------------
# Copyright 2014 Esri
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#==============================================================================
#Name:          Utilities.py
#
#Purpose:       Various utility functions
#
#==============================================================================
import sys, os, traceback
import ctypes
import walkingDirTrees
import fileinput
import string

def makePath(driveLetter, dirPathList):
    # Returns string that represents a file/folder path contructed
    # by joining the drive letter string (i.e. driveLetter variable)
    # and all elements of the path list (i.e. dirPathList variable) where
    # path delimiter is the appropriate delimiter for operating system.
    
    
    # Remove all forward/back slashes that may be inappropriate for
    # OS; also reinsert drive colon character in case it's in
    # improper position; also capitalize drive letter for
    # consistency
    # Pre-process drive letter string to ensure value is appropriate
    # Remove:
    #   White space
    #   Forward/back slashes (let Python insert appropriate character)
    #   Colon (remove incase user added colon in wrong position)
    # Capitalize drive letter
    driveLetter = driveLetter.replace(" ", "")
    driveLetter = driveLetter.replace("/", "")
    driveLetter = driveLetter.replace("\\", "")
    driveLetter = driveLetter.replace(":", "")
    driveLetter = driveLetter.upper()
    
    
    # Re-insert drive letter colon character to ensure that
    # it exists at end of driveLetter string
    driveLetter = driveLetter + ":"
    
    # Return properly constructed path
    return os.path.join(driveLetter + os.sep, *dirPathList)

def changeOwnership(dirToModifyOwnership, ownerAccount):
    
    if os.path.exists(dirToModifyOwnership):
        print "\t\tAssigning ownership of folder/file '" + dirToModifyOwnership + "' to user account '" + ownerAccount
        os.popen("icacls " + dirToModifyOwnership + " /setowner " + ownerAccount +" /t")
        print "\t\tDone."
        print

def getFreeSpace(path, spaceUnit):
    # Determines space available where "folder" parameter is located.
    # Returns available space in units specified by "spaceUnit" parameter.
    
    free_bytes = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(path), None, \
                                               None, ctypes.pointer(free_bytes))
    
    return convertSizeUnit(free_bytes.value, "GB")

def getDirSize(root, sizeUnit):
    #code example from:
    #http://stackoverflow.com/questions/1987119/
    #   fast-folder-size-calculation-in-python-on-windows
    # Added call to convertSizeUnit myself
    size = 0 
    for path, dirs, files in os.walk(root): 
        for f in files: 
            size +=  os.path.getsize( os.path.join( path, f ) )
    
    return convertSizeUnit(size, "GB") 

def convertSizeUnit(sizeInBytesValue, sizeUnit):
    # Convert Bytes to different unit
    
    sizeUnit = sizeUnit.upper()
    
    if sizeUnit == "B":     # Byte
        size = sizeInBytesValue
    elif sizeUnit == "KB":  # Kilobyte
        size = sizeInBytesValue / 1024.0
    elif sizeUnit == "MB":  # Megabyte
        size = sizeInBytesValue / 1024.0 ** 2
    elif sizeUnit == "GB":  # Gigabyte
        size = sizeInBytesValue / 1024.0 ** 3
    elif sizeUnit == "TB":  # Terebyte
        size = sizeInBytesValue / 1024.0 ** 4
    elif sizeUnit == "PB":  # Petabyte
        size = sizeInBytesValue / 1024.0 ** 5
    elif sizeUnit == "EB":  # Exabyte
        size = sizeInBytesValue / 1024.0 ** 6
    else:                   # Byte
        size = sizeInBytesValue
        
    return size

def findFilePath(rootPath, fileName, returnFirst=True):
    # Given a root path to search ("rootPath") find the path of the file
    # with name "fileName". "fileName" variable can also be a pattern
    # (i.e. *.txt).
    # NOTE: if more then one file is found, it returns only first path found.
    # NOTE: if returnFirst=True the only first found file is returned as string
    #   otherwise all files are returned as list
    
    fileList = walkingDirTrees.listFiles(rootPath, fileName)
    
    if returnFirst:
        return fileList[0]
    else:
        return fileList

def findFolderPath(rootPath, folderName, returnFirst=True):
    # Given a root path to search ("rootPath") find the path of the folder
    # with name "folderName". "folderName" variable can also be a pattern
    # (i.e. *.txt).
    # NOTE: if more then one folder is found, it returns only first path found.
    # NOTE: if returnFirst=True the only first found folder is returned as string
    #   otherwise all files are returned as list
    
    # Traverse folder structure. This will return both folders and files.
    folderList = walkingDirTrees.listFiles(rootPath, folderName, recurse=1, return_folders=1)
    
    # Edit list in place; only keep those paths which are directories.
    folderList[:] = [folderPath for folderPath in folderList if os.path.isdir(folderPath)]
    
    if returnFirst:
        return folderList[0]
    else:
        return folderList

def findInFile(filePath, strToFind):
    foundInLine = None
    if os.path.exists(filePath):
        f = open(filePath, "r")
        for line in f:
            # remove leading/trailing spaces
            line = line.strip()
            if line.find(strToFind) > -1:
                foundInLine = line
                break
    else:
        print "\tError: File " + filePath + " does not exist."
    
    return foundInLine
    
def editFiles(filesToEdit, findString, replaceString):
    # Replace the "findString" with "replaceString" for each file
    # in the "filesToEdit" list.
    
    for f in filesToEdit:
        print
        print "\t\t-Editing file: " + f
        print "\t\t\tReplacing '" + findString + "'"
        print "\t\t\twith '" + replaceString + "'..."
        for line in fileinput.FileInput(f,inplace=1):
            # Also remove the newline character from end of line, otherwise
            # when "line" is printed below an extra newline character
            # will be embedded.
            line = line.replace(findString,replaceString).rstrip("\n")
            #!!! NOTE: you must print line to screen for "inplace" option to work
            print line
        print "\t\t\tDone."
        
def intersect(a, b):
    # Returns interset of two lists (i.e. returns a list containing
    # elements that exist in both list "a" and list "b").
    # NOTE: "a" and "b" can be dictionaries, is which case a list
    # of dictionary keys that exist in both are returned.
    return list(set(a) & set(b))
 
def getDrives():
    # Return list of drives letters.
    # From http://stackoverflow.com/questions/
    # 827371/is-there-a-way-to-list-all-the-available-drive-letters-in-python
    drives = [] 
    bitmask = ctypes.windll.kernel32.GetLogicalDrives() 
    for letter in string.uppercase: 
        if bitmask & 1: 
            drives.append(letter) 
        bitmask >>= 1 
 
    return drives

def doesDriveExist(driveLetter):
    # Returns boolean indicating if driveLetter exists
    exists = False
    existingDrives = str(getDrives()).upper()
    
    if existingDrives.find(driveLetter.upper()) > -1:
        exists = True
    
    return exists
    
def validate_user_repsonse_yesno(value):
    ''' Evaluate user response to yes/no question and return True/False '''
    response = False
    valid_values = ['y', 'yes'] # specified values in lowercase
    if not value:
        value = ''
    value = value.lower().strip().replace(" ","")
    if value in valid_values:
        response = True
    return response

    