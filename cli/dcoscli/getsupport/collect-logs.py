from subprocess import check_output
from subprocess import call
import json
import time
import datetime
import os
import tarfile

stamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H:%M:%S')
directory = '/tmp/dreamathon/logs/' + stamp

def createLogFileName(name):
	return directory + "/" + name + ".log"

def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))

if not os.path.exists(directory):
    os.makedirs(directory)
    print("creating output directory " + directory)

# master and slave logs
with open(createLogFileName("master"), "w") as outfile:
	print("getting logs from master")
	call(["dcos", "node", "log", "--lines=10000", "--master"], stdout=outfile)

a = check_output(["dcos", "node", "--json"])
b = json.loads(a.decode('utf-8'))

for i in range(0,len(b)):
	slaveId = b[i][u'id']
	print("getting logs from slaveId " + slaveId)
	with open(createLogFileName("slave_" + slaveId), "w") as outfile:
		call(["dcos", "node", "log", "--lines=10000", "--slave=" + slaveId], stdout=outfile)

# task logs
a = check_output(["dcos", "task", "--json"])
b = json.loads(a.decode('utf-8'))

for i in range(0,len(b)):
	taskId = b[i][u'id']
	print("getting logs from task " + taskId)
	with open(createLogFileName("task_" + taskId), "w") as outfile:
		call(["dcos", "task", "log", "--lines=10000", taskId], stdout=outfile)

# service logs

# may need to set the url on the docker image: "dcos config set core.dcos_url http://master.mesos"
a = check_output(["dcos", "service", "--json"])
b = json.loads(a.decode('utf-8'))

for i in range(0,len(b)):
	serviceName = b[i][u'name'] #name
	print("getting logs from service " + serviceName)
	with open(createLogFileName("service_" + serviceName), "w") as outfile:
		call(["dcos", "service", "log", "--lines=10000", serviceName], stdout=outfile)

 

# aggregation

a = make_tarfile(directory + ".tgz", directory)
print(a)
print("created " + directory + ".tgz of aggregated logs")