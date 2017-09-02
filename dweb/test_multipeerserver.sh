#!/usr/bin/env bash
#TODO-BACKPORT - review this file

ip="localhost"
for port in {4244..4250}
do
    echo "Trying port $port"
    python ./TransportDist_Peer.py $ip $port &
done
