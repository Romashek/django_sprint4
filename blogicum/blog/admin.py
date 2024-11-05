# Библиотеки сторонних разработчиков
from django.contrib import admin

# Локальные импорты
from .models import Post, Category, Location


admin.site.register(Post)
admin.site.register(Category)
admin.site.register(Location)
