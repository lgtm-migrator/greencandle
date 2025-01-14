#!/usr/bin/env python
#pylint: disable=no-member

"""
Redis cleanup-script
"""

import datetime
from greencandle.lib.redis_conn import Redis
from greencandle.lib.common import arg_decorator, epoch2date
from greencandle.lib import config

@arg_decorator
def main():
    """
    Cleanup old data from redis by removing candles > x days old
    depending on interval
    Run through cron, using pairs in config
    """

    pairs = config.main.pairs.split()

    data = {'5m': 1,
            '1h': 10,
            '4h': 50
            }

    redis = Redis()
    config.create_config()
    count = 0
    for interval, days in data.items():
        for pair in pairs:
            pair = pair.strip()
            print("Analysing pair {}".format(pair))
            items = redis.get_items(pair, interval)
            max_date = datetime.datetime.today() - datetime.timedelta(days=days)
            for item in items:
                epoch = float(item)/1000.0
                dtime = epoch2date(epoch, formatted=False)

                if dtime < max_date:
                    print("deleting {}".format(item))
                    count += 1
                    redis.conn.hdel("{}:{}".format(pair, interval), item)
    print("Deleted {} keys".format(count))


if __name__ == '__main__':
    main()
