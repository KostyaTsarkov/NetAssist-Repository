from ipv4 import IPv4Info
import socket
from logger import Logger

logger = Logger('app.log')


class IPDomainResolver:
    """
    Class to resolve IP addresses and domain names
    """

    def __init__(self) -> None:
        """
        Initializes an instance of the class.

        Args:
            address (str): A string representing the address.

        Returns:
            None
        """
        self.ip_address = None
        self.domain_name = None

    def resolve(self, address: str) -> None:
        """
        Resolves the given address (domain name or IP address) and sets the corresponding instance variables.
        If the address is an IP address, sets the `ip_address` variable to the given address and logs an info message.
        If the address is a domain name, sets the `domain_name` variable to the given address and tries to resolve it using `socket.getaddrinfo`.
        If the domain name can be resolved to an IP address, sets the `ip_address` variable to the first resolved IP address and logs an info message.
        If the domain name cannot be resolved, logs an error message.

        :param address: A string representing the address to resolve.
        :type address: str
        :return: None
        :rtype: None
        """
        self.address = address

        try:
            # Try to recognize the address as an IP address
            self.ip_address = IPv4Info().extract_info(self.address)['ip4_address']
            logger.log_info(f"{self.address} is a valid IP address")
        except ValueError as e:
            # The address is not an IP address, resolving domain name
            self.domain_name = self.address
            logger.log_error(f'Failed to resolve {self.address}: {e}')
            try:
                addresses = socket.getaddrinfo(self.domain_name, None)
                for addr in addresses:
                    if addr[0] == socket.AF_INET:
                        self.ip_address = addr[4][0]
                        logger.log_info(f"{self.domain_name} resolved to {self.ip_address}")
                        break
            except socket.gaierror as e:
                logger.log_error(f"Failed to resolve {self.domain_name}: {e}")

        return self.ip_address
# address = 'invalid_ip'

resolver = IPDomainResolver()
#resolver.resolve()
#print(resolver.ip_address)
