from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("students/", views.student_list, name="student_list"),
    path("students/create/", views.student_create, name="student_create"),
    path("students/edit/<int:pk>/", views.student_edit, name="student_edit"),
    path("detection/", views.live_detection, name="live_detection"),
    path("api/upload_image/", views.upload_image, name="upload_image"),
    path("report/", views.generate_report, name="generate_report"),
    # path("live_video/", views.live_video, name="live_video"),
    path("live/", views.live_page, name="live_page"),
    path("live/video/", views.live_video, name="live_video"),
    path("daily_no_helmet/", views.daily_no_helmet, name="daily_no_helmet"),
    path(
        "report/student/<int:student_id>/",
        views.generate_student_report,
        name="student_report",
    ),
    path(
        "report/daily_no_helmet/",
        views.generate_daily_no_helmet_report,
        name="daily_no_helmet_report",
    ),
]
