#!/bin/bash

#####################
#Desription:create VPC in AWS
#-Create VPC
#-Create a public subnet
#
#-Verfiy if user has AWS Installed , user might be using windows, linux or mac
#-Verify if AWS CLI is configured
#####################

#variables
VPC_NAME="demo-vpc"
CIDR_BLOCK="10.0.0.0/16"
subnet_cidr_block="10.0.3.0/24"
subnet_name="demo-subnet"
subnet_az="us-east-1a"

#Check if AWS CLI is installed
if ! command -v aws &> /dev/null
then
    echo "AWS CLI is not installed. Please install it and configure your credentials."
    exit 1
fi

#create VPC
vpc_id=$(aws ec2 create-vpc --cidr-block $CIDR_BLOCK --query 'Vpc.VpcId' --output text)
echo "VPC created with ID: $vpc_id"

#add tags to VPC
aws ec2 create-tags --resources $vpc_id --tags Key=Name,Value=$VPC_NAME
echo "Tag added to VPC: Name=$VPC_NAME"

#create public subnet
subnet_id=$(aws ec2 create-subnet --vpc-id $vpc_id --cidr-block $subnet_cidr_block --availability-zone $subnet_az --query 'Subnet.SubnetId' --output text)
echo "Public subnet created with ID: $subnet_id"

#add tags to subnet
aws ec2 create-tags --resources $subnet_id --tags Key=Name,Value=$subnet_name
echo "Tag added to subnet: Name=$subnet_name"

#end of script
