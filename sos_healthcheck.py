#!/usr/bin/env python

import os
import time
import sys
import shutil
import commands

### OL5 or OL6
OS_VER = "Linux"
st_uname = commands.getoutput('cat uname')
if st_uname.find("el6") > 0:
	OS_VER = "OL6"
if st_uname.find("el5") > 0 or st_uname.find("xen") > 0:
	OS_VER = "OL5"
print ""

### uptime
st_hostname = commands.getoutput('cat hostname').strip()
st_date = commands.getoutput('cat date').strip()
st_year = commands.getoutput('cat date|awk \'{print $NF}\'').strip()
st_timezone = commands.getoutput('cat date|awk \'{print $5}\'').strip()
st_uptime1 = commands.getoutput('cat uptime|awk --field-separator "," \'{print $1}\'').strip()
n_uptime1 = st_uptime1.index('up')
st_uptime2 = st_uptime1[n_uptime1+3:len(st_uptime1)]
print "[INFO] Host " + st_hostname + " already running for " + st_uptime2 + " till \"" + st_date + "\""
print ""

### load average
st_load15 = commands.getoutput('cat uptime|head -1|awk --field-separator "," \'{print $NF}\'').strip()
st_load5 = commands.getoutput('cat uptime|head -1|awk --field-separator "," \'{print $(NF-1)}\'').strip()
st_load1 = commands.getoutput('cat uptime|head -1|awk --field-separator "," \'{print $(NF-2)}\'').strip()
st_load1 = st_load1[st_load1.index(":")+1:len(st_load1)]
a_load = []
a_load.append(float(st_load15))
a_load.append(float(st_load5))
a_load.append(float(st_load1))
f_max_load = max(a_load)

n_core = commands.getoutput('cat proc/cpuinfo |grep processor|tail -1|awk \'{print $3}\'')
n_core = int(n_core) + 1

st_res = "INFO"
if f_max_load > ((n_core+1)/2):
	st_res = "WARNING"
print "[" +st_res+ "] Max load in last 15 minutes is " + str(f_max_load) + ", total cpu cores " + str(int(n_core))
print ""

### chkconfig ntp/kdump
st_runlevel = commands.getoutput('cat ./sos_commands/startup/runlevel|awk \'{print $2}\'')
st_kdump = commands.getoutput('cat chkconfig| grep kdump')
if st_kdump.find(st_runlevel+":on") <0:
	print "[INFO] kdump not enabled"
else:
	print "[INFO] kdump enabled"
st_ntp = commands.getoutput('cat chkconfig| grep ntp')
if st_ntp.find(st_runlevel+":on") <0:
	print "[INFO] ntp not enabled"
else:
	print "[INFO] ntp enabled"
st_iptables = commands.getoutput('cat chkconfig| grep iptables')
if st_iptables.find(st_runlevel+":on") <0:
	print "[INFO] iptables not enabled"
else:
	print "[INFO] iptables enabled"

### check sysctl
st_sysrq = commands.getoutput('cat sos_commands/kernel/sysctl_-a |grep sysrq|awk \'{print $3}\'')
if st_sysrq == "0":
	print "[INFO] sysrq not enabled"
else:
	print "[INFO] sysrq enabled"

### check selinux
if os.path.exists("etc/sysconfig/selinux"):
	st_selinux = commands.getoutput('cat etc/sysconfig/selinux|grep -v "^#"|grep "SELINUX="|awk --field-separator "=" \'{print $2}\'')
	if st_selinux == "disabled":
		print "[INFO] SELinux disabled"
	else:
		print "[WARNING] SELinux not disabled"
	print ""

### rpmdb error
st_rpm_db = commands.getoutput('cat installed-rpms|grep "db3 error"|wc -l')
if int(st_rpm_db) > 0:
	print "[WARNING] rpmdb corrupted"

### packages oracle-validate
if OS_VER == "OL5":
	st_rpm = commands.getoutput('cat installed-rpms|grep oracle-validated|wc -l')
	if int(st_rpm) == 0:
		print "[INFO] Package oracle-validated not installed"
if OS_VER == "OL6":
	st_rpm = commands.getoutput('cat installed-rpms|grep oracle-rdbms-server-11gR2-preinstall|wc -l')
	if int(st_rpm) == 0:
		print "[INFO] Package oracle-rdbms-server-11gR2-preinstall not installed"
