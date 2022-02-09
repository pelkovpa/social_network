from core.models import CreatedModel
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(CreatedModel):
    text = models.TextField("Текст поста", help_text="Введите текст поста")
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор",
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="posts",
        verbose_name="Группа",
        help_text="Выберите группу",
    )
    image = models.ImageField("Картинка", upload_to="posts/", blank=True)

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "Пост"
        verbose_name_plural = "Посты"


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField()


class Follow(models.Model):
    # Пользователь, который подписывается
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="follower"
    )
    # Пользователь, на которого подписываются
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following"
    )
