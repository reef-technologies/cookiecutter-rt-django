from django.contrib import admin  # noqa
from django.contrib.admin import register  # noqa


admin.site.site_header = "{{ cookiecutter.django_project_name }} Administration"
admin.site.site_title = "{{ cookiecutter.django_project_name }}"
admin.site.index_title = "Welcome to {{ cookiecutter.django_project_name }} Administration"
