#!/bin/sh
set -e
repo=/srv/data/Public/repos/ceph
dist=xenial
ceph_release=jewel
export_dir="../build-pkg-ceph-${ceph_release}-${dist}"
if [ ! -d "$export_dir" ]; then mkdir -p "$export_dir"; fi

exec gbp buildpackage \
        --git-ignore-new \
        --git-pristine-tar \
        --git-pristine-tar-commit \
        --git-export-dir="$export_dir" \
        --git-cleaner='git clean -dfx' \
        --git-builder="sbuild -v --dist=${dist} --post-build-commands \"reprepro -Vb${repo} --ignore=wrongdistribution --ignore=missingfile include ${ceph_release}-${dist} %SBUILD_CHANGES\"" \
	$@
