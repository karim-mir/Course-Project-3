import psycopg2
from psycopg2 import sql
import configparser

class DBManager:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('../database.ini')

        if 'postgresql' not in config:
            print("Секция [postgresql] не найдена в файле database.ini")

        # Получаем параметры подключения из файла
        self.host = config['postgresql']['host']
        self.user = config['postgresql']['user']
        self.password = config['postgresql']['password']
        self.port = config['postgresql']['port']
        self.dbname = config['postgresql']['dbname']

        # Подключаемся к PostgreSQL без указания базы данных
        self.connection = psycopg2.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            port=self.port,
            database='postgres'  # Подключаемся к существующей базе данных
        )
        self.cursor = self.connection.cursor()
        self.create_database()  # Создаем базу данных, если она не существует
        self.connection.close()  # Закрываем текущее соединение

        # Подключаемся к только что созданной базе данных
        self.connection = psycopg2.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            port=self.port,
            database=self.dbname
        )
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_database(self):
        try:
            self.cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.dbname)))
            self.connection.commit()
        except psycopg2.errors.DuplicateDatabase:
            print(f"Database {self.dbname} already exists.")

    def create_tables(self):
        # Создание таблицы для организаций
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                vacancies_count INTEGER DEFAULT 0
            );
        """)

        # Создание таблицы для вакансий
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS vacancies (
                id SERIAL PRIMARY KEY,
                company_id INTEGER REFERENCES companies(id),
                title VARCHAR(255) NOT NULL,
                salary INTEGER,
                url VARCHAR(255) NOT NULL
            );
        """)
        self.connection.commit()

    def close(self):
        self.cursor.close()
        self.connection.close()

    def insert_company(self, name):
        self.cursor.execute("""
            INSERT INTO companies (name) VALUES (%s) RETURNING id;
        """, (name,))
        company_id = self.cursor.fetchone()[0]
        self.connection.commit()  # Сохраняем изменения
        return company_id

    def insert_vacancy(self, company_id, title, salary, url):
        self.cursor.execute("""
            INSERT INTO vacancies (company_id, title, salary, url) VALUES (%s, %s, %s, %s);
        """, (company_id, title, salary, url))
        self.connection.commit()

    def get_companies_and_vacancies_count(self):
        self.cursor.execute("""
            SELECT c.name, COUNT(v.id)
            FROM companies c 
            LEFT JOIN vacancies v ON c.id = v.company_id 
            GROUP BY c.id;
        """)
        return self.cursor.fetchall()

    def get_all_vacancies(self):
        self.cursor.execute("""
            SELECT c.name, v.title, v.salary, v.url 
            FROM vacancies v 
            JOIN companies c ON v.company_id = c.id;
        """)
        return self.cursor.fetchall()

    def get_avg_salary(self):
        self.cursor.execute("""
            SELECT AVG(salary) FROM vacancies;
        """)
        return self.cursor.fetchone()[0]

    def get_vacancies_with_higher_salary(self):
        avg_salary = self.get_avg_salary()
        self.cursor.execute("""
            SELECT c.name, v.title, v.salary, v.url 
            FROM vacancies v 
            JOIN companies c ON v.company_id = c.id 
            WHERE v.salary > %s;
        """, (avg_salary,))
        return self.cursor.fetchall()

    def get_vacancies_with_keyword(self, keyword):
        self.cursor.execute("""
            SELECT c.name, v.title, v.salary, v.url 
            FROM vacancies v 
            JOIN companies c ON v.company_id = c.id 
            WHERE v.title ILIKE %s;
        """, (f'%{keyword}%',))
        return self.cursor.fetchall()
