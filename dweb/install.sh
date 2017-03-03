#!/bin/bash
# env
# set -x

fPIPUPGRADE=true
fMAKECHANGE=true
fVERBOSE=true

PIPINSTALLS="py-dateutil pycrypto sha3 requests"
#OTHER MODULES USE OFTEN : pytz CherryPy lxml xlwt phonenumbers Py-dateutil requests-mock passlib
PIPEGREP=`echo $PIPINSTALLS | sed -e 's/ /|/g'`
DIRS="../cache ../cache_http"
#GROUP="wheel"  # Define if want all checkAndCreate to use group

if ${fPIPUPGRADE}
then
	if ! which gcc >/dev/null
	then
		echo "GCC NOT PRESENT, MOST LIKELY WILL FAIL TO INSTALL pycrypto"
	fi
	pip install ${PIPINSTALLS} -U | grep -v 'already up-to-date'
	# If previous line fails, uncomment this one and edit appropriately
	#pip install cherrypy --upgrade --ignore-installed six
	#pip install xslt -U # This doesnt seem to exist any more, there was a note about requiring it, but maybe not needed
fi
${fVERBOSE} && pip list --format=columns | egrep ${PIPEGREP}

checkAndCreate() {
    # Check for existance of diretory $1,
    # if doesnt exist then create and make g+rw and group=luminutes
    # make sure all directories and files in it are also g+w and luminutes
    if [ ! -d "$1" ]
    then
        if ${fMAKECHANGE}
        then
            ${fVERBOSE} && echo "Making $1"
            mkdir "$1"
            if [ -n "${GROUP}" ]
            then
                echo "GROUPING"
                chgrp "${GROUP}" "$1"
                chmod g+rw "$1"
            fi
        else
            echo "Need to make $1, with group ${GROUP} and perms g+w"
        fi
    else
    	true
        #${fVERBOSE} && echo -e "$1 exists"
    fi
    if [ -d "$1" ]
    then
        if ${fMAKECHANGE}
        then
            #echo "Fixing perms if needed"
            if [ -n "${GROUP:=}" ]
            then
                echo "GROUPING"
                sudo chgrp -R "${GROUP}" $1
                sudo chmod -R g+rw $1
            fi
	else
		# List bad ones if not making change
        	find $1 ! -group "${GROUP}" -o ! -perm -g=w -ls
        fi
    fi
}

for i in $DIRS
do
    checkAndCreate $i
done
