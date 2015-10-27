# encoding=utf8
import datetime
from distutils.version import StrictVersion
import hashlib
import os.path
import shutil
import socket
import sys
import time
import random
import string
import os

import seesaw
from seesaw.config import NumberConfigValue
from seesaw.externalprocess import ExternalProcess
from seesaw.item import ItemInterpolation, ItemValue
from seesaw.pipeline import Pipeline
from seesaw.project import Project
from seesaw.task import SimpleTask, LimitConcurrent
from seesaw.tracker import GetItemFromTracker, PrepareStatsForTracker, \
	UploadWithTracker, SendDoneToTracker
from seesaw.util import find_executable




# check the seesaw version
if StrictVersion(seesaw.__version__) < StrictVersion("0.1.5"):
	raise Exception("This pipeline needs seesaw version 0.1.5 or higher.")


###########################################################################
# Find a useful grabProject executable.
#
GRAB_TEST = find_executable(
	"grabProject",
	["1"],
	[
		"./grabProject.py",
		"../grabProject.py",
		"../../grabProject.py",
		"/home/warrior/grabProject.py",
		"/usr/bin/grabProject.py"
	]
)


###########################################################################
# The version number of this pipeline definition.
#
# Update this each time you make a non-cosmetic change.
# It will be added to the WARC files and reported to the tracker.
VERSION = "20150618.02"
USER_AGENT = 'DerpyGoogleCodeGrab'
TRACKER_ID = 'googlecode-rsync'
TRACKER_HOST = 'tracker.nerds.io'


###########################################################################
# This section defines project-specific tasks.
#
# Simple tasks (tasks that do not need any concurrency) are based on the
# SimpleTask class and have a process(item) method that is called for
# each item.
class CheckIP(SimpleTask):
	def __init__(self):
		SimpleTask.__init__(self, "CheckIP")
		self._counter = 0

	def process(self, item):
		# NEW for 2014! Check if we are behind firewall/proxy

		if self._counter <= 0:
			item.log_output('Checking IP address.')
			ip_set = set()

			ip_set.add(socket.gethostbyname('twitter.com'))
			ip_set.add(socket.gethostbyname('facebook.com'))
			ip_set.add(socket.gethostbyname('youtube.com'))
			ip_set.add(socket.gethostbyname('microsoft.com'))
			ip_set.add(socket.gethostbyname('icanhas.cheezburger.com'))
			ip_set.add(socket.gethostbyname('archiveteam.org'))

			if len(ip_set) != 6:
				item.log_output('Got IP addresses: {0}'.format(ip_set))
				item.log_output(
					'Are you behind a firewall/proxy? That is a big no-no!')
				raise Exception(
					'Are you behind a firewall/proxy? That is a big no-no!')

		# Check only occasionally
		if self._counter <= 0:
			self._counter = 10
		else:
			self._counter -= 1


class PrepareDirectories(SimpleTask):
	def __init__(self):
		SimpleTask.__init__(self, "PrepareDirectories")
		
	def process(self, item):
		item_name = item["item_name"]
		dirname = item["data_dir"]
		
		if os.path.isdir(dirname):
			shutil.rmtree(dirname)

		os.makedirs(dirname)

		item["item_dir"] = dirname
		#item["warc_file_base"] = "%s-%s-%s" % (self.warc_prefix,
		#									   item_name.replace(':', '_'),
		#									   time.strftime("%Y%m%d-%H%M%S"))

		#open("%(item_dir)s/%(warc_file_base)s.warc.gz" % item, "w").close()

		
class cleanItem(object):
	'''Removes the : in an item while formatting based on ItemInterpolation'''
	def __init__(self, s):
		self.s = s

	def realize(self, item):
		return string.replace(self.s % item,":",".")

	def __str__(self):
		return "<'" + string.replace(self.s % item,":",".") + "'>"
		