print ""

### memory check
hugepage_nr = commands.getoutput('cat proc/meminfo|egrep HugePages_Total|awk \'{print $2}\'')
hugepage_sz = commands.getoutput('cat proc/meminfo|egrep Hugepagesize|awk \'{print $2}\'')
total_mem = commands.getoutput('cat proc/meminfo|egrep MemTotal|awk \'{print $2}\'')
mem_cache = commands.getoutput('cat proc/meminfo|egrep Cached|grep -v Swap |awk \'{print $2}\'')
mem_buff = commands.getoutput('cat proc/meminfo|egrep Buffers |awk \'{print $2}\'')
mem_free = commands.getoutput('cat proc/meminfo|egrep MemFree |awk \'{print $2}\'')
mem_anon = commands.getoutput('cat proc/meminfo|egrep AnonPages |awk \'{print $2}\'')
mem_pagetable = commands.getoutput('cat proc/meminfo|egrep PageTables |awk \'{print $2}\'')

if hugepage_nr.strip() == "" or int(hugepage_nr) == 0:
	print "[INFO] No HugePage memory"

if hugepage_nr.strip() != "" and int(hugepage_nr) > 0:
        hugepage_total = int(hugepage_nr) * int(hugepage_sz)
        hugepage_ratio = float(hugepage_total) / float(total_mem) * 100
        print "[INFO] HugePage memory %.2f%% of total memory" %hugepage_ratio

f_mem_avail = 100* (float(mem_cache)+float(mem_buff)+float(mem_free))/float(total_mem)
print "[INFO] Available memory (free+cached+buffer) %.2f%% of total memory" %f_mem_avail

f_mem_anon = 100 * float(mem_anon)/float(total_mem)
print "[INFO] Anonymous memory %.2f%% of total memory" %f_mem_anon

f_mem_pagetable = 100 * float(mem_pagetable)/float(total_mem)
print "[INFO] PageTables memory %.2f%% of total memory" %f_mem_pagetable

### 0 swap
st_swap_total = commands.getoutput('cat free |grep Swap|awk \'{print $2}\'')
if int(st_swap_total) == 0:
	print "[WARNING] Zero size swap space"
print ""

### 100% disk usage
bDf = False
st_volumes = commands.getoutput('cat df |awk \'{print $5}\'|grep "%"|grep -v Use|awk --field-separator "%" \'{print $1}\'')
for i in range (0,len(st_volumes.split('\n'))):
	st_vol = st_volumes.split('\n')[i]
	if int(st_vol) > 90:
		bDf = True
		break
if bDf == True:
	print "[WARNING] Some file system usage > 90%"
else:
	print "[INFO] All file systems usage < 90%"
print ""

### check ps
st_stateD = commands.getoutput('cat ps | grep -v USER| grep "D\ "|wc -l')
if int(st_stateD) != 0:
	print "[WARNING] D state processes existing"
st_osw = commands.getoutput('cat ps | grep -v USER| egrep -i "osw|Exawat"|wc -l')
if int(st_osw) > 0:
	print "[INFO] OSWatcher (or ExaWatcher) is running"
else:
	print "[WARNING] No OSWatcher running"
print ""

### network - huge MTU
bMTU = False
st_mtu1 = commands.getoutput('cat ifconfig |grep MTU|awk \'{print $6}\'|grep MTU|sort|uniq|awk --field-separator ":" \'{print $2}\'')
if  st_mtu1.strip() != '':
	for i in range (0,len(st_mtu1.split('\n'))):
		st_mtu = st_mtu1.split('\n')[i]
		if int(st_mtu) != 16436 and int(st_mtu) > 1500:
			bMTU = True
			st_huge_mtu = st_mtu
			break
st_mtu2 = commands.getoutput('cat ifconfig |grep MTU|awk \'{print $4}\'|grep MTU|sort|uniq|awk --field-separator ":" \'{print $2}\'')
if  st_mtu2.strip() != '':
	for i in range (0,len(st_mtu2.split('\n'))):
		st_mtu = st_mtu2.split('\n')[i]
		if int(st_mtu) != 16436 and int(st_mtu) > 1500:
			bMTU = True
			st_huge_mtu = st_mtu
			break
