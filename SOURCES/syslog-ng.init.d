#!/bin/sh
#
# syslog-ng starts/stops syslog-ng service
#
# chkconfig: - 12 88
# description: Syslog is the facility by which many daemons use to log \
#     messages to various system log files.
#

### BEGIN INIT INFO
# Provides: $syslog
# Required-Start: $local_fs
# Required-Stop: $local_fs
# Short-Description: Next-generation syslog server
# Description: syslog-ng, as the name shows, is a syslogd replacement, but
#     with new functionality for the new generation. The original syslogd
#     allows messages only to be sorted based on priority/facility pairs;
#     syslog-ng adds the possibility to filter based on message contents
#     using regular expressions. The new configuration scheme is intuitive
#     and powerful.  Forwarding logs over TCP and remembering all forwarding
#     hops makes it ideal for firewalled environments.  
### END INIT INFO

# Source function library.
. /etc/init.d/functions

[ -e /etc/sysconfig/syslog-ng ] && . /etc/sysconfig/syslog-ng

RETVAL=0

check_syntax()
{
	[ -x /sbin/syslog-ng ] || exit 5
	syslog-ng -s $SYSLOGNG_OPTIONS
	RETVAL=$?
	return $RETVAL
}

verify_config()
{
	check_syntax
	RETVAL=$?
	[ $RETVAL -eq 0 ] || exit $retval
}

checkconfig()
{
	action $"Checking Configuration: " check_syntax
}

start()
{
	verify_config
	echo -n $"Starting syslog-ng: "
	if [ -e $SYSLOGNG_COMPAT_PID ]; then
		failure "PID file for existing syslog daemon exists"
	fi
	daemon syslog-ng $SYSLOGNG_OPTIONS
	ln -sf $SYSLOGNG_PID $SYSLOGNG_COMPAT_PID
	RETVAL=$?
	echo
	[ $RETVAL -eq 0 ] && touch /var/lock/subsys/syslog-ng
	return $RETVAL
}

stop()
{
	echo -n $"Stopping syslog-ng: "
	REMOVE_COMPAT_PID=0
	if [ -e $SYSLOGNG_COMPAT_PID -a $(<$SYSLOGNG_PID) == $(<$SYSLOGNG_COMPAT_PID) ]; then
		REMOVE_COMPAT_PID=1
	fi
	killproc syslog-ng
	RETVAL=$?
	echo
	[ $RETVAL -eq 0 ] && rm -f /var/lock/subsys/syslog-ng
	[ $RETVAL -eq 0 -a $REMOVE_COMPAT_PID -eq 1 ] && rm -f $SYSLOGNG_COMPAT_PID
	return $RETVAL
}

reload()
{
	verify_config
	echo -n $"Reloading syslog-ng: "
	killproc syslog-ng -HUP
	RETVAL=$?
	echo
	return $RETVAL
}

restart()
{
	stop
	start
}


case "$1" in
	start|stop|reload)
		$1
		;;
	restart|force_reload)
		restart
		;;
	status)
		status syslog-ng
		;;
	checkconfig|configtest|check|test)
		checkconfig
		;;
	condrestart|try-restart)
		[ -f /var/lock/subsys/syslog-ng ] && restart || :
		;;
	*)
		echo $"Usage: $0 {start|stop|restart|reload|condrestart|checkconfig}"
		exit 1
esac

exit $?

# vim: ft=sh:ts=4:ai:si:
