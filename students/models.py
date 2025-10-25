from django.db import models
import hashlib
from django.contrib.postgres.fields import JSONField 

class Student(models.Model):
    student_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    level = models.CharField(max_length=20)
    classroom = models.CharField(max_length=20)
    homeroom_teacher = models.CharField(max_length=100)
    head_of_department = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='students/')

    def __str__(self):
        return self.full_name


class DetectionLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to='detections/')
    timestamp = models.DateTimeField(auto_now_add=True)
    helmet_detected = models.BooleanField(default=True)

    bboxes = models.JSONField(default=list)
    image_hash = models.CharField(max_length=64, blank=True) 

    def save(self, *args, **kwargs):
        if self.image:
            self.image_hash = hashlib.sha256(self.image.read()).hexdigest()
            self.image.seek(0)
        super().save(*args, **kwargs)