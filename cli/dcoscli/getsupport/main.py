"""Prepare/request support for DCOS troubleshooting

Usage:
    dcos get-support --info
    dcos get-support collect-logs --dest=<path> [--max-lines=<count>]
    dcos get-support ship-logs  --source=<path> --url=<url>
    dcos get-support create-tunnel --host=<host> --listen-on=<port> --user=<user> --passwd=<passwd>

Options:
    -h, --help       Show this screen
    --info           Show a short description of this subcommand
    --version        Show version
    --max-lines=N    Maximum N log lines to suck out [default: 100]

"""
import os

import requests

import dcoscli
import docopt
from dcos import (cmds,
                  emitting,
                  http,
                  subcommand,
                  util)
from dcos.errors import DCOSException

from . import collectlogs

emitter = emitting.FlatEmitter()
logger = util.get_logger(__name__)


def main():
    try:
        return _main()
    except DCOSException as e:
        emitter.publish(e)
        return 1


def _main():
    util.configure_process_from_environ()

    args = docopt.docopt(
        __doc__,
        version='dcos-config version {}'.format(dcoscli.version))

    http.silence_requests_warnings()

    return cmds.execute(_cmds(), args)


def _collect_logs(dest, max_lines):
    print('Collect cluster logs to {}'.format(dest))
    collectlogs._collect_logs(dest, max_lines)


def _ship_logs(source, url):
    print('ship logs to {} from {}'.format(url, source))

    content_length = os.path.getsize(source)

    headers = {
        'Content-Encoding': 'gzip',
        'X-Sumo-Name': 'DCOS {}'.format(source),
        'Content-length': content_length,
    }

    resp = requests.post(url, data=open(source, 'rb'), headers=headers)
    print('Response from {0} for {1}: {2.status_code} {2.text}'.
                     format(url, source, resp))
    if not str(resp.status_code).startswith('20'):
        raise DCOSException('Upload to {} for {} failed: {}'.format(
            url, source, resp.text))
    else:
        print('{} uploaded successfully'.format(source))


def _create_tunnel(host, listen_on, user, passwd):
    print('create tunnel to {}, on {}, auth - {}/{}'.format(host, listen_on, user, passwd))


def _cmds():
    """
    :returns: all the supported commands
    :rtype: list of dcos.cmds.Command
    """

    return [
        cmds.Command(
            hierarchy=['get-support', 'collect-logs'],
            arg_keys=['--dest', '--max-lines'],
            function=_collect_logs),

        cmds.Command(
            hierarchy=['get-support', 'ship-logs'],
            arg_keys=['--source', '--url'],
            function=_ship_logs),

        cmds.Command(
            hierarchy=['get-support', 'create-tunnel'],
            arg_keys=['--host', '--user', '--passwd', '--listen-on'],
            function=_create_tunnel),

        cmds.Command(
            hierarchy=['get-support'],
            arg_keys=['--info'],
            function=_info),
    ]


def _info(info):
    """
    :param info: Whether to output a description of this subcommand
    :type info: boolean
    :returns: process status
    :rtype: int
    """

    emitter.publish(__doc__.split('\n')[0])
    return 0
