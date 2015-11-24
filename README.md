#Google Code Repository Grab
This script's goal is to download the source code and repository data from Google Code projects. This document is still in progress.

##Work Flow
See workflow.txt for a diagram outlining workflow of the script and output files for different repository types.

##Requirements
Python 2.7+

Git: 1.5.1+

SVN: 1.7.0+

Mercurial: 3.0+

#Pipeline

Distribution-specific setup
-------------------------
### For Debian/Ubuntu:

    adduser --system --group --shell /bin/bash archiveteam
    apt-get install -y git-core libgnutls-dev screen python-dev python-pip bzip2 zlib1g-dev mercurial subversion
    pip install seesaw
    wget http://mercurial.selenic.com/release/mercurial-3.6.1.tar.gz
    tar -xzf mercurial-3.6.1.tar.gz
    cd mercurial-3.6.1; make all; make install
    su -c "cd /home/archiveteam; git clone https://github.com/chpwssn/googlecode-repograb.git; cd googlecode-grab;" archiveteam
    screen su -c "cd /home/archiveteam/googlecode-repograb/; run-pipeline pipeline.py --concurrent 2 --address '127.0.0.1' YOURNICKHERE" archiveteam
    [... ctrl+A D to detach ...]


# Grab Project

##Required Flags
	-p projectname, --project=projectname Google Code project name

	-D DATADIR, --data-dir=DATADIR Data directory

##Optional Flags
	  --version             show program's version number and exit
  
	  -h, --help            show this help message and exit
  
	  -d, --dry-run         run without downloading repository
  
	  -P, --phone-home      send crash reports and other diagnostic information
  
	  -l, --log             log debug info to defined file
  
	  --paranoid            Do paranoid repository verification

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