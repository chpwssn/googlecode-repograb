#Google Code Repository Grab
This script's goal is to download the source code and repository data from Google Code projects. This document is still in progress.

##Work Flow
See workflow.txt for a diagram outlining workflow of the script and output files for different repository types.

##Requirements
Python 2.7+

Git: 1.5.1+

SVN: 1.7.0+

Mercurial: 3.0+


##Required Flags
	-p projectname, --project=projectname Google Code project name

	-D DATADIR, --data-dir=DATADIR Data directory

##Optional Flags
	--version             show program's version number and exit
 
 	-h, --help            show this help message and exit
  
	-d, --dry-run         run without downloading repository
  
	-P, --phone-home      send crash reports and other diagnostic information back  
	
	-l, --log             log debug info to grabProject.log

##Examples
Examples write to a data directory "data" and write to the log file.

###Mercurial Example
	./grabProject.py -p pyglet -D data -l
	
###SVN Example
	./grabProject.py -p foobnix -D data -l
	
###Git Example
	./grabProject.py -p damnvid -D data -l
	
##Phone Home
Phone Home, or central reporting, is disabled by default and is used in the initial testing stages. This causes the script to send back useful data including:
* URL Errors encountered by the script
* Report discovered repository sources. Automates building a single list of repositories.