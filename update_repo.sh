#! /bin/bash

source helper.sh

rm -f .commit_hash

helper "repo dir not found" pushd $1 1> /dev/null
helper "can't reset git" git reset --hard HEAD

COMMIT=$(helper "can't call 'git log' on repo" git log -n1)
if [$? != 0]; then
    echo "can't call 'git log' on repo"
    exit 1
fi

HASH=`echo $COMMIT | awk '{ print $2}'`

helper "can't pull from repo" git pull

COMMIT=$(helper "can't call 'git log' on repo" git log -n1)
if [$? != 0]; then
    echo "can't call 'git log' on repo"
    exit 1
fi

NEWHASH=`echo $COMMIT | awk '{ print $2}'`

if [NEWHASH != $COMMIT]; then
    popd 1> /dev/null
    echo $NEWHASH > .commit_hash
fi