if bMTU == True:
	print "[INFO] Some network interface using MTU larger than 1500 (MTU:" + st_huge_mtu + ")"
else:
	print "[INFO] All network interface using MTU 1500."
print ""

### network - static router
st_route = "0"
st_rule = "0"
if os.path.exists('etc/sysconfig/network-scripts/route-*'):
	st_route = commands.getoutput('ll etc/sysconfig/network-scripts/route-*|wc -l')
if os.path.exists('etc/sysconfig/network-scripts/rule-*'):
	st_rule = commands.getoutput('ll etc/sysconfig/network-scripts/rule-*|wc -l')
if int(st_route) != 0 or int(st_rule) != 0:
	print "[INFO] Static route exist"

### cpu pin

### /var/log/messages
st_ls_varlog = commands.getoutput('ls -1 var/log/messages*\.gz').split('\n')
for i in range (0,len(st_ls_varlog)):
	commands.getoutput('gunzip ' + st_ls_varlog[i])

st_ls_varlog = commands.getoutput('ls -1 var/log/messages*').split('\n')
st_first_log = commands.getoutput('head -1 ' + st_ls_varlog[len(st_ls_varlog)-1])
st_first_log_date = st_first_log[0:15]
st_last_log = commands.getoutput('tail -1 ' + st_ls_varlog[0])
st_last_log_date = st_last_log[0:15]
print "[INFO] Log since \"" + st_first_log_date + "\" to \"" + st_last_log_date + "\" available, timezone " + st_timezone

if OS_VER == "OL5":
	st_reboot_date = commands.getoutput('cat var/log/messages*|grep "restart"|grep "syslogd" |grep -v "04:02"|cut -c1-15')
if OS_VER == "OL6":
	st_reboot_date = commands.getoutput('cat var/log/messages*|grep "imklog"|grep -v "04:02"|cut -c1-15')
time_stamps = []
st_reboot_nr = str(len(st_reboot_date.strip().split('\n')))
if st_reboot_date.strip() == "" or len(st_reboot_date.split('\n')) == 0:
	print "[INFO] No reboot found in /var/log/messages*"
else:
	print "[INFO] " + st_reboot_nr + " reboots found in /var/log/messages*"
	for i in range (0, len(st_reboot_date.split('\n'))-1):
		time_stamps.append(time.strptime(st_year + " " + st_reboot_date.split('\n')[i], "%Y %b %d %H:%M:%S"))
	time_latest = max(time_stamps)	
	print "[INFO] Latest reboot happened on \"" + time.strftime("%b %d %H:%M:%S", time_latest) + " " + st_timezone + "\""

### typical error oom/panic/oops/hung_check_timer/softlockup/page alloc/nfs not responding
### kernel BUG/WARNING/Call Trace
def check_message(st_mesg):

	st_messages = commands.getoutput('cat var/log/messages*|grep "' + st_mesg + '"|cut -c1-15')
	time_stamps = []
	if st_messages.strip() != "":
		st_messages_nr = str(len(st_messages.strip().split('\n')))
		print "[WARNING] " + st_messages_nr + " \"" + st_mesg + "\" found in /var/log/messages*"
		for i in range (0, len(st_messages.strip().split('\n'))):
			time_stamps.append(time.strptime(st_year + " " + st_messages.split('\n')[i], "%Y %b %d %H:%M:%S"))
		time_first = min(time_stamps)	
		time_last = max(time_stamps)	
		print "[WARNING] First \"" + st_mesg + "\" happened on \"" + time.strftime("%b %d %H:%M:%S", time_first) + " " + st_timezone + "\""
		print "[WARNING] Last  \"" + st_mesg + "\" happened on \"" + time.strftime("%b %d %H:%M:%S", time_last) + " " + st_timezone + "\""

check_message("soft lockup")
check_message("blocked for more than 120 seconds")
check_message("not responding still trying")
check_message("kernel: WARNING:")
check_message("kernel: BUG:")
check_message("Call Trace")
check_message("Out of Memory")
check_message("page allocation failure")
check_message("ocfs2 is very sorry to be fencing this system by restarting")
print ""

