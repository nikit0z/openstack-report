#!/usr/bin/env python

import urllib2
import os
import json
from netaddr import iter_iprange


def report():
    auth_data = authorize()
    active_vms = get_all_active_vms(auth_data)
    print('Total number of vms is: %s') % len(active_vms.keys())
    active_projects = get_active_projects(active_vms)
    print('Total number of active projects is: %s') % len(active_projects)
    resources = get_resources_usage(auth_data)
    print('Total number of computes: %s') % resources['count']
    print('VCPUs used/total: %s/%s') % (resources['vcpus_used'], resources['vcpus'])
    print('RAM (Mb) used/total: %s/%s') % (resources['memory_mb_used'], resources['memory_mb'])
    print('Storage (Gb) used/total: %s/%s') % (resources['local_gb_used'], resources['local_gb'])
    floatingips = get_floatingip_usage(auth_data)
    print('Floating IPs used/total: %s/%s') % (floatingips['used'], floatingips['total'])


def authorize():
    auth_data = {}
    # need to replace v2 with v3 if possible here
    url = endpoints['keystone'] + '/tokens'
    try:
        admin_tenant = os.environ['OS_TENANT_NAME']
        admin_user = os.environ['OS_USERNAME']
        admin_pass = os.environ['OS_PASSWORD']
    except:
        raise
    params = {
        "auth": {
            "tenantName": admin_tenant,
            "passwordCredentials": {
                "username": admin_user,
                "password": admin_pass
            }
        }
    }
    responce = api_request(url, params, None)
    auth_data['token'] = responce['access']['token']['id']
    auth_data['tenant_id'] = responce['access']['token']['tenant']['id']	
    return auth_data


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


def get_all_active_vms(auth_data):
    active_vms = {}
    url = endpoints['compute'] + '/' + auth_data['tenant_id'] + '/servers/detail?all_tenants=1'
    for server in api_request(url, None, {"X-Auth-Token": auth_data['token']})['servers']:
        active_vms[server['id']] = {'name': server['name'], 'project_id': server['tenant_id']}
    return active_vms


def get_active_projects(active_vms):
    active_projects = []
    for vm in active_vms.keys():
        project_id = active_vms[vm]['project_id']
        if project_id not in active_projects:
                active_projects.append(project_id)
    return active_projects


def get_resources_usage(auth_data):
    url = endpoints['compute'] + '/' + auth_data['tenant_id'] + '/os-hypervisors/statistics'
    return api_request(url, None, {"X-Auth-Token": auth_data['token']})['hypervisor_statistics']


def get_floatingip_usage(auth_data):
    floatingips = {}
    url = endpoints['neutron'] + '/floatingips'
    responce = api_request(url, None, {"X-Auth-Token": auth_data['token']})['floatingips']
    floatingip_net_id = responce[0]['floating_network_id']
    floatingips['total'] = get_floatingip_total(floatingip_net_id, auth_data)
    floatingips['used'] = len(responce)
    return floatingips


def get_floatingip_total(floatingip_net_id, auth_data):
    url = endpoints['neutron'] + '/subnets?network_id=' + floatingip_net_id
    responce = api_request(url, None, {"X-Auth-Token": auth_data['token']})['subnets'][0]['allocation_pools'][0]
    return len(list(iter_iprange(responce['start'], responce['end'])))


if __name__ == '__main__':
    endpoints = {}
    try:
        endpoints['keystone'] = os.environ['KEYSTONE_ENDPOINT']
        endpoints['compute'] = os.environ['COMPUTE_ENDPOINT']
        endpoints['neutron'] = os.environ['NEUTRON_ENDPOINT']
    except:
        raise
    report()
