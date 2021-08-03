def get_ip_address():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(("8.8.8.8", 80))
        ip_addr = sock.getsockname()[0]
    return ip_addr

ip_address = get_ip_address()
webserver_port = 8087
