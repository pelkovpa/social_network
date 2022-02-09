from django.core.cache import cache
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django import forms
from django.conf import settings

from posts.models import Post, Group, Comment, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.user_author = User.objects.create_user(username="auth")
        cls.user = User.objects.create_user(username="NoName")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text="Тестовый пост",
            group=cls.group,
            image=SimpleUploadedFile(
                name="small.gif", content=small_gif, content_type="image/gif"
            ),
        )
        cls.comment = Comment.objects.create(
            post=cls.post, author=cls.user_author, text="Тестовый комментарий"
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.user_author,
        )
        cls.author_client = Client()
        cls.author_client.force_login(cls.user_author)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client_1 = Client()
        cls.user_authorized = User.objects.create(username="authorized")
        cls.authorized_client_1.force_login(cls.user_authorized)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_posts", kwargs={"slug": "test_slug"}
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={"username": "NoName"}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": "1"}
            ): "posts/post_detail.html",
            reverse("posts:post_create"): "posts/create_post.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": "1"}
            ): "posts/create_post.html",
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_create_and_edit_show_correct_form(self):
        """Шаблон post_create и post_edit формируют правильные формы."""
        response_create = self.authorized_client.get(
            reverse("posts:post_create")
        )
        response_edit = self.author_client.get(
            reverse("posts:post_edit", kwargs={"post_id": "1"})
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field_create = response_create.context.get(
                    "form"
                ).fields.get(value)
                form_field_edit = response_edit.context.get("form").fields.get(
                    value
                )
                self.assertIsInstance(form_field_create, expected)
                self.assertIsInstance(form_field_edit, expected)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.author_client.get(reverse("posts:index"))
        object = response.context["page_obj"][0]
        post_text = object.text
        post_author = object.author.username
        post_image = object.image
        self.assertEqual(post_text, "Тестовый пост")
        self.assertEqual(post_author, "auth")
        self.assertEqual(post_image, "posts/small.gif")

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse("posts:group_posts", kwargs={"slug": "test_slug"})
        )
        object_post = response.context["page_obj"][0]
        post_text = object_post.text
        post_author = object_post.author.username
        post_image = object_post.image
        self.assertEqual(post_text, "Тестовый пост")
        self.assertEqual(post_author, "auth")
        self.assertEqual(post_image, "posts/small.gif")

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse("posts:profile", kwargs={"username": "auth"})
        )
        object = response.context["page_obj"][0]
        post_text = object.text
        post_author = object.author.username
        post_image = object.image
        self.assertEqual(post_text, "Тестовый пост")
        self.assertEqual(post_author, "auth")
        self.assertEqual(post_image, "posts/small.gif")

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse("posts:post_detail", kwargs={"post_id": "1"})
        )
        object_post = response.context["post"]
        post_text = object_post.text
        post_author = object_post.author.username
        post_image = object_post.image
        object_comments = response.context["comments"][0]
        comment_text = object_comments.text
        comment_author = object_comments.author.username
        self.assertEqual(post_text, "Тестовый пост")
        self.assertEqual(post_author, "auth")
        self.assertEqual(post_image, "posts/small.gif")
        self.assertEqual(comment_text, "Тестовый комментарий")
        self.assertEqual(comment_author, "auth")

    def test_cache_index_page(self):
        """Кэш страницы index работает правильно"""
        response = self.authorized_client.get(reverse("posts:index"))
        content = response.content
        Post.objects.get(id=1).delete()
        response = self.authorized_client.get(reverse("posts:index"))
        content_1 = response.content
        cache.clear()
        response = self.authorized_client.get(reverse("posts:index"))
        content_cache_clear = response.content
        self.assertEqual(content, content_1)
        self.assertNotEqual(content, content_cache_clear)

    def test_user_can_follow_and_unfollow_author(self):
        """Авторизированный пользователь может подписаться на автора
        и удалить из подписок"""
        # После подписки на автора количество объектов Follow увеличивается
        self.authorized_client_1.get(
            reverse("posts:profile_follow", kwargs={"username": "auth"})
        )
        self.assertEqual(len(Follow.objects.all()), 2)
        # После отписки от автора количество объектов Follow уменьшается
        self.authorized_client_1.get(
            reverse("posts:profile_unfollow", kwargs={"username": "auth"})
        )
        self.assertEqual(len(Follow.objects.all()), 1)

    def test_follow_page_show_correct_context(self):
        """Pапись пользователя появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан."""
        # Подписанный на автора пользователь видит пост автора
        response = self.authorized_client.get(reverse("posts:follow_index"))
        object = response.context["page_obj"][0]
        object_text = object.text
        self.assertEqual(object_text, "Тестовый пост")
        self.assertEqual(len(response.context["page_obj"]), 1)
        # Не подписанный на автора пользователь не видит его постов
        response = self.author_client.get(reverse("posts:follow_index"))
        self.assertEqual(len(response.context["page_obj"]), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        NUMBER_OF_POSTS = 12
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_slug",
            description="Тестовое описание",
        )
        for i in range(NUMBER_OF_POSTS):
            cls.post = Post.objects.create(
                author=cls.user, text="Тестовый пост", group=cls.group
            )
        cls.author_client = Client()
        cls.author_client.force_login(cls.user)

    def test_first_page_contains_ten_records(self):
        # Проверка: количество постов на первой странице равно 10.
        response_posts = self.author_client.get(reverse("posts:index"))
        response_group_list = self.author_client.get(
            reverse("posts:group_posts", kwargs={"slug": "test_slug"})
        )
        response_profile = self.author_client.get(
            reverse("posts:profile", kwargs={"username": "auth"})
        )
        self.assertEqual(len(response_posts.context["page_obj"]), 10)
        self.assertEqual(len(response_group_list.context["page_obj"]), 10)
        self.assertEqual(len(response_profile.context["page_obj"]), 10)

    def test_second_page_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response_posts = self.author_client.get(
            reverse("posts:index") + "?page=2"
        )
        response_group_list = self.author_client.get(
            reverse("posts:group_posts", kwargs={"slug": "test_slug"})
            + "?page=2"
        )
        response_profile = self.author_client.get(
            reverse("posts:profile", kwargs={"username": "auth"}) + "?page=2"
        )
        self.assertEqual(len(response_posts.context["page_obj"]), 2)
        self.assertEqual(len(response_group_list.context["page_obj"]), 2)
        self.assertEqual(len(response_profile.context["page_obj"]), 2)
