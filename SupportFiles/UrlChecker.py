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
# Usage:
# python.exe UrlChecker.py [Output File:(.csv)] [Directory To Check]
# [File Filters(default:".html,.erb")]
# Requirements/Constraints: Must run with Python 2.X (because of use of urllib2)
# -------------------------------------------------------------------------------
# Description: a URL Checking script
# 1. This script will crawl the specified local directory
# 2. Open each text file matching the file filter/extension
# 3. Check for valid URLs in the file (verify that the URL provides a valid
#    response)
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
    """Prints what the script arguments are."""
    print 'Usage: python.exe UrlChecker.py [Output File(.csv)]' \
        '[Directory To Check] [File Filters(ex/default:".html,.erb")]'


def main():
    """Calls main application"""
    try:

        # Set this path to local folder containing the web site repo you want
        # to crawl (or pass in as parameter)
        # Currently defaults to current path
        default_path = '.'
        # Ex: default_path = 'C:/my-website/html'

        # if this verbose flag is set - it will list all URLs found
        # (not just failing ones)
        verbose = True

        # a list of all the errors found
        url_errors_list = []

        if len(sys.argv) < 2:
            ouput_file = 'UrlResults.csv'
        else:
            ouput_file = sys.argv[1]

        if len(sys.argv) < 3:
            path = default_path
        else:
            path = sys.argv[2]

        if len(sys.argv) < 4:
            patterns = ['.html', '.erb']
            # Add usage() if not all args supplied:
            usage()
        else:
            stringfilter = sys.argv[3]
            patterns = stringfilter.split(',')

        print '[Output File]:        ' + ouput_file
        print '[Directory To Check]: ' + path
        print '[File Filters]:       ' + ', '.join(patterns)

        if not os.path.exists(path):
            raise Exception("Selected path does not exist: " + path)

        # Walks through directory structure looking for files matching patterns
        matching_file_list = \
            [os.path.join(dp, f)
             for dp, dn, filenames in os.walk(path)
             for f in filenames
             if os.path.splitext(f)[1] in patterns]

        file_count, url_file_count, url_count = 0, 0, 0

        # For each file, searches the file for references to http and https.
        for current_file in matching_file_list:
            file_count += 1
            print 'Checking File #' + str(file_count) + ', file: ' + current_file
            searchfile = open(current_file, 'r')
            line_number = 0
            new_url_file = True
            for line in searchfile:
                line_number += 1

                if '<!--' in line:
                    # HACK: ignore comment line
                    # (also assumes only one line comments)
                    continue

                if 'href=' in line:
                    # Get a list of items between quotes " "
                    quoted_items = re.findall('"([^"]*)"', line)
                    print quoted_items
                    for quoted_item in quoted_items:
                        # If Web Link found, then test URL
                        if ('/' or 'http' or 'https') in quoted_item:
                            print 'quoted item ' + quoted_item
                            bad_url = False
                            url, code, message = '', '', ''
                            try:
                                url = quoted_item
                                response = urllib2.urlopen(url)
                                code = str(response.getcode())
                                check_url = response.geturl()
                                # just in case we want to check the 2
                                message = 'no error'

                            except urllib2.HTTPError as http_err:
                                bad_url = True
                                code = str(http_err.code)
                                # message = TODO
                                # if more info needed then
                                # potentially strip from response
                                # error_message = http_err.read()
                                # print(error_message)

                            except urllib2.URLError as url_err:
                                bad_url = True
                                code = '0'
                                message = url_err.args

                            except ValueError:
                                pass

                            if bad_url or verbose:
                                url_count += 1
                                if new_url_file:
                                    url_file_count += 1
                                    new_url_file = False
                                url_error = [str(url_count), str(url_file_count),
                                             current_file, str(line_number), url,
                                             code, message]
                                url_errors_list.append(url_error)

            searchfile.close

        if verbose:
            print(str(url_count) + ' URLs found in ' + str(file_count) +
                  ' files checked.')
        else:
            if url_count == 0:
                print 'No Bad URLs found - Good Work!'
                return
            else:
                print(str(url_count) + ' BAD URLs found in ' +
                      str(url_file_count) + ' files, among ' +
                      str(file_count) + ' files checked. See csv report.')

        # Now output URL Errors to file
        with open(ouput_file, 'wb') as csvfile:
            # Python3 Note: will need changed (to 'w')
            error_writer = csv.writer(csvfile)

            # Header Row
            error_writer.writerow(['URL Count', 'File Count', 'File Name',
                                   'Line Number', 'URL', 'Return Code',
                                   'Message'])

            for row in url_errors_list:
                error_writer.writerow(row)

        # if we made it here, we have bad links, so return a failure code so
        # calling script will know
        sys.exit(-1)

    except Exception as err:
        print traceback.format_exception_only(type(err), err)[0].rstrip()
        sys.exit(-1)

if __name__ == '__main__':
    print 'Start Time: ' + str(datetime.datetime.now())
    main()
    print 'End Time: ' + str(datetime.datetime.now())
