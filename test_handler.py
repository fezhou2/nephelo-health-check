# test_handler.py
# July 2015, Feng Zhou
#
# Copyright (c) 2015 by cisco Systems, Inc.
# All rights reserved.
#
import subprocess
import re
import os

def file_check(task, server, timeout):
    '''check files'''

def package_check(task, server, timeout):
    '''check files'''

def service_check(task, server, timeout):
    '''check files'''

def api_check(task, server, timeout):
    '''check files'''

def shell_check(task, server, user_input_ds, timeout):
    '''run tests for shell commands'''
    test_json = {'status': 0}

    #login to user

    session=subprocess.Popen(task['command'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res=session.communicate()
    test_json['output'] = res[0]

    #condition is match, check pattern (several, list) in command output
    if task['condition'].lower()=='match' and isinstance(task['pattern'], list):
        for my_pattern in task['pattern']:
            if not re.search(my_pattern, res[0]):
                test_json['status'] = 2

    #condition is match, check pattern in command output
    elif task['condition'].lower()=='match': 
        if not re.search(task['pattern'], res[0]):
            test_json['status'] = 2

    #condition is verify, run verification command
    elif task['condition'].lower()=='verify':
        try:
            test_json['status'] = os.system(task['verify'])
        except Exception:
            test_json['status'] = 2
            pass

    #condition is succeed, just get return code
    else:
        test_json['status'] = session.returncode

    print "result:\n {}".format(res[0])
    print "error:\n {}".format(res[1])
    print "test outcome:\n {}".format(test_json['status'])
    return test_json


def cli_check(task, server, user_input_ds, timeout):
    '''check json data task on server and append result to results(json)'''

    test_json = {'status': 0}
    task['command'] = "source "+user_input_ds['openstack_source_file']+"&& "+task['command']

    session=subprocess.Popen(task['command'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res=session.communicate()
    test_json['output'] = res[0]

    #condition is match, check pattern (several, list) in command output
    if task['condition'].lower()=='match' and isinstance(task['pattern'], list):
        for my_pattern in task['pattern']:
            if not re.search(my_pattern, res[0]):
                test_json['status'] = 2

    #condition is match, check pattern in command output
    elif task['condition'].lower()=='match': 
        if not re.search(task['pattern'], res[0]):
            test_json['status'] = 2

    #condition is verify, run verification command
    elif task['condition'].lower()=='verify':
        try:
            test_json['status'] = os.system(task['verify'])
        except Exception:
            test_json['status'] = 2
            pass

    #condition is succeed, just get return code
    else:
        test_json['status'] = session.returncode

    print "result:\n {}".format(res[0])
    print "error:\n {}".format(res[1])
    print "test outcome:\n {}".format(test_json['status'])
    return test_json

