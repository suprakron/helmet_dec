from ultralytics import YOLO
import cv2

 
model = YOLO('yolov8n.pt')

def detect_helmet(image):
    """
    ตรวจจับหมวกกันน็อกในภาพด้วย YOLOv8n
    """
    results = model(image)
    detections = results[0].boxes.data.cpu().numpy()

    persons, helmets = [], []
    for det in detections:
        x1, y1, x2, y2, conf, cls = det
        cls_name = model.names[int(cls)]
        if cls_name == 'person':
            persons.append((x1, y1, x2, y2))
        elif 'helmet' in cls_name.lower():
            helmets.append((x1, y1, x2, y2))

    if len(persons) > 0 and len(helmets) == 0:
        return False  
    return True  
