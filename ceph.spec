# vim: set noexpandtab ts=8 sw=8 :
#
# spec file for package ceph
#
# Copyright (C) 2004-2016 The Ceph Project Developers. See COPYING file
# at the top-level directory of this distribution and at
# https://github.com/ceph/ceph/blob/master/COPYING
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon.
#
# This file is under the GNU Lesser General Public License, version 2.1
#
# Please submit bugfixes or comments via http://tracker.ceph.com/
# 
%bcond_with ocf
%bcond_without cephfs_java
%bcond_with tests
%bcond_without tcmalloc
%bcond_without libs_compat
%bcond_with lowmem_builder
%if 0%{?fedora} || 0%{?rhel}
%bcond_without selinux
%endif
%if 0%{?suse_version}
%bcond_with selinux
%endif


%if (0%{?el5} || (0%{?rhel_version} >= 500 && 0%{?rhel_version} <= 600))
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%if %{with selinux}
# get selinux policy version
%{!?_selinux_policy_version: %global _selinux_policy_version %(sed -e 's,.*selinux-policy-\\([^/]*\\)/.*,\\1,' /usr/share/selinux/devel/policyhelp 2>/dev/null || echo 0.0.0)}

%define relabel_files() \
restorecon -R /usr/bin/ceph-mon > /dev/null 2>&1; \
restorecon -R /usr/bin/ceph-osd > /dev/null 2>&1; \
restorecon -R /usr/bin/ceph-mds > /dev/null 2>&1; \
restorecon -R /usr/bin/radosgw > /dev/null 2>&1; \
restorecon -R /etc/rc\.d/init\.d/ceph > /dev/null 2>&1; \
restorecon -R /etc/rc\.d/init\.d/radosgw > /dev/null 2>&1; \
restorecon -R /var/run/ceph > /dev/null 2>&1; \
restorecon -R /var/lib/ceph > /dev/null 2>&1; \
restorecon -R /var/log/ceph > /dev/null 2>&1; \
restorecon -R /var/log/radosgw > /dev/null 2>&1;
%endif

%{!?_udevrulesdir: %global _udevrulesdir /lib/udev/rules.d}

# Use systemd files on RHEL 7 and above and in SUSE/openSUSE.
# Note: We don't install unit files for the services yet. For now,
# the _with_systemd variable only implies that we'll install
# /etc/tmpfiles.d/ceph.conf in order to set up the socket directory in
# /var/run/ceph.
%if 0%{?fedora} || 0%{?rhel} >= 7 || 0%{?suse_version}
%global _with_systemd 1
%{!?tmpfiles_create: %global tmpfiles_create systemd-tmpfiles --create}
%endif

# LTTng-UST enabled on Fedora, RHEL 6, and SLES 12
%if 0%{?fedora} || 0%{?rhel} == 6 || 0%{?suse_version} == 1315
%global _with_lttng 1
%endif

# unify libexec for all targets
%global _libexecdir %{_exec_prefix}/lib


#################################################################################
# common
#################################################################################
Name:		ceph
Version:	10.1.0
Release:	0%{?dist}
Epoch:		1
Summary:	User space components of the Ceph file system
License:	LGPL-2.1 and CC-BY-SA-1.0 and GPL-2.0 and BSL-1.0 and GPL-2.0-with-autoconf-exception and BSD-3-Clause and MIT
%if 0%{?suse_version}
Group:         System/Filesystems
%endif
URL:		http://ceph.com/
Source0:	http://ceph.com/download/%{name}-%{version}.tar.bz2
%if 0%{?fedora} || 0%{?rhel}
Patch0:		init-ceph.in-fedora.patch
%endif
#################################################################################
# dependencies that apply across all distro families
#################################################################################
Requires:       ceph-osd = %{epoch}:%{version}-%{release}
Requires:       ceph-mds = %{epoch}:%{version}-%{release}
Requires:       ceph-mon = %{epoch}:%{version}-%{release}
Requires(post):	binutils
%if 0%{with cephfs_java}
BuildRequires:	java-devel
BuildRequires:	sharutils
%endif
%if 0%{with selinux}
BuildRequires:	checkpolicy
BuildRequires:	selinux-policy-devel
BuildRequires:	/usr/share/selinux/devel/policyhelp
%endif
BuildRequires:	gcc-c++
BuildRequires:	boost-devel
BuildRequires:  cmake
BuildRequires:	cryptsetup
BuildRequires:	fuse-devel
BuildRequires:	gdbm
BuildRequires:	hdparm
BuildRequires:	leveldb-devel > 1.2
BuildRequires:	libaio-devel
BuildRequires:	libcurl-devel
BuildRequires:	libxml2-devel
BuildRequires:	libblkid-devel >= 2.17
BuildRequires:	libudev-devel
BuildRequires:	libtool
BuildRequires:	make
BuildRequires:	parted
BuildRequires:	perl
BuildRequires:	pkgconfig
BuildRequires:	python
BuildRequires:	python-devel
BuildRequires:	python-nose
BuildRequires:	python-requests
BuildRequires:	python-virtualenv
BuildRequires:	snappy-devel
BuildRequires:	util-linux
BuildRequires:	valgrind-devel
BuildRequires:	xfsprogs
BuildRequires:	xfsprogs-devel
BuildRequires:	xmlstarlet
BuildRequires:	yasm

#################################################################################
# distro-conditional dependencies
#################################################################################
%if 0%{?suse_version}
%if 0%{?_with_systemd}
BuildRequires:  pkgconfig(systemd)
BuildRequires:	systemd-rpm-macros
BuildRequires:	systemd
%{?systemd_requires}
%endif
PreReq:		%fillup_prereq
BuildRequires:	net-tools
BuildRequires:	libbz2-devel
%if 0%{with tcmalloc}
BuildRequires:	gperftools-devel
%endif
BuildRequires:  btrfsprogs
BuildRequires:	mozilla-nss-devel
BuildRequires:	keyutils-devel
BuildRequires:	libatomic-ops-devel
BuildRequires:  libopenssl-devel
BuildRequires:  lsb-release
BuildRequires:  openldap2-devel
BuildRequires:	python-Cython
%endif
%if 0%{?fedora} || 0%{?rhel} 
%if 0%{?_with_systemd}
Requires:	systemd
%endif
BuildRequires:	btrfs-progs
BuildRequires:	nss-devel
BuildRequires:	keyutils-libs-devel
BuildRequires:	libatomic_ops-devel
Requires(post):	chkconfig
Requires(preun):	chkconfig
Requires(preun):	initscripts
BuildRequires:	gperftools-devel
BuildRequires:  openldap-devel
BuildRequires:  openssl-devel
BuildRequires:  redhat-lsb-core
BuildRequires:	Cython
%endif
# boost
%if 0%{?fedora} || 0%{?rhel} 
BuildRequires:  boost-random
%endif
# python-argparse for distros with Python 2.6 or lower
%if (0%{?rhel} && 0%{?rhel} <= 6)
BuildRequires:	python-argparse
%endif
# lttng and babeltrace for rbd-replay-prep
%if 0%{?_with_lttng}
%if 0%{?fedora} || 0%{?rhel}
BuildRequires:	lttng-ust-devel
BuildRequires:	libbabeltrace-devel
%endif
%if 0%{?suse_version}
BuildRequires:	lttng-ust-devel
BuildRequires:  babeltrace-devel
%endif
%endif
# expat and fastcgi for RGW
%if 0%{?suse_version}
BuildRequires:	libexpat-devel
BuildRequires:	FastCGI-devel
%endif
%if 0%{?rhel} || 0%{?fedora}
BuildRequires:	expat-devel
BuildRequires:	fcgi-devel
%endif
# python-sphinx
%if 0%{?rhel} > 0 && 0%{?rhel} < 7
BuildRequires:	python-sphinx10
%endif
%if 0%{?fedora} || 0%{?suse_version} || 0%{?rhel} >= 7
BuildRequires:	python-sphinx
%endif
#hardened-cc1
%if 0%{?fedora} || 0%{?rhel}
BuildRequires:  redhat-rpm-config
%endif

