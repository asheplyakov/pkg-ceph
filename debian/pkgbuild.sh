#!/bin/sh
set -e
repo=/srv/data/Public/repos/ceph
dist=precise
ceph_release=hammer
build_chroot='mos60'
export_dir="../build-pkg-ceph-${ceph_release}-${dist}"
if [ ! -d "$export_dir" ]; then mkdir -p "$export_dir"; fi

exec gbp buildpackage \
        --git-ignore-new \
        --git-pristine-tar \
        --git-pristine-tar-commit \
        --git-export-dir="$export_dir" \
        --git-cleaner='git clean -dfx' \
        --git-builder="sbuild -v --dist=${build_chroot} --post-build-commands \"reprepro -Vb${repo} --ignore=wrongdistribution --ignore=missingfile include ${ceph_release}-${dist} %SBUILD_CHANGES\"" \
	$@
