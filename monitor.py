import os
import socket
import re
import argparse
import SocketServer
import subprocess
import time
import sys
import helpers

def commit_observe():
    parser = argparse.ArgumentParser()
    parser.add_argument("--forwarder-server",
                        help="forwarder ussage host:port, " \
                        "default is: localhost:8878",
                        default="localhost:8878",
                        action="store")
    parser.add_argument("repo", metavar="REPO", type=str,
                        help="path to the repo this will monitor")
    args = parser.parse_args()
    forwarder_host, forwarder_port = args.forwarder_server.split(":")

    while True:
        try:
            subprocess.check_output(["./update_repo.sh", args.repo])
        except subprocess.CalledProcessError as e:
            raise Exception ("not able to update and check the repo. " + "Reason: %s" % e.output)

        if os.path.isfile(".commit_hash"):
            try:
                response = helpers.communicate(forwarder_host, int(forwarder_port), "status")
            except socket.error as e:
                raise Exception("can't talk to forwarder server: %s" % e)
            if response == "OK":
                commit = ""
                with open(".commit_hash", "r") as f:
                    commit = f.readline()
                response = helpers.communicate(forwarder_host, int(forwarder_port), "forward:%s" % commit)

                if response != "OK":
                    raise Exception("can't forward the test: %s" % response)

                print "forwarded"

            else:
                raise Exception("can't forward the test: %s" % response)

    time.sleep(5)


if __name__="__main__":
    commit_observe()
