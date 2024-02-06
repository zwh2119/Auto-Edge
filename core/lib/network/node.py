from kubernetes import client, config
from core.lib.common import reverse_key_value_in_dict
from core.lib.network import find_all_ips


class NodeInfo:
    __node_info_hostname = None
    __node_info_ip = None

    @classmethod
    def get_node_info(cls):
        if not cls.__node_info_hostname:
            cls.__node_info_hostname, cls.__node_info_ip = cls.__extract_node_info()

        return cls.__node_info_hostname

    @classmethod
    def get_node_info_reverse(cls):
        if not cls.__node_info_ip:
            cls.__node_info_hostname, cls.__node_info_ip = cls.__extract_node_info()

        return cls.__node_info_ip

    @staticmethod
    def __extract_node_info():
        config.load_kube_config()
        v1 = client.CoreV1Api()
        nodes = v1.list_node().items

        assert nodes, 'Invalid node config in KubeEdge system'

        node_dict = {}

        for node in nodes:
            node_name = node.metadata.name
            addresses = node.status.addresses
            for address in addresses:
                if address.type == "InternalIP":
                    node_dict[node_name] = address.address

        node_dict_reverse = reverse_key_value_in_dict(node_dict)

        return node_dict, node_dict_reverse

    @staticmethod
    def hostname2ip(hostname: str) -> str:
        node_info = NodeInfo.get_node_info()
        assert hostname in node_info, f'hostname "{hostname}" not exists in system!'

        return node_info[hostname]

    @staticmethod
    def ip2hostname(ip: str) -> str:
        node_info = NodeInfo.get_node_info_reverse()
        assert ip in node_info, f'ip "{ip}" not exists in system!'

        return node_info[ip]

    @staticmethod
    def url2hostname(url: str) -> str:
        ips = find_all_ips(url)
        assert len(ips) == 1, 'url "{url}" contains none or more than one legal ip!'
        return NodeInfo.ip2hostname(ips[0])

