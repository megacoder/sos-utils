#!/usr/bin/env python

import os
import sys
import shutil
import commands

##########################################
# Author: jiaqing.lao@oracle.com
# Apply: OL5/OL6, OVS3.x
# Usage: change dir to unzipped sosreport folder, execute mysos.py
# Option: -p package
# Version: v1.1 (July 24th 2014)
##########################################

### name the output file with hostname and date
st_hostname = commands.getoutput('cat hostname')
st_date = commands.getoutput('cat date |awk \'{print $2$3}\'')
st_layout = "sos_layout_" + st_hostname.strip() + "_" + st_date.strip()
print "file " + st_layout + " will be created under " + os.getcwd() + "\n"

### if Linux or OVS
THE_RELEASE = 'Linux'
if os.path.exists('etc/enterprise-release'):
	the_release = commands.getoutput('cat etc/enterprise-release')
if os.path.exists('etc/redhat-release'):
	the_release = commands.getoutput('cat etc/redhat-release')
if os.path.exists('etc/ovs-release'):
	THE_RELEASE = 'OVS'
if the_release.find('Oracle VM server') >= 0:
	THE_RELEASE = 'OVS'

f_soslayout = open(st_layout,"w+r")

### general info
f_soslayout.write("--uname\n")
f_soslayout.write(commands.getoutput('cat uname')+'\n')
f_soslayout.write("\n")

f_soslayout.write("--date\n")
f_soslayout.write(commands.getoutput('cat date')+'\n')
f_soslayout.write("\n")

f_soslayout.write("--uptime\n")
f_soslayout.write(commands.getoutput('cat uptime')+'\n')
f_soslayout.write("\n")

f_soslayout.write("--sysinfo\n")
cpu_nr = commands.getoutput('cat proc/cpuinfo |grep processor|tail -1|awk \'{print $3}\'')
cpu_nr = int(cpu_nr) + 1
if os.path.isdir('./sos_commands/xen') and os.path.exists('sos_commands/xen/xm_info'):
	f_soslayout.write('total dom0 cores number: %i\n' %cpu_nr)
	cpus_all = commands.getoutput('cat sos_commands/xen/xm_info|grep nr_cpus|awk \'{print $3}\'')
	cpus_all_nr = int(cpus_all)
	f_soslayout.write('total phy cores number: %i\n' %cpus_all_nr)
else:
	f_soslayout.write('total phy cores number: %i\n' %cpu_nr)

ram_all = commands.getoutput('cat proc/meminfo|grep MemTotal|awk \'{print $2}\'')
ram_nr = float(ram_all)/1024/1024
if os.path.isdir('./sos_commands/xen') and os.path.exists('sos_commands/xen/xm_info'):
	f_soslayout.write('total dom0 memory: %.2f GB\n' %ram_nr)
	ram_phy_all = commands.getoutput('cat sos_commands/xen/xm_info |grep total_memory|awk \'{print $3}\'')
	ram_phy_nr = float(ram_phy_all)/1024
	f_soslayout.write('total phy memory: %.2f GB\n' %ram_phy_nr)
else:
	f_soslayout.write('total phy memory: %.2f GB\n' %ram_nr)
f_soslayout.write("\n")

### memory info
f_soslayout.write("--meminfo\n")
f_soslayout.write(commands.getoutput('cat proc/meminfo|egrep "MemTotal|SwapTotal|HugePages_Total|AnonPages|PageTables"')+'\n')

hugepage_nr = commands.getoutput('cat proc/meminfo|egrep HugePages_Total|awk \'{print $2}\'')
hugepage_sz = commands.getoutput('cat proc/meminfo|egrep Hugepagesize|awk \'{print $2}\'')
total_mem = commands.getoutput('cat proc/meminfo|egrep MemTotal|awk \'{print $2}\'')
if hugepage_nr.strip() != ""  and int(hugepage_nr) > 0:
	hugepage_total = int(hugepage_nr) * int(hugepage_sz)
	hugepage_ratio = float(hugepage_total) / float(total_mem) * 100
	f_soslayout.write('      >>> Hugepage %.2f%% of total memory\n' %hugepage_ratio)
