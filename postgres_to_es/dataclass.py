import datetime as dt
import uuid
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Person:
    """Класс для представления персоны"""
    id: uuid.UUID
    name: str


@dataclass
class Genre:
    """Класс для представления жанра"""
    id: uuid.UUID
    name: str


@dataclass
class Filmwork:
    """Класс для представления фильма"""
    id: uuid.UUID
    title: str
    description: str
    imdb_rating: float
    type: str
    created_at: dt.datetime
    updated_at: dt.datetime
    actors: Optional[List[Person]] = None
    directors: Optional[List[Person]] = None
    writers: Optional[List[Person]] = None
    actors_names: Optional[List[str]] = None
    director: Optional[List[str]] = None
    writers_names: Optional[List[str]] = None
    genre: List[Optional[Genre]] = field(default_factory=list)

    def add_person(self, role: str, person: Person) -> None:
        """Добавляет персон в фильм в соответствии с ролью"""
        if role == 'actor':
            if not self.actors:
                self.actors = []
                self.actors_names = []
            if person not in self.actors:
                self.actors.append(person)
                self.actors_names.append(person.name)
        if role == 'director':
            if not self.director:
                self.director = []
                self.directors = []
            if person not in self.directors:
                self.directors.append(person)
                self.director.append(person.name)
        if role == 'writer':
            if not self.writers:
                self.writers = []
                self.writers_names = []
            if person not in self.writers:
                self.writers.append(person)
                self.writers_names.append(person.name)

    def add_genre(self, genre: Genre) -> None:
        "Добаляет жанры"
        if genre not in self.genre:
            self.genre.append(genre)


@dataclass
class FilmworkStorage:
    """
    Класс-контейнер для хранения объектов Filmwork
    """
    objects: List[Optional[Filmwork]] = field(default_factory=list)

    def get_or_append(self, film: Filmwork) -> Filmwork:
        """
        Добавляет фильм, если фильма с таким id нет в контейнере.
        Иначе возвращает фильм с таким id из контейнера
        """
        if self.count:
            for item in self.objects:
                if item.id == film.id:
                    return item
        self.objects.append(film)
        return film

    def get_all(self) -> List[Optional[Filmwork]]:
        """Возвращает все сохранненные фильмы в контейнере"""
        return self.objects

    def count(self) -> int:
        """Возвращцает количество объектов в контейнере"""
        return len(self.objects)

    def clear(self) -> None:
        """Удаляет содержимое контейнера"""
        self.objects.clear()
