#!/bin/env python2.7
# ------------------------------------------------------------------------------
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
# ------------------------------------------------------------------------------
# Name: UrlChecker.py
# Usage: python.exe UrlChecker.py [Output File:(.csv)] [Directory To Check]
# 					[File Filters(default:".html,.erb")] [Local Server URL]
# Requirements/Constraints: Must run with Python 2.X (because of use of urllib2)
# -------------------------------------------------------------------------------
# Description: a URL Checking script
# 1. This script will crawl the specified local directory
# 2. Open each text file matching the file filter/extension
# 3. Check for valid URLs in the file (verify that the URL provides a valid response)
# 4. Output bad URLs to a csv file
# -------------------------------------------------------------------------------

import csv
import datetime
import os
import re
import sys
import traceback
import urllib2    # Python3 Note: will need changed


def usage():
	''' Prints how to use script'''
	print('Usage: python.exe UrlChecker.py [Output File(.csv)] [Directory To Check] '
		  '[File Filters(ex/default:".html,.erb")] [Local Server URL]')


def checkUrl(url):
	badUrl = False
	code, message = '', ''
	try:
		response = urllib2.urlopen(url)
		code = str(response.getcode())
		checkUrl = response.geturl()  # just in case we want to check the 2
		message = 'no error'

	except urllib2.HTTPError as httpErr:
		badUrl = True
		code = str(httpErr.code)
		# message = TODO
		# if more info needed then potentially strip from response
		# error_message = httpErr.read()

	except urllib2.URLError as urlErr:
		badUrl = True
		code = re.sub("\D", "", str(urlErr.args))  # strips out string leaves only error code
		message = urlErr.reason

	except Exception as generalErr:
		badUrl = True
		message = 'Unknown Error: ' + str(generalErr)

	return badUrl, code, message

