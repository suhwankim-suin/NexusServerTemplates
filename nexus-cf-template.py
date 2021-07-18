"""Generating CloudFormation template."""

from requests import get

from troposphere  import (
	Base64,
	ec2,
	GetAtt,
	Join,
	Output,
	Parameter,
	Ref,
	Template,
)

ApplicationPort = "3000"
NexusPort="8081"
SshPort="22"
PublicCidrIp = Join("",[
                  get("https://api.ipify.org").text,
                  "/32",
                ])

t = Template()

t.set_description("Nexus Server Instance Creation")

t.add_parameter(Parameter(
	"KeyPair",
	Description="Name of an existing EC2 KeyPair to SSH",
	Type="AWS::EC2::KeyPair::KeyName",
	ConstraintDescription="must be the name of an existing EC2 KeyPair.",
))
t.add_resource(ec2.SecurityGroup(
	"SecurityGroup",
	GroupDescription="Allow SSH and TCP/{} access".format(ApplicationPort),
	SecurityGroupIngress = [
		ec2.SecurityGroupRule (
			IpProtocol="tcp",
			FromPort=SshPort,
			ToPort=SshPort,
			CidrIp=PublicCidrIp
		),
        ec2.SecurityGroupRule (
			IpProtocol="tcp",
			FromPort=ApplicationPort,
			ToPort=ApplicationPort,
			CidrIp="0.0.0.0/0"
		),
        ec2.SecurityGroupRule (
			IpProtocol="tcp",
			FromPort=NexusPort,
			ToPort=NexusPort,
			CidrIp=PublicCidrIp
		),
	],
))
ud = Base64(Join('\n',[
    "#!/bin/bash",
    "sudo yum install --enablerepo=epel -y nodejs",
    "wget http://bit.ly/2vESNuc -O /home/ec2-user/helloworld.js",
    "wget http://bit.ly/2vVvT18 -O /etc/init/helloworld.conf",
    "start helloworld"
]))

"""AMI ==> Red Hat Enterprise Linux 8 (HVM), SSD Volume Type - ami-0bb1758bf5a69ca5c (64비트 x86) / ami-0ae6cf93168b8df72 (64비트 Arm)"""
t.add_resource(ec2.Instance(
	"instance",
    ImageId="ami-0bb1758bf5a69ca5c",
    InstanceType="t2.large",
    SecurityGroups=[Ref("SecurityGroup")],
    KeyName=Ref("KeyPair"),
    UserData=ud,
))

t.add_output(Output(
    "InstancePublicIP",
    Description="Public IP of our instance.",
    Value=GetAtt("instance","PublicIp"),
))
t.add_output(Output(
    "WebUrl",
    Description="Application endpoint",
    Value=Join("",[
        "http://",GetAtt("instance","PublicDnsName"),
        ":",ApplicationPort
    ]),
))
print(t.to_json())