f_soslayout.write("\n")

### hardware info
f_soslayout.write("--dmidecode\n")
f_soslayout.write(commands.getoutput('cat dmidecode |grep -A 2 "System Information"')+'\n')
f_soslayout.write(commands.getoutput('cat dmidecode |grep -A 3 "BIOS Information"')+'\n')
f_soslayout.write("\n")

f_soslayout.write("--lspci\n")
f_soslayout.write(commands.getoutput('cat lspci|egrep "^[0-9]|^[a-z]"|egrep "Ethernet|Fibre|InfiniBand"')+'\n')
f_soslayout.write("\n")

### sysctl settings
f_soslayout.write("--sysctl\n")
f_soslayout.write(commands.getoutput('cat sos_commands/kernel/sysctl_-a |egrep "panic|sysrq|lockup|min_free"')+'\n')
f_soslayout.write("\n")

### specific packages
if len(sys.argv) > 2: 
	if sys.argv[1] == '-p':
		f_soslayout.write("--packages\n")
		f_soslayout.write(commands.getoutput('cat installed-rpms |grep '+sys.argv[2]+'|sort|awk \'{print $1}\'')+'\n')
		f_soslayout.write("\n")

### storage layout
f_soslayout.write("--storage\n")
cnt_sdxx = commands.getoutput('cat proc/partitions |awk \'{print $4}\' |grep sd |grep -v [0-9]|wc -l')
if int(cnt_sdxx) > 0:
        f_soslayout.write('%i sdxx devices.\n' %int(cnt_sdxx))
else:
        f_soslayout.write('no sdxx devices.\n')

cnt_xvdxx = commands.getoutput('cat proc/partitions |awk \'{print $4}\' |grep xvd |grep -v [0-9]|wc -l')
if int(cnt_xvdxx) > 0:
        f_soslayout.write('%i xvdxx devices(virtual disk).\n' %int(cnt_xvdxx))

cnt_vxdmp = commands.getoutput('cat proc/partitions |awk \'{print $4}\' |grep VxDMP |grep -v p|wc -l')
if int(cnt_vxdmp) > 0:
        f_soslayout.write('%i  VxDMP devices(Symantec Veritas).\n' %int(cnt_vxdmp))

cnt_mdxx = '0'
if os.path.exists('sos_commands/devicemapper/mdadm_-D_.dev.md'):
	cnt_mdxx = commands.getoutput('cat sos_commands/devicemapper/mdadm_-D_.dev.md|grep "/dev/md"|grep ":$"|wc -l')
	lel_mdxx = commands.getoutput('cat sos_commands/devicemapper/mdadm_-D_.dev.md |grep "Raid Level"|sort|uniq|awk \'{print $4}\'')
if int(cnt_mdxx) > 0:
       	f_soslayout.write('%i mdxx devices(soft raid)' %int(cnt_mdxx))
       	f_soslayout.write(' in %s.\n' %lel_mdxx)

cnt_dmmp = '0'
if os.path.exists('sos_commands/devicemapper/multipath_-v4_-ll'):
	cnt_dmmp = commands.getoutput('cat sos_commands/devicemapper/multipath_-v4_-ll |egrep "dm-"|egrep -v "device|blacklisted"|wc -l')

if int(cnt_dmmp) <= 0:
        f_soslayout.write('no dm-mp devices.\n')
else:
	if THE_RELEASE == 'OVS':
		nPos = 3
	else:
		nPos = 4
        st_vendors = commands.getoutput('cat sos_commands/devicemapper/multipath_-v4_-ll |egrep "dm-"|egrep -v "blacklisted|device"|awk \'{print $'+str(nPos)+'}\'|sort|uniq')
	if len(st_vendors.split('\n')) > 1:
		print "Warning: More than 1 storage vendors, calculation of path numbers might not correct\n"
        nr_paths = float(cnt_sdxx) / float(cnt_dmmp)
        f_soslayout.write('%i dm-mp devices, ' %int(cnt_dmmp))
        f_soslayout.write('each has about %i paths, ' %round(nr_paths))
        f_soslayout.write('storage is %s\n'  %st_vendors.split('\n'))

