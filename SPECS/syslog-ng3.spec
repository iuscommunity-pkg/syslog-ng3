%{?_with_spoofsource:%define spoofsource 1}
%define evtlog_ver 0.2.7-2

%define _sbindir /sbin
%define _localstatedir /var/lib/syslog-ng
%define realname syslog-ng

Name: syslog-ng3
Version: 3.2.2
Release: 1.ius%{?dist}
Summary: Next-generation syslog server

Group: System Environment/Daemons
License: GPLv2+
Url: http://www.balabit.com/products/syslog_ng/
Source0: http://www.balabit.com/downloads/files/syslog-ng/sources/2.1/src/syslog-ng-%{version}.tar.gz
Source1: syslog-ng.conf
Source2: syslog-ng.init.d
Source10: sysklogd-syslog-ng.sysconfig
Source11: sysklogd-1.4.1-logrotate.d-syslog.log
Source12: sysklogd-1.4.1-44-logrotate.d-syslog.log
Source20: rsyslog-syslog-ng.sysconfig
Source21: rsyslog-3.14.1-logrotate.d-rsyslog.log
Source30: rsyslog-syslog-ng-fc10.sysconfig
Source31: rsyslog-3.21.9-logrotate.d-rsyslog.log
BuildRoot: %{_tmppath}/%{realname}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires: eventlog-devel >= %{evtlog_ver}
BuildRequires: pkgconfig
BuildRequires: glib2-devel
%if 0%{?fedora}
BuildRequires: glib2-static
%endif
%if 0%{?rhel}
BuildRequires: tcp_wrappers
BuildRequires: eventlog-static >= %{evtlog_ver}
%else
BuildRequires: tcp_wrappers-devel
%endif
BuildRequires: libnet-devel
Requires: logrotate
Requires(post): /sbin/chkconfig
Requires(preun): /sbin/chkconfig
Requires(preun): /sbin/service
Requires(postun): /sbin/service
Provides: syslog
%if 0%{?rhel} == 4
# makes vixie-cron and initscripts happy
Provides: sysklogd = 1.3.33-6
%endif
# merge separate syslog-vim package into one
Provides: syslog-ng-vim = %{version}-%{release}
Obsoletes: syslog-ng-vim < 2.0.8-1


%description
syslog-ng, as the name shows, is a syslogd replacement, but with new 
functionality for the new generation. The original syslogd allows 
messages only to be sorted based on priority/facility pairs; syslog-ng 
adds the possibility to filter based on message contents using regular 
expressions. The new configuration scheme is intuitive and powerful. 
Forwarding logs over TCP and remembering all forwarding hops makes it 
ideal for firewalled environments.


%prep
%setup -q -n syslog-ng-3.2.2

# fix perl path
%{__sed} -i 's|^#!/usr/local/bin/perl|#!%{__perl}|' contrib/relogger.pl

%define logrotated_dst syslog
%if 0%{?rhel}
	%if 0%{?rhel} <= 4
		%define sysconfig_src %{SOURCE10}
		%define logrotated_src %{SOURCE11}
	%endif
	%if 0%{?rhel} >= 5
		%define sysconfig_src %{SOURCE10}
		%define logrotated_src %{SOURCE12}
	%endif
%endif
%if 0%{?fedora}
	%if 0%{?fedora} <= 9
		%define sysconfig_src %{SOURCE20}
		%define logrotated_src %{SOURCE21}
	%endif
	%if 0%{?fedora} >= 10
		%define sysconfig_src %{SOURCE30}
		%define logrotated_src %{SOURCE31}
	%endif
%endif


%build
%configure \
	--enable-ipv6 \
	--sysconfdir=%{_sysconfdir}/%{realname} \
	--enable-tcp-wrapper \
%if 0%{?spoofsource}
	--enable-spoof-source \
%endif
%if 0%{?rhel}
	--enable-mixed-linking
%else
	--enable-dynamic-linking
%endif


make %{_smp_mflags}


%install
%{__rm} -rf %{buildroot}
make DESTDIR=%{buildroot} install

# Needs to be created
%{__mkdir} -p %{buildroot}/var/lib/syslog-ng

