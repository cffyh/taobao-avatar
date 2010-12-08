Name: avatar
Version: 0.1.7
Release: beta
Summary: Avatar Fetcher
Vendor:Taobao, Inc
Group: Taobao/Avatar
Packager: luyan
Url: https://code.google.com/p/taobao-avatar/
License: GPL
BuildArchitectures: noarch
%description
Avatar Fetcher
%prep
%pre
%post
%preun
%postun
%files
/usr/local/bin/avatar
%changelog
* Tue Nov 16 2010 BuPing <buping@taobao.com> 0.1.7-beta
- Avatar Fetcher - fix diff tmpdir bug, will cause base64 decode error, fix mkdir exists prompt
* Tue Nov 9 2010 BuPing <buping@taobao.com> 0.1.6-beta
- Avatar Fetcher - fix repeat download rpm bug, fix tmp files process nasty action
* Fri Nov 5 2010 BuPing <buping@taobao.com> 0.1.5-alpha
- Avatar Fetcher - do not snap walle and avatar package
* Thu Nov 1 2010 BuPing <buping@taobao.com> 0.1.4-alpha
- Avatar Fetcher - add --nomode to rpmverify
* Mon Nov 1 2010 BuPing <buping@taobao.com> 0.1.3-alpha
- Avatar Fetcher - add --nomtime to rpmverify
* Wed Sep 8 2010 BuPing <buping@taobao.com> 0.1.2-alpha
- Avatar Fetcher - add diff judgment, only text file will generate patch
* Thu Sep 2 2010 BuPing <buping@taobao.com> 0.1.1-alpha
- Avatar Fetcher - fix locate rpm bug, add release parameter
* Tue Aug 31 2010 BuPing <buping@taobao.com> 0.1.0-alpha
- Avatar Fetcher - Avatar internal test release
