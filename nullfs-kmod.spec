%global	kmod_name nullfs

%global	debug_package %{nil}

%define __spec_install_post \
  %{__arch_install_post}\
  %{__os_install_post}\
  %{__mod_compress_install_post}

%define __mod_compress_install_post \
  if [ $kernel_version ]; then \
    find %{buildroot} -type f -name '*.ko' | xargs %{__strip} --strip-debug; \
    find %{buildroot} -type f -name '*.ko' | xargs xz; \
  fi

# Generate kernel symbols requirements:
%global _use_internal_dependency_generator 0

%{!?kversion: %global kversion %(uname -r)}

Name:           %{kmod_name}-kmod
Version:        0.17
Release:        7%{?dist}
Summary:        A virtual file system that behaves like /dev/null
License:        GPLv3+
URL:            https://github.com/abbbi/%{kmod_name}

Source0:        %{url}/archive/v%{version}.tar.gz#/nullfsvfs-%{version}.tar.gz
Patch0:         https://github.com/abbbi/nullfsvfs/commit/63661607ded4e3ee0ba35cf50e1166a2b203daeb.patch

BuildRequires:  elfutils-libelf-devel
BuildRequires:  gcc
BuildRequires:  kernel-devel
BuildRequires:  kmod
BuildRequires:  redhat-rpm-config

%if 0%{?rhel} == 7
BuildRequires:  kernel-abi-whitelists
%else
BuildRequires:  kernel-abi-stablelists
BuildRequires:  kernel-rpm-macros
%endif

%description
A virtual file system that behaves like /dev/null. It can handle regular file
operations but writing to files does not store any data. The file size is
however saved, so reading from the files behaves like reading from /dev/zero
with a fixed size.

Writing and reading is basically an NOOP, so it can be used for performance
testing with applications that require directory structures.

%package -n kmod-%{kmod_name}
Summary:    %{kmod_name} kernel module(s)

Provides:   kabi-modules = %{kversion}
Provides:   %{kmod_name}-kmod = %{?epoch:%{epoch}:}%{version}-%{release}
Requires:   module-init-tools

%description -n kmod-%{kmod_name}
This package provides the %{kmod_name} kernel module(s) built for the Linux kernel
using the family of processors.

%prep
%autosetup -p1 -n nullfsvfs-%{version}

echo "override %{kmod_name} * weak-updates/%{kmod_name}" > kmod-%{kmod_name}.conf

%build
make -C %{_usrsrc}/kernels/%{kversion} M=$PWD modules

%install
export INSTALL_MOD_PATH=%{buildroot}
export INSTALL_MOD_DIR=extra/%{kmod_name}
make -C %{_usrsrc}/kernels/%{kversion} M=$PWD modules_install

install -d %{buildroot}%{_sysconfdir}/depmod.d/
install kmod-%{kmod_name}.conf %{buildroot}%{_sysconfdir}/depmod.d/
# Remove the unrequired files.
rm -f %{buildroot}/lib/modules/%{kversion}/modules.*

%post -n kmod-%{kmod_name}
if [ -e "/boot/System.map-%{kversion}" ]; then
    /usr/sbin/depmod -aeF "/boot/System.map-%{kversion}" "%{kversion}" > /dev/null || :
fi
modules=( $(find /lib/modules/%{kversion}/extra/%{kmod_name} | grep '\.ko$') )
if [ -x "/usr/sbin/weak-modules" ]; then
    printf '%s\n' "${modules[@]}" | /usr/sbin/weak-modules --add-modules
fi

%preun -n kmod-%{kmod_name}
rpm -ql kmod-%{kmod_name}-%{version}-%{release} | grep '\.ko$' > /var/run/rpm-kmod-%{kmod_name}-modules

%postun -n kmod-%{kmod_name}
if [ -e "/boot/System.map-%{kversion}" ]; then
    /usr/sbin/depmod -aeF "/boot/System.map-%{kversion}" "%{kversion}" > /dev/null || :
fi
modules=( $(cat /var/run/rpm-kmod-%{kmod_name}-modules) )
rm /var/run/rpm-kmod-%{kmod_name}-modules
if [ -x "/usr/sbin/weak-modules" ]; then
    printf '%s\n' "${modules[@]}" | /usr/sbin/weak-modules --remove-modules
fi


%files -n kmod-%{kmod_name}
%license LICENSE
/lib/modules/%{kversion}/extra/*
%config /etc/depmod.d/kmod-%{kmod_name}.conf

%changelog
* Wed Sep 25 2024 Simone Caronni <negativo17@gmail.com> - 0.17-7
- Rebuild.

* Wed Jun 05 2024 Simone Caronni <negativo17@gmail.com> - 0.17-6
- Rebuild for latest kernel.

* Mon Jun 03 2024 Simone Caronni <negativo17@gmail.com> - 0.17-5
- Add patch for EL 9.4 kernel backports.

* Wed Apr 03 2024 Simone Caronni <negativo17@gmail.com> - 0.17-4
- Sync uname -r with kversion passed from scripts.

* Wed Apr 03 2024 Simone Caronni <negativo17@gmail.com> - 0.17-3
- Rebuild.

* Wed Nov 29 2023 Simone Caronni <negativo17@gmail.com> - 0.17-2
- Rename to nullfs.

* Mon Nov 20 2023 Simone Caronni <negativo17@gmail.com> - 0.17-1
- Update to 0.17.

* Thu May 25 2023 Simone Caronni <negativo17@gmail.com> - 0.15-2
- Rebuild for updated kernels.

* Mon May 08 2023 Simone Caronni <negativo17@gmail.com> - 0.15-1
- Update to 0.15.

* Mon Nov 21 2022 Simone Caronni <negativo17@gmail.com> - 0.13-1
- Update to 0.13.

* Thu Sep 29 2022 Simone Caronni <negativo17@gmail.com> - 0.12.1-3
- Rebuild for updated kABI.

* Wed Jul 20 2022 Simone Caronni <negativo17@gmail.com> - 0.12.1-2
- Rebuild for updated kABI.

* Fri Dec 31 2021 Simone Caronni <negativo17@gmail.com> - 0.12.1-1
- Update to 0.12.1.

* Thu Sep 23 2021 Simone Caronni <negativo17@gmail.com> - 0.10-1
- Update to 0.10.

* Wed Aug 18 2021 Simone Caronni <negativo17@gmail.com> - 0.8-2
- Simplify kernel requirements.

* Wed Aug 18 2021 Simone Caronni <negativo17@gmail.com> - 0.8-1
- Update to 0.8.
- Add missing build requirement for correctly adding kernel symbols as
  requirements.
- Strip modules.
- Compress modules with xz.
- Update description.

* Thu Jun 03 2021 Simone Caronni <negativo17@gmail.com> - 0.5-1
- Update to 0.5.

* Wed Jan 13 2021 Simone Caronni <negativo17@gmail.com> - 0.3-1
- Update to 0.3.
- Merge kmodtool script into SPEC file and remove obsolete stuff.

* Thu Dec 10 2020 Simone Caronni <negativo17@gmail.com> - 0.2-1
- First build.
