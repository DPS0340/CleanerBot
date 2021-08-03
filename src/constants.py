def get_ip_address():
    from requests import get
    return get('https://ipapi.co/ip/').text

ip_address = get_ip_address()
webserver_port = 8087