%{__install} -d -m 755 %{buildroot}%{_sysconfdir}/%{realname}
%{__install} -p -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/%{realname}/syslog-ng.conf

%{__install} -d -m 755 %{buildroot}%{_sysconfdir}/init.d
%{__install} -p -m 755 %{SOURCE2} %{buildroot}%{_sysconfdir}/init.d/syslog-ng

%{__install} -d -m 755 %{buildroot}%{_sysconfdir}/sysconfig
%{__install} -p -m 644 %{sysconfig_src} %{buildroot}%{_sysconfdir}/sysconfig/%{realname}

%{__install} -d -m 755 %{buildroot}%{_sysconfdir}/logrotate.d
%{__install} -p -m 644 %{logrotated_src} %{buildroot}%{_sysconfdir}/logrotate.d/%{logrotated_dst}

# make local state dir
%{__install} -d -m 755 %{buildroot}/%{_localstatedir}

# fix authors file
/usr/bin/iconv -f iso8859-1 -t utf-8 AUTHORS > AUTHORS.conv && \
	%{__mv} -f AUTHORS.conv AUTHORS

# fix executable perms on contrib files
%{__chmod} -x contrib/relogger.pl
%{__chmod} -x contrib/syslog2ng

# fix script interpreter
sed -i 's/\/usr\/local\/bin\/perl/\/usr\/bin\/perl/' contrib/relogger.pl

# install vim files
%{__install} -d -m 755 %{buildroot}%{_datadir}/%{realname}
%{__install} -p -m 644 contrib/syslog-ng.vim %{buildroot}%{_datadir}/%{realname}
for vimver in 63 64 70 71 ; do
	%{__install} -d -m 755 %{buildroot}%{_datadir}/vim/vim$vimver/syntax
	cd %{buildroot}%{_datadir}/vim/vim$vimver/syntax
	ln -s ../../../%{realname}/syslog-ng.vim .
	cd -
done


%clean
rm -rf %{buildroot}


%post
/sbin/chkconfig --add %{realname}


%preun
if [ "$1" = 0 ]; then
	/sbin/service %{realname} stop > /dev/null 2>&1
	/sbin/chkconfig --del %{realname}
fi


%postun
if [ "$1" -ge 1 ]; then
	/sbin/service %{realname} condrestart >/dev/null 2>&1
fi


%triggerin -- vim-common
VIMVERNEW=`rpm -q --qf='%%{epoch}:%%{version}\n' vim-common | sort | tail -n 1 | sed -e 's/[0-9]*://' | sed -e 's/\.[0-9]*$//' | sed -e 's/\.//'`
[ -d %{_datadir}/vim/vim${VIMVERNEW}/syntax ] && \
	cd %{_datadir}/vim/vim${VIMVERNEW}/syntax && \
	ln -sf ../../../%{realname}/syslog-ng.vim . || :

%triggerun -- vim-common
VIMVEROLD=`rpm -q --qf='%%{epoch}:%%{version}\n' vim-common | sort | head -n 1 | sed -e 's/[0-9]*://' | sed -e 's/\.[0-9]*$//' | sed -e 's/\.//'`
[ $2 = 0 ] && rm -f %{_datadir}/vim/vim${VIMVEROLD}/syntax/syslog-ng.vim || :

%triggerpostun -- vim-common
VIMVEROLD=`rpm -q --qf='%%{epoch}:%%{version}\n' vim-common | sort | head -n 1 | sed -e 's/[0-9]*://' | sed -e 's/\.[0-9]*$//' | sed -e 's/\.//'`
VIMVERNEW=`rpm -q --qf='%%{epoch}:%%{version}\n' vim-common | sort | tail -n 1 | sed -e 's/[0-9]*://' | sed -e 's/\.[0-9]*$//' | sed -e 's/\.//'`
if [ $1 = 1 ]; then
	rm -f %{_datadir}/vim/vim${VIMVEROLD}/syntax/syslog-ng.vim || :
	[ -d %{_datadir}/vim/vim${VIMVERNEW}/syntax ] && \
		cd %{_datadir}/vim/vim${VIMVERNEW}/syntax && \
		ln -sf ../../../%{realname}/syslog-ng.vim . || :
fi



%files
%defattr(-,root,root)
%doc AUTHORS COPYING README ChangeLog NEWS

