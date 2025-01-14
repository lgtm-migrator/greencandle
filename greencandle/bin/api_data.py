#!/usr/bin/env python
#pylint: disable=no-member, wrong-import-position,no-else-return,logging-not-lazy,broad-except
"""
Flask module for manipulating API trades and displaying relevent graphs
"""
import atexit
import time
from pathlib import Path
from collections import defaultdict
from flask import Flask, request, Response
from apscheduler.schedulers.background import BackgroundScheduler
from greencandle.lib import config
from greencandle.lib.common import arg_decorator
from greencandle.lib.redis_conn import Redis
from greencandle.lib.logger import get_logger
config.create_config()
LONG = set()
SHORT = set()
ALL = defaultdict(dict)
PAIRS = config.main.pairs.split()
LOGGER = get_logger(__name__)
APP = Flask(__name__, template_folder="/etc/gcapi", static_url_path='/',
            static_folder='/etc/gcapi')

@APP.route('/healthcheck', methods=["GET"])
def healthcheck():
    """
    Docker healthcheck
    Return 200
    """
    return Response(status=200)

def analyse_loop():
    """
    Gather data from redis and analyze
    """
    run_file = Path('/var/run/gc-data-{}'.format(config.main.interval))

    while not run_file.is_file():
        # file doesn't exist
        LOGGER.info("Waiting for data collection to complete...")
        time.sleep(30)

    redis = Redis()
    for pair in PAIRS:
        pair = pair.strip()
        LOGGER.debug("Analysing pair: %s" % pair)
        try:
            result = redis.get_action(pair=pair, interval=config.main.interval)

            ALL[pair]['date'] = result[2]
            if result[4]['buy'] and not result[4]['sell']:
                LONG.add(pair)
                SHORT.discard(pair)
                ALL[pair]['action'] = 'buy'
            elif result[4]['sell'] and not result[4]['buy']:
                SHORT.add(pair)
                LONG.discard(pair)
                ALL[pair]['action'] = 'sell'

        except Exception as err_msg:
            LOGGER.critical("Error with pair %s %s" % (pair, str(err_msg)))
    LOGGER.info("End of current loop")
    del redis

@APP.route('/get_data', methods=["GET"])
def get_data():
    """
    Get data for all pairs including date last updated
    """
    return ALL

@APP.route('/get_trend', methods=["GET"])
def get_trend():
    """
    Buy/sell actions for API trades
    """
    pair = request.args.get('pair')
    if pair in LONG:
        return "long"
    elif pair in SHORT:
        return "short"
    elif not pair:
        return {"long": list(LONG), "short": list(SHORT)}
    else:
        return "Invalid Pair"

@APP.route('/get_stoch', methods=["GET"])
def get_stoch():
    """
    Return stochastic values for given pair
    """
    pair = request.args.get('pair')
    redis = Redis()
    items = redis.get_items(pair, config.main.interval)[-2:]
    result1 = redis.get_item(items[0], 'STOCHRSI_14')
    result2 = redis.get_item(items[1], 'STOCHRSI_14')
    return (result1, result2)

@arg_decorator
def main():
    """
    API for determining entrypoint for given pair
    according to buy/sell rules.
    """

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=analyse_loop, trigger="interval",
                      seconds=int(config.main.check_interval))
    scheduler.start()
    APP.run(debug=False, host='0.0.0.0', port=6000, threaded=True)

    atexit.register(scheduler.shutdown)

if __name__ == '__main__':
    main()
