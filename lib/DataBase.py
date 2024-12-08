from dataclasses import dataclass
from sre_constants import SUCCESS
import psycopg2
import requests
from io import BytesIO
import uuid

def connect(h,db,us,p):
    conn=psycopg2.connect(host=h,database=db,user=us,password=p)
    print("Succesful connection to BD")
    return conn



def Get_pat(conn,doctor_id):
    cur = conn.cursor()
    cur.callproc('get_pat', (doctor_id,))
    profile = cur.fetchall()
    cur.close()
    return profile


def pat_inf(conn,pat_id):
    cur = conn.cursor()
    cur.execute("select surname,name,date_of_birth from patient where patient_id=(%s);", (pat_id,))
    profile = cur.fetchall()
    cur.close()
    return profile

def get_scan(conn, patient_id):
    # Подключение к базе данных и выполнение запроса
    cursor = conn.cursor()
    cursor.execute("SELECT get_scan_link(%s);", (patient_id,))
    file_path = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    # Параметры для доступа к PythonAnywhere
    username = 'Tonksy'
    api_token = '1f17ef2b15852f25408a5973ee759dcea57d42ea'

    # URL для запроса на скачивание файла
    url = f'https://www.pythonanywhere.com/api/v0/user/{username}/files/path/{file_path}'
    print(url)
    headers = {'Authorization': f'Token {api_token}'}
    # Выполнение GET-запроса для получения файла
    response = requests.get(url, headers=headers)
    print('url:',url)
    if response.status_code == 200:
        return url
    else:
        return None #print(f"Ошибка при загрузке: {response.status_code} - {response.text}")


def set_scan(conn, patient_id, date, img):

    # Настройки для PythonAnywhere
    username = 'Tonksy'
    api_token = '1f17ef2b15852f25408a5973ee759dcea57d42ea'

    # URL для загрузки файла на PythonAnywhere
    unique_id = uuid.uuid4()
    filename = f"{uuid.uuid4()}.jpg"
    url = f'https://www.pythonanywhere.com/api/v0/user/{username}/files/path/home/{username}/mysite/uploads/{filename}'
    headers = {'Authorization': f'Token {api_token}'}
    
    # Отправка файла на сервер PythonAnywhere
    response = requests.post(
        url,
        headers=headers,
        files={'content': img}
    )
    if response.status_code == 201:
        # Подключение к базе данных
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        # Обновляем путь к файлу в базе данных
        path = f'home/{username}/mysite/uploads/{filename}'
        cursor.execute("SELECT set_scan(%s, %s, %s);", (int(patient_id), date, path))
        cursor.fetchone()
        conn.commit()  # Коммит для сохранения изменений

        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()
    else:
        return # print(f"Ошибка при загрузке: {response.status_code} - {response.text}")




def Check_access(conn,login,password):
    cur = conn.cursor()
    cur.callproc('get_doctor', (login,password))
    profile = cur.fetchone()
    cur.close()
    return profile