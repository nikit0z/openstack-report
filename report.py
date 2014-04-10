#!/usr/bin/env python

import urllib2
import os
import json


def report():
    token = authorize()
    active_vms = get_all_active_vms(token)
    active_projects = get_active_projects(active_vms)
    print('Total number of active projects is: %s') % len(active_projects)
    print('Total number of vms is: %s') % len(active_vms.keys())
    resources = get_resources_usage(token)
    print('Total number of computes: %s') % resources['count']
    print('VCPUs used/total: %s/%s') % (resources['vcpus_used'], resources['vcpus'])
    print('RAM (Mb) used/total: %s/%s') % (resources['memory_mb_used'], resources['memory_mb'])
    print('Storage (Gb) used/total: %s/%s') % (resources['local_gb_used'], resources['local_gb'])


def authorize():
    # add check of variables
    # need to replace v2 with v3 if possible here
    url = os.environ['KEYSTONE_ENDPOINT'] + '/tokens'
    params = {
        "auth": {
            "tenantName": "admin",
            "passwordCredentials": {
                "username": "admin",
                "password": "admin"
            }
        }
    }
    return api_request(url, params, None)['access']['token']['id']


def api_request(url, params, headers):
    if params:
        request = urllib2.Request(url, json.dumps(params))
    else:
        request = urllib2.Request(url)
    request.add_header("Content-Type", "application/json")
    if headers:
        for header in headers.keys():
                request.add_header(header, headers[header])
    response = urllib2.urlopen(request)
    return json.load(response)


def get_all_active_vms(token):
    # remove hardcode
    active_vms = {}
    url = os.environ['COMPUTE_ENDPOINT'] + '/1445d1b184b1402982db31d4b4756796/servers/detail?all_tenants=1'
    for server in api_request(url, None, {"X-Auth-Token": token})['servers']:
        active_vms[server['id']] = {'name': server['name'], 'project_id': server['tenant_id']}
    return active_vms


def get_active_projects(active_vms):
    active_projects = []
    for vm in active_vms.keys():
        project_id = active_vms[vm]['project_id']
        if project_id not in active_projects:
                active_projects.append(project_id)
    return active_projects


def get_resources_usage(token):
    # remove hardcode
    url = os.environ['COMPUTE_ENDPOINT'] + '/1445d1b184b1402982db31d4b4756796/os-hypervisors/statistics'
    return api_request(url, None, {"X-Auth-Token": token})['hypervisor_statistics']


if __name__ == '__main__':
    report()
