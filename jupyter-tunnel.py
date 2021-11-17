#!/usr/bin/env python
"""Script to run jupyter notebook remotely. 
It automatically finds an available port, sshs to the server, making ssh tunnel, calls jupyter notebook.

Please copy to your ~/bin and edit to have your preferred host and port as defaults
"""

import sys
import argparse
import subprocess
import re
import os

__author__ = 'Apuã Paquola'


def get_ssh_user_args(user):
    if user is not None:
        ssh_user_args = ['-l',
                         user]
    else:
        ssh_user_args = []

    return ssh_user_args


def used_ports_iter(host, ssh_port, user):
    """ iterates through output of local and remote ss -tnl command and gets local tcp ports that are being listened to """

    local_command = ['ss', '-tln']
    remote_command = ['ssh'] + get_ssh_user_args(user) + ['-p', str(ssh_port), host, 'ss -tln']

    for command in [local_command, remote_command]:
        with subprocess.Popen(command, stdout=subprocess.PIPE) as p:
            for line in p.stdout:
                l = line.decode().rstrip()
                m = re.search("^LISTEN\s+\S+\s+\S+\s+\S+:(\d+)\s", l)
                if m and m.group(1) is not None:
                    yield int(m.group(1))

                
def get_available_port(default_tunnel_port, host, ssh_port, user):
    """ gets first unused port """
    used_ports = set(used_ports_iter(host, ssh_port, user))
    i = default_tunnel_port
    while i in used_ports:
        i += 1
    return i


def jupyter_command(directory, tunnel_port):
    return """cd '%s'; jupyter lab --no-browser --port=%d""" \
        %(directory, tunnel_port)




def run_remote_jupyter(host, ssh_port, directory, user, tunnel_port):

    with subprocess.Popen(['ssh'] + get_ssh_user_args(user) +
                          ['-p',
                           str(ssh_port),
                           '-t',
                           '-L',
                           'localhost:%d:localhost:%d' % (tunnel_port, tunnel_port),
                           host,
                           jupyter_command(directory, tunnel_port)],
                          stdout=subprocess.PIPE) as p:
        url_found = False
        for line in p.stdout:
            l = line.decode()
            if not url_found:
                m = re.search('(http://localhost:\S+)', l)
                if m is not None:
                    subprocess.Popen(["firefox",
                                      "--private-window",
                                      m.group(1)],
                                     stdin=subprocess.DEVNULL,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
                    url_found = True
            print(line.decode(), end='')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='myhost')
    parser.add_argument('--dir', default=os.getcwd())
    parser.add_argument('--user', default=None)
    parser.add_argument('--default-tunnel-port', type=int, default=8888)
    parser.add_argument('-p', '--ssh-port', type=int, default=22)
    args=parser.parse_args()

    tunnel_port = get_available_port(args.default_tunnel_port, args.host, args.ssh_port, args.user)
    run_remote_jupyter(args.host, args.ssh_port, args.dir, args.user, tunnel_port)

                       
if __name__ == '__main__':
    main()
