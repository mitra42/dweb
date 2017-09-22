#!/bin/bash

PIPS=py-dateutil
cd /usr/local/mitra42_dweb
pip install --disable-pip-version-check -U $PIPS
[ -d cache_http ] || mkdir cache_http
if git commit -a -m "Local changes"
then
	git push
fi
git checkout deployed # Will run server branch
git pull
git merge origin/deployable
if git commit -a -m "merged
then
	git push
fi
echo "Starting Server "
cd dweb
if ps -f | grep ServerHTTP | grep -v grep 
then
	echo "You need to kill that process above first"
else
	python -m ServerHTTP &
	ps -f | grep ServerHTTP | grep -v grep
fi



