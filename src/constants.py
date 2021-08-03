def get_ip_address():
    import requests
    return requests.get('https://checkip.amazonaws.com').text.strip()

ip_address = get_ip_address()
webserver_port = 8087
