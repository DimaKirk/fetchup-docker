#!/bin/pyhon
import subprocess
import os

core_branch = "develop"
mgr_branch = "develop"
mgr_name = "bill-manager"
git_host = "git.ispsystem.net"
core_build_dir =  "/build"
discc_gen_hosts_dir = "distcc-gen-hosts"
need_core_rpm = False
thread_count = "20"
mgr_dir = "/usr/local/mgr5"

def RunShellCommand(command, check_return_code = True):
	print("run command '" + command + "'")
	p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
	line = True
	while line:
		line = p.stdout.readline()
		print line.strip()
	p.wait()
	if (check_return_code and p.returncode != 0):
		raise Exception("command '" + command + "' return error")
	return p.returncode

def SetupDistcc():
	print("setup distcc-gen-hosts")
	os.chdir(core_build_dir)
	if (not os.path.exists(discc_gen_hosts_dir)):
		RunShellCommand("git clone https://github.com/DimaKirk/distcc-gen-hosts.git")
	os.chdir(discc_gen_hosts_dir)
	RunShellCommand("git pull")
	RunShellCommand("python distcc-genhosts.py")

def GitClone(mgr, branch):
	if (os.path.exists(mgr)):
		print("use existing " + mgr)
		os.chdir(mgr)
		RunShellCommand("git pull")
	else:
		RunShellCommand("git clone git@" + git_host + ":" + mgr + ".git")
		os.chdir(mgr)
		RunShellCommand("git submodule init")
		RunShellCommand("git submodule update")
	RunShellCommand("git checkout " + branch)
	RunShellCommand("git pull")


print("Script for make up")
if (not os.path.exists("/root/.ssh")):
	os.mkdir("/root/.ssh")
RunShellCommand("ssh-keyscan " + git_host + " > ~/.ssh/known_hosts")
RunShellCommand("ssh-keyscan intrepo.download.ispsystem.com >> ~/.ssh/known_hosts")

if (not os.path.exists(core_build_dir)):
	os.mkdir(core_build_dir)

SetupDistcc()
os.chdir(core_build_dir)
print("checkout COREmanager")
GitClone("core-manager", core_branch)
print("make COREmanager")
RunShellCommand("make clean")
#RunShellCommand("COMPILER='clang' CCOMPILER='clang++' NOEXTERNAL=yes make centos-prepare")
RunShellCommand("COMPILER='distcc clang' CCOMPILER='distcc clang++' NOEXTERNAL=yes make dist DISTDIR=/usr/local/mgr5 -j" + thread_count)
core_ver_file = os.path.join(core_build_dir, "core_ver");
if (not os.path.exists(core_ver_file) or need_core_rpm):
	if (not os.path.exists(core_ver_file)):
		open(core_ver_file, "w").write("10000")
	print("make rpm COREmanager")
	core_ver = int(open(core_ver_file, "r").read()) + 1;
	open(core_ver_file, "w").write(str(core_ver))
	RunShellCommand("COMPILER='clang' CCOMPILER='clang++' NOEXTERNAL=yes make rpm-dep")
	RunShellCommand("make -j" + thread_count + " rpm PKG_VERSION=5.99.0 PKG_REL=" + str(core_ver))
	RunShellCommand("rpm --nodeps -iU .build/packages/coremanager-5.99.0-" + str(core_ver) + ".el7.centos.x86_64.rpm")


os.chdir(os.path.join(mgr_dir, "src"));
print("checkout " + mgr_name)
GitClone(mgr_name, mgr_branch)
print("make " + mgr_name)
RunShellCommand("make clean")
RunShellCommand("COMPILER='distcc clang' CCOMPILER='distcc clang++' NOEXTERNAL=yes make install -j" + thread_count)
print("make up")
RunShellCommand("chmod 600 autotool/dkey")
RunShellCommand("COMPILER='clang' CCOMPILER='clang++' NOEXTERNAL=yes make up")






