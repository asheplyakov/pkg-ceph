#!/bin/sh
set -e
repo=/srv/data/Public/repos/ceph
dist=trusty
ceph_release=jewel
export_dir="../build-pkg-ceph-${ceph_release}-${dist}"
gpg_info_file="$HOME/.cache/gpg-agent-info"
if [ ! -d "$export_dir" ]; then mkdir -p "$export_dir"; fi

if [ -f "$gpg_info_file" ]; then
	. "$gpg_info_file"
	# so reprepro can use gpg-agent when signing Release file
	export GPG_AGENT_INFO
	export GPG_TTY=$(tty)

fi

gbp buildpackage \
        --git-ignore-new \
        --git-pristine-tar \
        --git-pristine-tar-commit \
        --git-export-dir="$export_dir" \
	--git-postexport='set -e;
                ver=`dpkg-parsechangelog -l${GBP_TMP_DIR}/debian/changelog --show-field Version` &&
		git_ver=`git --git-dir=$GBP_GIT_DIR rev-parse HEAD` &&
		(
		  echo "$git_ver";
		  echo "v${ver}";
		) > "${GBP_GIT_DIR%/.git}/src/.git_version"
		patch_dir=$GBP_TMP_DIR/debian/patches;
		( cd ${GBP_GIT_DIR%/.git} &&
		  git add src/.git_version &&
		  git commit -m "Set the embedded version string to the package version";
		)
		git --git-dir=$GBP_GIT_DIR format-patch --stdout -1 HEAD > $patch_dir/decapod_ceph_version.diff &&
		(
		  cd "${GBP_GIT_DIR%/.git}" && git reset --hard HEAD^;
		)
		if ! grep -e "^decapod_ceph_version\.diff" $patch_dir/series; then
			echo "decapod_ceph_version.diff" >> $patch_dir/series
		fi;
		' \
        --git-cleaner='git clean -dfx' \
        --git-builder="sbuild -v --dist=${dist}" \
	--git-postbuild="reprepro -Vb${repo} --ignore=wrongdistribution --ignore=missingfile include ${ceph_release}-${dist} \$GBP_CHANGES_FILE" \
	$@

reprepro -Vb${repo} export "${ceph_release}-${dist}"
