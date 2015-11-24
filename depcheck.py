import re, subprocess
from config import *

#Python cmp function improvement for version compare borrowed from:
# http://stackoverflow.com/questions/1714027/version-number-comparison
# Returns zero for equal version numbers, Positive for version1 newer than version2, negative for version1 older than version2
def versioncompare(version1, version2):
	def normalize(v):
		return [int(x) for x in re.sub(r'(\.0+)*$','', v).split(".")]
	return cmp(normalize(version1), normalize(version2))

#Check dependencies are present and in the minimum versions
def checkDeps():
	versionre = re.compile(r"version ([0-9.]*)")
	gitversion = versionre.search(subprocess.check_output("git --version", shell=True)).group(1)
	retstring = ""
	retstring += "Local Git version: "+gitversion
	if gitversion:
		if versioncompare(gitversion,minimumGitVersion) < 0:
			raise Exception("Detected git version of "+gitversion+" is too low, "+minimumGitVersion+" required.")
	svnversion = versionre.search(subprocess.check_output("svn --version", shell=True)).group(1)
	retstring += " Local SVN version: "+svnversion
	if svnversion:
		if versioncompare(svnversion,minimumSVNVersion) < 0:
			raise Exception("Detected git version of "+svnversion+" is too low, "+minimumSVNVersion+" required.")
	hgversion = versionre.search(subprocess.check_output("hg --version", shell=True)).group(1)
	retstring += " Local Mercurial version: "+hgversion
	if hgversion:
		if versioncompare(hgversion,minimumHGVersion) < 0:
			raise Exception("Detected Mercurial version of "+hgversion+" is too low, "+minimumHGVersion+" required.")
	return True


if __name__ == "__main__":
	checkDeps()