def get_ip_address():
    import requests
    return requests.get('https://checkip.amazonaws.com').text.strip()

ip_address = get_ip_address()
arca_proxy_port = 8087
dcinside_gallog_proxy_port = 8086
dcinside_login_proxy_port = 8085
arca_url = "https://arca.live"
dcinside_gallog_url = "https://gallog.dcinside.com"
dcinside_login_url = "https://dcid.dcinside.com"
dcinside_proxy_url = "http://cleanerbot.dcinside.com"
dcinside_logout_url = "https://dcid.dcinside.com/join/logout.php"
cookies_map = {}
sessions = {}