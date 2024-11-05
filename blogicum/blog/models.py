from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class PublishedModel(models.Model):
    is_published = models.BooleanField(
        default=True,
        verbose_name="Опубликовано",
        help_text="Снимите галочку, чтобы скрыть публикацию.")
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name="Добавлено")

    class Meta:
        abstract = True


class Post(PublishedModel):
    title = models.CharField(max_length=256,
                             blank=False,
                             verbose_name="Заголовок")
    text = models.TextField(blank=False, verbose_name="Текст")
    pub_date = models.DateTimeField(
        blank=False,
        verbose_name="Дата и время публикации",
        help_text=("Если установить дату и время в будущем — можно делать "
                   + "отложенные публикации."))
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               blank=False,
                               related_name='posts',
                               verbose_name="Автор публикации")
    location = models.ForeignKey("Location",
                                 on_delete=models.SET_NULL,
                                 null=True,
                                 verbose_name="Местоположение")
    category = models.ForeignKey("Category",
                                 on_delete=models.SET_NULL,
                                 blank=False, null=True,
                                 verbose_name="Категория")
    image = models.ImageField('Фото', blank=True)

    def __str__(self):
        return self.title

    def comment_count(self):
        return self.comments.count()

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = "публикация"
        verbose_name_plural = "Публикации"


class Category(PublishedModel):
    title = models.CharField(max_length=256,
                             blank=False,
                             verbose_name="Заголовок")
    description = models.TextField(blank=False,
                                   verbose_name="Описание")
    slug = models.SlugField(
        unique=True, blank=False,
        verbose_name="Идентификатор",
        help_text=("Идентификатор страницы для URL; разрешены символы "
                   + "латиницы, цифры, дефис и подчёркивание."))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "Категории"


class Location(PublishedModel):
    name = models.CharField(
        max_length=256,
        blank=False,
        verbose_name="Название места")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "местоположение"
        verbose_name_plural = "Местоположения"


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField('Оставьте ваш комментарий')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at',)
