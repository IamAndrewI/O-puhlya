import os
from time import sleep
import configparser
import lib.DataBase as DB
import lib.aimodel as AI
from flask import Flask, render_template, request, jsonify, session, redirect,send_from_directory,send_file
from flask_cors import CORS
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader

# Reading config
config = configparser.ConfigParser()
config.read("conf/boardsettings.ini")
host = config["DB"]["host"]
database = config["DB"]["database"]
user = config["DB"]["user"]
password = config["DB"]["password"]
model_path = 'conf/best.pt'

# connect to DB
conn = DB.connect(host, database, user, password)
app = Flask(__name__)
CORS(app)
app.secret_key = 'ваш_секретный_ключ'
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    # Проверка на пустые поля
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Логин и пароль не могут быть пустыми'}), 400

    user_profile = DB.Check_access(conn, username, password)

    # Проверка на корректность данных пользователя
    if user_profile is None or user_profile[0] is None:
        return jsonify({'status': 'error', 'message': 'Неверный логин или пароль'}), 401

    session['user_profile'] = user_profile  # Сохраняем все данные о пользователе в сессии
    return jsonify({'status': 'success', 'redirect': '/application'})

@app.route('/api/get_user_info', methods=['GET'])
def get_user_info():
    user_profile = session.get('user_profile')
    if user_profile[0] is None:
        return jsonify({'status': 'error', 'message': 'Пользователь не авторизован'}), 401

    return jsonify({'status': 'success', 'data': user_profile})

@app.route('/application')
def success():
    return render_template('application.html')

@app.route('/logout')
def logout():
    session.pop('user_profile', None)  # Удаляем данные о пользователе из сессии
    return redirect('/')  # Перенаправляем на главную страницу
@app.route('/images/<path:filename>')

def send_image(filename):
    return send_from_directory('images', filename)

@app.route('/scan', methods=['POST'])
def scan():
    if 'image' not in request.files:
        return jsonify({'result': 'Не найдено изображение.'}), 400
    IMAGE_FOLDER = 'static/'

    image_file = request.files['image']
    
    # Путь к изображению
    image_path = os.path.join(IMAGE_FOLDER, image_file.filename)

    # Если файл уже существует, удаляем его
    if os.path.exists(image_path):
        os.remove(image_path)

    # Сохраните новое изображение на сервере
    image_file.save(image_path)

    # Вызов функции process
    prediction = AI.process(model_path, image_path)

    # Верните результаты в формате JSON
    return jsonify({'result': prediction})  # Предполагается, что prediction - это словарь с 'image_path' и 'details'
    # Верните результаты в формате JSON
    return jsonify({'result': prediction})  # Предполагается, что prediction - это словарь с 'image_path' и 'details'

@app.route('/api/get_patients', methods=['GET'])
def get_patients():
    user_profile = session.get('user_profile')
    if user_profile is None or user_profile[3] is None:
        return jsonify({'status': 'error', 'message': 'Пользователь не авторизован'}), 401

    doctor_id = user_profile[3]  # Получаем ID доктора из профиля
    patients = DB.Get_pat(conn, doctor_id)  # Получаем список пациентов

    if patients is None:
        return jsonify({'status': 'error', 'message': 'Нет пациентов для отображения'}), 404

    return jsonify({'status': 'success', 'data': patients})  # Возвращаем список пациентов

@app.route('/api/get_scan', methods=['GET'])
def get_scan():
    patient_id = request.args.get('patient_id')
    
    # Формируем имя файла на основе patient_id
    if patient_id is None:
        return jsonify({'status': 'error', 'message': 'Отсутствует patient_id.'}), 400
    
    # Здесь предполагается, что файл называется i{patient_id}.jpeg
    image_filename = f"i{patient_id}.jpg"
    
    # Формируем путь к изображению в папке static
    path = f"/static/{image_filename}"
    
    # Возвращаем путь к изображению
    return jsonify({'status': 'success', 'image_path': path})


@app.route('/api/generate_report', methods=['POST'])
def generate_report():
    user_profile = session.get('user_profile')
    data = request.json
    patient_id = data.get('patient_id')
    scan_result = data.get('scan_result')
    image_path = os.path.join('static', 'result_image.jpg')  # Получаем путь к изображению
    pat = DB.pat_inf(conn,patient_id)
    print(pat)
    # Проверка на наличие необходимых данных
    if patient_id is None or scan_result is None or image_path is None:
        return jsonify({'status': 'error', 'message': 'Отсутствуют необходимые данные.'}), 400

    # Создание директории, если она не существует
    report_directory = 'reports'
    if not os.path.exists(report_directory):
        os.makedirs(report_directory)

    report_path = f"{report_directory}/report_{patient_id}.pdf"

    try:
        # Регистрация шрифта
        pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))

        c = canvas.Canvas(report_path, pagesize=letter)
        width, height = letter
        # Установка шрифта
        c.setFont('DejaVu', 16)

        # Добавление информации
        c.drawString(150, height - 25, f"Отчёт о сканировании головного мозга")
        c.setFont('DejaVu', 12)
        c.drawString(100, height - 50, f"Пациент:{pat[0][0]} {pat[0][1]}")
        c.drawString(100, height - 70, f"Доктор: {user_profile[2]} {user_profile[0]} {user_profile[1]}")
        c.drawString(100, height - 90, f"Дата: {datetime.now().strftime('%Y-%m-%d')}")
        c.drawString(100, height - 110, "Результаты сканирования:")
        c.drawString(280, height - 110, scan_result)
        if os.path.exists(image_path):
            print(f"Изображение найдено: {image_path}")
        else:
            print(f"Изображение не найдено: {image_path}")
        # Добавление изображения
        if os.path.exists(image_path):
            image = ImageReader(image_path)
            img_width, img_height = image.getSize()    # Укажите нужные размеры
            max_width = 400  # Максимальная ширина области
            max_height = 400
            scale = min(max_width / img_width, max_height / img_height)
            new_width = img_width * scale
            new_height = img_height * scale
            c.drawImage(image_path, 100, height - 520, width=new_width, height=new_height, preserveAspectRatio=True)
        # Добавление места для подписи
        c.drawString(195, height - 550, "__________________________")
        c.drawString(100, height - 550, "Подпись врача")

        # Сохранение PDF
        c.save()

        return send_file(report_path, as_attachment=True)

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8800, debug=True)
