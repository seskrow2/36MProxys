# 36m-proxys.py
import os
import sys
import re
import time
import threading
import requests
import json
import random
import pycurl
import certifi
from io import BytesIO
from typing import Union
from colorama import Fore, init, Style

# --- Global Initializations ---
init(convert=True)
lock = threading.Lock()

# --- UI and Console Functions ---
class UI:
    @staticmethod
    def banner():
        """Returns the application's ASCII art banner."""
        banner = f'''
        \t\t\t   #######   #####   ##   ##  #####   #####  #   ## #####  ####
        \t\t\t      ##    ##   ##  ### ### ##   ## ##   ## ##  ##  ##   # ##  ##
        \t\t\t      ##    ######   ## # ## ####### #######  ## ##  #####  ##  ##
        \t\t\t      ##    ##   ##  ##   ## ##   ## ##   ##  #####  ##     ##  ##
        \t\t\t      ##    ##   ##  ##   ## ##   ## ##   ##   ###   #####  ####
        \t\t\t\t\t\t\b{Fore.LIGHTBLACK_EX}A NightfallGT X Plasmonix Project {Style.RESET_ALL}
        '''
        return banner

    @staticmethod
    def menu():
        """Returns the main menu options."""
        menu = f'''
[{Fore.LIGHTBLUE_EX}1{Style.RESET_ALL}] Scraper
[{Fore.LIGHTBLUE_EX}2{Style.RESET_ALL}] Checker'''
        return menu

def write(args):
    """Thread-safe print function."""
    with lock:
        sys.stdout.flush()
        print(args)

def animated(args):
    """Displays a simple loading animation in the console."""
    l = ['|', '/', '-', '\\']
    for i in l + l + l:
        sys.stdout.write(f'\r[{Fore.LIGHTBLUE_EX}{i}{Style.RESET_ALL}] {args}')
        sys.stdout.flush()
        time.sleep(0.2)

# --- Core Proxy Logic ---

class ProxyChecker:
    def __init__(self, timeout: int = 10000, verbose: bool = False):
        self.timeout = timeout
        self.verbose = verbose
        self.proxy_judges = [
            'https://www.proxy-listen.de/azenv.php',
            'http://mojeip.net.pl/asdfa/azenv.php',
            'http://httpheader.net/azenv.php',
            'http://pascal.hoez.free.fr/azenv.php'
        ]
        self.ip = self.get_ip()
        if self.ip == "":
            print("ERROR: Could not retrieve public IP. The checker may not work correctly.")
        self.check_proxy_judges()

    def check_proxy_judges(self) -> None:
        checked_judges = []
        for judge in self.proxy_judges:
            if self.send_query(url=judge):
                checked_judges.append(judge)
        self.proxy_judges = checked_judges
        if len(checked_judges) == 0:
            print("ERROR: All proxy judges are outdated or unreachable.")
        elif len(checked_judges) == 1:
            print('WARNING: Only one operational proxy judge remains.')

    def get_ip(self) -> str:
        r = self.send_query(url='https://api.ipify.org/')
        return r['response'] if r else ""

    def send_query(self, proxy: Union[str, bool] = False, url: str = None, tls=1.3, user: str = None, password: str = None) -> Union[bool, dict]:
        response = BytesIO()
        c = pycurl.Curl()
        if self.verbose: c.setopt(c.VERBOSE, True)
        c.setopt(c.URL, url or random.choice(self.proxy_judges))
        c.setopt(c.WRITEDATA, response)
        c.setopt(c.TIMEOUT_MS, self.timeout)
        if user is not None and password is not None: c.setopt(c.PROXYUSERPWD, f"{user}:{password}")
        c.setopt(c.SSL_VERIFYHOST, 0)
        c.setopt(c.SSL_VERIFYPEER, 0)
        if proxy:
            c.setopt(c.PROXY, proxy)
            if proxy.startswith('https'):
                c.setopt(c.SSL_VERIFYHOST, 2)
                c.setopt(c.SSL_VERIFYPEER, 1)
                c.setopt(c.CAINFO, certifi.where())
                if tls == 1.3: c.setopt(c.SSLVERSION, c.SSLVERSION_TLSv1_3)
                elif tls == 1.2: c.setopt(c.SSLVERSION, c.SSLVERSION_TLSv1_2)
        try:
            c.perform()
        except pycurl.error:
            return False
        if c.getinfo(c.HTTP_CODE) != 200: return False
        timeout = round(c.getinfo(c.CONNECT_TIME) * 1000)
        response_body = response.getvalue().decode('iso-8859-1', errors='ignore')
        return {'timeout': timeout, 'response': response_body}

    def parse_anonymity(self, r: str) -> str:
        if self.ip in r: return 'Transparent'
        privacy_headers = ['VIA', 'X-FORWARDED-FOR', 'X-FORWARDED', 'FORWARDED-FOR', 'FORWARDED-FOR-IP', 'FORWARDED', 'CLIENT-IP', 'PROXY-CONNECTION']
        if any(header in r for header in privacy_headers): return 'Anonymous'
        return 'Elite'

    def get_country(self, ip: str) -> list:
        r = self.send_query(url=f'https://ip2c.org/{ip}')
        if r and r['response'].startswith('1;'):
            parts = r['response'].split(';')
            return [parts[3], parts[1]]
        return ['-', '-']

    def check_proxy(self, proxy: str, check_country: bool = True, protocol: Union[str, list] = None, retries: int = 1, user: str = None, password: str = None) -> Union[bool, dict]:
        protocols_to_test = ['http', 'socks4', 'socks5']
        for _ in range(retries):
            for proto in protocols_to_test:
                r = self.send_query(proxy=f'{proto}://{proxy}', user=user, password=password)
                if not r: continue
                anonymity = self.parse_anonymity(r['response'])
                country, country_code = self.get_country(proxy.split(':')[0]) if check_country else ('-', '-')
                return {'protocols': [proto], 'anonymity': anonymity, 'timeout': r['timeout'], 'country': country, 'country_code': country_code}
        return False

