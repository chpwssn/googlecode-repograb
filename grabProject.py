#!/usr/bin/env python 
# Google Code Repository Grabber
# This tool is meant to be supplied with a Google Code project name and result in the download of the project's source.
# TODO:
# Add minimum version checking for dependencies
# Catch and respond to too many requests HTTP response
# Handle source not exsiting
# Check archive api for connection validation on url error
# Add verification of re results
# Add some sort of local size reporting for debugging/analysis 
# Talk about bundle vs tarball: bundle only? tarball only? both? bundle in the tarball?
# Handle passing file names to pipeline if necesary 

import re, urllib2, os, time
from optparse import OptionParser

#Some Config Here
logging = False
logFileName = "grabProject.log"

#Define Error Codes
ERROR_NO_PROJECT = 1
ERROR_PROJECT_NOT_FOUND = 2
ERROR_SERVICE_UNAVAILABLE = 3
ERROR_BAD_HTTPRESPONSE = 4
ERROR_SOURCE_NOT_PRESENT = 5
ERROR_NO_DATA_DIR = 6
ERROR_DATA_DIR_NOT_FOUND = 7
ERROR_NO_SOURCES_FOUND = 8

#Write a string to the log file
def logString(string):
	global logging, logFile
	if logging and logFile:
		logFile.write(string+"\n")
		
#Parse a Google Code Project's /source/checkout page for repository targets
# Input: text page source
# Return: array of arrays with checkout commands
def parseSourcePage(filecontents):
	#HG Search
	print "Searching for hg repository"
	logString("Searching for hg repository")
	hg = re.compile(r"id=\"checkoutcmd\">(hg [^<]*)")
	hgres = hg.findall(filecontents)
	print "Found hg results:"
	print hgres
	#SVN Search
	print "Searching for SVN repository"
	logString("Searching for SVN repository")
	svn = re.compile(r"id=\"checkoutcmd\">(svn [^\n]*)</tt>")
	svnres = svn.findall(filecontents)
	count = 0
	#Remove the HTML tags that the checkout pages to emphasize http
	for res in svnres:
		svnres[count] = re.sub(r"(<[^>]*>)","",res)
		count+=1
	print "Found svn results:"
	print svnres
	#Git Search
	print "Searching for git repository"
	logString("Searching for git repository")
	git = re.compile(r"id=\"checkoutcmd\">(git [^<]*)")
	gitres = git.findall(filecontents)
	print "Found git results:"
	print gitres
	#Validate 
	#TODO: Add more validation here
	return [hgres, svnres, gitres]
	
#Download a Git repository based on the clone command given in the project's /source/checkout page
def getGitRepo(basecommand):
	global options
	#Lots of assumptions in this section
	#print os.uname()
	#We assume the form 'git clone target', this needs to be checked in future versions
	grabTime = str(time.time())
	repoDest = options.datadir+options.project
	fullcommand = basecommand +" "+repoDest
	print "Executing: "+fullcommand
	logString("Executing: "+fullcommand)
	os.system(fullcommand)
	baseLocation = os.getcwd()
	os.chdir(repoDest)
	bundleName = options.project+".git."+grabTime+".bundle"
	print "Generating bundle "+bundleName+" in "+repoDest
	logString("Generating bundle "+bundleName+" in "+repoDest)
	os.system("git bundle create "+bundleName+" --branches --tags")
	os.system("git bundle verify "+bundleName)
	#TODO: actually verify that the verify properly verified the bundle, with verification
	os.chdir(baseLocation)
	print "Moving bundle file to data directory"
	os.system("mv "+repoDest+"/"+bundleName+" "+options.datadir)
	compressedName = options.project+".git."+grabTime+".tar.gz"
	print "Compressing entire repository to "+compressedName
	logString("Compressing entire repository to "+compressedName)
	os.system("tar -czf "+options.datadir+compressedName+" "+repoDest)
	print "Removing raw repository directory from data directory"
	os.system("rm -rf "+repoDest)
	return [options.datadir+compressedName,options.datadir+bundleName]
	
#Download a Mercurial repository based on the clone command given in the project's /source/checkout page
def getHGRepo(basecommand):
	global options
	#Lots of assumptions in this section
	#We assume the form 'hg clone target', this needs to be checked in future versions
	grabTime = str(time.time())
	repoDest = options.datadir+options.project
	fullcommand = basecommand +" "+repoDest
	print "Executing: "+fullcommand
	logString("Executing: "+fullcommand)
	os.system(fullcommand)
	baseLocation = os.getcwd()
	os.chdir(repoDest)
	bundleName = options.project+"."+grabTime+".hg"
	print "Generating bundle "+bundleName+" in "+repoDest
	os.system("hg bundle --base null "+bundleName)
	os.chdir(baseLocation)
	print "Moving bundle file to data directory"
	os.system("mv "+repoDest+"/"+bundleName+" "+options.datadir)
	compressedName = options.project+".hg."+grabTime+".tar.gz"
	print "Compressing entire repository to "+compressedName
	logString("Compressing entire repository to "+compressedName)
	os.system("tar -czf "+options.datadir+compressedName+" "+repoDest)
	print "Removing raw repository directory from data directory"
	os.system("rm -rf "+repoDest)
	return [options.datadir+compressedName,options.datadir+bundleName]
	
#Download a Subversion repository based on the checkout command given in the project's /source/checkout page
def getSVNRepo(basecommand):
	global options
	#Lots of assumptions in this section
	#We assume the form 'svn checkout target local-dir'
	grabTime = str(time.time())
	bundleDest = options.datadir+options.project+"."+grabTime+".svndump"
	#We need to strip the target url since we are going to do a svnrdump, not a standard checkout
	svnsearch = re.compile(r"(https?://.*/svn/)")
	svntarget = svnsearch.findall(basecommand)[0]
	fullcommand = "svnrdump dump "+svntarget+" > "+bundleDest
	os.system(fullcommand)
	return [bundleDest]
	
	
