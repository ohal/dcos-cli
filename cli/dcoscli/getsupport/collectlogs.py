from subprocess import check_output
from subprocess import call
import json
import time
import datetime
import os
import tarfile

from dcos import util


logger = util.get_logger(__name__)

STAMP = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H:%M:%S')

LOG_DIR = os.path.join('/tmp', 'dreamathon', 'logs', STAMP)


def make_path(path):
    print("creating directory: {}".format(path))
    if not os.path.exists(path):
        os.makedirs(path)


def log_filename(name):
    return os.path.join(LOG_DIR, name) + '.log'


def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def _collect_master_logs(max_lines):
    # master and slave logs
    with open(log_filename("master"), "w") as outfile:
        print("getting logs from master")
        call(["dcos", "node", "log",
              "--lines={}".format(max_lines),
              "--master"],
             stdout=outfile)


def _collect_node_logs(max_lines):
    nodes_json = check_output(["dcos", "node", "--json"])
    nodes = json.loads(nodes_json.decode('utf-8'))

    for node in nodes:
        slave_id = node['id']
        print("getting logs from node : {}".format(slave_id))
        with open(log_filename('slave_{}'.format(slave_id)), "w") as outfile:
            call(["dcos", "node", "log",
                  "--lines={}".format(max_lines),
                  "--slave=" + slave_id],
                 stdout=outfile)


def _collect_task_logs(max_lines):
    # task logs
    tasks_json = check_output(["dcos", "task", "--json"])
    tasks = json.loads(tasks_json.decode('utf-8'))

    for task in tasks:
        task_id = task['id']
        print("getting logs from task: {} ".format(task_id))
        with open(log_filename('task_{}'.format(task_id)), "w") as outfile:
            call(["dcos", "task", "log",
                  "--lines={}".format(max_lines),
                  task_id],
                 stdout=outfile)


def _collect_service_logs(max_lines):
    # service logs

    # may need to set the url on the docker image: "dcos config set core.dcos_url http://master.mesos"
    service_json = check_output(["dcos", "service", "--json"])
    services = json.loads(service_json.decode('utf-8'))

    for service in services:
        service_name = service['name']
        print("getting logs from service {} ".format(service_name))
        with open(log_filename("service_{}".format(service_name)), "w") as outfile:
            call(["dcos", "service", "log",
                  "--lines={}".format(max_lines),
                  service_name],
                 stdout=outfile)


def _collect_logs(dest, max_lines):

    make_path(LOG_DIR)
    make_path(dest)

    # aggregation
    collectors = (_collect_master_logs,
                  _collect_node_logs,
                  _collect_task_logs,
                  _collect_service_logs
                 )
    for collector in collectors:
        try:
            collector(max_lines)
        except Exception as e:
            logger.exception(e)
            print('{} raised exception {}'.format(collector.__name__, e))

    tar_file = os.path.join(dest, 'logs.tgz')
    make_tarfile(tar_file, LOG_DIR)
    print("created aggregated logs {}".format(tar_file))


def _run_across_node():
    nodes_json = check_output(["dcos", "node", "--json"])
    nodes = json.loads(nodes_json.decode('utf-8'))

    for node in nodes:
        slave_id = node['id']
        print("Executing commands on node {}".format(slave_id))
        #with open(log_filename('slave_{}'.format(slave_id)), "w") as outfile:
        print('dcos node ssh --slave={} "uptime"'.format(slave_id))