def main():

	try:

		# Set this path to local folder containing the web site repo you want to crawl
		# (or pass in as parameter) - currently defaults to current path
		DEFAULT_PATH = '.'
		# Ex: DEFAULT_PATH = 'C:/my-website/html'

		#######################################################
		# The DEFAULT_SERVER_URL_FOR_LOCAL_LINKS if not passed in as a parameter
		# This server address will be added to all local links, ex:
		# if DEFAULT_SERVER_URL_FOR_LOCAL_LINKS = 'http://localhost'
		# "a href="/military/land-operations/templates/" --> becomes -->
		# "a href="http://localhost/military/land-operations/templates/"
		# NOTE: Setting this value to None disables this link expansion capability
		# TODO: Set this URL if desired:
		DEFAULT_SERVER_URL_FOR_LOCAL_LINKS = None # "http://localhost:4567" # = None to disable
		#######################################################

		# if this verbose flag is set - it will list all URLs found (not just failing ones)
		verbose = False

		# a list of all the errors found
		urlErrorsList = []

		if len(sys.argv) < 2:
			outputFile = 'UrlResults.csv'
		else:
			outputFile = sys.argv[1]

		if len(sys.argv) < 3:
			path = DEFAULT_PATH
		else:
			path = sys.argv[2]

		if len(sys.argv) < 4:
			patterns = ['.html', '.erb']
		else:
			stringFilter = sys.argv[3]
			patterns = stringFilter.split(',')

		if len(sys.argv) < 5:
			# Add usage() if not all args supplied:
			usage()
			serverUrlForLocalLinks = DEFAULT_SERVER_URL_FOR_LOCAL_LINKS
		else:
			serverUrlForLocalLinks = sys.argv[4]

		if serverUrlForLocalLinks is None:
			hRefForLocalLinks = None
		else:
			hRefForLocalLinks = 'href="' + serverUrlForLocalLinks + '/'

		print('[Output File]:        ' + outputFile)
		print('[Directory To Check]: ' + path)
		print('[File Filters]:       ' + ', '.join(patterns))
		if serverUrlForLocalLinks is not None:
			print('[Local Server URL]:   ' + serverUrlForLocalLinks)
			# Verify that the server is up & available
			badUrl, code, message = checkUrl(serverUrlForLocalLinks)
			if badUrl:
				print('*****WARNING: Server Host Unreachable*****')
				print('Is server running at: ' + serverUrlForLocalLinks + '?')
				print('*****All local links will fail*******')

		if not os.path.exists(path):
			raise Exception("Selected path does not exist: " + path)

		# if an existing file was selected for outputFile, make sure we can access/open
		# (just in case we have the file open in excel or other program that locks access to it)
		if os.path.isfile(outputFile):
			try:
				open(outputFile, 'w')
			except:
				raise Exception('Cannot open/access existing file for writing: ' + outputFile)

		# Walks through directory structure looking for files matching patterns
		matchingFileList = \
			[os.path.join(dp, f) \
				for dp, dn, filenames in os.walk(path) \
					for f in filenames \
						if os.path.splitext(f)[1] in patterns]

		fileCount, urlFileCount, urlCount = 0, 0, 0

		# For each file, searches the file for references to http and https.
		for currentFile in matchingFileList:
			try:
				fileCount += 1
				print('Checking File #' + str(fileCount) + ', file: ' + currentFile)
				searchfile = open(currentFile, 'r')
				lineNumber = 0
				newUrlFile = True
				commentBlock = False
				for line in searchfile:
					lineNumber += 1

					###################################
					# Ignore comments/comment blocks
					if '<!--' in line:
						# debug: print('Start of Comment Block at Line #:'  + str(lineNumber) + ': ' + line)
						commentBlock = True

					if commentBlock and ('-->' in line):
						# debug: print('End of Comment Block at Line #:'  + str(lineNumber) + ': ' + line)
						line = line.split('-->')[1]  # TRICKY: still check this line, just in case stuff after comment
						commentBlock = False

					if commentBlock:
						# debug: print('Skipping Comment Line #:'  + str(lineNumber) + ': ' + line)
						continue
					###################################

					if 'href="/' in line:
						if hRefForLocalLinks is not None:
							oldLine = line
							line = line.replace('href="/', hRefForLocalLinks)
							# debug: print('Replaced local link line-Original: ' + oldLine + 'Replaced: ' + line)

					if 'http' in line:
						# Get a list of items between quotes " "
						quotedItems = re.findall('"([^"]*)"', line)
						for quotedItem in quotedItems:
							# If Web Link found, then test URL
							if ('http' or 'https') in quotedItem:
								url = quotedItem
								badUrl, code, message = checkUrl(url)

								if badUrl or verbose:
									urlCount += 1
									if newUrlFile:
										urlFileCount += 1
										newUrlFile = False
									urlError = [str(urlCount), str(urlFileCount), currentFile, str(lineNumber), url, code, message]
									urlErrorsList.append(urlError)

				searchfile.close
			except Exception as loopErr:
				print("Unknown exception while processing file: " + currentFile)
				print(traceback.format_exception_only(type(loopErr), loopErr)[0].rstrip())

		if verbose:
			print(str(urlCount) + ' URLs found in ' + str(fileCount) + ' files checked.')
		else:
			if urlCount == 0:
				print('No Bad URLs found - Good Work!')
				return
			else:
				print(str(urlCount) + ' BAD URLs found in ' + str(urlFileCount) + ' files, among ' + str(fileCount) + ' files checked. See csv report.')

		# Now output URL Errors to file
		with open(outputFile, 'wb') as csvfile:   # Python3 Note: will need changed (to 'w')
			errorWriter = csv.writer(csvfile)

			# Header Row
			errorWriter.writerow(['URL Count', 'File Count', 'File Name', 'Line Number', 'URL', 'Return Code', 'Message'])

			for row in urlErrorsList:
				errorWriter.writerow(row)

		# if we made it here, we have bad links, so return a failure code so calling script will know
		sys.exit(-1)

	except Exception as err:
		print(traceback.format_exception_only(type(err), err)[0].rstrip())
		sys.exit(-1)

if __name__ == '__main__':
	print('Start Time: ' + str(datetime.datetime.now()))
	main()
	print('End Time: ' + str(datetime.datetime.now()))