%description
Ceph is a massively scalable, open-source, distributed storage system that runs
on commodity hardware and delivers object, block and file system storage.


#################################################################################
# packages
#################################################################################
%package base
Summary:       Ceph Base Package
Group:         System Environment/Base
Requires:      ceph-common = %{epoch}:%{version}-%{release}
Requires:      librbd1 = %{epoch}:%{version}-%{release}
Requires:      librados2 = %{epoch}:%{version}-%{release}
Requires:      libcephfs1 = %{epoch}:%{version}-%{release}
Requires:      librgw2 = %{epoch}:%{version}-%{release}
%if 0%{with selinux}
Requires:      ceph-selinux = %{epoch}:%{version}-%{release}
%endif
Requires:      python
Requires:      python-requests
Requires:      python-setuptools
Requires:      grep
Requires:      xfsprogs
Requires:      logrotate
Requires:      parted
Requires:      util-linux
Requires:      hdparm
Requires:      cryptsetup
Requires:      findutils
Requires:      which
%if 0%{?suse_version}
Requires:      lsb-release
%endif
%if 0%{?fedora} || 0%{?rhel}
Requires:      redhat-lsb-core
%endif
%description base
Base is the package that includes all the files shared amongst ceph servers

%package -n ceph-common
Summary:	Ceph Common
Group:		System Environment/Base
Requires:	librbd1 = %{epoch}:%{version}-%{release}
Requires:	librados2 = %{epoch}:%{version}-%{release}
Requires:	libcephfs1 = %{epoch}:%{version}-%{release}
Requires:	python-rados = %{epoch}:%{version}-%{release}
Requires:	python-rbd = %{epoch}:%{version}-%{release}
Requires:	python-cephfs = %{epoch}:%{version}-%{release}
Requires:	python-requests
%if 0%{?_with_systemd}
%{?systemd_requires}
%endif
%if 0%{?suse_version}
Requires(pre):	pwdutils
%endif
# python-argparse is only needed in distros with Python 2.6 or lower
%if (0%{?rhel} && 0%{?rhel} <= 6)
Requires:	python-argparse
%endif
%description -n ceph-common
Common utilities to mount and interact with a ceph storage cluster.
Comprised of files that are common to Ceph clients and servers.

%package mds
Summary:	Ceph Metadata Server Daemon
Group:		System Environment/Base
Requires:	ceph-base = %{epoch}:%{version}-%{release}
%description mds
ceph-mds is the metadata server daemon for the Ceph distributed file system.
One or more instances of ceph-mds collectively manage the file system
namespace, coordinating access to the shared OSD cluster.

%package mon
Summary:	Ceph Monitor Daemon
Group:		System Environment/Base
Requires:	ceph-base = %{epoch}:%{version}-%{release}
# For ceph-rest-api
%if 0%{?fedora} || 0%{?rhel}
Requires:      python-flask
%endif
%if 0%{?suse_version}
Requires:      python-Flask
%endif
%description mon
ceph-mon is the cluster monitor daemon for the Ceph distributed file
system. One or more instances of ceph-mon form a Paxos part-time
parliament cluster that provides extremely reliable and durable storage
of cluster membership, configuration, and state.

%package fuse
Summary:	Ceph fuse-based client
Group:		System Environment/Base
%description fuse
FUSE based client for Ceph distributed network file system

%package -n rbd-fuse
Summary:	Ceph fuse-based client
Group:		System Environment/Base
Requires:	librados2 = %{epoch}:%{version}-%{release}
Requires:	librbd1 = %{epoch}:%{version}-%{release}
%description -n rbd-fuse
FUSE based client to map Ceph rbd images to files

%package -n rbd-mirror
Summary:	Ceph daemon for mirroring RBD images
Group:		System Environment/Base
Requires:	ceph-common = %{epoch}:%{version}-%{release}
Requires:	librados2 = %{epoch}:%{version}-%{release}
%description -n rbd-mirror
Daemon for mirroring RBD images between Ceph clusters, streaming
changes asynchronously.

%package -n rbd-nbd
Summary:	Ceph RBD client base on NBD
Group:		System Environment/Base
Requires:	librados2 = %{epoch}:%{version}-%{release}
Requires:	librbd1 = %{epoch}:%{version}-%{release}
%description -n rbd-nbd
NBD based client to map Ceph rbd images to local device

%package radosgw
Summary:	Rados REST gateway
Group:		Development/Libraries
Requires:	ceph-common = %{epoch}:%{version}-%{release}
%if 0%{with selinux}
Requires:	ceph-selinux = %{epoch}:%{version}-%{release}
%endif
Requires:	librados2 = %{epoch}:%{version}-%{release}
Requires:	librgw2 = %{epoch}:%{version}-%{release}
%if 0%{?rhel} || 0%{?fedora}
Requires:	mailcap
# python-flask for powerdns
Requires:	python-flask
%endif
%if 0%{?suse_version}
# python-Flask for powerdns
Requires:      python-Flask
%endif
%description radosgw
RADOS is a distributed object store used by the Ceph distributed
storage system.  This package provides a REST gateway to the
object store that aims to implement a superset of Amazon's S3
service as well as the OpenStack Object Storage ("Swift") API.

%if %{with ocf}
%package resource-agents
Summary:	OCF-compliant resource agents for Ceph daemons
Group:		System Environment/Base
License:	LGPL-2.0
Requires:	ceph-base = %{epoch}:%{version}
Requires:	resource-agents
%description resource-agents
Resource agents for monitoring and managing Ceph daemons
under Open Cluster Framework (OCF) compliant resource
managers such as Pacemaker.
%endif

%package osd
Summary:	Ceph Object Storage Daemon
Group:		System Environment/Base
Requires:	ceph-base = %{epoch}:%{version}-%{release}
# for sgdisk, used by ceph-disk
%if 0%{?fedora} || 0%{?rhel}
Requires:	gdisk
%endif
%if 0%{?suse_version}
Requires:	gptfdisk
%endif
%description osd
ceph-osd is the object storage daemon for the Ceph distributed file
system.  It is responsible for storing objects on a local file system
and providing access to them over the network.

%package -n librados2
Summary:	RADOS distributed object store client library
Group:		System Environment/Libraries
License:	LGPL-2.0
%if 0%{?rhel} || 0%{?fedora}
Obsoletes:	ceph-libs < %{epoch}:%{version}-%{release}
%endif
%description -n librados2
RADOS is a reliable, autonomic distributed object storage cluster
developed as part of the Ceph distributed storage system. This is a
shared library allowing applications to access the distributed object
store using a simple file-like interface.

%package -n librados2-devel
Summary:	RADOS headers
Group:		Development/Libraries
License:	LGPL-2.0
Requires:	librados2 = %{epoch}:%{version}-%{release}
Obsoletes:	ceph-devel < %{epoch}:%{version}-%{release}
%description -n librados2-devel
This package contains libraries and headers needed to develop programs
that use RADOS object store.

