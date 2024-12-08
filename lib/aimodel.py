from ultralytics import YOLO
import numpy as np
import cv2
import os


def process(model_path, image_path):
    # Загрузка модели
    model = YOLO(model_path)
    # Загрузка изображения
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Преобразование для корректного отображения
    # Предсказание
    results = model.predict(source=image_path, conf=0.25, save=False)  # Уверенность >= 25%
    res =''
    # Извлечение информации из результатов
    detections = results[0].boxes  # Все найденные bounding boxes
    if len(detections) > 0:
        for box in detections:
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Координаты рамки
            confidence = box.conf[0] * 100         # Уверенность в процентах
            label = f"Tumor: {confidence:.2f}%"   # Метка с уверенностью
            # Рисование рамки и текста
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Рамка (зеленая)
            res = f"Опухоль обнаружена, вероятность: {confidence:.2f}%"
    else:
        # Добавим текст на изображение для случая, когда опухоль не найдена
        res = 'Опухоль не обнаружена'

    # Создание пути для сохранения изображения в папке static
    result_image_filename = 'result_image.jpg'  # Имя файла
    result_image_path = os.path.join('static', result_image_filename)  # Путь к файлу

    # Сохранение изображения в папке static
    cv2.imwrite(result_image_path, image)

    return {'image_path': result_image_filename, 'details': res}  # Возвращаем имя файла
