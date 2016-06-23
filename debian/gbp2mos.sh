#!/bin/sh
set -e
# MOS packaging CI insists on keeping the source under $pkgname directory,
# and debianization files in debian. Moving around files manually is a bit
# error prone (it's easy to forget 'git add something'), hence this script.
MYDIR="${0%/*}"
cd ${MYDIR}/..

mkdir -p -m 755 ceph
git ls-files | grep -vE '^debian[/]' | xargs cp -a --parents --target-directory=ceph
git add ceph
git ls-files | grep -vE '^(debian|ceph)[/]' | xargs git rm -f --
git commit -m 'Shuffle files for MOS CI'