%package -n librgw2
Summary:	RADOS gateway client library
Group:		System Environment/Libraries
License:	LGPL-2.0
Requires:	librados2 = %{epoch}:%{version}-%{release}
%description -n librgw2
This package provides a library implementation of the RADOS gateway
(distributed object store with S3 and Swift personalities).

%package -n librgw2-devel
Summary:	RADOS gateway client library
Group:		Development/Libraries
License:	LGPL-2.0
Requires:	librados2 = %{epoch}:%{version}-%{release}
%description -n librgw2-devel
This package contains libraries and headers needed to develop programs
that use RADOS gateway client library.

%package -n python-rados
Summary:	Python libraries for the RADOS object store
Group:		System Environment/Libraries
License:	LGPL-2.0
Requires:	librados2 = %{epoch}:%{version}-%{release}
Obsoletes:	python-ceph < %{epoch}:%{version}-%{release}
%description -n python-rados
This package contains Python libraries for interacting with Cephs RADOS
object store.

%package -n libradosstriper1
Summary:	RADOS striping interface
Group:		System Environment/Libraries
License:	LGPL-2.0
Requires:	librados2 = %{epoch}:%{version}-%{release}
%description -n libradosstriper1
Striping interface built on top of the rados library, allowing
to stripe bigger objects onto several standard rados objects using
an interface very similar to the rados one.

%package -n libradosstriper1-devel
Summary:	RADOS striping interface headers
Group:		Development/Libraries
License:	LGPL-2.0
Requires:	libradosstriper1 = %{epoch}:%{version}-%{release}
Requires:	librados2-devel = %{epoch}:%{version}-%{release}
Obsoletes:	ceph-devel < %{epoch}:%{version}-%{release}
%description -n libradosstriper1-devel
This package contains libraries and headers needed to develop programs
that use RADOS striping interface.

%package -n librbd1
Summary:	RADOS block device client library
Group:		System Environment/Libraries
License:	LGPL-2.0
Requires:	librados2 = %{epoch}:%{version}-%{release}
%if 0%{?rhel} || 0%{?fedora}
Obsoletes:	ceph-libs < %{epoch}:%{version}-%{release}
%endif
%description -n librbd1
RBD is a block device striped across multiple distributed objects in
RADOS, a reliable, autonomic distributed object storage cluster
developed as part of the Ceph distributed storage system. This is a
shared library allowing applications to manage these block devices.

%package -n librbd1-devel
Summary:	RADOS block device headers
Group:		Development/Libraries
License:	LGPL-2.0
Requires:	librbd1 = %{epoch}:%{version}-%{release}
Requires:	librados2-devel = %{epoch}:%{version}-%{release}
Obsoletes:	ceph-devel < %{epoch}:%{version}-%{release}
%description -n librbd1-devel
This package contains libraries and headers needed to develop programs
that use RADOS block device.

%package -n python-rbd
Summary:	Python libraries for the RADOS block device
Group:		System Environment/Libraries
License:	LGPL-2.0
Requires:	librbd1 = %{epoch}:%{version}-%{release}
Requires:	python-rados = %{epoch}:%{version}-%{release}
Obsoletes:	python-ceph < %{epoch}:%{version}-%{release}
%description -n python-rbd
This package contains Python libraries for interacting with Cephs RADOS
block device.

%package -n libcephfs1
Summary:	Ceph distributed file system client library
Group:		System Environment/Libraries
License:	LGPL-2.0
%if 0%{?rhel} || 0%{?fedora}
Obsoletes:	ceph-libs < %{epoch}:%{version}-%{release}
Obsoletes:	ceph-libcephfs
%endif
%description -n libcephfs1
Ceph is a distributed network file system designed to provide excellent
performance, reliability, and scalability. This is a shared library
allowing applications to access a Ceph distributed file system via a
POSIX-like interface.

%package -n libcephfs1-devel
Summary:	Ceph distributed file system headers
Group:		Development/Libraries
License:	LGPL-2.0
Requires:	libcephfs1 = %{epoch}:%{version}-%{release}
Requires:	librados2-devel = %{epoch}:%{version}-%{release}
Obsoletes:	ceph-devel < %{epoch}:%{version}-%{release}
%description -n libcephfs1-devel
This package contains libraries and headers needed to develop programs
that use Cephs distributed file system.

%package -n python-cephfs
Summary:	Python libraries for Ceph distributed file system
Group:		System Environment/Libraries
License:	LGPL-2.0
Requires:	libcephfs1 = %{epoch}:%{version}-%{release}
Requires:	python-rados = %{epoch}:%{version}-%{release}
Obsoletes:	python-ceph < %{epoch}:%{version}-%{release}
%description -n python-cephfs
This package contains Python libraries for interacting with Cephs distributed
file system.

%package -n ceph-test
Summary:	Ceph benchmarks and test tools
Group:		System Environment/Libraries
License:	LGPL-2.0
Requires:	ceph-common
Requires:	xmlstarlet
%description -n ceph-test
This package contains Ceph benchmarks and test tools.

%if 0%{with cephfs_java}

%package -n libcephfs_jni1
Summary:	Java Native Interface library for CephFS Java bindings
Group:		System Environment/Libraries
License:	LGPL-2.0
Requires:	java
Requires:	libcephfs1 = %{epoch}:%{version}-%{release}
%description -n libcephfs_jni1
This package contains the Java Native Interface library for CephFS Java
bindings.

%package -n libcephfs_jni1-devel
Summary:	Development files for CephFS Java Native Interface library
Group:		System Environment/Libraries
License:	LGPL-2.0
Requires:	java
Requires:	libcephfs_jni1 = %{epoch}:%{version}-%{release}
Obsoletes:	ceph-devel < %{epoch}:%{version}-%{release}
%description -n libcephfs_jni1-devel
This package contains the development files for CephFS Java Native Interface
library.

%package -n cephfs-java
Summary:	Java libraries for the Ceph File System
Group:		System Environment/Libraries
License:	LGPL-2.0
Requires:	java
Requires:	libcephfs_jni1 = %{epoch}:%{version}-%{release}
%if 0%{?el6}
Requires:	junit4
BuildRequires:	junit4
%else
Requires:       junit
BuildRequires:  junit
%endif
%description -n cephfs-java
This package contains the Java libraries for the Ceph File System.

%endif

%if 0%{with selinux}

%package selinux
Summary:	SELinux support for Ceph MON, OSD and MDS
Group:		System Environment/Base
Requires:	ceph-base = %{epoch}:%{version}-%{release}
Requires:	policycoreutils, libselinux-utils
Requires(post): selinux-policy-base >= %{_selinux_policy_version}, policycoreutils, gawk
Requires(postun): policycoreutils
%description selinux
This package contains SELinux support for Ceph MON, OSD and MDS. The package
also performs file-system relabelling which can take a long time on heavily
populated file-systems.

%endif

%if 0%{with libs_compat}

%package libs-compat
Summary:	Meta package to include ceph libraries
Group:		System Environment/Libraries
License:	LGPL-2.0
Obsoletes:	ceph-libs
Requires:	librados2 = %{epoch}:%{version}-%{release}
Requires:	librbd1 = %{epoch}:%{version}-%{release}
Requires:	libcephfs1 = %{epoch}:%{version}-%{release}
Provides:	ceph-libs

