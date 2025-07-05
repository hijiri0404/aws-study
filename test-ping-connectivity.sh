#!/bin/bash

# AWS Transit Gateway Ping Connectivity Test Script
# This script tests connectivity between EC2 instances in VPC-A and VPC-C through Transit Gateway

set -e

STACK_NAME="transit-gateway-vpc-stack"
REGION="us-east-1"
KEY_FILE="$HOME/.ssh/my-key-pair.pem"

echo "=== AWS Transit Gateway Ping Connectivity Test ==="
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Check if stack exists
if ! aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION &> /dev/null; then
    echo "Error: Stack '$STACK_NAME' not found. Please deploy the stack first."
    exit 1
fi

# Get stack outputs
echo "Getting stack outputs..."
OUTPUTS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs')

# Extract IP addresses and instance IDs
EC2_A_IP=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="EC2InstanceAPrivateIP") | .OutputValue')
EC2_C_IP=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="EC2InstanceCPrivateIP") | .OutputValue')
EC2_A_ID=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="EC2InstanceAInstanceId") | .OutputValue')
EC2_C_ID=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="EC2InstanceCInstanceId") | .OutputValue')

echo "EC2 Instance A (VPC-A) - IP: $EC2_A_IP, ID: $EC2_A_ID"
echo "EC2 Instance C (VPC-C) - IP: $EC2_C_IP, ID: $EC2_C_ID"
echo

# Check if instances are running
echo "Checking instance status..."
INSTANCE_A_STATE=$(aws ec2 describe-instances --instance-ids $EC2_A_ID --region $REGION --query 'Reservations[0].Instances[0].State.Name' --output text)
INSTANCE_C_STATE=$(aws ec2 describe-instances --instance-ids $EC2_C_ID --region $REGION --query 'Reservations[0].Instances[0].State.Name' --output text)

echo "Instance A State: $INSTANCE_A_STATE"
echo "Instance C State: $INSTANCE_C_STATE"

if [ "$INSTANCE_A_STATE" != "running" ] || [ "$INSTANCE_C_STATE" != "running" ]; then
    echo "Error: One or both instances are not running. Please wait for instances to be in 'running' state."
    exit 1
fi

# Function to test connectivity using AWS Systems Manager Session Manager
test_connectivity() {
    local source_instance=$1
    local target_ip=$2
    local source_name=$3
    local target_name=$4
    
    echo "Testing connectivity from $source_name to $target_name..."
    
    # Create a temporary script for ping test
    cat > /tmp/ping_test.sh << EOF
#!/bin/bash
echo "Pinging $target_ip from $source_name..."
ping -c 4 $target_ip
if [ \$? -eq 0 ]; then
    echo "✓ Ping successful from $source_name to $target_name"
else
    echo "✗ Ping failed from $source_name to $target_name"
fi
EOF
    
    # Execute the ping test using SSM
    echo "Executing ping test via AWS Systems Manager..."
    COMMAND_ID=$(aws ssm send-command \
        --instance-ids $source_instance \
        --document-name "AWS-RunShellScript" \
        --parameters 'commands=["ping -c 4 '$target_ip'"]' \
        --region $REGION \
        --query 'Command.CommandId' \
        --output text)
    
    echo "Command ID: $COMMAND_ID"
    echo "Waiting for command to complete..."
    
    # Wait for command to complete
    sleep 10
    
    # Get command result
    COMMAND_OUTPUT=$(aws ssm get-command-invocation \
        --command-id $COMMAND_ID \
        --instance-id $source_instance \
        --region $REGION \
        --query 'StandardOutputContent' \
        --output text)
    
    echo "Command output:"
    echo "$COMMAND_OUTPUT"
    echo
    
    # Check if ping was successful
    if echo "$COMMAND_OUTPUT" | grep -q "0% packet loss"; then
        echo "✓ Ping successful from $source_name to $target_name"
        return 0
    else
        echo "✗ Ping failed from $source_name to $target_name"
        return 1
    fi
}

# Alternative method using Session Manager for direct connection
test_connectivity_direct() {
    local source_instance=$1
    local target_ip=$2
    local source_name=$3
    local target_name=$4
    
    echo "=== Testing connectivity from $source_name to $target_name ==="
    echo "Source Instance: $source_instance"
    echo "Target IP: $target_ip"
    echo
    
    # Check if Session Manager plugin is available
    if ! command -v session-manager-plugin &> /dev/null; then
        echo "Warning: Session Manager plugin not found. Using SSM send-command instead."
        test_connectivity $source_instance $target_ip $source_name $target_name
        return $?
    fi
    
    echo "Starting Session Manager session to test connectivity..."
    echo "You can manually run: ping -c 4 $target_ip"
    echo "Or use the automated test below:"
    echo
    
    # Use automated test
    test_connectivity $source_instance $target_ip $source_name $target_name
    return $?
}

# Test connectivity from A to C
echo "=== Testing Connectivity ==="
test_connectivity_direct $EC2_A_ID $EC2_C_IP "VPC-A" "VPC-C"
A_TO_C_RESULT=$?

echo
echo "----------------------------------------"
echo

# Test connectivity from C to A
test_connectivity_direct $EC2_C_ID $EC2_A_IP "VPC-C" "VPC-A"
C_TO_A_RESULT=$?

echo
echo "=== Test Summary ==="
if [ $A_TO_C_RESULT -eq 0 ]; then
    echo "✓ VPC-A to VPC-C connectivity: SUCCESS"
else
    echo "✗ VPC-A to VPC-C connectivity: FAILED"
fi

if [ $C_TO_A_RESULT -eq 0 ]; then
    echo "✓ VPC-C to VPC-A connectivity: SUCCESS"
else
    echo "✗ VPC-C to VPC-A connectivity: FAILED"
fi

echo
echo "=== Transit Gateway Route Tables ==="
TGW_ID=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="TransitGatewayId") | .OutputValue')
echo "Transit Gateway ID: $TGW_ID"

# Get Transit Gateway route tables
aws ec2 describe-transit-gateway-route-tables --filters "Name=transit-gateway-id,Values=$TGW_ID" --region $REGION --query 'TransitGatewayRouteTables[*].[TransitGatewayRouteTableId,State]' --output table

echo
echo "=== Manual Testing Instructions ==="
echo "If automated tests fail, you can manually test using:"
echo "1. Connect to EC2 Instance A:"
echo "   aws ssm start-session --target $EC2_A_ID --region $REGION"
echo "   Then run: ping $EC2_C_IP"
echo
echo "2. Connect to EC2 Instance C:"
echo "   aws ssm start-session --target $EC2_C_ID --region $REGION"
echo "   Then run: ping $EC2_A_IP"
echo
echo "Note: Make sure AWS Systems Manager Session Manager plugin is installed"
echo "Download from: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html"