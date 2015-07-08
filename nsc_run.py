#!/usr/bin/env python
'''
	Merge JSON and metadata files for CTCM deployment.
'''
from argparse import ArgumentParser
import re
import json
from pprint import pprint
import os
import subprocess
from shutil import copy as copy_file
from test_handler import cli_check,package_check,file_check

_DEFAULT_TEST_TIMEOUT=300
_DEFAULT_TEST_RESULT_DIR = "./test_results_json"
_DEFAULT_TEST_INPUT_DIR = "./test_input_data"
OS_TYPE ='redhat'

user_input_ds={}

def read_user_input(answer_file):
    '''read user input from answer file, define test components/servers + auth info'''
    f = open(answer_file, "r")
    for item in f.readlines() :
        fields = item.split(":")
        fields[0].replace(" ","")
        fields[1].replace(" ","")
        user_input_ds[fields[0]] = fields[1].strip()
     
def get_json_content(json_file):
    '''read in json data, also determine context and component of test'''
    print "reading file {}".format(json_file)
    jdata={}
    with open(json_file, "r") as json_data:
        jdata = json.load(json_data)
    json_data.close()

    json_file_path=json_file.split("/")[1:]
    jdata["context"]="/".join(json_file_path)
    if not "component" in jdata.keys():
        jdata["component"]=json_file[0]
    print "context: {}  component: {}".format(jdata["context"], jdata["component"])
    return jdata
   
def read_test_data(test_data_ds, test_folder_name=_DEFAULT_TEST_INPUT_DIR):
    '''load all test .json files from test_folder_name to test_data_ds as big list'''
    if 'test_input_folder' in user_input_ds.keys():
        test_folder_name = user_input_ds['test_input_folder']
    allfiles = os.popen("find " + test_folder_name + " -type f -size +0 ").read().split()
    pprint(allfiles)
    for f in allfiles:
        jdata = get_json_content(f)
        test_data_ds.append(jdata)

def get_server_list(environment):
    '''Get the list of servers to login for enviroment'''
    servers=user_input_ds[environment]

    if re.search(',', servers):
        server_list=re.split(',',servers)
    else:
        server_list=[servers]

    return server_list

def run_openstack_cleanup(cleanupscript="./scripts/delete_openstack_objs.sh"):
    #run openstack_cleanup
    os.system("source "+user_input_ds['openstack_source_file']+"&& "+cleanupscript +" 2>&1 >/dev/null")


def checktask(task, server, results, timeout):
    '''generic checker - check json data task on server and decide the actual test to run'''
    print "\n==============================================================="
    out = {"name": task["name"], "type": task["type"], "server": server, "severity": task["severity"]}

    print "running check:  {},  type: {}".format(task["name"], task["type"])

    if task["type"].lower()=='shell' or task["type"].lower()=='cli':
        cli_check(task, server, out, user_input_ds, timeout)
    elif task["type"].lower()=='package':
        package_check(task, server, OS_TYPE, out, timeout)
    elif task["type"].lower()=='file':
        file_check(task, server, out, timeout)

    results.append(out)
    
    return out['status']

def execute_test(json_in, timeout):
    '''execute test based on json_in data, dump results into json_out'''

    json_out={'context': json_in['context'], 'results': []}
    server_list = get_server_list(json_in['environment'])

    '''execute each test, return status and append test results'''
    for task in json_in['tests']:
        for server in server_list:
            '''return status is the biggest of each test status, ok=0, warn=1, crit=2'''
            try:
                checktask(task, server, json_out['results'], timeout)
            except Exception:
                pass

    ''' get result data and write output json file'''
    write_test_results(json_out) 

    return json_out

def sort_tests(test_ds, by_component=1, by_environment=0):
    '''sort tests either by component or by environment so we can execute in sequence'''
    if by_component:
        sorted(test_ds, key=lambda test:test["component"])
    elif by_environment: 
        sorted(test_ds, key=lambda test:test["environment"])
    else:
        sorted(test_ds)

def valid_target(t_target, user_input_target):
    '''user_input_target is comma deliminated list of components/environments to check'''
    '''verify if t_target (test) is in one of them'''
    user_input_target.replace(" ", "")

    if re.search(',', user_input_target):
        u_targets=re.split(',',user_input_target)
    else:
        u_targets=[user_input_target]

    for ut in u_targets:
        if isinstance(t_target, list):    #t_target is a list
            for tt in t_target:
                tt.replace(" ", "")
                if tt.lower()==ut.lower() or tt.lower()=="all" or ut.lower()=="all":
                    return 1
        else:
            t_target.replace(" ", "")     #t_target is a string
            if t_target.lower()==ut.lower() or t_target.lower()=="all" or ut.lower()=="all":
                return 1

    return 0