class projectName(object):
	'''Returns a project item's value '''
	def __init__(self):
		pass

	def realize(self, item):
		item_name = item['item_name']
		assert ":" in item_name
		item_type, item_value = item_name.split(':', 1)
		assert "project" in item_type
		return item_value
		
	def __str__(self):
		return "<'" + string.replace(self.s % item,":",".") + "'>"
		
class fileList(object):
	'''Lists the files in the data dir'''
	def __init__(self):
		pass

	def realize(self, item):
		return os.listdir(item['data_dir'])
		
	def __str__(self):
		return "<'" + string.replace(self.s % item,":",".") + "'>"


class MoveFiles(SimpleTask):
	def __init__(self):
		SimpleTask.__init__(self, "MoveFiles")

	def process(self, item):
		os.rename("%(item_dir)s/%(warc_file_base)s.txt.gz" % item,
				  "%(data_dir)s/%(warc_file_base)s.txt.gz" % item)

		shutil.rmtree("%(item_dir)s" % item)


def get_hash(filename):
	with open(filename, 'rb') as in_file:
		return hashlib.sha1(in_file.read()).hexdigest()


CWD = os.getcwd()
PIPELINE_SHA1 = get_hash(os.path.join(CWD, 'pipeline.py'))


def stats_id_function(item):
	# NEW for 2014! Some accountability hashes and stats.
	d = {
		'pipeline_hash': PIPELINE_SHA1,
		'python_version': sys.version,
	}

	return d


###########################################################################
# Initialize the project.
#
# This will be shown in the warrior management panel. The logo should not
# be too big. The deadline is optional.
project = Project(
	title="sourceforgersync",
	project_html="""
		<img class="project-logo" alt="Project logo" src="http://a.fsdn.com/con/img/sftheme/logo.png" height="50px" title=""/>
		<h2>sourceforge.net <span class="links"><a href="http://sourceforge.net/">Website</a> &middot; <a href="http://tracker.archiveteam.org/sourceforgersync/">Leaderboard</a></span></h2>
		<p>Saving all project from SourceForge. rsyncing all of the source code repositories.</p>
	"""
)

pipeline = Pipeline(
	CheckIP(),
	GetItemFromTracker("http://%s/%s" % (TRACKER_HOST, TRACKER_ID), downloader, VERSION),
	PrepareDirectories(),
	#LimitConcurrent(1,ExternalProcess("Size Test",[RSYNC_TEST,"-t",getRsyncURL("foo"),"-m",MAX_RSYNC])),
	#LimitConcurrent(1,ExternalProcess("rsync", ["rsync", "--progress", "-av", getRsyncURL("foo"), cleanItem("%(data_dir)s/%(item_name)s")])),
	ExternalProcess("grabProject.py", ["python", "./grabProject.py", "-D", cleanItem("%(data_dir)s/"), "-p",  projectName(), "-l"]),
	ExternalProcess("sleep", [ "sleep", str(NumberConfigValue(name="example.sleep", title="Time to sleep", description="The example project will sleep n seconds.", min=1, max=15, default="5").value)]),
	ExternalProcess("echo", ["echo", "%(data_dir)s/"]),
	LimitConcurrent(NumberConfigValue(min=1, max=4, default="1",
		name="shared:rsync_threads", title="Rsync threads",
		description="The maximum number of concurrent uploads."),
		UploadWithTracker(
			"http://%s/%s" % (TRACKER_HOST, TRACKER_ID),
			downloader=downloader,
			version=VERSION,
			files= fileList(),
			rsync_target_source_path=ItemInterpolation("%(data_dir)s/"),
			rsync_extra_args=[
				"--recursive",
				"--partial",
				"--partial-dir", ".rsync-tmp",
			]
		),
	),
	PrepareStatsForTracker(
		defaults={"downloader": downloader, "version": VERSION},
		file_groups={
			"data": [
				cleanItem("%(data_dir)s")
			]
		},
		id_function=stats_id_function,
	),
	SendDoneToTracker(
		tracker_url="http://%s/%s" % (TRACKER_HOST, TRACKER_ID),
		stats=ItemValue("stats")
	)
)
