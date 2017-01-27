#!/bin/sh
set -e
repo=/srv/data/Public/repos/ceph
dist=trusty
ceph_release=hammer
export_dir="../build-pkg-ceph-${ceph_release}-${dist}"
if [ ! -d "$export_dir" ]; then mkdir -p "$export_dir"; fi

gbp buildpackage \
        --git-ignore-new \
        --git-pristine-tar \
        --git-pristine-tar-commit \
        --git-export-dir="$export_dir" \
	--git-postexport='set -e;
		( git --git-dir=$GBP_GIT_DIR rev-parse HEAD &&
		  ver=`dpkg-parsechangelog -l$GBP_TMP_DIR/debian/changelog --show-field Version`;
		  echo "v${ver}";
		) > $GBP_TMP_DIR/src/.git_version;
		' \
        --git-cleaner='git clean -dfx' \
	--git-prebuild='set -e;
		cd $GBP_BUILD_DIR;
		dpkg-source --commit . decapod_ceph_version;
		' \
        --git-builder="sbuild -v --dist=${dist} --post-build-commands \"reprepro -Vb${repo} --ignore=wrongdistribution --ignore=missingfile include ${ceph_release}-${dist} %SBUILD_CHANGES\"" \
	$@

reprepro -Vb${repo} export "${ceph_release}-${dist}"
