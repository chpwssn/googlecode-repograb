#!/usr/bin/env python 
# Google Code Repository Grabber
# This tool is meant to be supplied with a Google Code project name and result in the download of the project's source.
# TODO:
# Add minimum version checking for dependencies recommended: "git 1.5.1+ svn 1.7.0+ hg 3.0+ better but anything 1.0+ should work"
# Catch and respond to too many requests HTTP response
# Handle source not exsiting
# Check archive api for connection validation on url error
# Add some sort of local size reporting for debugging/analysis 
# Talk about bundle vs tarball: bundle only? tarball only? both? bundle in the tarball?
# Handle passing file names to pipeline if necesary 

import re, urllib2, os, time
from optparse import OptionParser
from urllib import urlencode
import subprocess

#Some Config Here
logging = False
logFileName = "grabProject.log"
phoneHomeDomain = "http://archiveapi.nerds.io/"
minimumGitVersion = "1.5.1"
minimumSVNVersion = "1.7.0"
minimumHGVersion = "3.0"

#Define Error Codes
ERROR_NO_PROJECT = 1
ERROR_PROJECT_NOT_FOUND = 2
ERROR_SERVICE_UNAVAILABLE = 3
ERROR_BAD_HTTPRESPONSE = 4
ERROR_SOURCE_NOT_PRESENT = 5
ERROR_NO_DATA_DIR = 6
ERROR_DATA_DIR_NOT_FOUND = 7
ERROR_NO_SOURCES_FOUND = 8
ERROR_URL_ERROR = 9
ERROR_GIT_VERIFY_FAIL = 10

#Python cmp function improvement for version compare borrowed from:
# http://stackoverflow.com/questions/1714027/version-number-comparison
# Returns zero for equal version numbers, Positive for version1 newer than version2, negative for version1 older than version2
def versioncompare(version1, version2):
	def normalize(v):
		return [int(x) for x in re.sub(r'(\.0+)*$','', v).split(".")]
	return cmp(normalize(version1), normalize(version2))

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
	#HG
	for hgsource in hgres:
		hgcommand = re.compile(r"^hg clone https?[^\s]*/")
		if not hgcommand.search(hgsource):
			print "Invalid hg clone command, this could be a problem later."
			logString("Invalid hg clone command: "+hgsource)
	#SVN 
	for svnsource in svnres:
		svncommand = re.compile(r"^svn checkout http[^\s]*/ [^/]*[a-zA-Z0-9]$")
		if not svncommand.search(svnsource):
			print "Invalid SVN checkout command, this could be a problem later."
			logString("Invalid SVN checkout command: "+svnsource)
	#Git
	for gitsource in gitres:
		gitcommand = re.compile(r"^git clone https?[^\s]*/")
		if not gitcommand.search(gitsource):
			print "Invalid git clone command, this could be a problem later."
			logString("Invalid git clone command: "+gitsource)
	return [hgres, svnres, gitres]
	
#Download a Git repository based on the clone command given in the project's /source/checkout page
def getGitRepo(basecommand):
	global options
	#Lots of assumptions in this section
	#print os.uname()
	#We assume the form 'git clone target' but issues should have been flagged by page parse validation
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
	os.system("git bundle create "+bundleName+" --all --branches --tags")
	verifyreturn = os.system("git bundle verify "+bundleName)
	#TODO: improve actually verify that the verify properly verified the bundle, with verification
	#Git bundle verify returns with non-zero if there are missing commits
	if not verifyreturn == 0:
		print "Git bundle verification failed, exiting"
		logString("Git bundle verification failed, exiting with code "+str(ERROR_GIT_VERIFY_FAIL))
		quit(ERROR_GIT_VERIFY_FAIL)
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
	#We assume the form 'hg clone target' but issues should have been flagged by page parse validation
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
	#We assume the form 'svn checkout target local-dir' but issues should have been flagged by page parse validation
	grabTime = str(time.time())
	bundleDest = options.datadir+options.project+"."+grabTime+".svndump"
	#We need to strip the target url since we are going to do a svnrdump, not a standard checkout
	svnsearch = re.compile(r"(https?://.*/svn/)")
	svntarget = svnsearch.findall(basecommand)[0]
	fullcommand = "svnrdump dump "+svntarget+" > "+bundleDest
	os.system(fullcommand)
	return [bundleDest]

#Sends the string back to the phone home api for logging instead of sifting through client logs
def phoneHome(repType,information):
	global options, phoneHomeDomain
	if options.phonehome:
		reqURL = 'http://archiveapi.nerds.io/phonehome/?'+urlencode({"project":options.project,"type":repType,"information":information})
		try:
			req = urllib2.Request(reqURL)
			f = urllib2.urlopen(req)
			print f.read()
		#Should do better checking here
		except:
			print "Could not phone home, please report error manually."
			logString("Could not phone home.")
			
	
	
#Option parsing
usage = "usage: "+__file__+" [options] -p <project name> -D <data directory>"

parser = OptionParser(usage, version=__file__+" 0.2")
parser.add_option("-p", "--project", dest="project",help="Google Code project name", metavar="projectname")
parser.add_option("-D", "--data-dir", dest="datadir",help="Data directory")
parser.add_option("-d", "--dry-run", action="store_true", dest="dryrun", help="run without downloading repository")
parser.add_option("-P", "--phone-home", action="store_true", dest="phonehome", help="send crash reports and other diagnostic information back to "+phoneHomeDomain)
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
	
#Dep Check, probably a better way to do this
versionre = re.compile(r"version ([0-9.]*)")
gitversion = versionre.search(subprocess.check_output("git --version", shell=True)).group(1)
logString("Local Git version: "+gitversion)
if gitversion:
	if versioncompare(gitversion,minimumGitVersion) < 0:
		logString("Git version too low, needs: "+minimumGitVersion)
		raise Exception("Detected git version of "+gitversion+" is too low, "+minimumGitVersion+" required.")
svnversion = versionre.search(subprocess.check_output("svn --version", shell=True)).group(1)
logString("Local SVN version: "+svnversion)
if svnversion:
	if versioncompare(svnversion,minimumSVNVersion) < 0:
		logString("SVN version too low, needs: "+minimumSVNVersion)
		raise Exception("Detected git version of "+svnversion+" is too low, "+minimumSVNVersion+" required.")
hgversion = versionre.search(subprocess.check_output("hg --version", shell=True)).group(1)
logString("Local Mercurial version: "+hgversion)
if hgversion:
	if versioncompare(hgversion,minimumHGVersion) < 0:
		logString("Mercurial version too low, needs: "+minimumHGVersion)
		raise Exception("Detected Mercurial version of "+hgversion+" is too low, "+minimumHGVersion+" required.")
	
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
#Catching URL Errors need to be manually debugged
except urllib2.URLError, e:
	print e.reason
	logString("Exiting with URLError "+str(e.reason)+" and exit code "+str(ERROR_URL_ERROR))
	phoneHome("crash", "URLError when checking to see if the project exists, error code "+str(ERROR_URL_ERROR))
	quit(ERROR_URL_ERROR)
		
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
#Catching URL Errors need to be manually debugged
except urllib2.URLError, e:
	print e.reason
	logString("Exiting with URLError "+str(e.reason)+" and exit code "+str(ERROR_URL_ERROR))
	quit(ERROR_URL_ERROR)
		
#If we've found code repositories on the checkout page, we need to grab them using the appropriate method
if sources:
	phoneHome("sources",sources) #helps collect the sources discovered in a central location, off by default
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
	
	
	

	