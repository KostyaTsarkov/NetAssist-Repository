import ipaddress


class IPv4Info:
    """
    This class represents an IPv4 address and provides methods to extract information from it.
    """

    @staticmethod
    def extract_info(netbox_ip_address: str) -> dict:
        """
        Extracts information from a given IPv4 address and returns a dictionary containing the extracted information.

        :param netbox_ip_address: A string representation of an IPv4 address in the format 'x.x.x.x/y'.
        :type netbox_ip_address: str

        :return: A dictionary containing the following keys:
            - 'ip4_address': a string containing the IPv4 address.
            - 'ip4_netmask': a string containing the IPv4 netmask.
            - 'ip4_network': a string containing the IPv4 network address.
            - 'ip4_prefix': a string containing the IPv4 prefix length.
            - 'ip4_broadcast': a string containing the IPv4 broadcast address.
            - 'ip4_gateway' (optional): a string containing the IPv4 gateway address, only if the IPv4 network has more than one address.
        :rtype: dict
        """
        # Convert the given IP address to CIDR notation
        ip_cidr = ipaddress.ip_interface(netbox_ip_address)

        # Initialize an empty dictionary called 'ipv4_dic' to store the extracted information
        ipv4_dic = dict()

        # Extract the IPv4 address and add it to the dictionary
        ipv4_dic['ip4_address'] = f"{ipaddress.IPv4Interface(ip_cidr).ip}"

        # Extract the IPv4 netmask and add it to the dictionary
        ipv4_dic['ip4_netmask'] = f"{ipaddress.IPv4Interface(ip_cidr).netmask}"

        # Extract the IPv4 network address and add it to the dictionary
        ipv4_dic['ip4_network'] = f"{ipaddress.IPv4Interface(ip_cidr).network}"

        # Extract the IPv4 prefix length and add it to the dictionary
        ipv4_dic['ip4_prefix'] = f"{ipaddress.IPv4Network(ipv4_dic['ip4_network']).prefixlen}"

        # Extract the IPv4 broadcast address and add it to the dictionary
        ipv4_dic['ip4_broadcast'] = f"{ipaddress.IPv4Network(ipv4_dic['ip4_network']).broadcast_address}"

        # If the IPv4 network has more than one address, extract the IPv4 gateway address and add it to the dictionary
        if (ipaddress.IPv4Network(ipv4_dic['ip4_network']).num_addresses) > 1:
            ipv4_dic['ip4_gateway'] = f"{list(ipaddress.IPv4Network(ipv4_dic['ip4_network']).hosts())[-1]}"

        # Return the dictionary containing the extracted information
        return ipv4_dic
