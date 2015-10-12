# Name of the package without any prefixes
%global pkg_name %{name}
%global pkg_name_shared mariadb
%global pkgnamepatch mariadb

# Regression tests may take a long time (many cores recommended), skip them by 
# passing --nocheck to rpmbuild or by setting runselftest to 0 if defining
# --nocheck is not possible (e.g. in koji build)
%{!?runselftest:%global runselftest 0}

# In f20+ use unversioned docdirs, otherwise the old versioned one
%global _pkgdocdirname %{pkg_name}%{!?_pkgdocdir:-%{version}}
%{!?_pkgdocdir: %global _pkgdocdir %{_docdir}/%{pkg_name}-%{version}}

# use Full RELRO for all binaries (RHBZ#1092548)
%global _hardened_build 1

# By default, patch(1) creates backup files when chunks apply with offsets.
# Turn that off to ensure such files don't get included in RPMs (cf bz#884755).
%global _default_patch_flags --no-backup-if-mismatch

# TokuDB engine is now part of MariaDB, but it is available only for x86_64;
# variable tokudb allows to build with TokuDB storage engine
# Disabled for galera since only InnoDB works there
%bcond_with tokudb

# Mroonga engine is now part of MariaDB, but it only builds for x86_64;
# variable mroonga allows to build with Mroonga storage engine
%bcond_with mroonga

# The Open Query GRAPH engine (OQGRAPH) is a computation engine allowing
# hierarchies and more complex graph structures to be handled in a relational
# fashion; enabled by default
%bcond_with oqgraph

# For some use cases we do not need some parts of the package
%bcond_with clibrary
%bcond_with embedded
%bcond_with devel
%bcond_with client
%bcond_with common
%bcond_with errmsg
%bcond_with bench
%bcond_with test
%bcond_with connect

# When there is already another package that ships /etc/my.cnf,
# rather include it than ship the file again, since conflicts between
# those files may create issues
%bcond_with config

# For deep debugging we need to build binaries with extra debug info
%bcond_with debug

# Include files for SysV init or systemd
%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
%bcond_without init_systemd
%bcond_with init_sysv
%global daemon_name mariadb
%global daemondir %{_unitdir}
%else
%bcond_with init_systemd
%bcond_without init_sysv
%global daemon_name mysqld
%global daemondir %{_sysconfdir}/rc.d/init.d
%endif

# MariaDB 10.0 and later requires pcre >= 8.35, otherwise we need to use
# the bundled library, since the package cannot be build with older version
%if 0%{?fedora} >= 21
%bcond_without pcre
%else
%bcond_with pcre
%endif

# We define some system's well known locations here so we can use them easily
# later when building to another location (like SCL)
%global logrotateddir %{_sysconfdir}/logrotate.d
%global logfiledir %{_localstatedir}/log/%{daemon_name}
%global logfile %{logfiledir}/%{daemon_name}.log
%global dbdatadir %{_localstatedir}/lib/mysql

# Home directory of mysql user should be same for all packages that create it
%global mysqluserhome /var/lib/mysql

# The evr of mysql we want to obsolete
%global obsoleted_mysql_evr 5.6-0
%global obsoleted_mysql_case_evr 5.5.30-5

# Provide mysql names for compatibility
%bcond_without mysql_names

# When replacing mysql by mariadb these packages are not upated, but rather
# installed and uninstalled. Thus we loose information about mysqld service
# enablement. To address this we use a file to store that information within
# the transaction. Basically the file is created when mysqld is enabled in
# the beginning of the transaction and mysqld is enabled again in the end
# of the transaction in case this flag file exists.
%global mysqld_enabled_flag_file %{_localstatedir}/lib/rpm-state/mysqld_enabled
%global mysqld_running_flag_file %{_localstatedir}/lib/rpm-state/mysqld_running

# If we build without common subpackage, we want to use mariadb's common files
%if %{with common}
%global datadirname %{pkgname}
%else
%global datadirname mariadb
%endif

# Make long macros shorter
%global sameevr   %{epoch}:%{version}-%{release}
%global compatver 10.0
%global bugfixver 17

Name:             mariadb-galera
Version:          %{compatver}.%{bugfixver}
Release:          8%{?with_debug:.debug}%{?dist}
Epoch:            1

Summary:          A community developed branch of MySQL
Group:            Applications/Databases
URL:              http://mariadb.org
# Exceptions allow client libraries to be linked with most open source SW,
# not only GPL code.  See README.mysql-license
License:          GPLv2 with exceptions and LGPLv2 and BSD

# Since galera only builds on these architectures, there is no reaon
# to build mariadb-galera on other architectures (#1092068)
ExclusiveArch: %{ix86} x86_64 %{arm} aarch64

Source0:          http://ftp.osuosl.org/pub/mariadb/%{pkg_name}-%{version}/src/%{pkg_name}-%{version}.tar.gz
Source2:          mysql_config_multilib.sh
Source3:          my.cnf.in
Source4:          my_config.h
Source5:          README.mysql-cnf
Source6:          README.mysql-docs
Source7:          README.mysql-license
Source9:          mysql-embedded-check.c
Source10:         mysql.tmpfiles.d.in
Source11:         mysql.service.in
Source12:         mysql-prepare-db-dir.sh
Source13:         mysql-wait-ready.sh
Source14:         mysql-check-socket.sh
Source15:         mysql-scripts-common.sh
Source16:         mysql-check-upgrade.sh
Source17:         mysql-compat.service.in
Source18:         mysql-compat.conf.in
Source19:         mysql.init.in
Source50:         rh-skipped-tests-base.list
Source51:         rh-skipped-tests-arm.list
Source52:         rh-skipped-tests-ppc-s390.list
# TODO: clustercheck contains some hard-coded paths, these should be expanded using template system
Source70:         clustercheck.sh
Source71:         LICENSE.clustercheck

# Comments for these patches are in the patch files
# Patches common for more mysql-like packages
Patch1:           %{pkgnamepatch}-strmov.patch
Patch2:           %{pkgnamepatch}-install-test.patch
Patch3:           %{pkgnamepatch}-s390-tsc.patch
Patch4:           %{pkgnamepatch}-logrotate.patch
Patch5:           %{pkgnamepatch}-file-contents.patch
Patch6:           %{pkgnamepatch}-dh1024.patch
Patch7:           %{pkgnamepatch}-scripts.patch
Patch8:           %{pkgnamepatch}-install-db-sharedir.patch

# Patches specific for this mysql package
Patch30:          %{pkgnamepatch}-errno.patch
Patch31:          %{pkgnamepatch}-string-overflow.patch
Patch32:          %{pkgnamepatch}-basedir.patch
Patch33:          %{pkgnamepatch}-covscan-signexpr.patch
Patch34:          %{pkgnamepatch}-covscan-stroverflow.patch
Patch35:          %{pkgnamepatch}-config.patch
Patch36:          %{pkgnamepatch}-ssltest.patch

Patch99:          galera-enc.patch

BuildRequires:    cmake
BuildRequires:    libaio-devel
BuildRequires:    openssl-devel
BuildRequires:    ncurses-devel
BuildRequires:    perl
BuildRequires:    libedit-devel
BuildRequires:    systemtap-sdt-devel
BuildRequires:    zlib-devel
# auth_pam.so plugin will be build if pam-devel is installed
BuildRequires:    pam-devel
%{?with_pcre:BuildRequires: pcre-devel >= 8.35}
# Tests requires time and ps and some perl modules
BuildRequires:    procps
BuildRequires:    time
BuildRequires:    perl(Env)
BuildRequires:    perl(Exporter)
BuildRequires:    perl(Fcntl)
BuildRequires:    perl(File::Temp)
BuildRequires:    perl(Data::Dumper)
BuildRequires:    perl(Getopt::Long)
BuildRequires:    perl(IPC::Open3)
BuildRequires:    perl(Socket)
BuildRequires:    perl(Sys::Hostname)
BuildRequires:    perl(Test::More)
BuildRequires:    perl(Time::HiRes)
BuildRequires:    krb5-devel
%{?with_init_systemd:BuildRequires: systemd}

Requires:         bash
Requires:         fileutils
Requires:         grep
%if %{with common}
Requires:         %{name}-common%{?_isa} = %{sameevr}
%else
Requires:         mariadb-common%{?_isa}
%endif

%if %{with mysql_names}
Provides:         mysql = %{sameevr}
Provides:         mysql%{?_isa} = %{sameevr}
Provides:         mysql-compat-client = %{sameevr}
Provides:         mysql-compat-client%{?_isa} = %{sameevr}
%endif

# MySQL (with caps) is upstream's spelling of their own RPMs for mysql
%{?obsoleted_mysql_case_evr:Obsoletes: MySQL < %{obsoleted_mysql_case_evr}}
%{?obsoleted_mysql_evr:Obsoletes: mysql < %{obsoleted_mysql_evr}}
Conflicts:        community-mysql
Conflicts:        mariadb

