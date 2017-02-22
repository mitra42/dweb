#!/bin/bash
# env
# set -x

fPIPUPGRADE=true
fMAKECHANGE=true
fVERBOSE=true

PIPINSTALLS="py-dateutil pycrypto"
#OTHER MODULES USE OFTEN : pytz CherryPy lxml xlwt py-dateutil phonenumbers Py-dateutil requests-mock passlib pycrypto"
PIPEGREP='py-dateutil|pycrypto'

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
