#Google Code Repository Grab
This script's goal is to download the source code and repository data from Google Code projects. This document is still in progress.

##Work Flow
See workflow.txt for a diagram outlining workflow of the script and output files for different repository types.

##Requirements
Minimum requirements are still in progress but packages are: git, svn, hg

##Required Flags
	-p projectname, --project=projectname Google Code project name

	-D DATADIR, --data-dir=DATADIR Data directory

##Optional Flags
	--version             show program's version number and exit
 
 	-h, --help            show this help message and exit
  
	-d, --dry-run         run without downloading repository
  
	-l, --log             log debug info to grabProject.log

##Examples
Examples write to a data directory "data" and write to the log file.

###Mercurial Example
	./grabProject.py -p pyglet -D data -l
	
###SVN Example
	./grabProject.py -p foobnix -D data -l
	
###Git Example
	./grabProject.py -p damnvid -D data -l