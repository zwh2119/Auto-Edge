#!/bin/bash

show_help() {
    echo "Usage: $0 -f <yaml_file> [-r <services_to_delete>]"
    echo "Delete Kubernetes resources based on the provided YAML file."
    echo ""
    echo "Options:"
    echo "  -f <yaml_file>        Specify the YAML file containing Kubernetes resources."
    echo "  -r <services_to_delete> Specify a list of services to delete (optional)."
    echo "                         If not provided, all services will be deleted."
    echo "                         Example: -r service1 service2"
    echo "  --help               Display this help message."
    exit 1
}

yaml_file=""
services_to_delete=""

while getopts ":f:r:" opt; do
    case $opt in
        f) yaml_file="$OPTARG";;
        r) shift
           services_to_delete=("$@")
           break;;
        \?) show_help;;
    esac
done

if [ -z "$yaml_file" ]; then
    show_help
fi

current_doc=""

# Function to process a document
process_document() {
    namespace=$(echo "$1" | yq eval '.metadata.namespace' -)
    deployment_name=$(echo "$1" | yq eval '.metadata.name' -)
    svc_name="$deployment_name-cloud"

    # Check if the service should be deleted
    if [ -z "$services_to_delete" ] || [[ " ${services_to_delete[@]} " == *" $deployment_name "* ]]; then
        # Perform other deletion operations as needed
        echo "Deleting resources for $deployment_name"

        # 1. Delete SVC
        kubectl delete svc "$svc_name" -n "$namespace"

        # 2. Delete Deployments
        deployments=$(kubectl get deploy -n "$namespace" -o json | jq -r --arg deployment_name "$deployment_name" '.items[] | select(.metadata.name | startswith($deployment_name)) | .metadata.name')
        for deployment in $deployments; do
            kubectl delete deploy "$deployment" -n "$namespace"
        done

        # 3. Delete Custom Resource (jointmultiedgeservice)
        kubectl delete jointmultiedgeservice "$deployment_name" -n "$namespace"

        # Add your additional deletion logic here
    fi
}

while IFS='' read -r line || [ -n "$line" ]; do
    if [[ "$line" == "---" ]]; then
        # Process the previous document
        if [ -n "$current_doc" ]; then
            process_document "$current_doc"
        fi

        # Reset the current_doc variable for the next document
        current_doc=""
    else
        # Concatenate lines to build the current document
        current_doc="$current_doc$line"$'\n'
    fi
done < "$yaml_file"

# Process the last document in case it doesn't end with ---
if [ -n "$current_doc" ]; then
    process_document "$current_doc"
fi

