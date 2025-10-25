from django import forms
from .models import Student

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'
        widgets = {
            'student_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'กรอกรหัสนักเรียน เช่น 65321001'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ชื่อ-นามสกุลนักเรียน'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'แผนกวิชา'
            }),
            'level': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ระดับชั้น เช่น ปวช.2'
            }),
            'classroom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ห้องเรียน เช่น 2/3'
            }),
            'homeroom_teacher': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ครูที่ปรึกษา'
            }),
            'head_of_department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'หัวหน้าแผนก'
            }),
            'photo': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'student_id': 'รหัสนักเรียน',
            'full_name': 'ชื่อ-นามสกุล',
            'department': 'แผนก',
            'level': 'ระดับชั้น',
            'classroom': 'ห้องเรียน',
            'homeroom_teacher': 'ครูที่ปรึกษา',
            'head_of_department': 'หัวหน้าแผนก',
            'photo': 'รูปถ่าย',
        }