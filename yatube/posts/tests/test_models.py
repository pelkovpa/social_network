from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Тестовый слаг",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = self.group
        post = self.post
        name_group = group.title
        text_post = post.text
        self.assertEqual(name_group, str(group))
        self.assertEqual(text_post, str(post))

    def test_verbose_names(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verbose_post = {
            "text": "Текст поста",
            "group": "Группа",
            "author": "Автор",
        }
        for field, expected_value in field_verbose_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value,
                )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_text_post = {
            "text": "Введите текст поста",
            "group": "Выберите группу",
        }
        for field, expected_value in field_help_text_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text, expected_value
                )
