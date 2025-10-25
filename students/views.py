import os 
import time 
import cv2 
import numpy 
import hashlib as np
from django.shortcuts import render, redirect, get_object_or_404
from io import BytesIO
from django.core.files.base import ContentFile
from django.http import JsonResponse, FileResponse,HttpResponse
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
from django.http import FileResponse
from reportlab.platypus import Table, TableStyle, Paragraph, SimpleDocTemplate, Image
 
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from .models import Student, DetectionLog
from .helmet_detector import detect_helmet
from .forms import StudentForm
from datetime import datetime
from ultralytics import YOLO
from PIL import Image
from django.http import StreamingHttpResponse
from django.utils import timezone
from datetime import datetime

model = YOLO("helmet_detection/yolov8n.pt")

@csrf_exempt
def upload_image(request):
    if request.method == "POST":
        image_data = request.body   
        if not image_data:
            return JsonResponse({'status': 'failed'})

        from django.core.files.base import ContentFile
        log = DetectionLog.objects.create(
            image=ContentFile(image_data, name=f"capture_{int(time.time())}.jpg"),
            helmet_detected=False,
            student=None
        )
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed'})
def should_save_log(last_save_time, interval=5):
    """
    เช็คว่าถึงเวลาบันทึก log ใหม่หรือยัง
    interval = วินาที
    """
    return (time.time() - last_save_time) >= interval
def gen_frames():
    stream_url = "http://172.20.10.5/stream"

    cap = cv2.VideoCapture(stream_url)

    if not cap.isOpened():
        print("❌ ไม่สามารถเชื่อมต่อกล้องได้:", stream_url)
        return

    last_save_time = 0  # เก็บเวลาที่บันทึก log ล่าสุด

    while True:
        success, frame = cap.read()
        if not success:
            print("⚠️  Lost connection, reconnecting...")
            cap.release()
            time.sleep(2)
            cap = cv2.VideoCapture(stream_url)
            continue

        # 🔍 ตรวจจับหมวกด้วย YOLO
        results = model(frame, verbose=False)

        bboxes = []  # เก็บ bounding box ของแต่ละคน

        for r in results:
            boxes = r.boxes.xyxy.cpu().numpy()
            class_ids = r.boxes.cls.cpu().numpy()
            confs = r.boxes.conf.cpu().numpy()

            for (box, cls, conf) in zip(boxes, class_ids, confs):
                x1, y1, x2, y2 = map(int, box)
                label = model.names[int(cls)]

                # 🔴 ไม่สวมหมวก / 🟢 สวมหมวก
                if label.lower() in ["no helmet", "no_helmet", "without_helmet"]:
                    color = (0, 0, 255)
                    text = "ไม่สวมหมวก"
                else:
                    color = (0, 255, 0)
                    text = "สวมหมวก"

                # วาดกล่อง + label
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{text} ({conf:.2f})",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                # เก็บ bbox สำหรับ log
                bboxes.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2, "class": text, "conf": float(conf)})

        # บันทึก log ทุก N วินาที และตรวจสอบความซ้ำซ้อน
        if should_save_log(last_save_time, interval=5):
            last_save_time = time.time()
            image_bytes = cv2.imencode('.jpg', frame)[1].tobytes()
            image_hash = hashlib.sha256(image_bytes).hexdigest()

            # ตรวจสอบ log ล่าสุด
            last_log = DetectionLog.objects.order_by('-timestamp').first()
            if not last_log or last_log.image_hash != image_hash:
                # บันทึก log ใหม่
                DetectionLog.objects.create(
                    image=ContentFile(image_bytes, name=f"capture_{int(time.time())}.jpg"),
                    helmet_detected=any(b['class']=="สวมหมวก" for b in bboxes),
                    bboxes=bboxes,
                    image_hash=image_hash
                )

        # แปลงภาพเป็น JPEG เพื่อสตรีม
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        cv2.waitKey(1)  # ช่วยให้ลื่นขึ้น

    cap.release()