%description libs-compat
This is a meta package, that pulls in librados2, librbd1 and libcephfs1. It
is included for backwards compatibility with distributions that depend on the
former ceph-libs package, which is now split up into these three subpackages.
Packages still depending on ceph-libs should be fixed to depend on librados2,
librbd1 or libcephfs1 instead.

%endif

%package devel-compat
Summary:	Compatibility package for Ceph headers
Group:		Development/Libraries
License:	LGPL-2.0
Obsoletes:	ceph-devel
Requires:	librados2-devel = %{epoch}:%{version}-%{release}
Requires:	libradosstriper1-devel = %{epoch}:%{version}-%{release}
Requires:	librbd1-devel = %{epoch}:%{version}-%{release}
Requires:	libcephfs1-devel = %{epoch}:%{version}-%{release}
%if 0%{with cephfs_java}
Requires:	libcephfs_jni1-devel = %{epoch}:%{version}-%{release}
%endif
Provides:	ceph-devel
%description devel-compat
This is a compatibility package to accommodate ceph-devel split into
librados2-devel, librbd1-devel and libcephfs1-devel. Packages still depending
on ceph-devel should be fixed to depend on librados2-devel, librbd1-devel,
libcephfs1-devel or libradosstriper1-devel instead.

%package -n python-ceph-compat
Summary:	Compatibility package for Cephs python libraries
Group:		System Environment/Libraries
License:	LGPL-2.0
Obsoletes:	python-ceph
Requires:	python-rados = %{epoch}:%{version}-%{release}
Requires:	python-rbd = %{epoch}:%{version}-%{release}
Requires:	python-cephfs = %{epoch}:%{version}-%{release}
Provides:	python-ceph
%description -n python-ceph-compat
This is a compatibility package to accommodate python-ceph split into
python-rados, python-rbd and python-cephfs. Packages still depending on
python-ceph should be fixed to depend on python-rados, python-rbd or
python-cephfs instead.

#################################################################################
# common
#################################################################################
%prep
%setup -q
%if 0%{?fedora} || 0%{?rhel}
%patch0 -p1 -b .init
%endif

%build
%if 0%{with cephfs_java}
# Find jni.h
for i in /usr/{lib64,lib}/jvm/java/include{,/linux}; do
    [ -d $i ] && java_inc="$java_inc -I$i"
done
%endif

./autogen.sh

%if %{with lowmem_builder}
RPM_OPT_FLAGS="$RPM_OPT_FLAGS --param ggc-min-expand=20 --param ggc-min-heapsize=32768"
%endif
export RPM_OPT_FLAGS=`echo $RPM_OPT_FLAGS | sed -e 's/i386/i486/'`

%{configure}	CPPFLAGS="$java_inc" \
		--prefix=/usr \
                --libexecdir=%{_libexecdir} \
		--localstatedir=/var \
		--sysconfdir=/etc \
%if 0%{?_with_systemd}
		--with-systemdsystemunitdir=%_unitdir \
%endif
		--docdir=%{_docdir}/ceph \
		--with-man-pages \
		--mandir="%_mandir" \
		--with-nss \
		--without-cryptopp \
		--with-debug \
%if 0%{with cephfs_java}
		--enable-cephfs-java \
%endif
%if 0%{with selinux}
		--with-selinux \
%endif
		--with-librocksdb-static=check \
		--with-radosgw \
		$CEPH_EXTRA_CONFIGURE_ARGS \
		%{?_with_ocf} \
		%{?_with_tcmalloc} \
		CFLAGS="$RPM_OPT_FLAGS" CXXFLAGS="$RPM_OPT_FLAGS"

%if %{with lowmem_builder}
%if 0%{?jobs} > 8
%define _smp_mflags -j8
%endif
%endif

make %{?_smp_mflags}


%if 0%{with tests}
%check
# run in-tree unittests
make %{?_smp_mflags} check-local

%endif



%install
make DESTDIR=$RPM_BUILD_ROOT install
rm -f $RPM_BUILD_ROOT%{_libdir}/ceph/erasure-code/libec_example.so
rm -f $RPM_BUILD_ROOT%{_libdir}/ceph/erasure-code/libec_fail_to_initialize.so
rm -f $RPM_BUILD_ROOT%{_libdir}/ceph/erasure-code/libec_fail_to_register.so
rm -f $RPM_BUILD_ROOT%{_libdir}/ceph/erasure-code/libec_hangs.so
rm -f $RPM_BUILD_ROOT%{_libdir}/ceph/erasure-code/libec_missing_entry_point.so
rm -f $RPM_BUILD_ROOT%{_libdir}/ceph/erasure-code/libec_missing_version.so
rm -f $RPM_BUILD_ROOT%{_libdir}/ceph/erasure-code/libec_test_jerasure_generic.so
rm -f $RPM_BUILD_ROOT%{_libdir}/ceph/erasure-code/libec_test_jerasure_neon.so
rm -f $RPM_BUILD_ROOT%{_libdir}/ceph/erasure-code/libec_test_jerasure_sse3.so
rm -f $RPM_BUILD_ROOT%{_libdir}/ceph/erasure-code/libec_test_jerasure_sse4.so
rm -f $RPM_BUILD_ROOT%{_libdir}/ceph/erasure-code/libec_test_shec_generic.so
rm -f $RPM_BUILD_ROOT%{_libdir}/ceph/erasure-code/libec_test_shec_neon.so
rm -f $RPM_BUILD_ROOT%{_libdir}/ceph/erasure-code/libec_test_shec_sse3.so
rm -f $RPM_BUILD_ROOT%{_libdir}/ceph/erasure-code/libec_test_shec_sse4.so
find $RPM_BUILD_ROOT -type f -name "*.la" -exec rm -f {} ';'
find $RPM_BUILD_ROOT -type f -name "*.a" -exec rm -f {} ';'
install -D src/etc-rbdmap $RPM_BUILD_ROOT%{_sysconfdir}/ceph/rbdmap
%if 0%{?fedora} || 0%{?rhel}
install -m 0644 -D etc/sysconfig/ceph $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/ceph
%endif
%if 0%{?suse_version}
install -m 0644 -D etc/sysconfig/ceph $RPM_BUILD_ROOT%{_localstatedir}/adm/fillup-templates/sysconfig.%{name}
%endif
%if 0%{?_with_systemd}
  install -m 0644 -D systemd/ceph.tmpfiles.d $RPM_BUILD_ROOT%{_tmpfilesdir}/ceph-common.conf
  install -m 0644 -D systemd/rbdmap.service $RPM_BUILD_ROOT%{_unitdir}/rbdmap.service
  install -m 0644 -D systemd/ceph-osd@.service $RPM_BUILD_ROOT%{_unitdir}/ceph-osd@.service
  install -m 0644 -D systemd/ceph-mon@.service $RPM_BUILD_ROOT%{_unitdir}/ceph-mon@.service
  install -m 0644 -D systemd/ceph-create-keys@.service $RPM_BUILD_ROOT%{_unitdir}/ceph-create-keys@.service
  install -m 0644 -D systemd/ceph-mds@.service $RPM_BUILD_ROOT%{_unitdir}/ceph-mds@.service
  install -m 0644 -D systemd/ceph-radosgw@.service $RPM_BUILD_ROOT%{_unitdir}/ceph-radosgw@.service
  install -m 0644 -D systemd/ceph-rbd-mirror@.service $RPM_BUILD_ROOT%{_unitdir}/ceph-rbd-mirror@.service
  install -m 0644 -D systemd/ceph.target $RPM_BUILD_ROOT%{_unitdir}/ceph.target
  install -m 0644 -D systemd/ceph-osd.target $RPM_BUILD_ROOT%{_unitdir}/ceph-osd.target
  install -m 0644 -D systemd/ceph-mon.target $RPM_BUILD_ROOT%{_unitdir}/ceph-mon.target
  install -m 0644 -D systemd/ceph-mds.target $RPM_BUILD_ROOT%{_unitdir}/ceph-mds.target
  install -m 0644 -D systemd/ceph-radosgw.target $RPM_BUILD_ROOT%{_unitdir}/ceph-radosgw.target
  install -m 0644 -D systemd/ceph-rbd-mirror.target $RPM_BUILD_ROOT%{_unitdir}/ceph-rbd-mirror.target
  install -m 0644 -D systemd/ceph-disk@.service $RPM_BUILD_ROOT%{_unitdir}/ceph-disk@.service
  install -m 0755 -D systemd/ceph $RPM_BUILD_ROOT%{_sbindir}/rcceph