def select_tests(test_data_ds):
    '''based on the components/servers user has chosen, select tests we need to run'''
    actual_tests_ds = []
    selected_tests = 0
    for t in test_data_ds:
        print "working on test {}".format(t['context'])
        if valid_target(t['component'],user_input_ds['component']):
            if valid_target(t['environment'], user_input_ds['environment']):
                actual_tests_ds.append(t)
                selected_tests += 1
                print "Chosen: {} for component {} environment {}".format(selected_tests, t['component'], t['environment'])
    print "All tests selected: {}".format(selected_tests)
    sort_tests(actual_tests_ds)
    #pprint(actual_tests_ds)
    return actual_tests_ds
    
def write_test_results(outdata):
    '''write output json into a file for test'''

    if 'test_output_folder' in user_input_ds.keys():
        outdir = user_input_ds['test_output_folder']
    else:
        outdir = _DEFAULT_TEST_RESULT_DIR

    filename = outdir+"/"+outdata['context']

    with open(filename, 'w') as outfile:
        json.dump(outdata, outfile, separators=(',', ': '), sort_keys=True, indent=4)
    outfile.close() 

def setup_openstack_auth():
    '''setup opentack loing by reading source file'''
    '''ensure we are not running as admin user'''
    if not 'openstack_source_file' in user_input_ds.keys():
        exit("This software can not run without openstack auth file")
    else:
        command = "grep -i name=admin "+user_input_ds['openstack_source_file']+" |grep -v ^\# |wc -l"
        text=subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout.read()
        if int(text)>0:
            exit("This software can not run with admin openstack tenant/user")

def setup_ssh_auth(user, password):
    '''setup ssh auth account info'''

def check_os_type():
    '''find out if we are redhat on ubuntu Linux'''

    text=subprocess.Popen('cat /proc/version*', shell=True, stdout=subprocess.PIPE).stdout.read()
    if re.search("Red Hat", text):
        OS_TYPE ='redhat'
    elif re.search("Ubuntu", text):
        OS_TYPE ='ubuntu'

    print "the OS type is {}".format(OS_TYPE)

def test_scheduler(tests_ds, test_timeout=_DEFAULT_TEST_TIMEOUT, nproc = 1):
    '''execute each test, keep going until finished all'''
    '''future improvement: launch tests in parallel with nproc at a time'''

    if 'test_timeout' in user_input_ds.keys():
        test_timeout=user_input_ds['test_timeout']

    ''' figure out our OS (redhat or ubuntu)'''
    check_os_type()
    ''' setup openstack CLI auth'''
    setup_openstack_auth()
    ''' setup ssh user auth info'''
    setup_ssh_auth(user_input_ds['ssh_user'], user_input_ds['ssh_password'])

    out_data_ds = []

    print "\nCleaning up openstack tenant environment\n"

    run_openstack_cleanup() 

    for test in tests_ds:
        ''' now run the test'''
        try:
            out_data_ds.append(execute_test(test, test_timeout))  
        except Exception:
            pass

    run_openstack_cleanup() 

    return out_data_ds

def print_summary_report(output_test_ds):
    '''print out stats summary of all finishe tests'''


def main():
    '''Usage: %prog [options] custom_json_file directory_for_deploy'''
    aparser = ArgumentParser(description=main.__doc__)
    aparser.add_argument(
        '--nproc',
        help='number of jobs to send in parallel, default=1'
    )
    aparser.add_argument(
        'answer_file',
        help='name of the user input answer file',
    )
    aparser.set_defaults(nproc=1)
    parsed = vars(aparser.parse_args())

    test_data_ds=[]
    my_real_tests=[]
    out_test_ds=[]

    '''read input data and define tests to run'''
    read_user_input(parsed['answer_file'])
    read_test_data(test_data_ds)
  
    my_real_tests = select_tests(test_data_ds)
    
    '''run the tests'''
    out_data_ds = test_scheduler(my_real_tests)
    print_summary_report(out_test_ds)

if __name__ == '__main__':
    main()

