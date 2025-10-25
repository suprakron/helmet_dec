from ultralytics import YOLO

# โหลดโมเดลเริ่มต้น
model = YOLO("helmet_detection/yolov8n.pt")

# เทรนโมเดล
model.train(
    data="training/data.yaml",    
    epochs=100,                  
    imgsz=640,                   
    batch=8,                     
    name="helmet_yolov8_custom", 
    device=0                    
)