# -----------------------------
# Endpoint สำหรับ Template
# -----------------------------
def live_video(request):
    return StreamingHttpResponse(gen_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame')
 

def live_page(request):
    return render(request, 'students/live_video.html')

def generate_report(request):
    """
    สร้างรายงาน PDF แสดงนักเรียนที่ไม่สวมหมวก พร้อมรายละเอียด
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    title = Paragraph("รายงานนักเรียนไม่สวมหมวกกันน็อก (ประจำวัน)", styles['Title'])
    elements.append(title)
    elements.append(Paragraph("โรงเรียน: โรงเรียนตัวอย่าง", styles['Normal']))
    elements.append(Paragraph("วัน/เวลา: {}".format(datetime.now().strftime("%d/%m/%Y")), styles['Normal']))
    elements.append(Paragraph("<br/>", styles['Normal']))  # เว้นบรรทัด

    # ดึง log ล่าสุดนักเรียนไม่สวมหมวก
    logs = DetectionLog.objects.filter(helmet_detected=False).order_by('timestamp')

    # สร้าง header table
    data = [["เวลา", "รหัสนักเรียน", "ชื่อ-สกุล", "ระดับชั้น", "แผนก", "ครูประจำชั้น", "ผลตรวจจับ"]]

    for log in logs:
        student = log.student
        student_id = student.student_id if student else "-"
        full_name = student.full_name if student else "ไม่ทราบชื่อ"
        level = student.level if student else "-"
        department = student.department if student else "-"
        teacher = student.teacher if student else "-"
        helmet_status = "ไม่สวมหมวก" if not log.helmet_detected else "สวมหมวก"

        data.append([log.timestamp.strftime('%H:%M:%S'), student_id, full_name, level, department, teacher, helmet_status])

    # สร้าง Table
    table = Table(data, colWidths=[60, 70, 120, 50, 60, 80, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="helmet_report.pdf")
def generate_student_report(request, student_id):
    student = Student.objects.filter(pk=student_id).first()
    if not student:
        return HttpResponse("ไม่พบข้อมูลนักเรียน")

    logs = DetectionLog.objects.filter(student=student).order_by('timestamp')

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"รายงานตรวจสอบหมวก: {student.full_name}", styles['Title']))
    elements.append(Paragraph(f"วันที่สร้างรายงาน: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Paragraph("<br/>", styles['Normal']))

    # Table header
    data = [["เวลา", "ผลตรวจจับ", "รูปภาพ"]]

    for log in logs:
        helmet_status = "สวมหมวก" if log.helmet_detected else "ไม่สวมหมวก"
        # เพิ่มรูปนักเรียนลง PDF
        image_path = None
        if log.image and os.path.exists(log.image.path):
            image_path = log.image.path
        if image_path:
            img = Image(image_path, width=80, height=60)
        else:
            img = Paragraph("-", styles['Normal'])
        data.append([log.timestamp.strftime("%H:%M:%S"), helmet_status, img])

    table = Table(data, colWidths=[60, 80, 120])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"{student.full_name}_helmet_report.pdf")


# ---------------------- PDF รายวันไม่สวมหมวก ----------------------
def generate_daily_no_helmet_report(request):
    today = datetime.now().date()
    logs = DetectionLog.objects.filter(helmet_detected=False, timestamp__date=today).order_by('timestamp')

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph("รายชื่อนักเรียนไม่สวมหมวกวันนี้", styles['Title']))
    elements.append(Paragraph(f"วันที่: {today.strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Paragraph("<br/>", styles['Normal']))

    # Table header
    data = [["เวลา", "รหัสนักเรียน", "ชื่อ-สกุล", "ระดับชั้น", "แผนก", "ครูประจำชั้น"]]

    for log in logs:
        student = log.student
        data.append([
            log.timestamp.strftime("%H:%M:%S"),
            student.student_id if student else "-",
            student.full_name if student else "ไม่ทราบชื่อ",
            student.level if student else "-",
            student.department if student else "-",
            student.teacher if student else "-"
        ])

    table = Table(data, colWidths=[60, 70, 120, 50, 60, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"daily_no_helmet_{today}.pdf")


def live_detection(request):
    logs = DetectionLog.objects.order_by("-timestamp")[:20]  # ล่าสุด 20 ภาพ
    return render(request, "students/live_detection.html", {"logs": logs})


def dashboard(request):
    students = Student.objects.all()
    detection_logs = DetectionLog.objects.filter(helmet_detected=False).order_by(
        "-timestamp"
    )[
        :20
    ]  # ล่าสุด 20 คน
    return render(
        request,
        "students/dashboard.html",
        {"students": students, "detection_logs": detection_logs},
    )

def daily_no_helmet(request):
    """
    แสดงรายชื่อนักเรียนที่ไม่สวมหมวกในวันปัจจุบัน
    """
    today = timezone.now().date()
    # filter log ของวันนี้และไม่สวมหมวก
    logs = DetectionLog.objects.filter(
        helmet_detected=False,
        timestamp__date=today
    ).order_by('timestamp')

    return render(request, "students/daily_no_helmet.html", {"logs": logs})

def student_list(request):
    students = Student.objects.all()
    return render(request, "students/student_list.html", {"students": students})


def student_create(request):
    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            print("Saved successfully") 
            return redirect("student_list")   
    else:
        form = StudentForm()
    return render(request, "students/student_form.html", {"form": form})


def student_edit(request, pk):
    student = Student.objects.get(pk=pk)
    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            return redirect("student_list")
    else:
        form = StudentForm(instance=student)
    return render(request, "students/student_form.html", {"form": form})
