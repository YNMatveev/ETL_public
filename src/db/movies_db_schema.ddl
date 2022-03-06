CREATE SCHEMA IF NOT EXISTS content;

CREATE TYPE filmwork_type AS ENUM ('movie', 'tv_show');

CREATE TABLE IF NOT EXISTS content.film_work (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title varchar(255) NOT NULL,
    description text,
    creation_date date,
    certificate text,
    file_path text,
    rating float(1) DEFAULT 0.0 CONSTRAINT min_max_rating CHECK (rating >= 0 AND rating <= 10),
    type filmwork_type NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);

CREATE TABLE IF NOT EXISTS content.person (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name varchar(255) NOT NULL,
    birth_date date,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);

CREATE TABLE IF NOT EXISTS content.genre (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name varchar(255),
    description text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);

CREATE TYPE person_role AS ENUM ('actor', 'director', 'writer');

CREATE TABLE IF NOT EXISTS content.person_film_work (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    film_work_id uuid REFERENCES content.film_work(id) ON DELETE CASCADE,
    person_id uuid REFERENCES content.person(id) ON DELETE CASCADE,
    role person_role NOT NULL,
    created_at timestamp with time zone
);

CREATE UNIQUE INDEX film_work_person_role ON content.person_film_work (film_work_id, person_id, role);

CREATE TABLE IF NOT EXISTS content.genre_film_work (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    film_work_id uuid REFERENCES content.film_work(id) ON DELETE CASCADE,
    genre_id uuid REFERENCES content.genre(id) ON DELETE CASCADE,
    created_at timestamp with time zone
);

CREATE UNIQUE INDEX film_work_genre ON content.genre_film_work (film_work_id, genre_id);