if os.path.isdir('./sos_commands/emc') and os.path.exists('sos_commands/emc/powermt_display_dev_all'):
        cnt_emc = commands.getoutput('cat sos_commands/emc/powermt_display_dev_all | egrep "Pseudo" | wc -l')
        if int(cnt_emc) > 0: 
                f_soslayout.write('%d emc powerpath devices.\n' %int(cnt_emc))
        else:
                f_soslayout.write('no emc powerpath devices.\n')

cnt_lvm2 = commands.getoutput('cat vgdisplay|egrep "PV Name|LV Name"|wc -l')
if int(cnt_lvm2) > 0:
        f_soslayout.write('LVM2 devices:\n')
        f_soslayout.write(commands.getoutput('cat vgdisplay|egrep "PV Name|LV Name"')+'\n')
else:
        f_soslayout.write('no LVM2 device.\n')

f_soslayout.write("\n")

### mounted file systems
f_soslayout.write('--mount (ext, ocfs2, nfs, gfs, fuse, cifs, btrfs)\n')
f_soslayout.write(commands.getoutput('cat mount |egrep "ext|ocfs2|nfs|gfs|fuse|cifs|btrfs"|egrep -v "xenfs|tmpfs|debugfs|sunrpc|dlmfs|nfsd|config"')+'\n')
f_soslayout.write("\n")

### modprobe.conf
if os.path.exists('etc/modprobe.conf'):
	f_soslayout.write('--modprobe.conf\n')
	f_soslayout.write(commands.getoutput('cat etc/modprobe.conf')+'\n')
	f_soslayout.write("\n")

###  network layout - bonding
cn_bond = commands.getoutput('ls -1 ./etc/sysconfig/network-scripts/ifcfg-*|grep bond|wc -l')
if int(cn_bond.strip()) != 0:
	f_soslayout.write('--network - bonding\n')
	st_ifcfgbonds = commands.getoutput('ls -1 ./etc/sysconfig/network-scripts/ifcfg-bond*|egrep -v "bak|orig"|awk --field-separator "-" \'{print $(NF)}\'|egrep -v "\."')
	cnt_bonds = len(st_ifcfgbonds.split('\n'))

	for cnt in range (0, cnt_bonds):
		st_ifcfgbond = st_ifcfgbonds.split('\n')[cnt]
		slaves = commands.getoutput('grep -ir ' + st_ifcfgbond + ' ./etc/sysconfig/network-scripts/ifcfg-*|grep -v "^#"|grep MASTER|awk --field-separator ":" \'{print $1}\'|awk --field-separator "-" \'{print $NF}\'')
		st_ifcfgbond = st_ifcfgbond + ' = ' + slaves.replace('\n'," + ") + '\n'
		f_soslayout.write(st_ifcfgbond)

	f_soslayout.write("\n")

f_soslayout.write('--network - ifconfig\n')
f_soslayout.write(commands.getoutput('cat ifconfig |egrep -i "inet|hwaddr" | egrep -v "127\.0\.0\.1|inet6|vif|tap"')+'\n')
f_soslayout.write("\n")

### for ovm3
if os.path.isdir('sos_commands/ocfs2'):
        f_soslayout.write('--ocfs2 cluster\n')
        f_soslayout.write(commands.getoutput('cat sos_commands/ovm3/dump_db_serverpool |grep pool_alias')+'\n')
        f_soslayout.write(commands.getoutput('cat sos_commands/ocfs2/ocfs2.cluster.conf |egrep "ip_address|name"|sed "s/ip_address = //g"|sed "s/name = /, /g"')+'\n')
	f_soslayout.write("\n")

        f_soslayout.write('--o2cb\n')
        f_soslayout.write(commands.getoutput('cat sos_commands/ocfs2/o2cb.status'))

f_soslayout.close()

print "file " + st_layout + " created under " + os.getcwd() + "\n"

