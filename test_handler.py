# test_handler.py
# July 2015, Feng Zhou
#
# Copyright (c) 2015 by cisco Systems, Inc.
# All rights reserved.
#
import subprocess
import re
import os

def file_check(task, server, test_json, timeout):
    '''check files'''
    test_json['status'] = 0
    test_json['output'] = ""
    missing_files = set([])
    bad_files = set([])

    #login to server

    if 'files' in task.keys():
        files_to_check = task['files'] if isinstance(task['files'], list) else [ task['files'] ]


    #verify each file
    for file in files_to_check:
        if re.search("exist", task['condition'].lower()):
            if not os.path.exists(file):
                test_json['status'] = 1
                missing_files.add(file)

        elif task['condition'].lower() == "match":
            patterns = task['pattern'] if isinstance(task['pattern'], list) else [ task['pattern'] ]
            for my_pattern in patterns:
                if os.system("grep " + my_pattern + " " + file)>0:
                    test_json['status'] = 1
                    bad_files.add(file)

    #report errors
    if len(missing_files)>0:
        test_json['output'] += "The following files are missing: " + ', '.join(missing_files)
    if len(bad_files)>0:
        test_json['output'] += "The following files are bad: " + ', '.join(bad_files)

    print "output: {}".format(test_json['output'])
    print "status: {}".format(test_json['status'])
    return test_json['status']

def package_check(task, server, os_type, test_json, timeout):
    '''check files'''
    test_json['status'] = 0
    missing_packages = []

    #login to server

    #build package list
    if 'rpm-packages' in task.keys() and os_type=='redhat':
        check_cmd = 'rpm -qa'
        packages_to_check = task['rpm-packages'] if isinstance(task['rpm-packages'], list) else [ task['rpm-packages'] ]

    elif 'apt-packages' in task.keys() and os_type=='ubuntu':
        check_cmd = 'dpkg -l'
        packages_to_check = task['apt-packages'] if isinstance(task['apt-packages'], list) else [ task['apt-packages'] ]

    #run package listing command
    res=subprocess.Popen(check_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    #verify each package
    for pkg in packages_to_check:
        #print "Verifying package is installed: {}".format(pkg)
        if not re.search(pkg, res[0]):
            test_json['status'] += 1
            missing_packages.append(pkg)

    test_json['output'] = "The following packages are missing: " + ', '.join(missing_packages)
    print "output: {}".format(test_json['output'])
    print "status: {}".format(test_json['status'])
    return test_json['status']

def service_check(task, server, timeout):
    '''check files'''

def api_check(task, server, timeout):
    '''check files'''

def cli_check(task, server, test_json, user_input_ds, timeout):
    '''check json data task on server and append result to results(json)'''
    test_json['status'] = 0
    print "running command: {}".format(task['command'])

    #login to user
    task['command'] = "source "+user_input_ds['openstack_source_file']+"&& "+task['command']

    session=subprocess.Popen(task['command'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res=session.communicate()
    test_json['output'] = res[0]

    #condition is verify, run verification command
    if task['condition'].lower()=='verify':
        print "verifying command: {}".format(task['verify'])
        task['verify'] = "source "+user_input_ds['openstack_source_file']+"&& "+task['verify']
        res=subprocess.Popen(task['verify'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    #empty line - failed
    if res[0]=='':
        test_json['status'] = 1
  
    else:
        patterns = task['pattern'] if isinstance(task['pattern'], list) else [task['pattern']]
        for my_pattern in patterns:
            if not re.search(my_pattern, res[0]):
                test_json['status'] = 1

    print "\nresult:\n{}".format(res[0])
    print "error:\n{}".format(res[1])
    print "status: {}".format(test_json['status'])
    return test_json['status']

