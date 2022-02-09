from django.test import TestCase, Client


class CoreURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_url_404_correct_template(self):
        """ "Страница 404 отдает кастомный шаблон"""
        template = "core/404.html"
        response = self.guest_client.get("/unexisting_page/")
        self.assertTemplateUsed(response, template)