#Option parsing
usage = "usage: "+__file__+" [options] -p <project name> -D <data directory>"

parser = OptionParser(usage, version=__file__+" 0.1")
parser.add_option("-p", "--project", dest="project",help="Google Code project name", metavar="projectname")
parser.add_option("-D", "--data-dir", dest="datadir",help="Data directory")
parser.add_option("-d", "--dry-run", action="store_true", dest="dryrun", help="run without downloading repository")
parser.add_option("-l", "--log", action="store_true", dest="logging", help="log debug info to "+logFileName)
(options, args) = parser.parse_args()

#Parse logging option and open the logging file if enabled or hard coded
logFile = None
if options.logging:
	logging = True
if logging:
	try:
		logFile = open(logFileName,"a")
	except IOError, e:
		print "Error: Could not open log file."
		print e.errno
	logString("Starting run at: "+str(time.time()))
	
#Make sure the project flag is set
if not options.project:
	print "No project defined, run:\npython "+__file__+" -h\nfor more information"
	logString("No project defined, exiting with error code "+str(ERROR_NO_PROJECT))
	quit(ERROR_NO_PROJECT)
	
#Make sure the data directory flag is set
if not options.datadir:
	print "No data directory defined, run:\npython "+__file__+" -h\nfor more information"
	logString("No data directory defined, exiting with error code "+str(ERROR_NO_DATA_DIR))
	quit(ERROR_NO_DATA_DIR)
	
#Make sure the data directory exists
if not os.path.exists(options.datadir):
	print "Data directory does not exist, going to die to be safe"
	logString("Data directory does not exist, going to die to be safe with error code "+str(ERROR_DATA_DIR_NOT_FOUND))
	quit(ERROR_DATA_DIR_NOT_FOUND)
	
#Check if a data dir ends in /, if not append one
if options.datadir:
	if not options.datadir[len(options.datadir)-1] == "/":
		options.datadir += "/"
	print "Working in "+options.datadir
	logString("Working in "+options.datadir)

# Grab web pages to get more info about the project
opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'googlecodegrabber')]

#Check to see if the project exists, if the Google Code page exists
try:
	print "Attempting to open project page: "+options.project
	logString("Attempting to open project page: "+options.project)
	opener.open('https://code.google.com/p/'+options.project+'/')
	print "Opened project page! It exists!"
	logString("Opened project page! It exists!")
#Catching any HTTPErrors
except urllib2.HTTPError, e:
	logString("Fetching project page returned error code "+str(e.code))
	if e.code == 404:
		#The project page does not exist, so the project likely doesn't exist in Google Code
		print "Fetching project page responded with "+str(e.code)+", project may not exist"
		logString("Exiting with error code "+str(ERROR_PROJECT_NOT_FOUND))
		quit(ERROR_PROJECT_NOT_FOUND)
	elif e.code == 503:
		#The service responds with 503, the item should be retried
		print "Fetching project page responded with "+str(e.code)+", service is under too much load"
		logString("Exiting with error code "+str(ERROR_SERVICE_UNAVAILABLE))
		quit(ERROR_SERVICE_UNAVAILABLE)
	else:
		#Some other HTTP error that should be examined
		print "Fetching project page responded with: "+str(e.code)
		logString("Exiting with error code "+str(ERROR_BAD_HTTPRESPONSE))
		quit(ERROR_BAD_HTTPRESPONSE)
		
#Check to see if /source/checkout exists for the project
try:
	print "Attempting to open source page"
	logString("Attempting to open source page: "+options.project)
	r = opener.open('https://code.google.com/p/'+options.project+'/source/checkout')
	logString("Opened project source page")
	#Get the repository sources from the /source/checkout page
	sources = parseSourcePage(r.read())
except urllib2.HTTPError, e:
	logString("Fetching project source page returned error code "+str(e.code))
	if e.code == 404:
		#The /source/checkout page does not exist, the project may not have a code repository
		print "Fetching project source page responded with "+str(e.code)+", source is not present"
		logString("Exiting with error code "+str(ERROR_SOURCE_NOT_PRESENT))
		quit(ERROR_SOURCE_NOT_PRESENT)
	elif e.code == 503:
		#The service responds with 503, the item should be retried
		print "Fetching project source page responded with "+str(e.code)+", service is under too much load"
		logString("Exiting with error code "+str(ERROR_SERVICE_UNAVAILABLE))
		quit(ERROR_SERVICE_UNAVAILABLE)
	else:
		#Some other HTTP error that should be examined
		print "Fetching project source page responded with: "+str(e.code)
		logString("Exiting with error code "+str(ERROR_BAD_HTTPRESPONSE))
		quit(ERROR_BAD_HTTPRESPONSE)
		
#If we've found code repositories on the checkout page, we need to grab them using the appropriate method
if sources:
	datafiles = set()
	for hgrepo in sources[0]:
		for resultfile in getHGRepo(hgrepo):
			datafiles.add(resultfile)
	for svnrepo in sources[1]:
		for resultfile in getSVNRepo(svnrepo):
			datafiles.add(resultfile)
	for gitrepo in sources[2]:
		for resultfile in getGitRepo(gitrepo):
			datafiles.add(resultfile)
	print datafiles
else:
	print "No sources found for project"
	logString("No sources found for project")
	quit(ERROR_NO_SOURCES_FOUND)
	
	
	

	