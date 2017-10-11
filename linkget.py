####!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import print_function
import os
import sys
import requests
import BeautifulSoup
import random
import string
from time import sleep
from collections import deque
from Queue import Queue
from threading import Thread
from urlparse import urlparse
from flask import Flask
from socket import error as SocketError


# Start Flask
api = Flask(__name__)

# This will be our core config method, used for some shit in our api
core_config = {'pause': False,
               'pause_timer': 10,
               'terminate': False,
               'end_test': False
               }

# Request timeout
get_timeout = 60

# Links already scrapped
processed = []

# Link queue
link_queue = deque()

# Dict for internal stuff, just a key/value
# where $URL:$STATUS_CODE
result = {}

# Max number of threads if MAX_THREADS isnt set
max_rqps = 2

# Aways remember that sudo fuck with your $ENV
# so sudo MAX_THREADS=XXX linkget.py $URL
if os.getenv('MAX_THREADS'):
    max_rqps = int(os.getenv('MAX_THREADS'))

# Requests operation
http_op = ""


class Worker(Thread):
    """ The thread pool worker """
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as error:
                logger("Error", error)
            finally:
                self.tasks.task_done()


class ThreadPool(object):
    """ Here is the pool of threads that will execute our worker """
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """ Add a task to the pool """
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """ Wait for the threads in pool to finish """
        self.tasks.join()


# First steps with the api
# i'll try a hackysh approach to that, and fuck you!
@api.route('/api/v1/<api_module>', methods=['GET', 'POST'])
def main_api(api_module):
    """ Main API function, it'll try to execute the function that match
    with the api_module flask rest method"""
    try:
        return getattr(sys.modules[__name__], "api_{0}".format(api_module))()
    except Exception as error:
        return 'Api module not found or not implemented!\n{0}\n'.format(error)


def api_pause():
    """ Api method for a pause in the scrapping """
    core_config["pause"] = True
    return 'Ok'


def api_start():
    """ Api method to continue after a pause """
    core_config["pause"] = False
    return 'Ok'


def api_queuelist():
    """ Api Method that return the number of remaining itens in queue """
    return str(len(link_queue)) + '\n'


def api_rqps():
    """ Api method to print the MAX_THREADS var """
    return str(max_rqps) + '\n'


def api_stop():
    """ Api method to stop scrapping and exit the program """
    link_queue = deque()
    core_config["terminate"] = True
    return 'OK'


def api_terminate():
    """ Api method to force terminate of everything and hoppefully do a clean
    interpreter shutdown """
    processed = []
    link_queue = deque()
    core_config["terminate"] = True
    core_config["pause_timer"] = 0
    return 'Ok'


def logger(logtype, logstr):
    """ Main logging function """
    print("{0}: {1}".format(logtype, logstr))
    pass


def print_error(error_str):
    """ when the output is stdout, print errors in red """
    print('\033[91m' + error_str + '\033[0m')
    return


def getputrank(url, domain_s):
    """ This is the function, it will try to download your url
    parse the received html for another links on the same domain
    and add them to the scrapping pool """
    if domain_s != get_domain(url) or url in processed:
        return
    #sys.stdout.write('\r'+url+'\n')
    agent_info = {'User-Agent': rand_ua()}
    site_request = requests.get(url, timeout=get_timeout, headers=agent_info)
    if site_request.status_code != 200:
        print_error('URL: {0}, STATUS: {1}'.format(url, site_request.status_code))
        return
    processed.append(url)
    result[url] = site_request.status_code
    if 'cloudflare' in site_request.text:
        print('challenged by cloudflare')
        return
    #sys.stdout.write('\r'+url+'\n')
    agent_info = {'User-Agent': rand_ua()}
    site_request = requests.get(url, timeout=get_timeout, headers=agent_info)
    if site_request.status_code != 200:
        print_error('URL: {0}, STATUS: {1}'.format(url, site_request.status_code))
        return
    processed.append(url)
    result[url] = site_request.status_code
    try:
        soup = BeautifulSoup.BeautifulSoup(site_request.text)

        for link in soup.findAll("a"):
            if not link.get("href") in result:
                print('a')
                if str(link.get("href")).startswith('http'):
                    print('b')
                    link_queue.append(link.get("href"))
                    print('c')
                elif str(link.get("href")).startswith('/'):
                    link_queue.append(url + link.get("href"))
                    print('d')
                    link_queue.append(url+link.get("href"))
    except Exception as error:
        logger("Error", error)
    return


def get_domain(url):
    """ Return the domain name from a link """
    parsed_uri = urlparse(url)
    domain_parsed = '{uri.netloc}'.format(uri=parsed_uri)
    return domain_parsed


def randomword(length):
    return ''.join(random.choice(string.lowercase) for i in range(length))


def rand_ua():
    """ Return a random user agent every time """
    agent_list = [
        'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36,',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20130401 Firefox/31.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A',
        'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5355d Safari/8536.25',
        'Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/4.0 (compatible; MSIE 6.0b; Windows NT 5.0; .NET CLR 1.1.4322)',
        'Opera/9.80 (S60; SymbOS; Opera Tablet/9174; U; en) Presto/2.7.81 Version/10.5',
        'Mozilla/5.0 (Windows NT 5.1; U; pl; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 11.00',
        'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'Googlebot/2.1 (+http://www.googlebot.com/bot.html)',
        'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)']
    return agent_list[random.randint(0, len(agent_list) - 1)]


def main():
    """ Our main function """
    pool = ThreadPool(max_rqps)
    domain = get_domain(sys.argv[1])
    link_queue.append(sys.argv[1])
    # We need 1 slot in that pool for our flask app
    # api.run(host='0.0.0.0', port=5000, debug=True)
    # Threads of threads of threads....
    pool.add_task(api.run, host='0.0.0.0', port=5000)
    while core_config["terminate"] is False:
        try:
            if core_config["pause"]:
                sleep(float(core_config["pause_timer"]))
                continue
            if len(link_queue) > 0:
                pool.add_task(getputrank, link_queue.pop(), domain)
        except KeyboardInterrupt:
            print_error("\nWaiting for the thread pool to exit...")
            del pool
            print_error("\nExiting with {0} itens in queue.".format(len(link_queue)))
            break
        except Exception as error:
            logger("Error", error)
            # will be a query in our http api, soon!
            # len(link_queue) to get remaining itens
    return 0


if __name__ == '__main__':
    sys.exit(main())