%{_bindir}/loggen
%{_bindir}/pdbtool
%{_bindir}/update-patterndb

%{_sbindir}/syslog-ng
%{_sbindir}/syslog-ng-ctl

%{_datadir}/include/scl/pacct/plugin.conf
%{_datadir}/include/scl/syslogconf/README
%{_datadir}/include/scl/syslogconf/convert-syslogconf.awk
%{_datadir}/include/scl/syslogconf/plugin.conf
%{_datadir}/include/scl/system/generate-system-source.sh
%{_datadir}/include/scl/system/plugin.conf
%{_datadir}/xsd/patterndb-1.xsd
%{_datadir}/xsd/patterndb-2.xsd
%{_datadir}/xsd/patterndb-3.xsd

/var/lib/syslog-ng
%{_prefix}/lib/syslog-ng
%{_libdir}/libsyslog-ng-patterndb.la
%{_libdir}/libsyslog-ng-patterndb.so
%{_libdir}/libsyslog-ng-patterndb.so.0
%{_libdir}/libsyslog-ng-patterndb.so.0.0.0
%{_libdir}/libsyslog-ng.la
%{_libdir}/libsyslog-ng.so
%{_libdir}/libsyslog-ng.so.0
%{_libdir}/libsyslog-ng.so.0.0.0

%{_mandir}/man1/loggen.1.gz
%{_mandir}/man1/pdbtool.1.gz
%{_mandir}/man1/syslog-ng-ctl.1.gz
%{_mandir}/man5/syslog-ng.conf.5.gz
%{_mandir}/man8/syslog-ng.8.gz

%{_sysconfdir}/init.d/syslog-ng
%{_sysconfdir}/logrotate.d/syslog
%{_sysconfdir}/sysconfig/syslog-ng
%{_sysconfdir}/syslog-ng/modules.conf
%{_sysconfdir}/syslog-ng/scl.conf
%{_sysconfdir}/syslog-ng/syslog-ng.conf
%{_datadir}/syslog-ng/syslog-ng.vim
%{_datadir}/vim/vim63/syntax/syslog-ng.vim
%{_datadir}/vim/vim64/syntax/syslog-ng.vim
%{_datadir}/vim/vim70/syntax/syslog-ng.vim
%{_datadir}/vim/vim71/syntax/syslog-ng.vim


%changelog
* Wed Mar 23 2011 Jeffrey Ness <jeffrey.ness@rackspace.com> - 3.2.2-1.ius
- Migrating EPEL package to IUS with latest sources from upstream

* Tue Mar 24 2009 Douglas E. Warner <silfreed@silfreed.net> - 2.1.4-1
- update to 2.1.4
- enabling mixed linking to compile only non-system libs statically
- lots of packaging updates to be able to build on RHEL4,5, Fedora9+ and be
  parallel-installable with rsyslog and/or sysklogd on those platforms
- removing BR for flex & byacc to try to prevent files from being regenerated
- fixing build error with cfg-lex.l and flex 2.5.4
- Fixed a possible DoS condition triggered by a destination port unreachable
  ICMP packet received from a UDP destination.  syslog-ng started eating all
  available memory and CPU until it crashed if this happened.
- Fixed the rate at which files regular were read using the file() source.
- Report connection breaks as a write error instead of reporting POLLERR as
  the write error path reports more sensible information in the logs.

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.10-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Mon Dec 02 2008 Douglas E. Warner <silfreed@silfreed.net> 2.0.10-1
- update to 2.0.10
- fix for CVE-2008-5110

