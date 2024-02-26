from kubernetes import client, config
import yaml


class KubeHelper:

    @staticmethod
    def apply_custom_resources(yaml_file_path):
        config.load_kube_config()

        with open(yaml_file_path, 'r') as file:
            docs = yaml.safe_load_all(file)
            api_instance = client.CustomObjectsApi()

            for doc in docs:
                group = 'sedna.io'  # The API group of the Custom Resource
                version = doc['apiVersion'].split('/')[-1]  # Extract version
                namespace = doc['metadata']['namespace']  # Extract namespace
                plural = 'jointmultiedgeservices'  # Plural form of the CRD, make sure it's correct

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
                    return False
            return True

    @staticmethod
    def check_pods_running(namespace):
        config.load_kube_config()
        v1 = client.CoreV1Api()

        pods = v1.list_namespaced_pod(namespace)

        all_running = True
        for pod in pods.items:
            if pod.status.phase != "Running" or not all([c.ready for c in pod.status.container_statuses]):
                all_running = False

        return all_running

    @staticmethod
    def get_pod_recourse_info():
        pass

    @staticmethod
    def check_pods_exist(namespace):
        config.load_kube_config()
        v1 = client.CoreV1Api()

        pods = v1.list_namespaced_pod(namespace)
        return len(pods.items()) == 0

    @staticmethod
    def delete_resources(namespace):
        config.load_kube_config()
        v1 = client.CoreV1Api()

        # Delete Services
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
        cr_list = custom_api.list_namespaced_custom_object(group=group, version=version, namespace=namespace,
                                                           plural=plural)
        for cr in cr_list.get('items', []):
            print(f"Deleting Custom Resource: {cr['metadata']['name']} in namespace {namespace}")
            custom_api.delete_namespaced_custom_object(group=group, version=version, plural=plural,
                                                       name=cr['metadata']['name'], namespace=namespace,
                                                       body=client.V1DeleteOptions())
