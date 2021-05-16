#!/usr/bin/env python
#pylint: disable=bare-except
"""
Flask module for manipulating API trades and displaying relevent graphs
"""
import re
import sys
import json
import subprocess
from collections import defaultdict
import requests
import yaml
from flask import Flask, render_template, request
APP = Flask(__name__, template_folder="/etc/gcapi", static_url_path='/etc/gcapi/',
            static_folder='/etc/gcapi')

def get_pairs():
    """
    get details from docker_compose, configstore, and router config
    output in reversed JSON format
    """
    docker_compose = open("install/docker-compose_prod.yml", "r")
    pairs_dict = {}
    names = {}
    length = defaultdict(int)
    pattern = "CONFIG_ENV"
    for line in docker_compose:
        if re.search(pattern, line.strip()) and not line.strip().endswith(('prod', 'api', 'cron')):
            env = line.split('=')[1].strip()
            command = 'configstore package get {} pairs'.format(env)
            result = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
            #subprocess.run(["ls", "-l", "/dev/null"], capture_output=True)
            pairs =  result.stdout.read().split()
            command = 'configstore package get {} name'.format(env)
            result = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
            name = result.stdout.read().split()
            pairs_dict[env] = [pair.decode('utf-8') for pair in pairs]
            length[env] += 1
            names[env] = name[0].decode('utf-8')
    for key, val in pairs_dict.items():
        length[key] = len(val)
    return pairs_dict, dict(length), names

def divide_chunks(lst, num):
    """
    Divide list into lists of lists
    using given chunk size
    """

    # looping till length l
    for i in range(0, len(lst), num):
        yield lst[i:i + num]

@APP.route('/charts', methods=["GET"])
def charts():
    """Charts for given strategy/config_env"""
    config_env = request.args.get('config_env')
    groups = list(divide_chunks(get_pairs()[0][config_env],2))

    return render_template('charts.html', groups=groups)

def list_to_dict(rlist):
    """
    Convert colon seperated string list to key/value dict
    """
    links = dict(map(lambda s : s.split(':'), rlist))
    return {v: k for k, v in links.items() if k.startswith("be")}

@APP.route("/forward", methods=['POST', 'GET'])
def move_forward():
    """
    get buy/sell request
    """
    pair = request.args.get('pair')
    strategy = request.args.get('strategy')
    action = request.args.get('action')

    send_trade(pair, strategy, action)
    return action()

def send_trade(pair, strategy, action):
    """
    Create BUY/SELL post request and send to API router
    """
    payload = {"pair": pair,
               "text": "Manual action from API",
               "action": action,
               "strategy": strategy}
    url = "https://api-router/webhook"
    try:
        requests.post(url, json=json.dumps(payload), timeout=1)
    except:
        pass

@APP.route('/trade', methods=["GET"])
def trade():
    """
    Buy/sell actions for API trades
    """
    pairs, _, names = get_pairs()

    rev_names =  {v: k for k, v in names.items() }
    with open('/etc/router_config.json', 'r') as json_file:
        router_config=json.load(json_file)


    with open("install/docker-compose_prod.yml", 'r') as stream:
        try:
            output = (yaml.safe_load(stream))
        except yaml.YAMLError as exc:
            print(exc)
    links_list = output['services']['be-api-router']['links']
    links_dict = list_to_dict(links_list)

    my_dic = defaultdict(set)
    for strat, short_name in router_config.items():
        for item in short_name:
            name = item.split(':')[0]
            container = links_dict[name]
            if container.startswith('be-'):
                actual_name = container[3:]
            else:
                continue
            config_env = rev_names[actual_name]
            xxx = pairs[config_env]
            my_dic[strat] |= set(xxx)

    return render_template('action.html', my_dic=my_dic)

@APP.route('/menu', methods=["GET"])
def menu():
    """
    Menu of strategies
    """
    length = get_pairs()[1]
    return render_template('menu.html', strats=length)

def main():
    """main func"""

    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("API for interacting with trading system")
        sys.exit(0)
    APP.run(debug=True, host='0.0.0.0', port=5000, threaded=True)

if __name__ == '__main__':
    main()