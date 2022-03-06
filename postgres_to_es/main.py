import datetime as dt
import json
import logging
from dataclasses import asdict
from logging.config import dictConfig
from pathlib import Path
from time import sleep
from typing import Iterator, List, Tuple, Union

import elasticsearch
import psycopg2
import yaml
from elasticsearch import Elasticsearch, helpers
from psycopg2.extensions import connection as pg_connection
from psycopg2.extras import DictCursor

import sql
from backoff import backoff
from config import Config, DSNSettings, ESHost, ESSettings, PostgresSettings
from dataclass import Filmwork, FilmworkStorage, Genre, Person
from state import State, YamlFileStorage

CONFIG_FILENAME = 'config.yaml'
if __name__ == '__main__':
    logger = logging.getLogger(__name__)


class ElasticSaver:
    """Класс для работы с elasticsearch"""
    index_name: str
    host: ESHost
    index_config: str
    es_client: Elasticsearch

    def __init__(self, params: ESSettings):
        self.index_name = params.index_name
        self.host = params.default_host
        self.index_config = params.index_config
        self.es_client = self.get_es_client()
        if not self.check_index():
            self._create_index()

    def check_index(self) -> bool:
        """Проверяет существование индекса с указанным именем"""
        return self.es_client.indices.exists(index=self.index_name)

    @backoff(logger=logger)
    def get_es_client(self) -> Elasticsearch:
        """Создает клиент elasticsearch"""
        logger.info('Подключение к elasticsearch...')
        host = f'{self.host.host}:{self.host.port}'
        _client = Elasticsearch(hosts=host)
        _client.cluster.health(wait_for_status="yellow")
        logger.info('Соединение с elasticsearch успешно установлено!')
        return _client

    def _create_index(self) -> None:
        """Создает индекс с заданными настройками и названием"""
        path = Path(__file__).parent.joinpath(self.index_config)
        with open(path, 'r', encoding='utf-8') as index_file:
            index_settings = json.load(index_file)

        settings = index_settings.get('settings')
        mappings = index_settings.get('mappings')
        self.es_client.indices.create(index=self.index_name,
                                      settings=settings,
                                      mappings=mappings)

    def save_to_es(self, data: List[Filmwork]) -> None:
        """Загружает данные в индекс"""
        actions = [
            {
                "_index": "movies",
                "_id": movie.id,
                "_source": asdict(movie)
            }
            for movie in data
        ]
        while True:
            try:
                records, errors = helpers.bulk(client=self.es_client,
                                               actions=actions,
                                               raise_on_error=False,
                                               stats_only=True)

                if records:
                    logger.info('Фильмов обновлено в Elasticsearch: %s',
                                records)
                if errors:
                    logger.error(
                        'При обновлении Elasticsearch произошло ошибок: %s',
                        errors)
                return
            except elasticsearch.ConnectionError as error:
                logger.error(
                        'Отсутствует подключение к Elasticsearch %s',
                        error)
                self.es_client = self.get_es_client()


class DataTransformer:
    """
    Класс для преобразования данных из postgres в объекты класса Filmork и
    хранения их в контейнере для последующего сохранения в elasticsearch
    """
    inner_storage: FilmworkStorage

    def __init__(self):
        self.inner_storage = FilmworkStorage()

    def trasform_data(self, data: Iterator[Tuple]) -> List[Filmwork]:
        """Преобразует данные из postgres в объекты класса Filmork """
        if self.inner_storage:
            self.inner_storage.clear()

        for movie in data:
            film_id, *data, role, person_id, fullname, genre_id, name = movie
            candidate = Filmwork(film_id, *data)
            person = Person(person_id, fullname)
            genre = Genre(genre_id, name)
            movie = self.inner_storage.get_or_append(candidate)
            movie.add_person(role, person)
            movie.add_genre(genre)
        logger.info('Подготовлено фильмов к обновлению в еlasticsearch: %s',
                    self.inner_storage.count())

        return self.inner_storage.get_all()


class PostgresLoader:
    """Класс для выгрузки данных из postgres"""
    dsn: DSNSettings
    connection: pg_connection
    state: State
    check_date: dt.datetime
    limit: int

    def __init__(self, params: PostgresSettings, state: State):
        self.dsn = params.dsn
        self.connection = self.get_connection()
        self.state = state
        self.check_date = self.state.get_state('last_update') or dt.datetime.min
        self.limit = params.limit

    @backoff(logger=logger)
    def get_connection(self) -> pg_connection:
        """Создает подключение к postgres"""
        logger.info('Подключение к postgres...')
        with psycopg2.connect(**self.dsn.dict(), cursor_factory=DictCursor) as pg_conn:
            logger.info('Соединение с postgres успешно установлено')
            return pg_conn

    def executor(self, sql_query: str, params: tuple) -> Iterator[Tuple]:
        """Выполняет sql запрос"""
        while True:
            try:
                if self.connection.closed:
                    self.connection = self.get_connection()
                cursor = self.connection.cursor()
                cursor.execute(sql_query, params)
                while True:
                    chunk_data = cursor.fetchmany(self.limit)
                    if not chunk_data:
                        return
                    for row in chunk_data:
                        yield row
            except psycopg2.OperationalError as pg_error:
                logger.error('Ошибка соединения при выполнении SQL запроса %s',
                             pg_error)

    @backoff(logger=logger, is_connection=False)
    def load_data(self) -> Union[Iterator[Tuple], List]:
        """
        Выгружает из postgres данные, обновленные после указанной даты:
        - находит новые записи и определяет id изменившихся фильмов
        - выгружает информацию для этих фильмов
        """
        now = dt.datetime.utcnow()
        films_ids = self.executor(sql.movies_ids, (self.check_date,))
        films_ids = tuple([record[0] for record in films_ids])
        if films_ids:
            films_data = self.executor(sql.movies_data, (films_ids,))
            self.state.set_state('last_update', str(now))
            self.check_date = now
            return films_data
        return []


def setup_logger() -> None:
    """Настраивает логирование скрипта"""
    log_file = Path(__file__).parent.joinpath('log', 'etl.log')
    log_file.parent.mkdir(parents=True, exist_ok=True)
    config.logger['handlers']['file']['filename'] = log_file
    config.logger['handlers']['file_error']['filename'] = log_file
    dictConfig(config.logger)


def get_state_storage() -> State:
    """Настраиват контейнер для хранения состояний"""
    state_file_path = Path(__file__).parent.joinpath(config.etl.state_file_name)
    storage = YamlFileStorage(state_file_path)
    return State(storage)


def start_etl_process() -> None:
    """Запускает etl-процесс"""
    logger.info('Скрипт начал работу...')
    elastic = ElasticSaver(config.etl.es)
    state = get_state_storage()
    postgres = PostgresLoader(config.etl.postgres, state)
    transformer = DataTransformer()
    time_log_status = dt.datetime.utcnow()
    while True:
        now = dt.datetime.utcnow()
        data = postgres.load_data()
        if data:
            tranformed_data = transformer.trasform_data(data)
            elastic.save_to_es(tranformed_data)
        if now > time_log_status + dt.timedelta(seconds=config.etl.log_status_period):
            logger.info('Скрипт работает в штатном режиме...')
            time_log_status = now
        sleep(config.etl.fetch_delay)


if __name__ == '__main__':
    config_file = Path(__file__).parent.joinpath(CONFIG_FILENAME)
    config_dict = yaml.safe_load(config_file.open(encoding='utf-8'))
    config = Config.parse_obj(config_dict)
    setup_logger()
    start_etl_process()
