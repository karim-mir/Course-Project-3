import sys
from functools import wraps
from typing import Callable, Dict, Tuple
from database import DBManager
from api import employer_ids, get_employer_data

COMMANDS: Dict[str, Tuple[str, Callable]] = {}


def register_as_command(number: str, description: str):
    def decorator(func):
        COMMANDS[number] = (description, func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)

        return wrapper

    return decorator


@register_as_command('1', 'Создать базу данных и таблицы')
def create_database_command(db_manager: DBManager) -> None:
    db_manager.create_database_if_not_exists()  # Создание базы данных, если она не существует

    # Создание таблиц
    db_manager.cursor.execute('''
        CREATE TABLE IF NOT EXISTS organizations (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL
        );
    ''')
    db_manager.cursor.execute('''
        CREATE TABLE IF NOT EXISTS vacancies (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            organization_id INTEGER,
            FOREIGN KEY (organization_id) REFERENCES organizations (id)
        );
    ''')
    db_manager.connection.commit()
    print("База данных и таблицы созданы.")


@register_as_command('2', 'Заполнить таблицу организаций')
def fill_organizations_command(db_manager: DBManager) -> None:
    for employer_id in employer_ids:
        employer_data, _ = get_employer_data(employer_id)
        if employer_data:
            try:
                db_manager.cursor.execute('''
                    INSERT INTO organizations (id, name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING;
                ''', (employer_data['id'], employer_data['name']))
                db_manager.connection.commit()
            except Exception as e:
                print(f"Ошибка при добавлении организации {employer_data['name']}: {e}")
    print("Таблица организаций заполнена.")


@register_as_command('3', 'Заполнить таблицу вакансий')
def fill_vacancies_command(db_manager: DBManager) -> None:
    for employer_id in employer_ids:
        employer_data, vacancy_data = get_employer_data(employer_id)
        if vacancy_data:
            for vacancy in vacancy_data['items']:
                try:
                    db_manager.cursor.execute('''
                        INSERT INTO vacancies (title, organization_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;
                    ''', (vacancy['name'], employer_id))
                except Exception as e:
                    print(f"Ошибка при добавлении вакансии {vacancy['name']} для работодателя {employer_id}: {e}")
                    db_manager.connection.commit()
                    print("Таблица вакансий заполнена.")

@register_as_command('0', 'Выйти')
def exit_program(db_manager: DBManager) -> None:
    db_manager.close()
    print("До свидания")
    sys.exit(0)


def main():
    db_manager = DBManager()  # Создание экземпляра DBManager
    try:
        while True:
            print("\nВыберите команду:")
            for number, (description, _) in COMMANDS.items():
                print(f"{number}: {description}")

            choice = input("Введите номер команды: ")
            command = COMMANDS.get(choice)

            if command:
                description, func = command
                func(db_manager)
            else:
                print("Некорректный выбор. Пожалуйста, повторите.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        db_manager.close()  # Закрытие соединения с базой данных


if __name__ == "__main__":
    main()
