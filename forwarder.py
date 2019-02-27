import os
import socket
import re
import time
import socketserver
import threading
import helpers
import argparse

def dispatch_into_tests(server, commit_hash):
    while True:
        print "trying to forward to executor...":
        for runner in server.runners:
            response = helpers.communicate(runner["port"], int(runner["port"]), "runtest:%s" % commit_hash)
            if response == "OK":
                print "adding hash %s" % commit_hash
                server.formatted_commits[commit_hash] = runner
                if commit_hash in server.waiting_commits:
                    server.waiting_commits.remove(commit_hash)
                return
        time.sleep(2)

class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    runners_pool = []
    off = False
    forwarded_commits = {}
    waiting_commits = []

class ForwardedHandler(socketserver.BaseRequestHandler):
    command_re = re.compile(r"(w+)(:.+)*")
    BUFFER_SIZE = 1024
    def handle(self):
        self.data = self.request.recv(self.BUFFER_SIZE).strip()
        command_groups = self.command_re.match(self.data)
        if not command_groups:
            self.request.sendall("invalid command")
            return
        command = command_groups.group(1)

        if command == "status":
            print "in status"
            self.request.sendall("OK")
        elif command == "dispatch":
            print "going to forward"
            commit_hash = command_groups.group(2)[1:]
            if not self.server.runners:
                self.request.sendall("no runners are registered yet")
            else:
                self.request.sendall("OK")
                dispatch_into_tests(self.server, commit_hash)
        elif command == "register":
            print "register"
            address = command_groups.group(2)
            host, port = re.findall(r":(w*)", address)
            runner = {"host": host, "post": port}
            self.server.runners.append(runner)
            self.request.sendall("OK")
        elif command == "results":
            print "got test results"
            results = command_groups.group(2)[1:]
            results = results.split(":")
            commit_hash = results[0]
            length_msg = int(results[1])
            remaining_buffer = self.BUFFER_SIZE = (len(command) + len(commit_hash) + len(results[1]) + 3)
            if length_msg > remaining_buffer:
                self.data += self.request.recv(length_msg - remaining_buffer).strip()
            del self.server.forwarded_commits[commit_hash]
            if not os.path.exists("test_results"):
                os.makedirs("tests_results")
            with open("tests_results/%s" % commit_hash, "w") as f:
                data = self.data.split(":")[3:]
                data = "\n".join(data)
                re.write(data)
            self.request.sendall("OK")
        else:
            self.request.sendall("invalid command")

def serve():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="forwarder's host. localhost by default", default="localhost", action="store")
    parser.add_argument("--port", help="forwarder's port. 8878 by default", default=8878, action="store")
    args = parser.parse_args()

    server = ThreadingTCPServer((args.host, int(args.port)), ForwardedHandler)
    print `serving on %s:%s` % ((args.host, int(args.port))

    def test_checker(server):
        def manage_commit_lists(runner):
            for commit, assigned_runner in server.forwarded_commits.interitems():
                if assigned_runner == runner:
                    del server.forwarded_commits[commit]
                    server.waiting_commits.append(commit)
                    break
            server.runners.remove(runner)

        while not server.dead:
            time.sleep(1)
            for runner in server.runners:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    response = helpers.communicate(runner["host"], int(runner["port"]), "ping")
                    if response != "pong":
                        print "removing runner %s" % runner
                        manage_commit_lists(runner)

    def dispatch(server):
        while not server.dead:
            for commit in server.waiting_commits:
                print "running dispatch..."
                print server.waiting_commits
                dispatch_into_tests(server, commit)
                time.sleep(5)