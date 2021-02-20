from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_app_accessible_by_name(self):
        """URL, генерируемый при помощи имени
        - about:author
        - about:tech , доступен.
        """
        templates_url_names = ['about:author',
                               'about:tech',
                               ]

        for reverse_name in templates_url_names:
            with self.subTest():
                response = self.guest_client.get(reverse(reverse_name))
                self.assertEqual(response.status_code, 200)

    def test_app_page_uses_correct_template(self):
        """При запросе к - about:author about:tech
        применяется соответсвующий шаблон.
        """

        templates_url_names = {'about/author.html': 'about:author',
                               'about/tech.html': 'about:tech',
                               }
        for template, reverse_name in templates_url_names.items():
            with self.subTest():
                response = self.guest_client.get(reverse(reverse_name))
                self.assertTemplateUsed(response, template)