class XProxy:
    headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    # --- FULL URL LISTS ---
    proxy_w_regex = [
        ["http://spys.me/proxy.txt","%ip%:%port% "],
        ["http://www.httptunnel.ge/ProxyListForFree.aspx"," target=\"_new\">%ip%:%port%</a>"],
        ["https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.json", "\"ip\":\"%ip%\",\"port\":\"%port%\","],
        ["https://raw.githubusercontent.com/fate0/proxylist/master/proxy.list", '"host": "%ip%".*?"country": "(.*?){2}",.*?"port": %port%'],
        ["https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt", '%ip%:%port% (.*?){2}-.-S \\+'],
        ["https://www.us-proxy.org/", "<tr><td>%ip%<\\/td><td>%port%<\\/td><td>(.*?){2}<\\/td><td class='hm'>.*?<\\/td><td>.*?<\\/td><td class='hm'>.*?<\\/td><td class='hx'>(.*?)<\\/td><td class='hm'>.*?<\\/td><\\/tr>"],
        ["https://free-proxy-list.net/", "<tr><td>%ip%<\\/td><td>%port%<\\/td><td>(.*?){2}<\\/td><td class='hm'>.*?<\\/td><td>.*?<\\/td><td class='hm'>.*?<\\/td><td class='hx'>(.*?)<\\/td><td class='hm'>.*?<\\/td><\\/tr>"],
        ["https://www.sslproxies.org/", "<tr><td>%ip%<\\/td><td>%port%<\\/td><td>(.*?){2}<\\/td><td class='hm'>.*?<\\/td><td>.*?<\\/td><td class='hm'>.*?<\\/td><td class='hx'>(.*?)<\\/td><td class='hm'>.*?<\\/td><\\/tr>"],
        ['https://www.socks-proxy.net/', "%ip%:%port%"],
        ['https://free-proxy-list.net/uk-proxy.html', "<tr><td>%ip%<\\/td><td>%port%<\\/td><td>(.*?){2}<\\/td><td class='hm'>.*?<\\/td><td>.*?<\\/td><td class='hm'>.*?<\\/td><td class='hx'>(.*?)<\\/td><td class='hm'>.*?<\\/td><\\/tr>"],
        ['https://free-proxy-list.net/anonymous-proxy.html', "<tr><td>%ip%<\\/td><td>%port%<\\/td><td>(.*?){2}<\\/td><td class='hm'>.*?<\\/td><td>.*?<\\/td><td class='hm'>.*?<\\/td><td class='hx'>(.*?)<\\/td><td class='hm'>.*?<\\/td><\\/tr>"],
        ["https://www.proxy-list.download/api/v0/get?l=en&t=https", '"IP": "%ip%", "PORT": "%port%",'],
        ["https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=6000&country=all&ssl=yes&anonymity=all", "%ip%:%port%"],
        ["https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt", "%ip%:%port%"],
        ["https://raw.githubusercontent.com/shiftytr/proxy-list/master/proxy.txt", "%ip%:%port%"],
        ["https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt", "%ip%:%port%"],
        ["https://www.hide-my-ip.com/proxylist.shtml", '"i":"%ip%","p":"%port%",'],
        ["https://raw.githubusercontent.com/scidam/proxy-list/master/proxy.json", '"ip": "%ip%",\n.*?"port": "%port%",'],
        ['https://www.freeproxychecker.com/result/socks4_proxies.txt', "%ip%:%port%"],
        ['https://proxy50-50.blogspot.com/', '%ip%</a></td><td>%port%</td>'], 
        ['http://free-fresh-proxy-daily.blogspot.com/feeds/posts/default', "%ip%:%port%"],
        ['http://www.live-socks.net/feeds/posts/default', "%ip%:%port%"],
        ['http://www.socks24.org/feeds/posts/default', "%ip%:%port%"],
        ['http://www.proxyserverlist24.top/feeds/posts/default',"%ip%:%port%" ] ,
        ['http://proxysearcher.sourceforge.net/Proxy%20List.php?type=http',"%ip%:%port%"],
        ['http://proxysearcher.sourceforge.net/Proxy%20List.php?type=socks', "%ip%:%port%"],
        ['https://www.my-proxy.com/free-anonymous-proxy.html', '%ip%:%port%'],
        ['https://www.my-proxy.com/free-transparent-proxy.html', '%ip%:%port%'],
        ['https://www.my-proxy.com/free-socks-4-proxy.html', '%ip%:%port%'],
        ['https://www.my-proxy.com/free-socks-5-proxy.html','%ip%:%port%'],
        ['https://www.my-proxy.com/free-proxy-list.html','%ip%:%port%'],
        ['https://www.my-proxy.com/free-proxy-list-2.html','%ip%:%port%'],
        ['https://www.my-proxy.com/free-proxy-list-3.html','%ip%:%port%'],
        ['https://www.my-proxy.com/free-proxy-list-4.html', '%ip%:%port%'],
        ['https://www.my-proxy.com/free-proxy-list-5.html','%ip%:%port%'],
        ['https://www.my-proxy.com/free-proxy-list-6.html','%ip%:%port%'],
        ['https://www.my-proxy.com/free-proxy-list-7.html','%ip%:%port%'],
        ['https://www.my-proxy.com/free-proxy-list-8.html','%ip%:%port%'],
        ['https://www.my-proxy.com/free-proxy-list-9.html','%ip%:%port%'],
        ['https://www.my-proxy.com/free-proxy-list-10.html','%ip%:%port%'],
    ]

    proxy_direct = [
        'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all',
        'https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=5000&country=all&ssl=all&anonymity=all',
        'https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=5000&country=all&ssl=all&anonymity=all',         
        'https://www.proxyscan.io/download?type=http',
        'https://www.proxyscan.io/download?type=https',
        'https://www.proxyscan.io/download?type=socks4',
        'https://www.proxyscan.io/download?type=socks5',
        'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
        'https://github.com/TheSpeedX/PROXY-List/blob/master/socks4.txt',
        'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt',
        'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
        'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt',
        'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt',
        'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt',
        'https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt',
        'https://multiproxy.org/txt_all/proxy.txt',
        'http://rootjazz.com/proxies/proxies.txt',
        'http://ab57.ru/downloads/proxyold.txt',
        'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
        'https://proxy-spider.com/api/proxies.example.txt',
        'https://proxylist.live/nodes/socks4_1.php?page=1&showall=1',
        'https://raw.githubusercontent.com/opsxcq/proxy-list/master/list.txt',
        'https://www.proxy-list.download/api/v1/get?type=socks4',
        'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt',
        'https://raw.githubusercontent.com/almroot/proxylist/master/list.txt',
        'https://raw.githubusercontent.com/jetkai/proxy-list/main/proxies-socks5.txt',
        'https://raw.githubusercontent.com/jetkai/proxy-list/main/proxies-http.txt',
        'https://raw.githubusercontent.com/jetkai/proxy-list/main/proxies-socks4.txt',
        'https://raw.githubusercontent.com/r3xzt/proxy-list/main/all.txt',
        'https://raw.githubusercontent.com/Volodichev/proxy-list/main/http.txt',
        'https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt',
        'https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt',
        'https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt',
        'https://raw.githubusercontent.com/roma8ok/proxy-list/main/proxy-list-socks5.txt',
        'https://raw.githubusercontent.com/roma8ok/proxy-list/main/proxy-list-http.txt',
        'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies.txt',
        'https://raw.githubusercontent.com/BlackSnowDot/proxylist-update-every-minute/main/http.txt',
        'https://raw.githubusercontent.com/BlackSnowDot/proxylist-update-every-minute/main/https.txt',
        'https://raw.githubusercontent.com/BlackSnowDot/proxylist-update-every-minute/main/proxy.txt',
        'https://raw.githubusercontent.com/BlackSnowDot/proxylist-update-every-minute/main/socks.txt',
        'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt',
        'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt',
        'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt',
        'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/http.txt',
        'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/socks4.txt',
        'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/socks5.txt',
        'https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks4.txt',
        'https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt',
        'https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks5.txt',
        'https://github.com/mmpx12/proxy-list/blob/master/http.txt',
        'https://github.com/mmpx12/proxy-list/blob/master/socks4.txt',
        "https://www.freeproxychecker.com/result/socks5_proxies.txt",
        'https://github.com/mmpx12/proxy-list/blob/master/socks5.txt',
        'https://raw.githubusercontent.com/zevtyardt/proxy-list/main/all.txt',
        'https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt',
        'https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/http.txt',
        'https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/https.txt',
        'https://raw.githubusercontent.com/saisuiu/uiu/main/free.txt',
        'https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt',
        'https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/socks5.txt',
        'https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks4.txt',
        'https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/socks4.txt',
    ]
    # --- END OF LISTS ---

    def __init__(self):
        self.proxy_output = []
        self.scrape_counter = 0
        self.checked_counter = 0
        self.alive_counter = 0
        self.start = time.time()

    def _update_title(self):
        while True:
            elapsed = time.strftime('%H:%M:%S', time.gmtime(time.time() - self.start))
            title = f'36MProxys - Elapsed: {elapsed} | Scraped: {self.scrape_counter} | Checked: {self.checked_counter} | Alive: {self.alive_counter}'
            sys.stdout.write(f"\033]0;{title}\007")
            sys.stdout.flush()
            time.sleep(0.4)

    def file_read(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except IOError as e:
            write(f"[{Fore.RED}ERROR{Style.RESET_ALL}] Could not read file: {e}")
            return []

    def file_write(self, name, contents):
        with open(name, 'w', encoding='utf-8') as f:
            for item in contents:
                f.write(item + '\n')

    def background_task(self):
        self.start = time.time()
        threading.Thread(target=self._update_title, daemon=True).start()

    def get_proxies(self):
        return self.proxy_output

class ProxyScrape(XProxy):
    def _scrape_regex(self, url, custom_regex):
        try:
            proxylist = requests.get(url, timeout=10, headers=self.headers).text
            ip_pattern = '([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3})'
            port_pattern = '([0-9]{1,5})'
            custom_regex = custom_regex.replace('%ip%', ip_pattern).replace('%port%', port_pattern)
            for match in re.finditer(re.compile(custom_regex), proxylist):
                try:
                    proxy = f"{match.group(1)}:{match.group(2)}"
                    if proxy not in self.proxy_output:
                        self.proxy_output.append(proxy)
                        write(f'{Fore.LIGHTBLUE_EX}[SCRAPED]{Style.RESET_ALL} {proxy}')
                        self.scrape_counter += 1
                except IndexError: continue
        except requests.RequestException:
            write(f'[{Fore.YELLOW}WARNING{Style.RESET_ALL}] Failed to connect to {url}')

    def scrape_w_regex(self):
        threads = []
        for source in self.proxy_w_regex:
            thread = threading.Thread(target=self._scrape_regex, args=(source[0], source[1]))
            threads.append(thread)
            thread.start()
        for thread in threads: thread.join()

    def _scrape_direct_url(self, url):
        try:
            page = requests.get(url, timeout=10, headers=self.headers).text
            for proxy in re.findall(re.compile('([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}):([0-9]{1,5})'), page):
                full_proxy = f"{proxy[0]}:{proxy[1]}"
                if full_proxy not in self.proxy_output:
                    self.proxy_output.append(full_proxy)
                    write(f'{Fore.LIGHTBLUE_EX}[SCRAPED]{Style.RESET_ALL} {full_proxy}')
                    self.scrape_counter += 1
        except requests.RequestException:
            write(f'[{Fore.YELLOW}WARNING{Style.RESET_ALL}] Failed to connect to {url}')

    def scrape_direct(self):
        threads = []
        for source in self.proxy_direct:
            thread = threading.Thread(target=self._scrape_direct_url, args=(source,))
            threads.append(thread)
            thread.start()
        for thread in threads: thread.join()

class ProxyCheck(XProxy):
    def __init__(self):
        super().__init__()
        animated('Loading checker engine...')
        self.checker = ProxyChecker()
        os.system('clear')
        
    def check(self, proxy_list):
        for proxy in proxy_list:
            c = self.checker.check_proxy(proxy)
            with lock: self.checked_counter += 1
            if c:
                with lock: self.alive_counter += 1
                write(f"{Fore.GREEN}[ALIVE]{Style.RESET_ALL} {proxy} | Type: {c['protocols'][0]} | Anonymity: {c['anonymity']} | Timeout: {c['timeout']}ms | Country: {c['country_code']}")
                with open(f"{c['protocols'][0]}_alive.txt", 'a', encoding='utf-8') as f:
                    f.write(proxy + '\n')
            else:
                write(f"{Fore.RED}[DEAD]{Style.RESET_ALL} {proxy}")

def main():
    os.system('clear')
    ui = UI()
    print(ui.banner())
    print(ui.menu())
    try:
        user_input = int(input(f'[{Fore.LIGHTBLUE_EX}?{Style.RESET_ALL}] Choice> '))
        if user_input == 1:
            p = ProxyScrape()
            os.system('clear')
            print(ui.banner())
            p.background_task()
            animated('Scraping proxies from all sources...')
            p.scrape_w_regex()
            p.scrape_direct()
            output = p.get_proxies()
            print(f'\n[{Fore.GREEN}*{Style.RESET_ALL}] Total proxies scraped: {len(output)}')
            animated('Checking for duplicates...')
            clean_output = sorted(list(set(output)))
            print(f'\n[{Fore.LIGHTBLUE_EX}+{Style.RESET_ALL}] Found {len(clean_output)} unique proxies.')
            animated('Writing to scraped.txt...')
            p.file_write('scraped.txt', clean_output)
            print(f'\n[{Fore.GREEN}+{Style.RESET_ALL}] Finished. Proxies saved to scraped.txt.')
            input("Press Enter to continue...")
        elif user_input == 2:
            pc = ProxyCheck()
            print(ui.banner())
            path_str = input(f"[{Fore.LIGHTBLUE_EX}#{Style.RESET_ALL}] Enter the path to your proxy file: ")
            path_str = os.path.expanduser(path_str)
            if not os.path.isfile(path_str):
                print(f"\n[{Fore.RED}ERROR{Style.RESET_ALL}] File not found: '{path_str}'")
                print(f"[{Fore.YELLOW}INFO{Style.RESET_ALL}] Tip: Use 'termux-setup-storage' and place your file in ~/storage/downloads/")
                return
            proxy_list = pc.file_read(path_str)
            if not proxy_list:
                print(f'[{Fore.RED}!{Style.RESET_ALL}] File is empty or could not be read. Exiting.')
                return
            thread_count = int(input(f'[{Fore.LIGHTBLUE_EX}>{Style.RESET_ALL}] Enter number of threads [e.g., 100]: '))
            animated('Loading threads...')
            os.system('clear')
            print(ui.banner())
            pc.background_task()
            threads = []
            chunk_size = (len(proxy_list) + thread_count - 1) // thread_count
            for i in range(thread_count):
                sub_list = proxy_list[i * chunk_size : (i + 1) * chunk_size]
                if sub_list:
                    t = threading.Thread(target=pc.check, args=(sub_list,))
                    threads.append(t)
                    t.start()
            for t in threads: t.join()
            print(f'[{Fore.GREEN}+{Style.RESET_ALL}] Finished checking. Results saved to respective files (http_alive.txt, etc.).')
            input("Press Enter to continue...")
        else:
            main()
    except (ValueError, KeyboardInterrupt):
        print("\nExiting.")
        sys.exit(0)

if __name__ == '__main__':
    main()
