import datetime as dt
from functools import wraps
from time import sleep

import elasticsearch
import psycopg2


def backoff(start_sleep_time=0.01, factor=2, border_sleep_time=4,
            logger=None, is_connection=True):

    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            _factor = factor
            counter = 1
            begin = dt.datetime.now()
            while True:
                try:
                    connection = func(*args, **kwargs)
                    finish_time = (dt.datetime.now() - begin).total_seconds()
                    if logger and is_connection:
                        logger.info('Попыток: %s. Время: %s секунд',
                                    counter, finish_time)
                    return connection
                except psycopg2.OperationalError:
                    if logger:
                        logger.error('Не удается подлкючиться к postgres')
                except elasticsearch.ConnectionError:
                    if logger:
                        logger.error('Не удается подлкючиться к elasticsearch')
                wait = min(start_sleep_time * 2 ** _factor, border_sleep_time)
                _factor += 1
                counter += 1
                sleep(wait)

        return inner
    return func_wrapper
