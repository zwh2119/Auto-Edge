import time

from kubernetes import client, config
import yaml
from kube_helper import KubeHelper


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
            if doc is None:
                continue
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


def check_pods_running(namespace):
    # Load the kube config
    config.load_kube_config()

    # Create an instance of the CoreV1Api
    v1 = client.CoreV1Api()

    # List all pods in the specified namespace
    pods = v1.list_namespaced_pod(namespace)

    all_running = True
    for pod in pods.items:
        # Check if the pod status is not 'Running' or if any container is not ready
        if pod.status.phase != "Running" or not all([c.ready for c in pod.status.container_statuses]):
            all_running = False
            print(f"Pod {pod.metadata.name} is not fully running. Status: {pod.status.phase}")

    if all_running:
        print("All pods in the namespace are running.")
    else:
        print("Not all pods in the namespace are running.")

    return all_running


def delete_resources(namespace):
    config.load_kube_config()

    # Delete Services
    v1 = client.CoreV1Api()

    # If no specific services to delete, delete all services in the namespace
    svc_list = v1.list_namespaced_service(namespace)
    for svc in svc_list.items:
        print(f"Deleting Service: {svc.metadata.name} in namespace {namespace}")
        v1.delete_namespaced_service(name=svc.metadata.name, namespace=namespace)

    # Delete Deployments
    apps_v1 = client.AppsV1Api()
    deployments = apps_v1.list_namespaced_deployment(namespace)
    for dep in deployments.items:
        print(f"Deleting Deployment: {dep.metadata.name} in namespace {namespace}")
        apps_v1.delete_namespaced_deployment(name=dep.metadata.name, namespace=namespace)

    # Delete Custom Resources (e.g., JointMultiEdgeService)
    custom_api = client.CustomObjectsApi()
    group = 'sedna.io'
    version = 'v1alpha1'
    plural = 'jointmultiedgeservices'
    cr_list = custom_api.list_namespaced_custom_object(group=group, version=version, namespace=namespace, plural=plural)
    for cr in cr_list.get('items', []):
        print(f"Deleting Custom Resource: {cr['metadata']['name']} in namespace {namespace}")
        custom_api.delete_namespaced_custom_object(group=group, version=version, plural=plural, name=cr['metadata']['name'], namespace=namespace, body=client.V1DeleteOptions())


def get_node_info():
    config.load_kube_config()

    # Create an instance of the CoreV1Api
    v1 = client.CoreV1Api()

    # To get more detailed node information
    nodes = v1.list_node()
    for node in nodes.items:
        print(f"Node Name: {node.metadata.name}")
        print(node.status.addresses)
        print(node.status.capacity['cpu'])
        # for address in node.status.addresses:
        #     if address.type == "InternalIP":
        #         print(f"Internal IP: {address.address}")
        #     elif address.type == "Hostname":
        #         print(f"Hostname: {address.address}")

    # Assuming Metrics Server is installed and running
    api = client.CustomObjectsApi()

    # Example of fetching CPU usage for all pods in the `default` namespace
    cpu_usage = api.list_namespaced_custom_object(
        group="metrics.k8s.io",
        version="v1beta1",
        namespace="auto-edge",
        plural="pods"
    )

    for pod in cpu_usage.get('items', []):
        print(f"Pod: {pod['metadata']['name']}")
        for container in pod.get('containers', []):
            print(
                f"Container: {container['name']}, CPU: {container['usage']['cpu']}, Memory: {container['usage']['memory']}")

    group = 'metrics.k8s.io'
    version = 'v1beta1'
    plural = 'nodes'

    try:
        # Fetch the node metrics
        api_response = api.list_cluster_custom_object(group, version, plural)
        for node in api_response['items']:
            node_name = node['metadata']['name']
            cpu_usage = node['usage']['cpu']
            memory_usage = node['usage']['memory']
            print(f"Node: {node_name}, CPU Usage: {cpu_usage}, Memory Usage: {memory_usage}")
    except client.ApiException as e:
        print("Exception when calling CustomObjectsApi->list_cluster_custom_object: %s\n" % e)


def main():
    # # Path to your YAML file
    yaml_file_path = '/home/hx/zwh/Auto-Edge/templates/video_car_detection.yaml'

    KubeHelper.apply_custom_resources(yaml_file_path)
    while True:
        if KubeHelper.check_pods_running('auto-edge'):
            break
        time.sleep(0.3)

    time.sleep(2)

    # KubeHelper.delete_resources('auto-edge')

    get_node_info()


if __name__ == '__main__':
    main()
