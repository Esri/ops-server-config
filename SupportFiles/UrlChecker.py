#!/bin/env python2.7
#------------------------------------------------------------------------------
# Copyright 2014-2015 Esri
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
#------------------------------------------------------------------------------
# Name: UrlChecker.py
# Usage: python.exe UrlChecker.py [Output File:(.csv)] [Directory To Check] [File Filters(default:".html,.erb")]
# Requirements/Constraints: Must run with Python 2.X (because of use of urllib2)
#-------------------------------------------------------------------------------
# Description: a URL Checking script
# 1. This script will crawl the specified local directory
# 2. Open each text file matching the file filter/extension
# 3. Check for valid URLs in the file (verify that the URL provides a valid response)
# 4. Output bad URLs to a csv file
#-------------------------------------------------------------------------------

import csv    
import datetime  
import os
import re
import sys
import traceback
import urllib2    # Python3 Note: will need changed

def usage():
	print('Usage: python.exe UrlChecker.py [Output File(.csv)] [Directory To Check] [File Filters(ex/default:".html,.erb")]')

def main():

	try :

		HREF_FOR_LOCAL_LINKS = 'href="http://localhost:4567/'  # NOTE: set to None to not use

		# Set this path to local folder containing the web site repo you want to crawl (or pass in as parameter)		
		# Currently defaults to current path
		DEFAULT_PATH = '.'
		# Ex: DEFAULT_PATH = 'C:/my-website/html'
		 
		# if this verbose flag is set - it will list all URLs found (not just failing ones)
		verbose = False

		# a list of all the errors found
		urlErrorsList = []

		if len(sys.argv) < 2 :
			outputFile = 'UrlResults.csv'
		else :
			outputFile = sys.argv[1]

		if len(sys.argv) < 3 :
			path = DEFAULT_PATH
		else :
			path = sys.argv[2]

		if len(sys.argv) < 4 :
			patterns = ['.html', '.erb']
			# Add usage() if not all args supplied:
			usage()
		else :
			stringFilter = sys.argv[3]
			patterns = stringFilter.split(',')

		print('[Output File]:        ' + outputFile)
		print('[Directory To Check]: ' + path)
		print('[File Filters]:       ' + ', '.join(patterns))

		if not os.path.exists(path) : 
			raise Exception("Selected path does not exist: " + path)

		# Walks through directory structure looking for files matching patterns
		matchingFileList = \
			[os.path.join(dp, f) \
				for dp, dn, filenames in os.walk(path) \
					for f in filenames \
						if os.path.splitext(f)[1] in patterns]

		fileCount, urlFileCount, urlCount = 0, 0, 0

		# For each file, searches the file for references to http and https. 
		for currentFile in matchingFileList:			
			fileCount += 1
			print('Checking File #' + str(fileCount) + ', file: ' + currentFile)
			searchfile = open(currentFile, 'r')
			lineNumber = 0
			newUrlFile = True
			for line in searchfile:
				lineNumber += 1
				
				if '<!--' in line:   # HACK: ignore comment line (also assumes only one line comments)
					continue
				
				if 'href="/' in line:
					if HREF_FOR_LOCAL_LINKS is not None :
						oldLine = line
						line = line.replace('href="/', HREF_FOR_LOCAL_LINKS)
						#if debug neeeded
						#print('Replaced local link line:')
						#print('Original: ' + oldLine)
						#print('Replaced: ' + line)

				if 'href="http' in line:
					# Get a list of items between quotes " "
					quotedItems = re.findall('"([^"]*)"', line)
					for quotedItem in quotedItems:
						# If Web Link found, then test URL
						if ('http' or 'https') in quotedItem:
							badUrl = False
							url, code, message = '', '', ''							
							try:
								url = quotedItem
								response = urllib2.urlopen(url)
								code = str(response.getcode())
								checkUrl = response.geturl() # just in case we want to check the 2
								message = 'no error'

							except urllib2.HTTPError as httpErr:
								badUrl  = True
								code    = str(httpErr.code)
								# message = TODO
								# if more info needed then potentially strip from response
								# error_message = httpErr.read()
								# print(error_message)
					
							except urllib2.URLError as urlErr:
								badUrl  = True
								code    = '0'
								message = urlErr.args

							if badUrl or verbose :
								urlCount += 1
								if newUrlFile : 
									urlFileCount += 1
									newUrlFile = False
								urlError = [str(urlCount), str(urlFileCount), currentFile, str(lineNumber), url, code, message]
								urlErrorsList.append(urlError)

			searchfile.close

		if verbose: 
			print(str(urlCount) + ' URLs found in ' + str(fileCount) + ' files checked.')			
		else : 						
			if urlCount == 0 :			
				print('No Bad URLs found - Good Work!')
				return
			else : 
				print(str(urlCount) + ' BAD URLs found in ' + str(urlFileCount) + ' files, among ' + str(fileCount) + ' files checked. See csv report.')			
				
		# Now output URL Errors to file
		with open(outputFile, 'wb') as csvfile:   # Python3 Note: will need changed (to 'w')
			errorWriter = csv.writer(csvfile)

			# Header Row
			errorWriter.writerow(['URL Count', 'File Count', 'File Name', 'Line Number', 'URL', 'Return Code', 'Message'])

			for row in urlErrorsList : 
				errorWriter.writerow(row) 

		# if we made it here, we have bad links, so return a failure code so calling script will know
		sys.exit(-1)
		
	except Exception as err :
		print(traceback.format_exception_only(type(err), err)[0].rstrip())
		sys.exit(-1)

if __name__ == '__main__':
	print('Start Time: ' + str(datetime.datetime.now()))
	main()
	print('End Time: ' + str(datetime.datetime.now()))

