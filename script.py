#!/usr/bin/env python3
import boto3
import socket
import requests
import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--hosts', nargs='+', help='List of hosts to work with', required=True)
args = parser.parse_args()

def check_host(host):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # requests.head crashes when webserver isn't up so exception has to be added
    try:
        if requests.head("http://{}".format(host), timeout=4).status_code != 200:
            return False
        elif sock.connect_ex((host,22)) != 0:
            return False
        else:
            return True
    except Exception:
        return False

# Define stopped hosts
stopped_hosts = []

for host in args.hosts:
    if not check_host(host):
        stopped_hosts.append(host)
        print("Stopped host: " + host)


# Connect to AWS with boto3
ec2 = boto3.client('ec2')
ec2_resource = boto3.resource('ec2')

# Get ec2 instances we have
response = ec2.describe_instances()
instances = []

for reservation in response["Reservations"]:
    for instance in reservation["Instances"]:
        instances.append(instance)

# Create AMI of the stopped ec2 instances
current_time = datetime.datetime.now()

for host in stopped_hosts:
    try:
        host_ip = socket.gethostbyname(host)
    except Exception:
        # We need this exception if new DNS records are not still valid or some mistype is in place
        print("It seems {} can't be resolved".format(host))
        continue

    # Match stopped host IP with hosts we have and get it's name and id
    for instance in instances :
       if host_ip in instance.values():
           instance_name = instance['Tags'][0]['Value']
           instance_id = instance['InstanceId']

    # Create AMI and add tag
    image_id = ec2.create_image(InstanceId=instance_id,  Name="{}-{}".format(instance_name, current_time.strftime("%Y%m%d-%H%M%S")))['ImageId']
    ec2.create_tags(Resources=[image_id], Tags=[{'Key': 'descriptive_tag', 'Value': "{}-{}".format(instance_name, current_time.strftime("%Y%m%d-%H%M%S"))}])

    # Wait until image is created
    image = ec2_resource.Image(image_id)
    image.wait_until_exists(Filters=[{'Name': 'state', 'Values': ['available']}], Owners=['self'])
    print("Image {} is created".format(image_id))

    # Terminate stopped instance
    ec2.terminate_instances(InstanceIds=[instance_id])
    print("Instance {}({}) was terminated".format(instance_name, host))

# Clean up AMIs older then 7 days
response = ec2.describe_images(Owners=['self'])

for image in response['Images']:
    creation_time_string = image['CreationDate']
    creation_time = datetime.datetime.strptime(creation_time_string, '%Y-%m-%dT%H:%M:%S.%fZ')
    one_week = datetime.timedelta(hours=4)

    if current_time - creation_time > one_week:
        ec2_resource.Image(image['ImageId']).deregister()
        print("Image {} was deregistered".format(image['Name']))

# List instances
print("{:<15} {:<20} {:<14} {:<13} {:<25} {}".format('Instance Name', 'Instance Id', 'Instance Type', 'AMI', 'Creation Time', 'State'))

for instance in instances:
    if instance['State']['Name'] == 'terminated':
        state = "\033[31m{}\033[m".format(instance['State']['Name'])
    else:
        state = instance['State']['Name']

    print("{:<15} {:<20} {:<14} {:<13} {} {}".format(instance['Tags'][0]['Value'], instance['InstanceId'], instance['InstanceType'], instance['ImageId'], instance['LaunchTime'], state))
