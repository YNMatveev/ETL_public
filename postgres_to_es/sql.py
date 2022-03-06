movies_data= """
    SELECT
        fw.id AS fw_id,
        fw.title,
        fw.description,
        fw.rating,
        fw.type,
        fw.created_at,
        fw.updated_at,
        pfw.role,
        p.id,
        p.full_name,
        g.id,
        g.name
    FROM content.film_work AS fw
    LEFT JOIN content.person_film_work AS pfw ON pfw.film_work_id = fw.id
    LEFT JOIN content.person AS p ON p.id = pfw.person_id
    LEFT JOIN content.genre_film_work AS gfw ON gfw.film_work_id = fw.id
    LEFT JOIN content.genre AS g ON g.id = gfw.genre_id
    WHERE fw.id IN %s;
"""

movies_ids = """
    SELECT DISTINCT fw.id
    FROM content.film_work AS fw
    LEFT JOIN content.person_film_work AS pfw ON pfw.film_work_id = fw.id
    LEFT JOIN content.person AS p ON p.id = pfw.person_id
    LEFT JOIN content.genre_film_work AS gfw ON gfw.film_work_id = fw.id
    LEFT JOIN content.genre AS g ON g.id = gfw.genre_id
    WHERE GREATEST(fw.updated_at, p.updated_at, g.updated_at) > %s
    ORDER BY fw.id;
"""
