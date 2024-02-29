from kubernetes import client, config
import yaml
import psutil
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

        api = client.CustomObjectsApi()
        cpu_usage = api.list_namespaced_custom_object(
            group="metrics.k8s.io",
            version="v1beta1",
            namespace="auto-edge",
            plural="pods"
        )
        cpu_dict = {}
        mem_dict = {}

        for pod in cpu_usage.get('items', []):
            pod_name = pod['metadata']['name']
            if service_name in pod_name:
                container = pod.get('containers')[0]
                cpu_dict[pod_name] = int(container['usage']['cpu'][:-1]) / 1000000 / 1000
                mem_dict[pod_name] = int(container['usage']['memory'][:-2]) * 1024

        info = []

        pods = v1.list_namespaced_pod(namespace)
        for pod in pods.items:
            if service_name in pod.metadata.name:
                cpu_usage = f'{cpu_dict[pod.metadata.name] / KubeHelper.get_node_cpu(pod.spec.node_name) * 100:.2f}%' if pod.metadata.name in cpu_dict else ''
                mem_usage = f'{mem_dict[pod.metadata.name] / psutil.virtual_memory().total * 100:.2f}%' if pod.metadata.name in mem_dict else ''

                info_dict = {'age': pod.metadata.creation_timestamp.astimezone(pytz.timezone('Asia/Shanghai')).strftime(
                    '%Y-%m-%d %H:%M:%S'),
                    'hostname': pod.spec.node_name,
                    'ip': KubeHelper.get_node_ip(pod.spec.node_name),
                    'cpu': cpu_usage,
                    'memory': mem_usage,
                    'bandwidth': ''}
                info.append(info_dict)

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

    @staticmethod
    def get_node_cpu(hostname):
        config.load_kube_config()
        v1 = client.CoreV1Api()

        nodes = v1.list_node()
        for node in nodes.items:
            if node.metadata.name == hostname:
                return int(node.status.capacity['cpu'][-1])

        assert None, f'hostname of {hostname} not exists'
