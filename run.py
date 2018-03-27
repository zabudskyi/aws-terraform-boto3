#!/usr/bin/env python3
import boto3
import socket
import requests
import datetime
import argparse
from prettytable import PrettyTable


def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--hosts', nargs='+', help='List of hosts to work with', required=True)
    args = parser.parse_args()
    return args.hosts


def ec2_init():
    # Connect to AWS with boto3
    global ec2_client
    global ec2_resource
    ec2_client = boto3.client('ec2')
    ec2_resource = boto3.resource('ec2')


def check_host(host):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    timeout_in_s = 10

    # requests.head crashes when webserver isn't up so exception has to be added
    try:
        if requests.head("http://{}".format(host), timeout=timeout_in_s).status_code == 200 and sock.connect_ex((host, 22)) == 0:
            return True
        else:
            return False
    except Exception:
        return False


def unaccessible_hosts(hosts):
    # Define stopped hosts
    unaccessible_hosts = []

    for host in hosts:
        if not check_host(host):
            unaccessible_hosts.append(host)
            print("Unaccessible host: " + host)
    return unaccessible_hosts


def ec2_instances():
    # Get ec2 instances we have
    response = ec2_client.describe_instances()
    instances = []

    if "Reservations" in response:
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                instances.append(instance)
    return instances


def create_ami(current_time, stopped_hosts, instances):
    creation_time = current_time.strftime("%Y%m%d-%H%M%S")
    # We want to have the list of instances from which AMI's were created
    created_amis_instances_ids = []
    for host in stopped_hosts:
        try:
            host_ip = socket.gethostbyname(host)
        except Exception:
            # We need this exception if new DNS records are not still valid or some mistype is in place
            print("It seems {} can't be resolved".format(host))
            continue

        # Match stopped host IP with hosts we have and get it's name and id
        for instance in instances:
            if host_ip in instance.values():
                instance_name = instance['Tags'][0]['Value']
                instance_id = instance['InstanceId']
                created_amis_instances_ids.append(instance_id)

        # Create AMI and add tag
        image_id = ec2_client.create_image(InstanceId=instance_id,
                                           Name="{}-{}".format(instance_name, creation_time))['ImageId']
        ec2_client.create_tags(Resources=[image_id],
                               Tags=[{'Key': 'descriptive_tag', 'Value': "{}-{}".format(instance_name, creation_time)}])

        # Wait until image is created
        image = ec2_resource.Image(image_id)
        image.wait_until_exists(Filters=[{'Name': 'state', 'Values': ['available']}], Owners=['self'])
        print("Image {} is created".format(image_id))
    return created_amis_instances_ids


def clean_up_amis(current_time, amis_age_days):
    images = ec2_client.describe_images(Owners=['self'])
    for image in images['Images']:
        creation_time_string = image['CreationDate']
        creation_time = datetime.datetime.strptime(creation_time_string, '%Y-%m-%dT%H:%M:%S.%fZ')
        amis_age = datetime.timedelta(days=amis_age_days)

        if current_time - creation_time > amis_age:
            ec2_resource.Image(image['ImageId']).deregister()
            print("Image {} was deregistered".format(image['Name']))


def terminate_instances(instances_ids):
    for instance_id in instances_ids:
        ec2_client.terminate_instances(InstanceIds=[instance_id])
        print("Instance {} was terminated".format(instance_id))


def list_instances(instances):
    list = PrettyTable(['Instance Name', 'Instance Id', 'Instance Type', 'AMI', 'Creation Time', 'State'])

    for instance in instances:
        if instance['State']['Name'] == 'terminated':
            state = "\033[31m{}\033[m".format(instance['State']['Name'])
        else:
            state = instance['State']['Name']

        list.add_row([instance['Tags'][0]['Value'],
                      instance['InstanceId'],
                      instance['InstanceType'],
                      instance['ImageId'],
                      instance['LaunchTime'],
                      state])
    print(list)


def start():
    # Get hosts array as script argument and get current time
    hosts = argparser()
    current_time = datetime.datetime.now()

    # Connect to AWS and get instances
    ec2_init()
    instances_we_have = ec2_instances()
    stopped_instances = unaccessible_hosts(hosts)

    # Create AMI from stopped instances
    created_amis_instances_ids = create_ami(current_time, stopped_instances, instances_we_have)

    # Terminate stopped instances
    terminate_instances(created_amis_instances_ids)

    # Clean up AMIs older then 7 days
    amis_age_days = 7
    clean_up_amis(current_time, amis_age_days)

    # List instances
    list_instances(instances_we_have)


if __name__ == '__main__':
    start()
