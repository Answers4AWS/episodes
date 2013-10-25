#!/usr/bin/python

from troposphere import *
import troposphere.ec2 as ec2
import troposphere.elasticloadbalancing as elb
import troposphere.autoscaling as auto

t = Template()
t.add_description('Episode 4 example of user-data and cloud-init')

# Parameters
keypair = t.add_parameter(Parameter(
    'KeyPair',
    Description = 'Name of the keypair to use for SSH access',
    Type = 'String',
))
env = t.add_parameter(Parameter(
    'Environment',
    Description = 'Name of this environment',
    Type = 'String',
    Default = 'Production'
))
role = t.add_parameter(Parameter(
    'Role',
    Description = 'The role this server should be',
    Type = 'String',
    Default = 'Web'
))

# ELB
elb = t.add_resource(elb.LoadBalancer(
    'MyElasticLoadBalancer',
    AvailabilityZones = GetAZs(''),
    Listeners = [
        elb.Listener(
            LoadBalancerPort = '80',
            InstancePort = '80',
            Protocol = 'HTTP',
        ),
    ],
    HealthCheck = elb.HealthCheck(
        Target = 'HTTP:80/',
        HealthyThreshold = '3',
        UnhealthyThreshold = '5',
        Interval = '30',
        Timeout = '5',
    )
))

# Create a security group
sg = t.add_resource(ec2.SecurityGroup('MySecurityGroup'))
sg.GroupDescription = 'Allow access to MyInstance'
sg.SecurityGroupIngress = [
    ec2.SecurityGroupRule(
        IpProtocol = 'tcp',
        FromPort = '22',
        ToPort = '22',
        CidrIp = '0.0.0.0/0'
    ),
    ec2.SecurityGroupRule(
        IpProtocol = 'tcp',
        FromPort = '80',
        ToPort = '80',
        SourceSecurityGroupOwnerId = GetAtt(elb, 'SourceSecurityGroup.OwnerAlias'),
        SourceSecurityGroupName = GetAtt(elb, 'SourceSecurityGroup.GroupName')
    )
]


# Launch config
launch_config = t.add_resource(auto.LaunchConfiguration('MyLaunchConfig',
    ImageId = 'ami-ef277b86',
    InstanceType  = 't1.micro',
    KeyName = Ref(keypair),
    SecurityGroups = [Ref(sg)],
    UserData = Base64(Join('\n', [
        '#!/bin/bash',
        'apt-get update',
        'apt-get upgrade -y',
        'apt-get install apache2 -y',
        'echo "<html><body><h1>Welcome</h1>" > /var/www/index.html',
        Join('', ['echo "<h2>Environment: ', Ref(env), '</h2>" >> /var/www/index.html']),
        Join('', ['echo "<h2>Role: ', Ref(role), '</h2>" >> /var/www/index.html']),
        'echo "</body></html>" >> /var/www/index.html'
    ]))
))

# Autoscaling Group
asg = t.add_resource(auto.AutoScalingGroup('MyASG',
    AvailabilityZones = GetAZs(''),
    Cooldown = 120,
    LaunchConfigurationName = Ref(launch_config),
    LoadBalancerNames = [Ref(elb)],
    MaxSize = '1',
    MinSize = '1',
    Tags = [
        {'Key': 'Name',
        'Value': 'Episode 4',
        'PropagateAtLaunch': 'true'}
    ]
))

# Add output of ELB URL
t.add_output(Output(
    'URL',
    Description = 'URL of the sample website',
    Value = Join('', ['http://', GetAtt(elb, 'DNSName')])
))

# Print template
print(t.to_json())


# Create new CloudFormation Stack from template
from boto import cloudformation
try:
    conn = cloudformation.connect_to_region('us-east-1')
    id = conn.create_stack(
        'Episode4', 
        template_body=t.to_json(), 
        parameters=[('KeyPair', 'episode4')]
    )
    print 'Created ' + id
except Exception, e:
    print e
    print e.message