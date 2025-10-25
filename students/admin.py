from django.contrib import admin
from .models import Student, DetectionLog

# แสดง Student ใน Admin
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'full_name', 'level', 'department', 'photo')
    search_fields = ('student_id', 'full_name', 'level', 'department')
    list_filter = ('level', 'department')

# แสดง DetectionLog ใน Admin
@admin.register(DetectionLog)
class DetectionLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'helmet_detected', 'timestamp', 'image')
    search_fields = ('student__full_name',)
    list_filter = ('helmet_detected', 'timestamp')
