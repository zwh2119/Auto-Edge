from kubernetes import client, config
import yaml
import datetime
import pytz

class KubeHelper:

    @staticmethod
    def apply_custom_resources(yaml_file_path):
        config.load_kube_config()

        with open(yaml_file_path, 'r') as file:
            docs = yaml.safe_load_all(file)
            api_instance = client.CustomObjectsApi()

            for doc in docs:
                if doc is None:
                    continue
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
                except Exception as e:
                    print(f"An error occurred: {e}")
                    return False
            return True

    @staticmethod
    def check_pods_running(namespace='auto-edge'):
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
        return len(pods.items) > 0

    @staticmethod
    def check_pod_name(name, namespace='auto-edge'):
        config.load_kube_config()
        v1 = client.CoreV1Api()

        pods = v1.list_namespaced_pod(namespace)
        for pod in pods.items:
            if name in pod.metadata.name:
                return True
        return False

    @staticmethod
    def delete_resources(namespace='auto-edge'):
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
        return True

    @staticmethod
    def get_service_info(service_name, namespace='auto-edge'):
        config.load_kube_config()
        v1 = client.CoreV1Api()

        info = []

        pods = v1.list_namespaced_pod(namespace)
        for pod in pods.items:
            if service_name in pod.metadata.name:
                info_dict = {'age': pod.metadata.creation_timestamp.astimezone(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S'),
                             'hostname': pod.spec.node_name,
                             'ip': KubeHelper.get_node_ip(pod.spec.node_name),
                             'cpu': '20%',
                             'memory': '20%',
                             'bandwidth': '1Mbps'}
                info.append(info_dict)
                print('time: ', pod.metadata.creation_timestamp)
                # print(pod.metadata)

        return info

    @staticmethod
    def get_node_ip(hostname):
        config.load_kube_config()
        v1 = client.CoreV1Api()

        nodes = v1.list_node()
        for node in nodes.items:
            if node.metadata.name == hostname:
                for address in node.status.addresses:
                    if address.type == "InternalIP":
                        return address.address
        return ''

