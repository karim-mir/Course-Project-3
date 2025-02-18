import requests
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Список идентификаторов вакансий
employer_ids = [2870783, 117380646, 117371466, 117236141, 117217826,
                117039142, 117112666, 116694017, 105334747, 115960991]


def get_employer_data(employer_id):
    employer_url = f'https://api.hh.ru/employers/{employer_id}'
    vacancy_url = f'https://api.hh.ru/vacancies?employer_id={employer_id}'

    try:
        # Получение информации о работодателе
        employer_response = requests.get(employer_url, timeout=10)
        if employer_response.status_code == 404:
            logging.error(f"Работодатель с ID {employer_id} не найден.")
            return None, None
        employer_response.raise_for_status()  # Проверка на другие ошибки
        employer_data = employer_response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при получении данных о работодателе {employer_id}: {e}")
        return None, None

    try:
        # Получение вакансий работодателя
        vacancy_response = requests.get(vacancy_url, timeout=10)
        if vacancy_response.status_code == 404:
            logging.error(f"Вакансии для работодателя с ID {employer_id} не найдены.")
            return employer_data, None
        vacancy_response.raise_for_status()  # Проверка на другие ошибки
        vacancy_data = vacancy_response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при получении вакансий для работодателя {employer_id}: {e}")
        return employer_data, None

    return employer_data, vacancy_data

def main():
    for employer_id in employer_ids:
        employer_data, vacancy_data = get_employer_data(employer_id)
        if employer_data and vacancy_data:
            logging.info(f"Работодатель: {employer_data['name']}")
            logging.info("Вакансии:")
            for vacancy in vacancy_data['items']:
                salary = vacancy.get('salary')
                currency = salary.get('currency', 'не указана') if salary else 'не указана'

                if salary:
                    salary_from = salary.get('from', 'не указана')
                    salary_to = salary.get('to', 'не указана')
                else:
                    salary_from = salary_to = 'не указана'

                logging.info(f"- {vacancy['name']} (Зарплата: {salary_from} - {salary_to} {currency})")
            logging.info("\n")
        else:
            logging.error(f"Ошибка при получении данных о работодателе {employer_id}: данные отсутствуют или недоступны.")

if __name__ == "__main__":
    main()
