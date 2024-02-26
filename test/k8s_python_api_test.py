from kubernetes import client, config
import yaml

def apply_custom_resources(yaml_file_path):
    # Load kube config
    config.load_kube_config()

    # Open and load the YAML file
    with open(yaml_file_path, 'r') as file:
        # Load all documents from a multi-document YAML
        docs = yaml.safe_load_all(file)

        # Create an instance of the CustomObjectsApi
        api_instance = client.CustomObjectsApi()

        for doc in docs:
            # Extract necessary metadata for CustomObjectsApi
            group = 'sedna.io'  # The API group of the Custom Resource
            version = doc['apiVersion'].split('/')[-1]  # Extract version
            namespace = doc['metadata']['namespace']  # Extract namespace
            plural = 'jointmultiedgeservices'  # Plural form of the CRD, make sure it's correct

            # Attempt to create the custom resource in the specified namespace
            try:
                api_response = api_instance.create_namespaced_custom_object(
                    group=group,
                    version=version,
                    namespace=namespace,
                    plural=plural,
                    body=doc
                )
                print(f"Created {doc['kind']} named {doc['metadata']['name']} in {namespace} namespace.")
            except client.exceptions.ApiException as e:
                print(f"An error occurred: {e}")

# Path to your YAML file
yaml_file_path = '../templates/video_car_detection.yaml'

apply_custom_resources(yaml_file_path)