* Mon Sep 15 2008 Peter Vrabec <pvrabec@redhat.com> 2.0.8-3
- do not conflicts with rsyslog, both rsyslog and syslog-ng use 
  same pidfile and logrotate file (#441664)

* Sat Sep  6 2008 Tom "spot" Callaway <tcallawa@redhat.com> 2.0.8-2
- fix license tag

* Thu Jan 31 2008 Douglas E. Warner <silfreed@silfreed.net> 2.0.8-1
- updated to 2.0.8
- removed logrotate patch

* Tue Jan 29 2008 Douglas E. Warner <silfreed@silfreed.net> 2.0.7-2
- added patch from git commit a8b9878ab38b10d24df7b773c8c580d341b22383
  to fix log rotation (bug#430057)

* Tue Jan 08 2008 Douglas E. Warner <silfreed@silfreed.net> 2.0.7-1
- updated to 2.0.7
- force regeneration to avoid broken paths from upstream (#265221)
- adding loggen binary

* Mon Dec 17 2007 Douglas E. Warner <silfreed@silfreed.net> 2.0.6-1
- updated to 2.0.6
- fixes DoS in ZSA-2007-029

* Thu Nov 29 2007 Peter Vrabec <pvrabec@redhat.com> 2.0.5-3
- add conflicts (#400661)

* Wed Aug 29 2007 Fedora Release Engineering <rel-eng at fedoraproject dot org> - 2.0.5-2
- Rebuild for selinux ppc32 issue.

* Thu Jul 26 2007 Jose Pedro Oliveira <jpo at di.uminho.pt> - 2.0.5-1
- Update to 2.0.5

* Thu Jun  7 2007 Jose Pedro Oliveira <jpo at di.uminho.pt> - 2.0.4-4
- Add support for vim 7.1.

* Thu May 31 2007 Jose Pedro Oliveira <jpo at di.uminho.pt> - 2.0.4-3
- Increase the number of unix-stream max-connections (10 -> 32).

* Sat May 26 2007 Jose Pedro Oliveira <jpo at di.uminho.pt> - 2.0.4-2
- New upstream download location
  (https://lists.balabit.hu/pipermail/syslog-ng/2007-May/010258.html)

* Tue May 22 2007 Jose Pedro Oliveira <jpo at di.uminho.pt> - 2.0.4-1
- Update to 2.0.4.

* Mon Mar 26 2007 Jose Pedro Oliveira <jpo at di.uminho.pt> - 2.0.3-1
- Update to 2.0.3.

* Fri Mar 23 2007 Jose Pedro Oliveira <jpo at di.uminho.pt> - 2.0.3-0.20070323
- Update to latest snapshot (2007-03-23).

* Fri Mar  9 2007 Jose Pedro Oliveira <jpo at di.uminho.pt> - 2.0.3-0.20070309
- Enable support for TCP wrappers (--enable-tcp-wrapper).
- Optional support for spoofed source addresses (--enable-spoof-source)
  (disabled by default; build requires libnet).

* Sun Feb 25 2007 Jose Pedro Oliveira <jpo at di.uminho.pt> - 2.0.2-2
- Dynamic link glib2 and eventlog (--enable-dynamic-linking).
  For Fedora Core 6 (and above) both packages install their dynamic
  libraries in /lib.

* Mon Jan 29 2007 Jose Pedro Oliveira <jpo at di.uminho.pt> - 2.0.2-1
- Update to 2.0.2.

* Thu Jan  4 2007 Jose Pedro Oliveira <jpo at di.uminho.pt> - 2.0.1-1
- Update to 2.0.1.

* Fri Dec 15 2006 Jose Pedro Oliveira <jpo at di.uminho.pt> - 2.0.0-1
- Updated the init script patch: LSB Description and Short-Description.

* Fri Nov  3 2006 Jose Pedro Oliveira <jpo at di.uminho.pt> - 2.0.0-0
- Update to 2.0.0.

* Sun Sep 10 2006 Jose Pedro Oliveira <jpo at di.uminho.pt> - 1.6.11-3
- Rebuild for FC6.

* Sun Jun  4 2006 Jose Pedro Oliveira <jpo at di.uminho.pt> - 1.6.11-2
- Install the vim syntax file.

* Fri May  5 2006 Jose Pedro Oliveira <jpo at di.uminho.pt> - 1.6.11-1
- Update to 1.6.11.

* Sun Apr  2 2006 Jose Pedro Oliveira <jpo at di.uminho.pt> - 1.6.10-2
- Build option to support the syslog-ng spoof-source feature
  (the feature spoof-source is disabled by default).

* Thu Mar 30 2006 Jose Pedro Oliveira <jpo at di.uminho.pt> - 1.6.10-1
- Update to 1.6.10.
- The postscript documentation has been dropped (upstream).

* Wed Feb 15 2006 Jose Pedro Oliveira <jpo at di.uminho.pt> - 1.6.9-3
- Rebuild.

* Mon Dec 19 2005 Jose Pedro Oliveira <jpo at di.uminho.pt> - 1.6.9-2
- Provides syslog instead of sysklogd (#172885).

* Wed Nov 30 2005 Jose Pedro Oliveira <jpo at di.uminho.pt> - 1.6.9-1
- Build conflict statement
  (see: https://lists.balabit.hu/pipermail/syslog-ng/2005-June/007630.html)

* Wed Nov 23 2005 Jose Pedro Oliveira <jpo at di.uminho.pt> - 1.6.9-0
- Update to 1.6.9.
- The libol support library is now included in the syslog-ng tarball.

* Wed Jun 22 2005 Jose Pedro Oliveira <jpo at di.uminho.pt> - 1.6.8-2
- BuildRequire which, since it's not part of the default buildgroup
  (Konstantin Ryabitsev).

* Fri May 27 2005 Jose Pedro Oliveira <jpo at di.uminho.pt> - 1.6.8-1
- Update to 1.6.8.

* Thu May 26 2005 Jose Pedro Oliveira <jpo at di.uminho.pt> - 1.6.7-3
- Shipping the sysklogd logrotate file and using the same pidfile
  as suggested by Jeremy Katz.
- Patching the init script: no default runlevels.
- Removed the triggers to handle the logrotate file (no longer needed).
- The SELinux use_syslogng boolean has been dropped (rules enabled).

* Sat May 07 2005 Jose Pedro Oliveira <jpo at di.uminho.pt> - 1.6.7-2.fc4
- Increased libol required version to 0.3.16
  (https://lists.balabit.hu/pipermail/syslog-ng/2005-May/007385.html).

* Sat Apr 09 2005 Jose Pedro Oliveira <jpo at di.uminho.pt> - 0:1.6.7-0.fdr.1
- Update to 1.6.7.
- The Red Hat/Fedora Core configuration files are now included in the
  syslog-ng tarball (directory: contrib/fedora-packaging).

* Fri Mar 25 2005 Jose Pedro Oliveira <jpo at di.uminho.pt> - 0:1.6.6-0.fdr.4
- Logrotate file conflict: just comment/uncomment contents of the syslog
  logrotate file using triggers.

* Tue Feb 15 2005 Jose Pedro Oliveira <jpo at di.uminho.pt> - 0:1.6.6-0.fdr.3
- Require logrotate.
- Documentation updates (upstream).

* Sat Feb 05 2005 Jose Pedro Oliveira <jpo at di.uminho.pt> - 0:1.6.6-0.fdr.2
- Added contrib/relogger.pl (missing in syslog-ng-1.6.6).
- Requires libol 0.3.15.
- Added %%trigger scripts to handle the logrotate file.

* Fri Feb 04 2005 Jose Pedro Oliveira <jpo at di.uminho.pt> - 0:1.6.6-0.fdr.1
- Update to 1.6.6.
- Patches no longer needed.

* Fri Feb 04 2005 Jose Pedro Oliveira <jpo at di.uminho.pt> - 0:1.6.5-0.fdr.7
- Took ownership of the configuration directory (/etc/syslog-ng/).
- Updated the syslog-ng(8) manpage (upstream patch).
- Updated the configuration file: /proc/kmsg is a file not a pipe.
- Patched two contrib files: syslog2ng and syslog-ng.conf.RedHat.
- Logrotate file inline replacement: perl --> sed (bug 1332 comment 23).

* Tue Jan 25 2005 Jose Pedro Oliveira <jpo at di.uminho.pt> - 0:1.6.5-0.fdr.6
- Logrotate problem: only one logrotate file for syslog and syslog-ng.
- Configuration file: don't sync d_mail destination (/var/log/maillog).

* Mon Jan 24 2005 Jose Pedro Oliveira <jpo at di.uminho.pt> - 0:1.6.5-0.fdr.5
- SIGHUP handling upstream patch (syslog-ng-1.6.5+20050121.tar.gz).
- Static linking /usr libraries (patch already upstream).

* Thu Sep 30 2004 Jose Pedro Oliveira <jpo at di.uminho.pt> - 0:1.6.5-0.fdr.4
- make: do not strip the binaries during installation (install vs install-strip)
  (bug 1332 comment 18).
- install: preserve timestamps (option -p) (bug 1332 comment 18).

* Wed Sep  1 2004 Jose Pedro Oliveira <jpo at di.uminho.pt> 0:1.6.5-0.fdr.3
- use the tcp_wrappers static library instead (bug 1332 comment 15).

* Wed Sep  1 2004 Jose Pedro Oliveira <jpo at di.uminho.pt> 0:1.6.5-0.fdr.2
- added missing build requirement: flex (bug 1332 comment 13).

* Wed Aug 25 2004 Jose Pedro Oliveira <jpo at di.uminho.pt> 0:1.6.5-0.fdr.1
- update to 1.65.
- removed the syslog-ng.doc.patch patch (already upstream).
- removed the syslog-ng.conf.solaris documentation file.

* Wed Apr 21 2004 Jose Pedro Oliveira <jpo at di.uminho.pt> 0:1.6.2-0.fdr.3
- removed Conflits:
- changed the %post and %preun scripts
- splitted Requires( ... , ... ) into Requires( ... )

* Fri Mar  5 2004 Jose Pedro Oliveira <jpo at di.uminho.pt> 0:1.6.2-0.fdr.2
- corrected the source URL

* Sat Feb 28 2004 Jose Pedro Oliveira <jpo at di.uminho.pt> 0:1.6.2-0.fdr.1
- changed packaged name to be compliant with fedora.us naming conventions

* Fri Feb 27 2004 Jose Pedro Oliveira <jpo at di.uminho.pt> 0:1.6.2-0.fdr.0.2
- updated to version 1.6.2
- undo "Requires: tcp_wrappers" - tcp_wrappers is a static lib

* Sat Feb  7 2004 Jose Pedro Oliveira <jpo at di.uminho.pt> 0:1.6.1-0.fdr.2
- make %{?_smp_mflags}
- Requires: tcp_wrappers

* Sat Jan 10 2004 Jose Pedro Oliveira <jpo at di.uminho.pt> 0:1.6.1-0.fdr.1
- first release for fedora.us

* Fri Jan  9 2004 Jose Pedro Oliveira <jpo at di.uminho.pt> 1.6.1-1.1tux
- updated to version 1.6.1

* Tue Oct  7 2003 Jose Pedro Oliveira <jpo at di.uminho.pt> 1.6.0rc4-1.1tux
- updated to version 1.6.0rc4

* Tue Aug 26 2003 Jose Pedro Oliveira <jpo at di.uminho.pt> 1.6.0rc3-1.4tux
- installation scripts improved
- conflits line

* Sat Aug 16 2003 Jose Pedro Oliveira <jpo at di.uminho.pt> 1.6.0rc3-1.3tux
- install-strip

* Tue Jul 22 2003 Jose Pedro Oliveira <jpo at di.uminho.pt> 1.6.0rc3-1.2tux
- missing document: contrib/syslog-ng.conf.doc

* Thu Jun 12 2003 Jose Pedro Oliveira <jpo at di.uminho.pt> 1.6.0rc3-1.1tux
- Version 1.6.0rc3

* Sat Apr 12 2003 Jose Pedro Oliveira <jpo at di.uminho.pt> 1.6.0rc2 snapshot
- Reorganized specfile
- Corrected the scripts (%post, %postun, and %preun)
- Commented the mysql related lines; create an option for future inclusion

* Thu Feb 27 2003 Richard E. Perlotto II <richard@perlotto.com> 1.6.0rc1-1
- Updated for new version

* Mon Feb 17 2003 Richard E. Perlotto II <richard@perlotto.com> 1.5.26-1
- Updated for new version

* Sun Dec 20 2002 Richard E. Perlotto II <richard@perlotto.com> 1.5.24-1
- Updated for new version

* Sun Dec 13 2002 Richard E. Perlotto II <richard@perlotto.com> 1.5.23-2
- Corrected the mass of errors that occured with rpmlint
- Continue to clean up for the helpful hints on how to write to a database

* Sun Dec 08 2002 Richard E. Perlotto II <richard@perlotto.com> 1.5.23-1
- Updated file with notes and PGP signatures

