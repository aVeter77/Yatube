from django.test import Client, TestCase
from django.urls import reverse


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

    def test_urls(self):
        """Страница доступна."""

        urls_dict = {
            reverse('about:author'): 200,
            reverse('about:tech'): 200,
        }
        for address, status in urls_dict.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_template(self):
        """URL-адрес использует соответствующий шаблон."""

        urls_templates = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }
        for address, template in urls_templates.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
