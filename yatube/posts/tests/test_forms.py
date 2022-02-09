import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Post, Group, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user, text="Тестовый пост", group=cls.group
        )
        cls.author_client = Client()
        cls.author_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_create(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        form_data = {
            "group": self.group.id,
            "text": "Тестовый новый пост",
            "image": uploaded,
        }
        response = self.author_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                text="Тестовый новый пост",
                group=self.group.id,
                image="posts/small.gif",
            ).exists()
        )
        self.assertRedirects(
            response, reverse("posts:profile", kwargs={"username": "auth"})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_post_edit(self):
        """Валидная форма изменения записи в Post."""
        posts_count = Post.objects.count()
        small_gif_1 = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small_1.gif", content=small_gif_1, content_type="image/gif"
        )
        form_data = {
            "group": self.group.id,
            "text": "Редактированный пост",
            "image": uploaded,
        }
        response = self.author_client.post(
            reverse("posts:post_edit", kwargs={"post_id": "1"}),
            data=form_data,
            follow=True,
        )
        self.assertTrue(
            Post.objects.filter(
                text="Редактированный пост",
                group=self.group.id,
                image="posts/small_1.gif",
            ).exists()
        )
        self.assertRedirects(
            response, reverse("posts:post_detail", kwargs={"post_id": "1"})
        )
        self.assertEqual(Post.objects.count(), posts_count)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
        )
        cls.comment = Comment.objects.create(
            author=cls.user, text="Тестовый комментарий", post=cls.post
        )
        cls.authorized_client = Client()
        cls.user_1 = User.objects.create_user(username="authorized")
        cls.authorized_client.force_login(cls.user_1)
        cls.guest_client = Client()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_authorized_client_add_comment(self):
        """ "Авторизированный пользователь создает комментарий"""
        comment_count = Comment.objects.count()
        form_data = {"text": "Добавленный комментарий"}
        self.authorized_client.post(
            reverse("posts:add_comment", kwargs={"post_id": "1"}),
            data=form_data,
            follow=True,
        )
        self.assertTrue(Comment.objects.filter(text="Добавленный комментарий"))
        self.assertEqual(Comment.objects.count(), comment_count + 1)

    def test_guest_client_cant_add_comment(self):
        """ "Неавторизированный пользователь не может создать комментарий"""
        comment_count = Comment.objects.count()
        form_data = {"text": "Добавленный комментарий 1"}
        self.guest_client.post(
            reverse("posts:add_comment", kwargs={"post_id": "1"}),
            data=form_data,
            follow=True,
        )
        self.assertFalse(
            Comment.objects.filter(text="Добавленный комментарий 1")
        )
        self.assertEqual(Comment.objects.count(), comment_count)
