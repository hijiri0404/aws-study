#!/bin/bash

# AWS Transit Gateway Infrastructure Deployment Script
# This script deploys the CloudFormation stack for VPC-A, VPC-B, VPC-C with Transit Gateway

set -e

STACK_NAME="transit-gateway-vpc-stack"
TEMPLATE_FILE="aws-transit-gateway-infra.yaml"
KEY_PAIR_NAME="my-key-pair"
REGION="us-east-1"

echo "=== AWS Transit Gateway Infrastructure Deployment ==="
echo "Stack Name: $STACK_NAME"
echo "Template: $TEMPLATE_FILE"
echo "Key Pair: $KEY_PAIR_NAME"
echo "Region: $REGION"
echo

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Check if template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "Error: Template file '$TEMPLATE_FILE' not found."
    exit 1
fi

# Validate the CloudFormation template
echo "Validating CloudFormation template..."
aws cloudformation validate-template --template-body file://$TEMPLATE_FILE --region $REGION
if [ $? -eq 0 ]; then
    echo "✓ Template validation successful"
else
    echo "✗ Template validation failed"
    exit 1
fi

# Check if the stack already exists
echo "Checking if stack exists..."
if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION &> /dev/null; then
    echo "Stack '$STACK_NAME' already exists. Updating..."
    
    # Update the stack
    aws cloudformation update-stack \
        --stack-name $STACK_NAME \
        --template-body file://$TEMPLATE_FILE \
        --parameters ParameterKey=KeyPairName,ParameterValue=$KEY_PAIR_NAME \
        --region $REGION \
        --capabilities CAPABILITY_IAM
    
    echo "Waiting for stack update to complete..."
    aws cloudformation wait stack-update-complete --stack-name $STACK_NAME --region $REGION
    
    if [ $? -eq 0 ]; then
        echo "✓ Stack update completed successfully"
    else
        echo "✗ Stack update failed"
        exit 1
    fi
else
    echo "Creating new stack..."
    
    # Create the stack
    aws cloudformation create-stack \
        --stack-name $STACK_NAME \
        --template-body file://$TEMPLATE_FILE \
        --parameters ParameterKey=KeyPairName,ParameterValue=$KEY_PAIR_NAME \
        --region $REGION \
        --capabilities CAPABILITY_IAM
    
    echo "Waiting for stack creation to complete..."
    aws cloudformation wait stack-create-complete --stack-name $STACK_NAME --region $REGION
    
    if [ $? -eq 0 ]; then
        echo "✓ Stack creation completed successfully"
    else
        echo "✗ Stack creation failed"
        exit 1
    fi
fi

echo
echo "=== Stack Outputs ==="
aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs' --output table

echo
echo "=== Stack Resources ==="
aws cloudformation list-stack-resources --stack-name $STACK_NAME --region $REGION --query 'StackResourceSummaries[*].[ResourceType,LogicalResourceId,ResourceStatus]' --output table

echo
echo "=== Deployment Complete ==="
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo
echo "Next steps:"
echo "1. Wait for all resources to be fully operational"
echo "2. Use the ping test script to verify connectivity"
echo "3. Run: ./test-ping-connectivity.sh"