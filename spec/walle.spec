Name: walle
Version: 0.1.8
Release: beta
Summary: Avatar Installer
Vendor:Taobao, Inc
Group: Taobao/Avatar
Packager: luyan
Url: https://code.google.com/p/taobao-avatar/
License: GPL
BuildArchitectures: noarch
%description
Avatar Installer
%prep
%pre
%post
%preun
%postun
%files
/usr/local/bin/walle
%changelog
* Thu Dec 2 2010 BuPing <buping@taobao.com> 0.1.8-beta
- Avatar Installer - add chrgp to conf file
* Thu Dec 2 2010 BuPing <buping@taobao.com> 0.1.7-beta
- Avatar Installer - auto determine colo; rpmfiles process, add -z option to switch process method, add sudo -u patch to persist the owner
* Wed Nov 10 2010 BuPing <buping@taobao.com> 0.1.6-beta
- Avatar Installer - add -t option to answer no to patch command
* Thu Nov 4 2010 BuPing <buping@taobao.com> 0.1.5-alpha
- Avatar Installer - use rpm -ivh $all_location to install packages, use rpm -V to check exist package
* Mon Nov 1 2010 BuPing <buping@taobao.com> 0.1.4-alpha
- Avatar Installer - use rpmfind web cgi as rpm file locator, merge base and cust needed to install list
* Tue Sep 14 2010 BuPing <buping@taobao.com> 0.1.3-alpha
- Avatar Installer - fix openssl base64 longname auto add \n bug
* Thu Sep 9 2010 BuPing <buping@taobao.com> 0.1.2-alpha
- Avatar Installer - add --nodeps --justdb to rpm remove action
- add -N option to skip specified diff files
- make temp files clean move to /tmp/.avatar
- add -A option to match RHEL release package
- use openssl base64 instead of base64 due to rhel 4 no base64 command
* Thu Sep 2 2010 BuPing <buping@taobao.com> 0.1.1-alpha
- Avatar Installer - fix diff save method, echo will cause format problem, fix diff content parser
* Tue Aug 31 2010 BuPing <buping@taobao.com> 0.1.0-alpha
- Avatar Installer - Wall-E internal test release
