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

Name:           kmod-%{kmod_name}
Version:        0.17
Release:        8%{?dist}
Summary:        A virtual file system that behaves like /dev/null
License:        GPLv3+
URL:            https://github.com/abbbi/%{kmod_name}

Source0:        %{url}/archive/v%{version}.tar.gz#/nullfsvfs-%{version}.tar.gz
%if 0%{?rhel} == 9
Patch0:         https://github.com/abbbi/nullfsvfs/commit/63661607ded4e3ee0ba35cf50e1166a2b203daeb.patch
%endif

BuildRequires:  elfutils-libelf-devel
BuildRequires:  gcc
BuildRequires:  kernel-abi-stablelists
BuildRequires:  kernel-devel
BuildRequires:  kmod
BuildRequires:  redhat-rpm-config
BuildRequires:  kernel-rpm-macros

Provides:   kabi-modules = %{kversion}
Provides:   %{kmod_name}-kmod = %{?epoch:%{epoch}:}%{version}-%{release}
Requires:   module-init-tools

%description
A virtual file system that behaves like /dev/null. It can handle regular file
operations but writing to files does not store any data. The file size is
however saved, so reading from the files behaves like reading from /dev/zero
with a fixed size.

Writing and reading is basically an NOOP, so it can be used for performance
testing with applications that require directory structures.

This package provides the %{kmod_name} kernel module(s) built for the Linux kernel
using the family of processors.

%prep
%autosetup -p1 -n nullfsvfs-%{version}

echo "override %{kmod_name} * weak-updates/%{kmod_name}" > kmod-%{kmod_name}.conf

%build
make -C %{_usrsrc}/kernels/%{kversion} M=$PWD modules

%install
export INSTALL_MOD_PATH=%{buildroot}%{_prefix}
export INSTALL_MOD_DIR=extra/%{kmod_name}
make -C %{_usrsrc}/kernels/%{kversion} M=$PWD modules_install

install -d %{buildroot}%{_sysconfdir}/depmod.d/
install kmod-%{kmod_name}.conf %{buildroot}%{_sysconfdir}/depmod.d/
# Remove the unrequired files.
rm -f %{buildroot}%{_prefix}/lib/modules/%{kversion}/modules.*

%post
if [ -e "/boot/System.map-%{kversion}" ]; then
    %{_sbindir}/depmod -aeF "/boot/System.map-%{kversion}" "%{kversion}" > /dev/null || :
fi
modules=( $(find %{_prefix}/lib/modules/%{kversion}/extra/%{kmod_name} | grep '\.ko$') )
if [ -x "%{_sbindir}/weak-modules" ]; then
    printf '%s\n' "${modules[@]}" | %{_sbindir}/weak-modules --add-modules
fi

%preun
rpm -ql kmod-%{kmod_name}-%{version}-%{release} | grep '\.ko$' > %{_var}/run/rpm-kmod-%{kmod_name}-modules

%postun
if [ -e "/boot/System.map-%{kversion}" ]; then
    %{_sbindir}/depmod -aeF "/boot/System.map-%{kversion}" "%{kversion}" > /dev/null || :
fi
modules=( $(cat %{_var}/run/rpm-kmod-%{kmod_name}-modules) )
rm %{_var}/run/rpm-kmod-%{kmod_name}-modules
if [ -x "%{_sbindir}/weak-modules" ]; then
    printf '%s\n' "${modules[@]}" | %{_sbindir}/weak-modules --remove-modules
fi


%files
%license LICENSE
%{_prefix}/lib/modules/%{kversion}/extra/*
%config %{_sysconfdir}/depmod.d/kmod-%{kmod_name}.conf

%changelog
* Wed Mar 12 2025 Simone Caronni <negativo17@gmail.com> - 0.17-8
- Rename source package from nvidia-kmod to kmod-nvidia, the former is now used
  for the akmods variant.
- Use /usr/lib/modules for installing kernel modules and not /lib/modules.
- Trim changelog.

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