# Filtering: https://fedoraproject.org/wiki/Packaging:AutoProvidesAndRequiresFiltering
%if 0%{?fedora} > 14 || 0%{?rhel} > 6
%global __requires_exclude ^perl\\((hostnames|lib::mtr|lib::v1|mtr_|My::)
%global __provides_exclude_from ^(%{_datadir}/(mysql|mysql-test)/.*|%{_libdir}/mysql/plugin/.*\\.so)$
%else
%filter_from_requires /perl(\(hostnames\|lib::mtr\|lib::v1\|mtr_\|My::\)/d
%filter_provides_in -P (%{_datadir}/(mysql|mysql-test)/.*|%{_libdir}/mysql/plugin/.*\\.so)$
%filter_setup
%endif

%description
MariaDB is a community developed branch of MySQL.
MariaDB is a multi-user, multi-threaded SQL database server.
It is a client/server implementation consisting of a server daemon (mysqld)
and many different client programs and libraries. The base package
contains the standard MariaDB/MySQL client programs and generic MySQL files.


%if %{with clibrary}
%package          libs
Summary:          The shared libraries required for MariaDB/MySQL clients
Group:            Applications/Databases
%if %{with common}
Requires:         %{name}-common%{?_isa} = %{sameevr}
%else
Requires:         mariadb-common%{?_isa}
%endif
%if %{with mysql_names}
Provides:         mysql-libs = %{sameevr}
Provides:         mysql-libs%{?_isa} = %{sameevr}
%endif
%{?obsoleted_mysql_case_evr:Obsoletes: MySQL-libs < %{obsoleted_mysql_case_evr}}
%{?obsoleted_mysql_evr:Obsoletes: mysql-libs < %{obsoleted_mysql_evr}}

%description      libs
The mariadb-libs package provides the essential shared libraries for any
MariaDB/MySQL client program or interface. You will need to install this
package to use any other MariaDB package or any clients that need to connect
to a MariaDB/MySQL server. MariaDB is a community developed branch of MySQL.
%endif


%if %{with config}
%package          config
Summary:          The config files required by server and client
Group:            Applications/Databases

%description      config
The package provides the config file my.cnf and my.cnf.d directory used by any
MariaDB or MySQL program. You will need to install this package to use any
other MariaDB or MySQL package if the config files are not provided in the
package itself.
%endif


%if %{with common}
%package          common
Summary:          The shared files required by server and client
Group:            Applications/Databases
Requires:         %{_sysconfdir}/my.cnf

%description      common
The package provides the essential shared files for any MariaDB program.
You will need to install this package to use any other MariaDB package.
%endif


%if %{with errmsg}
%package          errmsg
Summary:          The error messages files required by server and embedded
Group:            Applications/Databases
Requires:         %{name}-common%{?_isa} = %{sameevr}

%description      errmsg
The package provides error messages files for the MariaDB daemon and the
embedded server. You will need to install this package to use any of those
MariaDB packages.
%endif


%package          server
Summary:          The MariaDB server and related files
Group:            Applications/Databases

# note: no version here = %%{version}-%%{release}
Requires:         mysql%{?_isa}
%if %{with common}
Requires:         %{name}-common%{?_isa} = %{sameevr}
%else
Requires:         mariadb-common%{?_isa}
%endif
Requires:         %{_sysconfdir}/my.cnf
Requires:         %{_sysconfdir}/my.cnf.d
%if %{with errmsg}
Requires:         %{name}-errmsg%{?_isa} = %{sameevr}
%else
Requires:         mariadb-errmsg%{?_isa}
%endif
Requires:         sh-utils, net-tools
Requires:         galera >= 25.3.3
Requires(pre):    /usr/sbin/useradd
%if %{with init_systemd}
# We require this to be present for %%{_tmpfilesdir}
Requires:         systemd
# Make sure it's there when scriptlets run, too
Requires(pre):    systemd
Requires(posttrans): systemd
%{?systemd_requires: %systemd_requires}
%endif
# mysqlhotcopy needs DBI/DBD support
Requires:         perl(DBI)
Requires:         perl(DBD::mysql)
# wsrep requirements
Requires:         rsync lsof
%if %{with mysql_names}
Provides:         mysql-server = %{sameevr}
Provides:         mysql-server%{?_isa} = %{sameevr}
Provides:         mysql-compat-server = %{sameevr}
Provides:         mysql-compat-server%{?_isa} = %{sameevr}
%endif
%{?obsoleted_mysql_case_evr:Obsoletes: MySQL-server < %{obsoleted_mysql_case_evr}}
Conflicts:        community-mysql-server
Conflicts:        mariadb-server
%{?obsoleted_mysql_evr:Obsoletes: mysql-server < %{obsoleted_mysql_evr}}

%description      server
MariaDB is a multi-user, multi-threaded SQL database server. It is a
client/server implementation consisting of a server daemon (mysqld)
and many different client programs and libraries. This package contains
the MariaDB server and some accompanying files and directories.
MariaDB is a community developed branch of MySQL.


%if %{with oqgraph}
%package          oqgraph-engine
Summary:          The Open Query GRAPH engine for MariaDB
Group:            Applications/Databases
Requires:         %{name}-server%{?_isa} = %{sameevr}
# boost and Judy required for oograph
BuildRequires:    boost-devel
BuildRequires:    Judy-devel

%description      oqgraph-engine
The package provides Open Query GRAPH engine (OQGRAPH) as plugin for MariaDB
database server. OQGRAPH is a computation engine allowing hierarchies and more
complex graph structures to be handled in a relational fashion. In a nutshell,
tree structures and friend-of-a-friend style searches can now be done using
standard SQL syntax, and results joined onto other tables.
%endif


%if %{with connect}
%package          connect-engine
Summary:          The CONNECT storage engine for MariaDB
Group:            Applications/Databases
Requires:         %{name}-server%{?_isa} = %{sameevr}

%description      connect-engine
The CONNECT storage engine enables MariaDB to access external local or
remote data (MED). This is done by defining tables based on different data
types, in particular files in various formats, data extracted from other DBMS
or products (such as Excel), or data retrieved from the environment
(for example DIR, WMI, and MAC tables).
%endif


%if %{with devel}
%package          devel
Summary:          Files for development of MariaDB/MySQL applications
Group:            Applications/Databases
Requires:         %{name}-libs%{?_isa} = %{sameevr}
Requires:         openssl-devel%{?_isa}
%if %{with mysql_names}
Provides:         mysql-devel = %{sameevr}
Provides:         mysql-devel%{?_isa} = %{sameevr}
%endif
%{?obsoleted_mysql_case_evr:Obsoletes: MySQL-devel < %{obsoleted_mysql_case_evr}}
%{?obsoleted_mysql_evr:Obsoletes: mysql-devel < %{obsoleted_mysql_evr}}
Conflicts:        community-mysql-devel
Conflicts:        mariadb-devel

%description      devel
MariaDB is a multi-user, multi-threaded SQL database server. This
package contains the libraries and header files that are needed for
developing MariaDB/MySQL client applications.
MariaDB is a community developed branch of MySQL.
%endif


%if %{with embedded}
%package          embedded
Summary:          MariaDB as an embeddable library
Group:            Applications/Databases
%if %{with common}
Requires:         %{name}-common%{?_isa} = %{sameevr}
%else
Requires:         mariadb-common%{?_isa}
%endif
%if %{with errmsg}
Requires:         %{name}-errmsg%{?_isa} = %{sameevr}
%else
Requires:         mariadb-errmsg%{?_isa}
%endif
%if %{with mysql_names}
Provides:         mysql-embedded = %{sameevr}
Provides:         mysql-embedded%{?_isa} = %{sameevr}
%endif
Conflicts:        mariadb-embedded
%{?obsoleted_mysql_case_evr:Obsoletes: MySQL-embedded < %{obsoleted_mysql_case_evr}}
%{?obsoleted_mysql_evr:Obsoletes: mysql-embedded < %{obsoleted_mysql_evr}}

%description      embedded
MariaDB is a multi-user, multi-threaded SQL database server. This
package contains a version of the MariaDB server that can be embedded
into a client application instead of running as a separate process.
MariaDB is a community developed branch of MySQL.


%package          embedded-devel
Summary:          Development files for MariaDB as an embeddable library
Group:            Applications/Databases
Requires:         %{name}-embedded%{?_isa} = %{sameevr}
Requires:         %{name}-devel%{?_isa} = %{sameevr}
%if %{with mysql_names}
Provides:         mysql-embedded-devel = %{sameevr}
Provides:         mysql-embedded-devel%{?_isa} = %{sameevr}
%endif
Conflicts:        community-mysql-embedded-devel
Conflicts:        mariadb-embedded-devel
%{?obsoleted_mysql_case_evr:Obsoletes: MySQL-embedded-devel < %{obsoleted_mysql_case_evr}}
%{?obsoleted_mysql_evr:Obsoletes: mysql-embedded-devel < %{obsoleted_mysql_evr}}

%description      embedded-devel
MariaDB is a multi-user, multi-threaded SQL database server. This
package contains files needed for developing and testing with
the embedded version of the MariaDB server.
MariaDB is a community developed branch of MySQL.
%endif


%if %{with bench}
%package          bench
Summary:          MariaDB benchmark scripts and data
Group:            Applications/Databases
Requires:         %{name}%{?_isa} = %{sameevr}
%if %{with mysql_names}
Provides:         mysql-bench = %{sameevr}
Provides:         mysql-bench%{?_isa} = %{sameevr}
%endif
Conflicts:        community-mysql-bench
Conflicts:        mariadb-bench
%{?obsoleted_mysql_case_evr:Obsoletes: MySQL-bench < %{obsoleted_mysql_case_evr}}
%{?obsoleted_mysql_evr:Obsoletes: mysql-bench < %{obsoleted_mysql_evr}}

%description      bench
MariaDB is a multi-user, multi-threaded SQL database server. This
package contains benchmark scripts and data for use when benchmarking
MariaDB.
MariaDB is a community developed branch of MySQL.
%endif


%if %{with test}
%package          test
Summary:          The test suite distributed with MariaD
Group:            Applications/Databases
Requires:         %{name}%{?_isa} = %{sameevr}
%if %{with common}
Requires:         %{name}-common%{?_isa} = %{sameevr}
%else
Requires:         mariadb-common%{?_isa}
%endif
Requires:         %{name}-server%{?_isa} = %{sameevr}
Requires:         perl(Env)
Requires:         perl(Exporter)
Requires:         perl(Fcntl)
Requires:         perl(File::Temp)
Requires:         perl(Data::Dumper)
Requires:         perl(Getopt::Long)
Requires:         perl(IPC::Open3)
Requires:         perl(Socket)
Requires:         perl(Sys::Hostname)
Requires:         perl(Test::More)
Requires:         perl(Time::HiRes)
%if %{with mysql_names}
Provides:         mysql-test = %{sameevr}
Provides:         mysql-test%{?_isa} = %{sameevr}
%endif
Conflicts:        community-mysql-test
Conflicts:        mariadb-test
%{?obsoleted_mysql_case_evr:Obsoletes: MySQL-test < %{obsoleted_mysql_case_evr}}
%{?obsoleted_mysql_evr:Obsoletes: mysql-test < %{obsoleted_mysql_evr}}

%description      test
MariaDB is a multi-user, multi-threaded SQL database server. This
package contains the regression test suite distributed with
the MariaDB sources.
MariaDB is a community developed branch of MySQL.
%endif

%prep
%setup -q -n mariadb-%{version}

%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1
%patch6 -p1
%patch7 -p1
%patch8 -p1
%patch30 -p1
%patch31 -p1
%patch32 -p1
%patch33 -p1
%patch34 -p1
%patch35 -p1
%patch36 -p1

%patch99 -p1

sed -i -e 's/2.8.7/2.6.4/g' cmake/cpack_rpm.cmake

# workaround for upstream bug #56342
rm -f mysql-test/t/ssl_8k_key-master.opt

# generate a list of tests that fail, but are not disabled by upstream
cat %{SOURCE50} > mysql-test/rh-skipped-tests.list

# disable some tests failing on different architectures
%ifarch %{arm} aarch64
cat %{SOURCE51} | tee -a mysql-test/rh-skipped-tests.list
%endif

%ifarch ppc ppc64 ppc64p7 s390 s390x
cat %{SOURCE52} | tee -a mysql-test/rh-skipped-tests.list
%endif

cp %{SOURCE2} %{SOURCE3} %{SOURCE10} %{SOURCE11} %{SOURCE12} %{SOURCE13} \
   %{SOURCE14} %{SOURCE15} %{SOURCE16} %{SOURCE17} %{SOURCE18} %{SOURCE19} \
   %{SOURCE70} scripts

%build

# fail quickly and obviously if user tries to build as root
%if %runselftest
    if [ x"$(id -u)" = "x0" ]; then
        echo "mysql's regression tests fail if run as root."
        echo "If you really need to build the RPM as root, use"
        echo "--nocheck to skip the regression tests."
        exit 1
    fi
%endif

CFLAGS="%{optflags} -D_GNU_SOURCE -D_FILE_OFFSET_BITS=64 -D_LARGEFILE_SOURCE"
# force PIC mode so that we can build libmysqld.so
CFLAGS="$CFLAGS -fPIC"
# GCC 4.9 causes segfaults: https://mariadb.atlassian.net/browse/MDEV-6360
CFLAGS="$CFLAGS -fno-delete-null-pointer-checks"
# gcc seems to have some bugs on sparc as of 4.4.1, back off optimization
# submitted as bz #529298
%ifarch sparc sparcv9 sparc64
CFLAGS=`echo $CFLAGS| sed -e "s|-O2|-O1|g" `
%endif
# significant performance gains can be achieved by compiling with -O3 optimization
# rhbz#1051069
%ifarch ppc64
CFLAGS=`echo $CFLAGS| sed -e "s|-O2|-O3|g" `
%endif
CXXFLAGS="$CFLAGS"
export CFLAGS CXXFLAGS

%if 0%{?_hardened_build}
# building with PIE
LDFLAGS="$LDFLAGS -pie -Wl,-z,relro,-z,now"
export LDFLAGS
%endif

# The INSTALL_xxx macros have to be specified relative to CMAKE_INSTALL_PREFIX
# so we can't use %%{_datadir} and so forth here.
%cmake . \
         -DBUILD_CONFIG=mysql_release \
         -DFEATURE_SET="community" \
         -DINSTALL_LAYOUT=RPM \
         -DDAEMON_NAME="%{daemon_name}" \
%if 0%{?mysqld_unit:1}
         -DDAEMON_NAME_COMPAT="%{mysqld_unit}" \
%endif
         -DLOG_LOCATION="%{logfile}" \
         -DLOG_LOCATION_COMPAT="%{old_logfile}" \
         -DPID_FILE_DIR="%{_localstatedir}/run/%{daemon_name}" \
         -DPID_FILE_DIR_COMPAT="%{_localstatedir}/run/%{mysqld_unit}" \
         -DNICE_PROJECT_NAME="MariaDB" \
         -DRPM="%{?rhel:rhel%{rhel}}%{!?rhel:fedora%{fedora}}" \
         -DCMAKE_INSTALL_PREFIX="%{_prefix}" \
         -DINSTALL_SYSCONFDIR="%{_sysconfdir}" \
         -DINSTALL_SYSCONF2DIR="%{_sysconfdir}/my.cnf.d" \
         -DINSTALL_DOCDIR="share/doc/%{_pkgdocdirname}" \
         -DINSTALL_DOCREADMEDIR="share/doc/%{_pkgdocdirname}" \
         -DINSTALL_INCLUDEDIR=include/mysql \
         -DINSTALL_INFODIR=share/info \
         -DINSTALL_LIBDIR="%{_lib}/mysql" \
         -DINSTALL_MANDIR=share/man \
         -DINSTALL_MYSQLSHAREDIR=share/%{pkg_name_shared} \
         -DINSTALL_MYSQLTESTDIR=share/mysql-test \
         -DINSTALL_PLUGINDIR="%{_lib}/mysql/plugin" \
         -DINSTALL_SBINDIR=libexec \
         -DINSTALL_SCRIPTDIR=bin \
         -DINSTALL_SQLBENCHDIR=share \
         -DINSTALL_SUPPORTFILESDIR=share/%{pkg_name_shared} \
         -DMYSQL_DATADIR="%{dbdatadir}" \
         -DMYSQL_UNIX_ADDR="/var/lib/mysql/mysql.sock" \
         -DENABLED_LOCAL_INFILE=ON \
         -DENABLE_DTRACE=ON \
         -DWITH_EMBEDDED_SERVER=ON \
         -DWITH_SSL=system \
         -DWITH_ZLIB=system \
%{?with_pcre: -DWITH_PCRE=system}\
         -DWITH_JEMALLOC=no \
%{!?with_tokudb: -DWITHOUT_TOKUDB=ON}\
%{!?with_mroonga: -DWITHOUT_MROONGA=ON}\
         -DTMPDIR=/var/tmp \
%{?with_debug: -DCMAKE_BUILD_TYPE=Debug}\
         %{?_hardened_build:-DWITH_MYSQLD_LDFLAGS="-pie -Wl,-z,relro,-z,now"}

make %{?_smp_mflags} VERBOSE=1

# debuginfo extraction scripts fail to find source files in their real
# location -- satisfy them by copying these files into location, which
# is expected by scripts
for e in innobase xtradb ; do
  for f in pars0grm.y pars0lex.l ; do
    cp -p "storage/$e/pars/$f" "storage/$e/$f"
  done
done

%install
make DESTDIR=%{buildroot} install

# cmake generates some completely wacko references to -lprobes_mysql when
# building with dtrace support.  Haven't found where to shut that off,
# so resort to this blunt instrument.  While at it, let's not reference
# libmysqlclient_r anymore either.
sed -e 's/-lprobes_mysql//' -e 's/-lmysqlclient_r/-lmysqlclient/' \
  %{buildroot}%{_bindir}/mysql_config >mysql_config.tmp
cp -p -f mysql_config.tmp %{buildroot}%{_bindir}/mysql_config
chmod 755 %{buildroot}%{_bindir}/mysql_config

# multilib header support
# we only apply this to known Red Hat multilib arches, per bug #181335
unamei=$(uname -i)
%ifarch %{arm}
unamei=arm
%endif
%ifarch %{power64}
unamei=ppc64
%endif
%ifarch %{arm} aarch64 %{ix86} x86_64 ppc %{power64} %{sparc} s390 s390x
mv %{buildroot}%{_includedir}/mysql/my_config.h %{buildroot}%{_includedir}/mysql/my_config_${unamei}.h
mv %{buildroot}%{_includedir}/mysql/private/config.h %{buildroot}%{_includedir}/mysql/private/my_config_${unamei}.h
install -p -m 644 %{SOURCE4} %{buildroot}%{_includedir}/mysql/
install -p -m 644 %{SOURCE4} %{buildroot}%{_includedir}/mysql/private/config.h
mv %{buildroot}%{_bindir}/mysql_config %{buildroot}%{_bindir}/mysql_config-%{__isa_bits}
install -p -m 0755 scripts/mysql_config_multilib %{buildroot}%{_bindir}/mysql_config
%endif

# install INFO_SRC, INFO_BIN into libdir (upstream thinks these are doc files,
# but that's pretty wacko --- see also %%{name}-file-contents.patch)
install -p -m 644 Docs/INFO_SRC %{buildroot}%{_libdir}/mysql/
install -p -m 644 Docs/INFO_BIN %{buildroot}%{_libdir}/mysql/
rm -rf %{buildroot}%{_pkgdocdir}/MariaDB-Galera-server-%{version}/

mkdir -p %{buildroot}%{logfiledir}
chmod 0750 %{buildroot}%{logfiledir}
touch %{buildroot}%{logfile}
%if 0%{?old_logfile:1}
ln -s %{logfile} %{buildroot}%{old_logfile}
%endif

# current setting in my.cnf is to use /var/run/mariadb for creating pid file,
# however since my.cnf is not updated by RPM if changed, we need to create mysqld
# as well because users can have odd settings in their /etc/my.cnf
%{?mysqld_unit:mkdir -p %{buildroot}%{_localstatedir}/run/%{mysqld_unit}}
mkdir -p %{buildroot}%{_localstatedir}/run/%{daemon_name}
install -p -m 0755 -d %{buildroot}%{_localstatedir}/lib/mysql

%if %{with config}
install -D -p -m 0644 scripts/my.cnf %{buildroot}%{_sysconfdir}/my.cnf
%else
rm -f %{buildroot}%{_sysconfdir}/my.cnf.d/mysql-clients.cnf
rm -f %{buildroot}%{_sysconfdir}/my.cnf
%endif

# install systemd unit files and scripts for handling server startup
%if %{with init_systemd}
install -D -p -m 644 scripts/mysql.service %{buildroot}%{daemondir}/%{daemon_name}.service
install -D -p -m 0644 scripts/mysql.tmpfiles.d %{buildroot}%{_tmpfilesdir}/%{name}.conf
%endif

# install alternative systemd unit file for compatibility reasons
%if 0%{?mysqld_unit:1}
install -p -m 644 scripts/mysql-compat.service %{buildroot}%{_unitdir}/%{mysqld_unit}.service
mkdir -p %{buildroot}%{_unitdir}/%{daemon_name}.service.d
install -p -m 644 scripts/mysql-compat.conf %{buildroot}%{_unitdir}/%{daemon_name}.service.d/mysql-compat.conf
%endif

# install SysV init script
%if %{with init_sysv}
install -D -p -m 755 scripts/mysql.init %{buildroot}%{_initddir}/%{daemon_name}
%endif

# helper scripts for service starting
install -p -m 755 scripts/mysql-prepare-db-dir %{buildroot}%{_libexecdir}/mysql-prepare-db-dir
install -p -m 755 scripts/mysql-wait-ready %{buildroot}%{_libexecdir}/mysql-wait-ready
install -p -m 755 scripts/mysql-check-socket %{buildroot}%{_libexecdir}/mysql-check-socket
install -p -m 755 scripts/mysql-check-upgrade %{buildroot}%{_libexecdir}/mysql-check-upgrade
install -p -m 644 scripts/mysql-scripts-common %{buildroot}%{_libexecdir}/mysql-scripts-common

# Remove libmysqld.a
rm -f %{buildroot}%{_libdir}/mysql/libmysqld.a

# libmysqlclient_r is no more.  Upstream tries to replace it with symlinks
# but that really doesn't work (wrong soname in particular).  We'll keep
# just the devel libmysqlclient_r.so link, so that rebuilding without any
# source change is enough to get rid of dependency on libmysqlclient_r.
rm -f %{buildroot}%{_libdir}/mysql/libmysqlclient_r.so*
ln -s libmysqlclient.so %{buildroot}%{_libdir}/mysql/libmysqlclient_r.so

# mysql-test includes one executable that doesn't belong under /usr/share,
# so move it and provide a symlink
mv %{buildroot}%{_datadir}/mysql-test/lib/My/SafeProcess/my_safe_process %{buildroot}%{_bindir}
ln -s ../../../../../bin/my_safe_process %{buildroot}%{_datadir}/mysql-test/lib/My/SafeProcess/my_safe_process

# should move this to /etc/ ?
rm -f %{buildroot}%{_bindir}/mysql_embedded
rm -f %{buildroot}%{_libdir}/mysql/*.a
rm -f %{buildroot}%{_datadir}/%{pkg_name_shared}/binary-configure
rm -f %{buildroot}%{_datadir}/%{pkg_name_shared}/magic
rm -f %{buildroot}%{_datadir}/%{pkg_name_shared}/ndb-config-2-node.ini
rm -f %{buildroot}%{_datadir}/%{pkg_name_shared}/mysql.server
rm -f %{buildroot}%{_datadir}/%{pkg_name_shared}/mysqld_multi.server
rm -f %{buildroot}%{_mandir}/man1/mysql-stress-test.pl.1*
rm -f %{buildroot}%{_mandir}/man1/mysql-test-run.pl.1*
rm -f %{buildroot}%{_bindir}/mytop

# put logrotate script where it needs to be
mkdir -p %{buildroot}%{logrotateddir}
mv %{buildroot}%{_datadir}/%{pkg_name_shared}/mysql-log-rotate %{buildroot}%{logrotateddir}/%{daemon_name}
chmod 644 %{buildroot}%{logrotateddir}/%{daemon_name}

mkdir -p %{buildroot}%{_sysconfdir}/ld.so.conf.d
echo "%{_libdir}/mysql" > %{buildroot}%{_sysconfdir}/ld.so.conf.d/%{name}-%{_arch}.conf

# copy additional docs into build tree so %%doc will find them
install -p -m 0644 %{SOURCE5} %{basename:%{SOURCE5}}
install -p -m 0644 %{SOURCE6} %{basename:%{SOURCE6}}
install -p -m 0644 %{SOURCE7} %{basename:%{SOURCE7}}
install -p -m 0644 %{SOURCE16} %{basename:%{SOURCE16}}
install -p -m 0644 %{SOURCE71} %{basename:%{SOURCE71}}

# install galera config file
install -p -m 0644 support-files/wsrep.cnf %{buildroot}%{_sysconfdir}/my.cnf.d/galera.cnf

# install the clustercheck script
mkdir -p %{buildroot}%{_sysconfdir}/sysconfig
touch %{buildroot}%{_sysconfdir}/sysconfig/clustercheck
install -p -m 0755 scripts/clustercheck %{buildroot}%{_bindir}/clustercheck

# install the list of skipped tests to be available for user runs
install -p -m 0644 mysql-test/rh-skipped-tests.list %{buildroot}%{_datadir}/mysql-test

# remove unneeded RHEL-4 SELinux stuff
rm -rf %{buildroot}%{_datadir}/%{pkg_name_shared}/SELinux/

# remove SysV init script
rm -f %{buildroot}%{_sysconfdir}/init.d/mysql

# remove duplicate logrotate script
rm -f %{buildroot}%{_sysconfdir}/logrotate.d/mysql

# remove solaris files
rm -rf %{buildroot}%{_datadir}/%{pkg_name_shared}/solaris/

# rename the wsrep README so it corresponds with the other README names
mv Docs/README-wsrep Docs/README.wsrep

%if %{without clibrary}
rm -rf %{buildroot}%{_libdir}/mysql/libmysqlclient*.so.*
rm -rf %{buildroot}%{_sysconfdir}/ld.so.conf.d
rm -f %{buildroot}%{_sysconfdir}/my.cnf.d/client.cnf
%endif

%if %{without embedded}
rm -f %{buildroot}%{_libdir}/mysql/libmysqld.so*
rm -f %{buildroot}%{_bindir}/{mysql_client_test_embedded,mysqltest_embedded}
rm -f %{buildroot}%{_mandir}/man1/{mysql_client_test_embedded,mysqltest_embedded}.1*
%endif

%if %{without devel}
rm -f %{buildroot}%{_bindir}/mysql_config*
rm -rf %{buildroot}%{_includedir}/mysql
rm -f %{buildroot}%{_datadir}/aclocal/mysql.m4
rm -f %{buildroot}%{_libdir}/mysql/libmysqlclient*.so
rm -f %{buildroot}%{_mandir}/man1/mysql_config.1*
%endif

%if %{without client}
rm -f %{buildroot}%{_bindir}/{msql2mysql,mysql,mysql_find_rows,\
mysql_plugin,mysql_waitpid,mysqlaccess,mysqladmin,mysqlbinlog,mysqlcheck,\
mysqldump,mysqlimport,mysqlshow,mysqlslap,my_print_defaults}
rm -f %{buildroot}%{_mandir}/man1/{msql2mysql,mysql,mysql_find_rows,\
mysql_plugin,mysql_waitpid,mysqlaccess,mysqladmin,mysqlbinlog,mysqlcheck,\
mysqldump,mysqlimport,mysqlshow,mysqlslap,my_print_defaults}.1*
%endif

%if %{without connect}
rm -f %{buildroot}%{_sysconfdir}/my.cnf.d/connect.cnf
%endif

%if %{without config}
rm -f %{buildroot}%{_sysconfdir}/my.cnf
rm -f %{buildroot}%{_sysconfdir}/my.cnf.d/mysql-clients.cnf
%endif

%if %{without common}
rm -rf %{buildroot}%{_datadir}/%{pkg_name_shared}/charsets
%endif

%if %{without errmsg}
rm -f %{buildroot}%{_datadir}/%{pkg_name_shared}/errmsg-utf8.txt
rm -rf %{buildroot}%{_datadir}/%{pkg_name_shared}/{english,czech,danish,dutch,estonian,\
french,german,greek,hungarian,italian,japanese,korean,norwegian,norwegian-ny,\
polish,portuguese,romanian,russian,serbian,slovak,spanish,swedish,ukrainian}
%endif

%if %{without bench}
rm -rf %{buildroot}%{_datadir}/sql-bench
%endif

%if %{without test}
rm -f %{buildroot}%{_bindir}/{mysql_client_test,my_safe_process}
rm -rf %{buildroot}%{_datadir}/mysql-test
rm -f %{buildroot}%{_mandir}/man1/mysql_client_test.1*
%endif

%check
%if %{with test}
%if %runselftest
make test VERBOSE=1
# hack to let 32- and 64-bit tests run concurrently on same build machine
export MTR_PARALLEL=1
# builds might happen at the same host, avoid collision
export MTR_BUILD_THREAD=%{__isa_bits}

# The cmake build scripts don't provide any simple way to control the
# options for mysql-test-run, so ignore the make target and just call it
# manually.  Nonstandard options chosen are:
# --force to continue tests after a failure
# no retries please
# test SSL with --ssl
# skip tests that are listed in rh-skipped-tests.list
# avoid redundant test runs with --binlog-format=mixed
# increase timeouts to prevent unwanted failures during mass rebuilds
(
  cd mysql-test
  perl ./mysql-test-run.pl --force --retry=0 --ssl \
    --skip-test-list=rh-skipped-tests.list \
    --suite-timeout=720 --testcase-timeout=30 \
    --mysqld=--binlog-format=mixed --force-restart \
    --shutdown-timeout=60 --max-test-fail=0
  # cmake build scripts will install the var cruft if left alone :-(
  rm -rf var
)
%endif
%endif

%pre server
/usr/sbin/groupadd -g 27 -o -r mysql >/dev/null 2>&1 || :
/usr/sbin/useradd -M -N -g mysql -o -r -d %{mysqluserhome} -s /sbin/nologin \
  -c "MySQL Server" -u 27 mysql >/dev/null 2>&1 || :

%if %{with init_systemd}
# Explicitly enable mysqld if it was enabled in the beginning
# of the transaction. Otherwise mysqld is disabled always when
# replacing mysql with mariadb, because it is not recognized
# as updating, but rather as removal and install.
if /bin/systemctl is-enabled mysqld.service >/dev/null 2>&1 ; then
    touch %mysqld_enabled_flag_file >/dev/null 2>&1 || :
fi

# Since mysqld.service became a symlink to mariadb.service, turning off
# the running mysqld service doesn't work fine (BZ#1002996). As a work-around
# we explicitly stop mysqld before upgrade and start after it again.
if [ ! -L %{_unitdir}/mysqld.service ] && /bin/systemctl is-active mysqld.service &>/dev/null ; then
    touch %mysqld_running_flag_file >/dev/null 2>&1 || :
    /bin/systemctl stop mysqld.service >/dev/null 2>&1 || :
fi

%posttrans server
if [ -f %mysqld_enabled_flag_file ] ; then
    /bin/systemctl enable %{daemon_name}.service >/dev/null 2>&1 || :
    rm -f %mysqld_enabled_flag_file >/dev/null 2>&1 || :
fi
if [ -f %mysqld_running_flag_file ] ; then
    /bin/systemctl start %{daemon_name}.service >/dev/null 2>&1 || :
    rm -f %mysqld_running_flag_file >/dev/null 2>&1 || :
fi
%endif

%if %{with clibrary}
%post libs -p /sbin/ldconfig
%endif

%if %{with embedded}
%post embedded -p /sbin/ldconfig
%endif

%post server
%if %{with init_systemd}
%systemd_post %{daemon_name}.service
%endif
%if %{with init_sysv}
if [ $1 = 1 ]; then
    /sbin/chkconfig --add %{daemon_name}
fi
%endif
/bin/chmod 0755 %{_localstatedir}/lib/mysql

%preun server
%if %{with init_systemd}
%systemd_preun %{daemon_name}.service
%endif
%if %{with init_sysv}
if [ $1 = 0 ]; then
    /sbin/service %{daemon_name} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{daemon_name}
fi
%endif

%if %{with clibrary}
%postun libs -p /sbin/ldconfig
%endif

%if %{with embedded}
%postun embedded -p /sbin/ldconfig
%endif

%postun server
%if %{with init_systemd}
%systemd_postun_with_restart %{daemon_name}.service
%endif
%if %{with init_sysv}
if [ $1 -ge 1 ]; then
    /sbin/service %{daemon_name} condrestart >/dev/null 2>&1 || :
fi
%endif

%if %{with client}
%files
%{_bindir}/msql2mysql
%{_bindir}/mysql
%{_bindir}/mysql_find_rows
%{_bindir}/mysql_plugin
%{_bindir}/mysql_waitpid
%{_bindir}/mysqlaccess
%{_bindir}/mysqladmin
%{_bindir}/mysqlbinlog
%{_bindir}/mysqlcheck
%{_bindir}/mysqldump
%{_bindir}/mysqlimport
%{_bindir}/mysqlshow
%{_bindir}/mysqlslap
%{_bindir}/my_print_defaults

%{_mandir}/man1/msql2mysql.1*
%{_mandir}/man1/mysql.1*
%{_mandir}/man1/mysql_find_rows.1*
%{_mandir}/man1/mysql_plugin.1*
%{_mandir}/man1/mysql_waitpid.1*
%{_mandir}/man1/mysqlaccess.1*
%{_mandir}/man1/mysqladmin.1*
%{_mandir}/man1/mysqlbinlog.1*
%{_mandir}/man1/mysqlcheck.1*
%{_mandir}/man1/mysqldump.1*
%{_mandir}/man1/mysqlimport.1*
%{_mandir}/man1/mysqlshow.1*
%{_mandir}/man1/mysqlslap.1*
%{_mandir}/man1/my_print_defaults.1*
%endif

%if %{with clibrary}
%files libs
%dir %{_libdir}/mysql
%{_libdir}/mysql/libmysqlclient.so.*
%{_libdir}/mysql/plugin/dialog.so
%{_libdir}/mysql/plugin/mysql_clear_password.so
%{_sysconfdir}/ld.so.conf.d/*
%config(noreplace) %{_sysconfdir}/my.cnf.d/client.cnf
%endif

%if %{with config}
%files config
# although the default my.cnf contains only server settings, we put it in the
# common package because it can be used for client settings too.
%config(noreplace) %{_sysconfdir}/my.cnf
%dir %{_sysconfdir}/my.cnf.d
%config(noreplace) %{_sysconfdir}/my.cnf.d/mysql-clients.cnf
%endif

%if %{with common}
%files common
%doc README COPYING COPYING.LESSER README.mysql-license
%doc storage/innobase/COPYING.Percona storage/innobase/COPYING.Google
%dir %{_libdir}/mysql
%dir %{_datadir}/%{pkg_name_shared}
%{_datadir}/%{pkg_name_shared}/charsets
%endif

%if %{with errmsg}
%files errmsg
%{_datadir}/%{pkg_name_shared}/errmsg-utf8.txt
%{_datadir}/%{pkg_name_shared}/english
%lang(cs) %{_datadir}/%{pkg_name_shared}/czech
%lang(da) %{_datadir}/%{pkg_name_shared}/danish
%lang(nl) %{_datadir}/%{pkg_name_shared}/dutch
%lang(et) %{_datadir}/%{pkg_name_shared}/estonian
%lang(fr) %{_datadir}/%{pkg_name_shared}/french
%lang(de) %{_datadir}/%{pkg_name_shared}/german
%lang(el) %{_datadir}/%{pkg_name_shared}/greek
%lang(hu) %{_datadir}/%{pkg_name_shared}/hungarian
%lang(it) %{_datadir}/%{pkg_name_shared}/italian
%lang(ja) %{_datadir}/%{pkg_name_shared}/japanese
%lang(ko) %{_datadir}/%{pkg_name_shared}/korean
%lang(no) %{_datadir}/%{pkg_name_shared}/norwegian
%lang(no) %{_datadir}/%{pkg_name_shared}/norwegian-ny
%lang(pl) %{_datadir}/%{pkg_name_shared}/polish
%lang(pt) %{_datadir}/%{pkg_name_shared}/portuguese
%lang(ro) %{_datadir}/%{pkg_name_shared}/romanian
%lang(ru) %{_datadir}/%{pkg_name_shared}/russian
%lang(sr) %{_datadir}/%{pkg_name_shared}/serbian
%lang(sk) %{_datadir}/%{pkg_name_shared}/slovak
%lang(es) %{_datadir}/%{pkg_name_shared}/spanish
%lang(sv) %{_datadir}/%{pkg_name_shared}/swedish
%lang(uk) %{_datadir}/%{pkg_name_shared}/ukrainian
%endif

%files server
%doc README.mysql-cnf

%{_bindir}/aria_chk
%{_bindir}/aria_dump_log
%{_bindir}/aria_ftdump
%{_bindir}/aria_pack
%{_bindir}/aria_read_log
%{_bindir}/myisamchk
%{_bindir}/myisam_ftdump
%{_bindir}/myisamlog
%{_bindir}/myisampack
%{_bindir}/mysql_convert_table_format
%{_bindir}/mysql_fix_extensions
%{_bindir}/mysql_install_db
%{_bindir}/mysql_secure_installation
%{_bindir}/mysql_setpermission
%{_bindir}/mysql_tzinfo_to_sql
%{_bindir}/mysql_upgrade
%{_bindir}/mysql_zap
%{_bindir}/mysqlbug
%{_bindir}/mysqldumpslow
%{_bindir}/mysqld_multi
%{_bindir}/mysqld_safe
%{_bindir}/mysqlhotcopy
%{_bindir}/mysqltest
%{_bindir}/innochecksum
%{_bindir}/perror
%{_bindir}/replace
%{_bindir}/resolve_stack_dump
%{_bindir}/resolveip
%{_bindir}/clustercheck
%{?with_tokudb:%{_bindir}/tokuftdump}

%{_bindir}/wsrep_sst_common
%{_bindir}/wsrep_sst_mysqldump
%{_bindir}/wsrep_sst_rsync
%{_bindir}/wsrep_sst_xtrabackup
%{_bindir}/wsrep_sst_xtrabackup-v2

%config(noreplace) %{_sysconfdir}/my.cnf.d/server.cnf
%config(noreplace) %{_sysconfdir}/my.cnf.d/galera.cnf

%{?with_tokudb:%config(noreplace) %{_sysconfdir}/my.cnf.d/tokudb.cnf}
%attr(0640,root,root) %ghost %config(noreplace) %{_sysconfdir}/sysconfig/clustercheck

%{_libexecdir}/mysqld

%{_libdir}/mysql/INFO_SRC
%{_libdir}/mysql/INFO_BIN
%if %{without common}
%dir %{_datadir}/%{pkg_name_shared}
%endif

%{_libdir}/mysql/plugin
%{?with_oqgraph:%exclude %{_libdir}/mysql/plugin/ha_oqgraph.so}
%{?with_connect:%exclude %{_libdir}/mysql/plugin/ha_connect.so}
%exclude %{_libdir}/mysql/plugin/dialog.so
%exclude %{_libdir}/mysql/plugin/mysql_clear_password.so

%{_mandir}/man1/aria_chk.1.gz
%{_mandir}/man1/aria_dump_log.1.gz
%{_mandir}/man1/aria_ftdump.1.gz
%{_mandir}/man1/aria_pack.1.gz
%{_mandir}/man1/aria_read_log.1.gz
%{_mandir}/man1/myisamchk.1*
%{_mandir}/man1/myisamlog.1*
%{_mandir}/man1/myisampack.1*
%{_mandir}/man1/mysql_convert_table_format.1*
%{_mandir}/man1/myisam_ftdump.1*
%{_mandir}/man1/mysql.server.1*
%{_mandir}/man1/mysql_fix_extensions.1*
%{_mandir}/man1/mysql_install_db.1*
%{_mandir}/man1/mysql_secure_installation.1*
%{_mandir}/man1/mysql_upgrade.1*
%{_mandir}/man1/mysql_zap.1*
%{_mandir}/man1/mysqlbug.1*
%{_mandir}/man1/mysqldumpslow.1*
%{_mandir}/man1/mysqld_multi.1*
%{_mandir}/man1/mysqld_safe.1*
%{_mandir}/man1/mysqlhotcopy.1*
%{_mandir}/man1/mysql_setpermission.1*
%{_mandir}/man1/mysqltest.1*
%{_mandir}/man1/innochecksum.1*
%{_mandir}/man1/perror.1*
%{_mandir}/man1/replace.1*
%{_mandir}/man1/resolve_stack_dump.1*
%{_mandir}/man1/resolveip.1*
%{_mandir}/man1/mysql_tzinfo_to_sql.1*
%{_mandir}/man8/mysqld.8*

%{_datadir}/%{pkg_name_shared}/fill_help_tables.sql
%{_datadir}/%{pkg_name_shared}/install_spider.sql
%{_datadir}/%{pkg_name_shared}/mysql_system_tables.sql
%{_datadir}/%{pkg_name_shared}/mysql_system_tables_data.sql
%{_datadir}/%{pkg_name_shared}/mysql_test_data_timezone.sql
%{_datadir}/%{pkg_name_shared}/mysql_performance_tables.sql
%{?with_mroonga:%{_datadir}/%{pkg_name_shared}/mroonga/install.sql}
%{?with_mroonga:%{_datadir}/%{pkg_name_shared}/mroonga/uninstall.sql}
%{_datadir}/%{pkg_name_shared}/my-*.cnf
%{_datadir}/%{pkg_name_shared}/wsrep.cnf
%{_datadir}/%{pkg_name_shared}/wsrep_notify

%{?mysqld_unit:%{_unitdir}/%{mysqld_unit}.service}
%{?mysqld_unit:%{_unitdir}/%{daemon_name}.service.d/mysql-compat.conf}
%{daemondir}/%{daemon_name}*
%{_libexecdir}/mysql-prepare-db-dir
%{_libexecdir}/mysql-wait-ready
%{_libexecdir}/mysql-check-socket
%{_libexecdir}/mysql-check-upgrade
%{_libexecdir}/mysql-scripts-common

%{?with_init_systemd:%{_tmpfilesdir}/%{name}.conf}
%{?mysqld_unit:%attr(0755,mysql,mysql) %dir %{_localstatedir}/run/%{mysqld_unit}}
%attr(0755,mysql,mysql) %dir %{_localstatedir}/run/%{daemon_name}
%attr(0755,mysql,mysql) %dir %{_localstatedir}/lib/mysql
%attr(0750,mysql,mysql) %dir %{logfiledir}
%attr(0640,mysql,mysql) %config %ghost %verify(not md5 size mtime) %{logfile}
%if 0%{?old_logfile:1}
                        %config %ghost %verify(not md5 size mtime) %{old_logfile}
%endif
%config(noreplace) %{logrotateddir}/%{daemon_name}

%if %{with oqgraph}
%files oqgraph-engine
%config(noreplace) %{_sysconfdir}/my.cnf.d/oqgraph.cnf
%{_libdir}/mysql/plugin/ha_oqgraph.so
%endif

%if %{with connect}
%files connect-engine
%config(noreplace) %{_sysconfdir}/my.cnf.d/connect.cnf
%{_libdir}/mysql/plugin/ha_connect.so
%endif

%if %{with devel}
%files devel
%{_bindir}/mysql_config
%{_bindir}/mysql_config-%{__isa_bits}
%{_includedir}/mysql
%{_datadir}/aclocal/mysql.m4
%{_libdir}/mysql/libmysqlclient.so
%{_libdir}/mysql/libmysqlclient_r.so
%{_mandir}/man1/mysql_config.1*
%endif

%if %{with embedded}
%files embedded
%{_libdir}/mysql/libmysqld.so.*

%files embedded-devel
%{_libdir}/mysql/libmysqld.so
%{_bindir}/mysql_client_test_embedded
%{_bindir}/mysqltest_embedded
%{_mandir}/man1/mysql_client_test_embedded.1*
%{_mandir}/man1/mysqltest_embedded.1*
%endif

%if %{with bench}
%files bench
%{_datadir}/sql-bench
%endif

%if %{with test}
%files test
%{_bindir}/mysql_client_test
%{_bindir}/my_safe_process
%attr(-,mysql,mysql) %{_datadir}/mysql-test
%{_mandir}/man1/mysql_client_test.1*
%endif

%changelog
* Tue Oct 06 2015 Robbie Harwood <rharowod@redhat.com> - 1:10.0.17-8
- Accidentally the buildrequires

* Tue Oct 06 2015 Robbie Harwood <rharwood@redhat.com> - 1:10.0.17-7
- GSSAPI

* Fri Oct 02 2015 Robbie Harwood <rharwood@redhat.com> - 1:10.0.17-6
- Disable self-test

* Wed Apr 01 2015 Honza Horak <hhorak@redhat.com> - 1:10.0.17-3
- Fix path to files shared with mariadb

* Wed Mar 11 2015 Honza Horak <hhorak@redhat.com> - 1:10.0.17-1
- Rebase to version 10.0.17
- Rework disabled tests handling
- Fix openssl_1 test

* Sat Jan 24 2015 Honza Horak <hhorak@redhat.com> - 1:10.0.15-1
- Rebase to version 10.0.15

* Thu Dec  4 2014 Peter Robinson <pbrobinson@fedoraproject.org> 1:10.0.13-7
- Build on aarch64 now we have galera

* Mon Oct 13 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.13-6
- Move mysqlimport man page to proper package
- Disable main.key_cache test on s390
  Releated: #1149647

* Wed Oct 08 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.13-5
- Disable tests connect.part_file, connect.part_table
  and connect.updelx
  Related: #1149647

* Wed Oct 01 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.13-4
- Add with_debug option
- Add bcond_without mysql_names
  Use more correct path when deleting mysql logrotate script

* Wed Oct 01 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.13-3
- Build with system libedit
  Resolves: #1079637

* Tue Sep 30 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.13-2
- Disable vcol_supported_sql_funcs_myisam test on all arches
  Related: #1096787
- Client related libraries moved from mariadb-server to mariadb-libs
  Related: #1138843
- Move connect engine to a separate package
  Rename oqgraph engine to align with upstream packages
- Move some files to correspond with MariaDB upstream packages
  client.cnf into -libs, mysql_plugin and msql2mysql into base,
  tokuftdump and aria_* into -server, errmsg-utf8.txt into -errmsg
- Remove duplicate cnf files packaged using %%doc
- Check upgrade script added to warn about need for mysql_upgrade

* Mon Sep 08 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.13-1
- Rebase to version 10.0.13

* Fri Sep 05 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.12-8
- Install systemd service file on RHEL-7+
  Server requires any mysql package, so it should be fine with older client
- Use configured value instead of hardcoded path in mysql_install_db script
  Related: #1134328
- Use %%cmake macro

* Wed Sep 03 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.12-7
- Disable failing tests: innodb_simulate_comp_failures_small, key_cache
  rhbz#1096787

* Wed Sep 03 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.12-6
- Upgrade to 10.0.12 and use layout from mariadb's spec

* Tue Sep 02 2014 Ryan O'Hara <rohara@redhat.com> - 1:5.5.38-3
- Fix paths in mysql_install_db script
  Resolves: #1134328

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:5.5.38-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Mon Jul 28 2014 Honza Horak <hhorak@redhat.com> - 1:5.5.38-1
- Rebase to 5.5.38
  https://kb.askmonty.org/en/mariadb-5538-changelog/

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:5.5.37-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Wed Apr 30 2014 Ryan O'Hara <rohara@redhat.com> - 1:5.5.37-2
- ExclusiveArch should be same as galera
- Include wsrep_sst_xtrabackup-v2

* Wed Apr 30 2014 Ryan O'Hara <rohara@redhat.com> - 1:5.5.37-1
- Rebase to 5.5.37
  https://kb.askmonty.org/en/mariadb-5537-changelog/
  Includes fixes for: CVE-2014-2440 CVE-2014-0384 CVE-2014-2432
  CVE-2014-2431 CVE-2014-2430 CVE-2014-2436 CVE-2014-2438 CVE-2014-2419

* Mon Apr 28 2014 Ryan O'Hara <rohara@redhat.com> - 1:5.5.36-10
- Disable regression tests by default

* Wed Apr 16 2014 Ryan O'Hara <rohara@redhat.com> - 1:5.5.36-9
- Update clustercheck script to read /etc/sysconfig/clustercheck

* Fri Apr 11 2014 Ryan O'Hara <rohara@redhat.com> - 1:5.5.36-8
- Include clustercheck script

* Wed Apr 09 2014 Ryan O'Hara <rohara@redhat.com> - 1:5.5.36-7
- Only build common and server subpackages

* Tue Apr 01 2014 Ryan O'Hara <rohara@redhat.com> - 1:5.5.36-6
- Change server subpackage to require any client that provides mysql

* Mon Mar 31 2014 Ryan O'Hara <rohara@redhat.com> - 1:5.5.36-5
- Fix required galera version

* Wed Mar 26 2014 Ryan O'Hara <rohara@redhat.com> - 1:5.5.36-4
- Add defattr to all subpackages

* Wed Mar 26 2014 Ryan O'Hara <rohara@redhat.com> - 1:5.5.36-3
- Fix paths in helper scripts
- Move language files into mariadb directory

* Tue Mar 18 2014 Ryan O'Hara <rohara@redhat.com> - 1:5.5.36-2
- Intitial mariadb-galera build

* Thu Mar 06 2014 Honza Horak <hhorak@redhat.com> - 1:5.5.36-1
- Rebase to 5.5.36
  https://kb.askmonty.org/en/mariadb-5536-changelog/

* Wed Feb  5 2014 Honza Horak <hhorak@redhat.com> 1:5.5.35-3
- Do not touch the log file in post script, so it does not get wrong owner
  Resolves: #1061045

* Thu Jan 30 2014 Honza Horak <hhorak@redhat.com> 1:5.5.35-1
- Rebase to 5.5.35
  https://kb.askmonty.org/en/mariadb-5535-changelog/
  Also fixes: CVE-2014-0001, CVE-2014-0412, CVE-2014-0437, CVE-2013-5908,
  CVE-2014-0420, CVE-2014-0393, CVE-2013-5891, CVE-2014-0386, CVE-2014-0401,
  CVE-2014-0402
  Resolves: #1054043
  Resolves: #1059546

* Wed Jan  8 2014 Honza Horak <hhorak@redhat.com> 1:5.5.34-4
- Read socketfile location in mariadb-prepare-db-dir script

* Mon Jan  6 2014 Honza Horak <hhorak@redhat.com> 1:5.5.34-3
- Don't test EDH-RSA-DES-CBC-SHA cipher, it seems to be removed from openssl
  which now makes mariadb/mysql FTBFS because openssl_1 test fails
  Related: #1044565
- Check if socket file is not being used by another process at a time
  of starting the service
  Related: #1045435
- Use %%ghost directive for the log file
  Related: 1043501

* Wed Nov 27 2013 Honza Horak <hhorak@redhat.com> 1:5.5.34-2
- Fix mariadb-wait-ready script

* Fri Nov 22 2013 Honza Horak <hhorak@redhat.com> 1:5.5.34-1
- Rebase to 5.5.34

* Mon Nov  4 2013 Honza Horak <hhorak@redhat.com> 1:5.5.33a-4
- Fix spec file to be ready for backport by Oden Eriksson
  Resolves: #1026404

* Mon Nov  4 2013 Honza Horak <hhorak@redhat.com> 1:5.5.33a-3
- Add pam-devel to build-requires in order to build
  Related: #1019945
- Check if correct process is running in mysql-wait-ready script
  Related: #1026313

* Mon Oct 14 2013 Honza Horak <hhorak@redhat.com> 1:5.5.33a-2
- Turn on test suite

* Thu Oct 10 2013 Honza Horak <hhorak@redhat.com> 1:5.5.33a-1
- Rebase to 5.5.33a
  https://kb.askmonty.org/en/mariadb-5533-changelog/
  https://kb.askmonty.org/en/mariadb-5533a-changelog/
- Enable outfile_loaddata test
- Disable tokudb_innodb_xa_crash test

* Mon Sep  2 2013 Honza Horak <hhorak@redhat.com> - 1:5.5.32-12
- Re-organize my.cnf to include only generic settings
  Resolves: #1003115
- Move pid file location to /var/run/mariadb
- Make mysqld a symlink to mariadb unit file rather than the opposite way
  Related: #999589

* Thu Aug 29 2013 Honza Horak <hhorak@redhat.com> - 1:5.5.32-11
- Move log file into /var/log/mariadb/mariadb.log
- Rename logrotate script to mariadb
- Resolves: #999589

* Wed Aug 14 2013 Rex Dieter <rdieter@fedoraproject.org> 1:5.5.32-10
- fix alternatives usage

* Tue Aug 13 2013 Honza Horak <hhorak@redhat.com> - 1:5.5.32-9
- Multilib issues solved by alternatives
  Resolves: #986959

* Sat Aug 03 2013 Petr Pisar <ppisar@redhat.com> - 1:5.5.32-8
- Perl 5.18 rebuild

* Wed Jul 31 2013 Honza Horak <hhorak@redhat.com> - 1:5.5.32-7
- Do not use login shell for mysql user

* Tue Jul 30 2013 Honza Horak <hhorak@redhat.com> - 1:5.5.32-6
- Remove unneeded systemd-sysv requires
- Provide mysql-compat-server symbol
- Create mariadb.service symlink
- Fix multilib header location for arm
- Enhance documentation in the unit file
- Use scriptstub instead of links to avoid multilib conflicts
- Add condition for doc placement in F20+

* Sun Jul 28 2013 Dennis Gilmore <dennis@ausil.us> - 1:5.5.32-5
- remove "Requires(pretrans): systemd" since its not possible
- when installing mariadb and systemd at the same time. as in a new install

* Sat Jul 27 2013 Kevin Fenzi <kevin@scrye.com> 1:5.5.32-4
- Set rpm doc macro to install docs in unversioned dir

* Fri Jul 26 2013 Dennis Gilmore <dennis@ausil.us> 1:5.5.32-3
- add Requires(pre) on systemd for the server package

* Tue Jul 23 2013 Dennis Gilmore <dennis@ausil.us> 1:5.5.32-2
- replace systemd-units requires with systemd
- remove solaris files

* Fri Jul 19 2013 Honza Horak <hhorak@redhat.com> 1:5.5.32-1
- Rebase to 5.5.32
  https://kb.askmonty.org/en/mariadb-5532-changelog/
- Clean-up un-necessary systemd snippets

* Wed Jul 17 2013 Petr Pisar <ppisar@redhat.com> - 1:5.5.31-7
- Perl 5.18 rebuild

* Mon Jul  1 2013 Honza Horak <hhorak@redhat.com> 1:5.5.31-6
- Test suite params enhanced to decrease server condition influence
- Fix misleading error message when uninstalling built-in plugins
  Related: #966873

* Thu Jun 27 2013 Honza Horak <hhorak@redhat.com> 1:5.5.31-5
- Apply fixes found by Coverity static analysis tool

* Wed Jun 19 2013 Honza Horak <hhorak@redhat.com> 1:5.5.31-4
- Do not use pretrans scriptlet, which doesn't work in anaconda
  Resolves: #975348

* Fri Jun 14 2013 Honza Horak <hhorak@redhat.com> 1:5.5.31-3
- Explicitly enable mysqld if it was enabled in the beggining
  of the transaction.

* Thu Jun 13 2013 Honza Horak <hhorak@redhat.com> 1:5.5.31-2
- Apply man page fix from Jan Stanek

* Fri May 24 2013 Honza Horak <hhorak@redhat.com> 1:5.5.31-1
- Rebase to 5.5.31
  https://kb.askmonty.org/en/mariadb-5531-changelog/
- Preserve time-stamps in case of installed files
- Use /var/tmp instead of /tmp, since the later is using tmpfs,
  which can cause problems
  Resolves: #962087
- Fix test suite requirements

* Sun May  5 2013 Honza Horak <hhorak@redhat.com> 1:5.5.30-2
- Remove mytop utility, which is packaged separately
- Resolve multilib conflicts in mysql/private/config.h

* Fri Mar 22 2013 Honza Horak <hhorak@redhat.com> 1:5.5.30-1
- Rebase to 5.5.30
  https://kb.askmonty.org/en/mariadb-5530-changelog/

* Fri Mar 22 2013 Honza Horak <hhorak@redhat.com> 1:5.5.29-11
- Obsolete MySQL since it is now renamed to community-mysql
- Remove real- virtual names

* Thu Mar 21 2013 Honza Horak <hhorak@redhat.com> 1:5.5.29-10
- Adding epoch to have higher priority than other mysql implementations
  when comes to provider comparison

* Wed Mar 13 2013 Honza Horak <hhorak@redhat.com> 5.5.29-9
- Let mariadb-embedded-devel conflict with MySQL-embedded-devel
- Adjust mariadb-sortbuffer.patch to correspond with upstream patch

* Mon Mar  4 2013 Honza Horak <hhorak@redhat.com> 5.5.29-8
- Mask expected warnings about setrlimit in test suite

* Thu Feb 28 2013 Honza Horak <hhorak@redhat.com> 5.5.29-7
- Use configured prefix value instead of guessing basedir
  in mysql_config
Resolves: #916189
- Export dynamic columns and non-blocking API functions documented
  by upstream

* Wed Feb 27 2013 Honza Horak <hhorak@redhat.com> 5.5.29-6
- Fix sort_buffer_length option type

* Wed Feb 13 2013 Honza Horak <hhorak@redhat.com> 5.5.29-5
- Suppress warnings in tests and skip tests also on ppc64p7

* Tue Feb 12 2013 Honza Horak <hhorak@redhat.com> 5.5.29-4
- Suppress warning in tests on ppc
- Enable fixed index_merge_myisam test case

* Thu Feb 07 2013 Honza Horak <hhorak@redhat.com> 5.5.29-3
- Packages need to provide also %%_isa version of mysql package
- Provide own symbols with real- prefix to distinguish from mysql
  unambiguously
- Fix format for buffer size in error messages (MDEV-4156)
- Disable some tests that fail on ppc and s390
- Conflict only with real-mysql, otherwise mariadb conflicts with ourself

* Tue Feb 05 2013 Honza Horak <hhorak@redhat.com> 5.5.29-2
- Let mariadb-libs to own /etc/my.cnf.d

* Thu Jan 31 2013 Honza Horak <hhorak@redhat.com> 5.5.29-1
- Rebase to 5.5.29
  https://kb.askmonty.org/en/mariadb-5529-changelog/
- Fix inaccurate default for socket location in mysqld-wait-ready
  Resolves: #890535

* Thu Jan 31 2013 Honza Horak <hhorak@redhat.com> 5.5.28a-8
- Enable obsoleting mysql

* Wed Jan 30 2013 Honza Horak <hhorak@redhat.com> 5.5.28a-7
- Adding necessary hacks for perl dependency checking, rpm is still
  not wise enough
- Namespace sanity re-added for symbol default_charset_info

* Mon Jan 28 2013 Honza Horak <hhorak@redhat.com> 5.5.28a-6
- Removed %%{_isa} from provides/obsoletes, which doesn't allow
  proper obsoleting
- Do not obsolete mysql at the time of testing

* Thu Jan 10 2013 Honza Horak <hhorak@redhat.com> 5.5.28a-5
- Added licenses LGPLv2 and BSD
- Removed wrong usage of %%{epoch}
- Test-suite is run in %%check
- Removed perl dependency checking adjustment, rpm seems to be smart enough
- Other minor spec file fixes

* Tue Dec 18 2012 Honza Horak <hhorak@redhat.com> 5.5.28a-4
- Packaging of MariaDB based on MySQL package