%else
  install -D src/init-rbdmap $RPM_BUILD_ROOT%{_initrddir}/rbdmap
  install -D src/init-ceph $RPM_BUILD_ROOT%{_initrddir}/ceph
  install -D src/init-radosgw $RPM_BUILD_ROOT%{_initrddir}/ceph-radosgw
  ln -sf ../../etc/init.d/ceph %{buildroot}/%{_sbindir}/rcceph
  ln -sf ../../etc/init.d/ceph-radosgw %{buildroot}/%{_sbindir}/rcceph-radosgw
%endif
mkdir -p $RPM_BUILD_ROOT%{_sbindir}
install -m 0644 -D src/logrotate.conf $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d/ceph
chmod 0644 $RPM_BUILD_ROOT%{_docdir}/ceph/sample.ceph.conf
chmod 0644 $RPM_BUILD_ROOT%{_docdir}/ceph/sample.fetch_config

# firewall templates
%if 0%{?suse_version}
install -m 0644 -D etc/sysconfig/SuSEfirewall2.d/services/ceph-mon %{buildroot}%{_sysconfdir}/sysconfig/SuSEfirewall2.d/services/ceph-mon
install -m 0644 -D etc/sysconfig/SuSEfirewall2.d/services/ceph-osd-mds %{buildroot}%{_sysconfdir}/sysconfig/SuSEfirewall2.d/services/ceph-osd-mds
%endif

# udev rules
install -m 0644 -D udev/50-rbd.rules $RPM_BUILD_ROOT%{_udevrulesdir}/50-rbd.rules
install -m 0644 -D udev/60-ceph-partuuid-workaround.rules $RPM_BUILD_ROOT%{_udevrulesdir}/60-ceph-partuuid-workaround.rules

%if (0%{?rhel} && 0%{?rhel} < 7)
install -m 0644 -D udev/95-ceph-osd-alt.rules $RPM_BUILD_ROOT/lib/udev/rules.d/95-ceph-osd.rules
%else
install -m 0644 -D udev/95-ceph-osd.rules $RPM_BUILD_ROOT/lib/udev/rules.d/95-ceph-osd.rules
%endif

%if 0%{?rhel} >= 7 || 0%{?fedora} || 0%{?suse_version}
mv $RPM_BUILD_ROOT/lib/udev/rules.d/95-ceph-osd.rules $RPM_BUILD_ROOT/usr/lib/udev/rules.d/95-ceph-osd.rules
mv $RPM_BUILD_ROOT/sbin/mount.ceph $RPM_BUILD_ROOT/usr/sbin/mount.ceph
mv $RPM_BUILD_ROOT/sbin/mount.fuse.ceph $RPM_BUILD_ROOT/usr/sbin/mount.fuse.ceph
%endif

#set up placeholder directories
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/ceph
%if ! 0%{?_with_systemd}
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/run/ceph
%endif
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/log/ceph
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/ceph/tmp
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/ceph/mon
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/ceph/osd
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/ceph/mds
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/ceph/radosgw
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/ceph/bootstrap-osd
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/ceph/bootstrap-mds
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/ceph/bootstrap-rgw

%clean
rm -rf $RPM_BUILD_ROOT

#################################################################################
# files and systemd scriptlets
#################################################################################
%files

%files base
%defattr(-,root,root,-)
%docdir %{_docdir}
%dir %{_docdir}/ceph
%{_docdir}/ceph/sample.ceph.conf
%{_docdir}/ceph/sample.fetch_config
%{_bindir}/crushtool
%{_bindir}/monmaptool
%{_bindir}/osdmaptool
%{_bindir}/ceph-run
%{_bindir}/ceph-detect-init
%{_bindir}/ceph-client-debug
%{_bindir}/cephfs
%if 0%{?_with_systemd}
%{_unitdir}/ceph-create-keys@.service
%else
%{_initrddir}/ceph
%endif
%{_sbindir}/ceph-create-keys
%{_sbindir}/rcceph
%if 0%{?rhel} >= 7 || 0%{?fedora} || 0%{?suse_version}
%{_sbindir}/mount.ceph
%else
/sbin/mount.ceph
%endif
%dir %{_libexecdir}/ceph
%{_libexecdir}/ceph/ceph_common.sh
%dir %{_libdir}/rados-classes
%{_libdir}/rados-classes/*
%dir %{_libdir}/ceph
%dir %{_libdir}/ceph/erasure-code
%{_libdir}/ceph/erasure-code/libec_*.so*
%dir %{_libdir}/ceph/compressor
%{_libdir}/ceph/compressor/libceph_*.so*
%if 0%{?_with_lttng}
%{_libdir}/libos_tp.so*
%{_libdir}/libosd_tp.so*
%endif
%config %{_sysconfdir}/bash_completion.d/ceph
%config(noreplace) %{_sysconfdir}/logrotate.d/ceph
%if 0%{?fedora} || 0%{?rhel}
%config(noreplace) %{_sysconfdir}/sysconfig/ceph
%endif
%if 0%{?suse_version}
%{_localstatedir}/adm/fillup-templates/sysconfig.*
%config %{_sysconfdir}/sysconfig/SuSEfirewall2.d/services/ceph-mon
%config %{_sysconfdir}/sysconfig/SuSEfirewall2.d/services/ceph-osd-mds
%endif
%{_unitdir}/ceph.target
%{python_sitelib}/ceph_detect_init*
%{python_sitelib}/ceph_disk*
%{_mandir}/man8/ceph-deploy.8*
%{_mandir}/man8/ceph-detect-init.8*
%{_mandir}/man8/ceph-create-keys.8*
%{_mandir}/man8/ceph-run.8*
%{_mandir}/man8/crushtool.8*
%{_mandir}/man8/osdmaptool.8*
%{_mandir}/man8/monmaptool.8*
%{_mandir}/man8/cephfs.8*
%{_mandir}/man8/mount.ceph.8*
#set up placeholder directories
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/tmp
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/bootstrap-osd
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/bootstrap-mds
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/bootstrap-rgw
%if ! 0%{?_with_systemd}
%attr(770,ceph,ceph) %dir %{_localstatedir}/run/ceph
%endif

%pre base
%if 0%{?_with_systemd}
  %if 0%{?suse_version}
    # service_add_pre and friends don't work with parameterized systemd service
    # instances, only with single services or targets, so we always pass
    # ceph.target to these macros
    %service_add_pre ceph.target
  %endif
%endif

%post base
/sbin/ldconfig
%if 0%{?_with_systemd}
  %if 0%{?suse_version}
    %fillup_only
    %service_add_post ceph.target
  %endif
%else
  /sbin/chkconfig --add ceph
%endif

%preun base
%if 0%{?_with_systemd}
  %if 0%{?suse_version}
    %service_del_preun ceph.target
  %endif
  # Disable and stop on removal.
  if [ $1 = 0 ] ; then
    SERVICE_LIST=$(systemctl | grep -E '^ceph-mon@|^ceph-create-keys@|^ceph-osd@|^ceph-mds@|^ceph-disk-'  | cut -d' ' -f1)
    if [ -n "$SERVICE_LIST" ]; then
      for SERVICE in $SERVICE_LIST; do
        /usr/bin/systemctl --no-reload disable $SERVICE > /dev/null 2>&1 || :
        /usr/bin/systemctl stop $SERVICE > /dev/null 2>&1 || :
      done
    fi
  fi
%else
  %if 0%{?rhel} || 0%{?fedora}
    if [ $1 = 0 ] ; then
      /sbin/service ceph stop >/dev/null 2>&1
      /sbin/chkconfig --del ceph
    fi
  %endif
%endif

%postun base
/sbin/ldconfig
%if 0%{?_with_systemd}
  if [ $1 = 1 ] ; then
    # Restart on upgrade, but only if "CEPH_AUTO_RESTART_ON_UPGRADE" is set to
    # "yes". In any case: if units are not running, do not touch them.
    SYSCONF_CEPH=/etc/sysconfig/ceph
    if [ -f $SYSCONF_CEPH -a -r $SYSCONF_CEPH ] ; then
      source $SYSCONF_CEPH
    fi
    if [ "X$CEPH_AUTO_RESTART_ON_UPGRADE" = "Xyes" ] ; then
      SERVICE_LIST=$(systemctl | grep -E '^ceph-mon@|^ceph-create-keys@|^ceph-osd@|^ceph-mds@|^ceph-disk-'  | cut -d' ' -f1)
      if [ -n "$SERVICE_LIST" ]; then
        for SERVICE in $SERVICE_LIST; do
          /usr/bin/systemctl try-restart $SERVICE > /dev/null 2>&1 || :
        done
      fi
    fi
  fi
%endif

#################################################################################
%files common
%defattr(-,root,root,-)
%{_bindir}/ceph
%{_bindir}/ceph-authtool
%{_bindir}/ceph-conf
%{_bindir}/ceph-dencoder
%{_bindir}/ceph-rbdnamer
%{_bindir}/ceph-syn
%{_bindir}/ceph-crush-location
%{_bindir}/cephfs-data-scan
%{_bindir}/cephfs-journal-tool
%{_bindir}/cephfs-table-tool
%{_bindir}/rados
%{_bindir}/rbd
%{_bindir}/rbd-replay
%{_bindir}/rbd-replay-many
%{_bindir}/rbdmap
%if 0%{?_with_lttng}
%{_bindir}/rbd-replay-prep
%endif
%{_bindir}/ceph-post-file
%{_bindir}/ceph-brag
%if 0%{?_with_systemd}
%{_tmpfilesdir}/ceph-common.conf
%endif
%{_mandir}/man8/ceph-authtool.8*
%{_mandir}/man8/ceph-conf.8*
%{_mandir}/man8/ceph-dencoder.8*
%{_mandir}/man8/ceph-rbdnamer.8*
%{_mandir}/man8/ceph-syn.8*
%{_mandir}/man8/ceph-post-file.8*
%{_mandir}/man8/ceph.8*
%{_mandir}/man8/rados.8*
%{_mandir}/man8/rbd.8*
%{_mandir}/man8/rbd-replay.8*
%{_mandir}/man8/rbd-replay-many.8*
%{_mandir}/man8/rbd-replay-prep.8*
%dir %{_datadir}/ceph/
%{_datadir}/ceph/known_hosts_drop.ceph.com
%{_datadir}/ceph/id_dsa_drop.ceph.com
%{_datadir}/ceph/id_dsa_drop.ceph.com.pub
%dir %{_sysconfdir}/ceph/
%config %{_sysconfdir}/bash_completion.d/rados
%config %{_sysconfdir}/bash_completion.d/rbd
%config(noreplace) %{_sysconfdir}/ceph/rbdmap
%if 0%{?_with_systemd}
%{_unitdir}/rbdmap.service
%else
%{_initrddir}/rbdmap
%endif
%{python_sitelib}/ceph_argparse.py*
%{python_sitelib}/ceph_daemon.py*
%{_udevrulesdir}/50-rbd.rules
%attr(3770,ceph,ceph) %dir %{_localstatedir}/log/ceph/
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/

%pre common
CEPH_GROUP_ID=""
CEPH_USER_ID=""
%if 0%{?rhel} || 0%{?fedora}
CEPH_GROUP_ID="-g 167"
CEPH_USER_ID="-u 167"
%endif
%if 0%{?rhel} || 0%{?fedora}
%{_sbindir}/groupadd ceph $CEPH_GROUP_ID -o -r 2>/dev/null || :
%{_sbindir}/useradd ceph $CEPH_USER_ID -o -r -g ceph -s /sbin/nologin -c "Ceph daemons" -d %{_localstatedir}/lib/ceph 2> /dev/null || :
%endif
%if 0%{?suse_version}
getent group ceph >/dev/null || groupadd -r ceph
getent passwd ceph >/dev/null || useradd -r -g ceph -d %{_localstatedir}/lib/ceph -s /sbin/nologin -c "Ceph daemons" ceph
%endif
exit 0

%post common
%if 0%{?_with_systemd}
%tmpfiles_create %{_tmpfilesdir}/ceph-common.conf
%endif

%postun common
# Package removal cleanup
if [ "$1" -eq "0" ] ; then
    rm -rf /var/log/ceph
    rm -rf /etc/ceph
fi

#################################################################################
%files mds
%{_bindir}/ceph-mds
%{_mandir}/man8/ceph-mds.8*
%if 0%{?_with_systemd}
%{_unitdir}/ceph-mds@.service
%{_unitdir}/ceph-mds.target
%else
%{_initrddir}/ceph
%endif
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/mds

#################################################################################
%files mon
%{_bindir}/ceph-mon
%{_bindir}/ceph-rest-api
%{_mandir}/man8/ceph-mon.8*
%{_mandir}/man8/ceph-rest-api.8*
%{python_sitelib}/ceph_rest_api.py*
%if 0%{?_with_systemd}
%{_unitdir}/ceph-mon@.service
%{_unitdir}/ceph-mon.target
%else
%{_initrddir}/ceph
%endif
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/mon

#################################################################################
%files fuse
%defattr(-,root,root,-)
%{_bindir}/ceph-fuse
%{_mandir}/man8/ceph-fuse.8*
%if 0%{?rhel} >= 7 || 0%{?fedora} || 0%{?suse_version}
%{_sbindir}/mount.fuse.ceph
%else
/sbin/mount.fuse.ceph
%endif

#################################################################################
%files -n rbd-fuse
%defattr(-,root,root,-)
%{_bindir}/rbd-fuse
%{_mandir}/man8/rbd-fuse.8*

#################################################################################
%files -n rbd-mirror
%defattr(-,root,root,-)
%{_bindir}/rbd-mirror
%{_mandir}/man8/rbd-mirror.8*
%if 0%{?_with_systemd}
%{_unitdir}/ceph-rbd-mirror@.service
%{_unitdir}/ceph-rbd-mirror.target
%endif

#################################################################################
%files -n rbd-nbd
%defattr(-,root,root,-)
%{_bindir}/rbd-nbd
%{_mandir}/man8/rbd-nbd.8*

#################################################################################
%files radosgw
%defattr(-,root,root,-)
%{_bindir}/radosgw
%{_bindir}/radosgw-admin
%{_bindir}/radosgw-token
%{_bindir}/radosgw-object-expirer
%{_mandir}/man8/radosgw.8*
%{_mandir}/man8/radosgw-admin.8*
%config %{_sysconfdir}/bash_completion.d/radosgw-admin
%dir %{_localstatedir}/lib/ceph/radosgw
%if 0%{?_with_systemd}
%{_unitdir}/ceph-radosgw@.service
%{_unitdir}/ceph-radosgw.target
%else
%{_initrddir}/ceph-radosgw
%{_sbindir}/rcceph-radosgw
%endif

%post radosgw
/sbin/ldconfig
%if 0%{?suse_version}
  # explicit systemctl daemon-reload (that's the only relevant bit of
  # service_add_post; the rest is all sysvinit --> systemd migration which
  # isn't applicable in this context (see above comment).
  /usr/bin/systemctl daemon-reload >/dev/null 2>&1 || :
%endif

%preun radosgw
%if 0%{?_with_systemd}
  # Disable and stop on removal.
  if [ $1 = 0 ] ; then
    SERVICE_LIST=$(systemctl | grep -E '^ceph-radosgw@'  | cut -d' ' -f1)
    if [ -n "$SERVICE_LIST" ]; then
      for SERVICE in $SERVICE_LIST; do
        /usr/bin/systemctl --no-reload disable $SERVICE > /dev/null 2>&1 || :
        /usr/bin/systemctl stop $SERVICE > /dev/null 2>&1 || :
      done
    fi
  fi
%endif

%postun radosgw
/sbin/ldconfig
%if 0%{?_with_systemd}
  if [ $1 = 1 ] ; then
    # Restart on upgrade, but only if "CEPH_AUTO_RESTART_ON_UPGRADE" is set to
    # "yes". In any case: if units are not running, do not touch them.
    SYSCONF_CEPH=/etc/sysconfig/ceph
    if [ -f $SYSCONF_CEPH -a -r $SYSCONF_CEPH ] ; then
      source $SYSCONF_CEPH
    fi
    if [ "X$CEPH_AUTO_RESTART_ON_UPGRADE" = "Xyes" ] ; then
      SERVICE_LIST=$(systemctl | grep -E '^ceph-radosgw@'  | cut -d' ' -f1)
      if [ -n "$SERVICE_LIST" ]; then
        for SERVICE in $SERVICE_LIST; do
          /usr/bin/systemctl try-restart $SERVICE > /dev/null 2>&1 || :
        done
      fi
    fi
  fi
%endif

#################################################################################
%files osd
%{_bindir}/ceph-clsinfo
%{_bindir}/ceph-bluefs-tool
%{_bindir}/ceph-objectstore-tool
%{_bindir}/ceph-osd
%{_sbindir}/ceph-disk
%{_sbindir}/ceph-disk-udev
%{_libexecdir}/ceph/ceph-osd-prestart.sh
%{_udevrulesdir}/60-ceph-partuuid-workaround.rules
%{_udevrulesdir}/95-ceph-osd.rules
%{_mandir}/man8/ceph-clsinfo.8*
%{_mandir}/man8/ceph-disk.8*
%{_mandir}/man8/ceph-osd.8*
%if 0%{?_with_systemd}
%{_unitdir}/ceph-osd@.service
%{_unitdir}/ceph-osd.target
%{_unitdir}/ceph-disk@.service
%else
%{_initrddir}/ceph
%endif
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/osd

#################################################################################
%if %{with ocf}

%files resource-agents
%defattr(0755,root,root,-)
# N.B. src/ocf/Makefile.am uses $(prefix)/lib
%dir %{_prefix}/lib/ocf
%dir %{_prefix}/lib/ocf/resource.d
%dir %{_prefix}/lib/ocf/resource.d/ceph
%if 0%{_with_systemd}
%exclude %{_prefix}/lib/ocf/resource.d/ceph/ceph
%exclude %{_prefix}/lib/ocf/resource.d/ceph/mds
%exclude %{_prefix}/lib/ocf/resource.d/ceph/mon
%exclude %{_prefix}/lib/ocf/resource.d/ceph/osd
%endif
%if ! 0%{_with_systemd}
%{_prefix}/lib/ocf/resource.d/ceph/ceph
%{_prefix}/lib/ocf/resource.d/ceph/mds
%{_prefix}/lib/ocf/resource.d/ceph/mon
%{_prefix}/lib/ocf/resource.d/ceph/osd
%endif
%{_prefix}/lib/ocf/resource.d/ceph/rbd

%endif

#################################################################################
%files -n librados2
%defattr(-,root,root,-)
%{_libdir}/librados.so.*
%if 0%{?_with_lttng}
%{_libdir}/librados_tp.so.*
%endif

%post -n librados2
/sbin/ldconfig

%postun -n librados2
/sbin/ldconfig

#################################################################################
%files -n librados2-devel
%defattr(-,root,root,-)
%dir %{_includedir}/rados
%{_includedir}/rados/librados.h
%{_includedir}/rados/librados.hpp
%{_includedir}/rados/buffer.h
%{_includedir}/rados/buffer_fwd.h
%{_includedir}/rados/page.h
%{_includedir}/rados/crc32c.h
%{_includedir}/rados/rados_types.h
%{_includedir}/rados/rados_types.hpp
%{_includedir}/rados/memory.h
%{_libdir}/librados.so
%if 0%{?_with_lttng}
%{_libdir}/librados_tp.so
%endif
%{_bindir}/librados-config
%{_mandir}/man8/librados-config.8*

#################################################################################
%files -n python-rados
%defattr(-,root,root,-)
%{python_sitearch}/rados.so
%{python_sitearch}/rados-*.egg-info

#################################################################################
%files -n libradosstriper1
%defattr(-,root,root,-)
%{_libdir}/libradosstriper.so.*

%post -n libradosstriper1
/sbin/ldconfig

%postun -n libradosstriper1
/sbin/ldconfig

#################################################################################
%files -n libradosstriper1-devel
%defattr(-,root,root,-)
%dir %{_includedir}/radosstriper
%{_includedir}/radosstriper/libradosstriper.h
%{_includedir}/radosstriper/libradosstriper.hpp
%{_libdir}/libradosstriper.so

#################################################################################
%files -n librbd1
%defattr(-,root,root,-)
%{_libdir}/librbd.so.*
%if 0%{?_with_lttng}
%{_libdir}/librbd_tp.so.*
%endif

%post -n librbd1
/sbin/ldconfig
mkdir -p /usr/lib64/qemu/
ln -sf %{_libdir}/librbd.so.1 /usr/lib64/qemu/librbd.so.1

%postun -n librbd1
/sbin/ldconfig

#################################################################################
%files -n librbd1-devel
%defattr(-,root,root,-)
%dir %{_includedir}/rbd
%{_includedir}/rbd/librbd.h
%{_includedir}/rbd/librbd.hpp
%{_includedir}/rbd/features.h
%{_libdir}/librbd.so
%if 0%{?_with_lttng}
%{_libdir}/librbd_tp.so
%endif

#################################################################################
%files -n librgw2
%defattr(-,root,root,-)
%{_libdir}/librgw.so.*

%post -n librgw2
/sbin/ldconfig

%postun -n librgw2
/sbin/ldconfig

#################################################################################
%files -n librgw2-devel
%defattr(-,root,root,-)
%dir %{_includedir}/rados
%{_includedir}/rados/librgw.h
%{_includedir}/rados/rgw_file.h
%{_libdir}/librgw.so

#################################################################################
%files -n python-rbd
%defattr(-,root,root,-)
%{python_sitearch}/rbd.so
%{python_sitearch}/rbd-*.egg-info

#################################################################################
%files -n libcephfs1
%defattr(-,root,root,-)
%{_libdir}/libcephfs.so.*

%post -n libcephfs1
/sbin/ldconfig

%postun -n libcephfs1
/sbin/ldconfig

#################################################################################
%files -n libcephfs1-devel
%defattr(-,root,root,-)
%dir %{_includedir}/cephfs
%{_includedir}/cephfs/libcephfs.h
%{_libdir}/libcephfs.so

#################################################################################
%files -n python-cephfs
%defattr(-,root,root,-)
%{python_sitearch}/cephfs.so
%{python_sitearch}/cephfs-*.egg-info
%{python_sitelib}/ceph_volume_client.py*

#################################################################################
%files -n ceph-test
%defattr(-,root,root,-)
%{_bindir}/ceph_bench_log
%{_bindir}/ceph_kvstorebench
%{_bindir}/ceph_multi_stress_watch
%{_bindir}/ceph_erasure_code
%{_bindir}/ceph_erasure_code_benchmark
%{_bindir}/ceph_omapbench
%{_bindir}/ceph_objectstore_bench
%{_bindir}/ceph_perf_objectstore
%{_bindir}/ceph_perf_local
%{_bindir}/ceph_perf_msgr_client
%{_bindir}/ceph_perf_msgr_server
%{_bindir}/ceph_psim
%{_bindir}/ceph_radosacl
%{_bindir}/ceph_rgw_jsonparser
%{_bindir}/ceph_rgw_multiparser
%{_bindir}/ceph_scratchtool
%{_bindir}/ceph_scratchtoolpp
%{_bindir}/ceph_smalliobench
%{_bindir}/ceph_smalliobenchdumb
%{_bindir}/ceph_smalliobenchfs
%{_bindir}/ceph_smalliobenchrbd
%{_bindir}/ceph_test_*
%{_bindir}/librgw_file*
%{_bindir}/ceph_tpbench
%{_bindir}/ceph_xattr_bench
%{_bindir}/ceph-coverage
%{_bindir}/ceph-monstore-tool
%{_bindir}/ceph-osdomap-tool
%{_bindir}/ceph-kvstore-tool
%{_bindir}/ceph-debugpack
%{_mandir}/man8/ceph-debugpack.8*
%dir %{_libdir}/ceph
%{_libdir}/ceph/ceph-monstore-update-crush.sh

#################################################################################
%if 0%{with cephfs_java}
%files -n libcephfs_jni1
%defattr(-,root,root,-)
%{_libdir}/libcephfs_jni.so.*

%post -n libcephfs_jni1
/sbin/ldconfig

%postun -n libcephfs_jni1
/sbin/ldconfig

#################################################################################
%files -n libcephfs_jni1-devel
%defattr(-,root,root,-)
%{_libdir}/libcephfs_jni.so

#################################################################################
%files -n cephfs-java
%defattr(-,root,root,-)
%{_javadir}/libcephfs.jar
%{_javadir}/libcephfs-test.jar
%endif

#################################################################################
%if 0%{with selinux}
%files selinux
%defattr(-,root,root,-)
%attr(0600,root,root) %{_datadir}/selinux/packages/ceph.pp
%{_datadir}/selinux/devel/include/contrib/ceph.if
%{_mandir}/man8/ceph_selinux.8*

%post selinux
# Install the policy
OLD_POLVER=$(%{_sbindir}/semodule -l | grep -P '^ceph[\t ]' | awk '{print $2}')
%{_sbindir}/semodule -n -i %{_datadir}/selinux/packages/ceph.pp
NEW_POLVER=$(%{_sbindir}/semodule -l | grep -P '^ceph[\t ]' | awk '{print $2}')

# Load the policy if SELinux is enabled
if %{_sbindir}/selinuxenabled; then
    %{_sbindir}/load_policy
else
    # Do not relabel if selinux is not enabled
    exit 0
fi

if test "$OLD_POLVER" == "$NEW_POLVER"; then
   # Do not relabel if policy version did not change
   exit 0
fi

# Check whether the daemons are running
%if 0%{?_with_systemd}
    /usr/bin/systemctl status ceph.target > /dev/null 2>&1
%else
    /sbin/service ceph status >/dev/null 2>&1
%endif
STATUS=$?

# Stop the daemons if they were running
if test $STATUS -eq 0; then
%if 0%{?_with_systemd}
    /usr/bin/systemctl stop ceph.target > /dev/null 2>&1
%else
    /sbin/service ceph stop >/dev/null 2>&1
%endif
fi

# Now, relabel the files
%relabel_files

# Start the daemons iff they were running before
if test $STATUS -eq 0; then
%if 0%{?_with_systemd}
    /usr/bin/systemctl start ceph.target > /dev/null 2>&1 || :
%else
    /sbin/service ceph start >/dev/null 2>&1 || :
%endif
fi

exit 0

%postun selinux
if [ $1 -eq 0 ]; then
    # Remove the module
    %{_sbindir}/semodule -n -r ceph

    # Reload the policy if SELinux is enabled
    if %{_sbindir}/selinuxenabled ; then
        %{_sbindir}/load_policy
    else
        # Do not relabel if SELinux is not enabled
        exit 0
    fi

    # Check whether the daemons are running
    %if 0%{?_with_systemd}
        /usr/bin/systemctl status ceph.target > /dev/null 2>&1
    %else
        /sbin/service ceph status >/dev/null 2>&1
    %endif
    STATUS=$?

    # Stop the daemons if they were running
    if test $STATUS -eq 0; then
    %if 0%{?_with_systemd}
        /usr/bin/systemctl stop ceph.target > /dev/null 2>&1
    %else
        /sbin/service ceph stop >/dev/null 2>&1
    %endif
    fi

    # Now, relabel the files
    %relabel_files

    # Start the daemons if they were running before
    if test $STATUS -eq 0; then
    %if 0%{?_with_systemd}
	/usr/bin/systemctl start ceph.target > /dev/null 2>&1 || :
    %else
	/sbin/service ceph start >/dev/null 2>&1 || :
    %endif
    fi
fi
exit 0

%endif # with selinux

#################################################################################
%if 0%{with libs_compat}
%files libs-compat
# We need an empty %%files list for ceph-libs-compat, to tell rpmbuild to actually
# build this meta package.
%endif

#################################################################################
%files devel-compat
# We need an empty %%files list for ceph-devel-compat, to tell rpmbuild to
# actually build this meta package.

#################################################################################
%files -n python-ceph-compat
# We need an empty %%files list for python-ceph-compat, to tell rpmbuild to
# actually build this meta package.


%changelog
