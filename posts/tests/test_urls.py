from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from posts.models import Post, Group
from django.urls import reverse

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности
        cls.author = User.objects.create(
            username='testuser1'
        )

        cls.author2 = User.objects.create(
            username='testuser2'
        )

        cls.group = Group.objects.create(
            title='название группы',
            slug='test-slug',
            description='описание группы'
        )
        cls.post = Post.objects.create(
            text='тестовый текст',
            pub_date='дата публикации',
            author=cls.author,
            group=cls.group
        )

    def setUp(self):

        # Создаем неавторизованный клиент
        self.guest_client = Client()
        self.user = TaskURLTests.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        # Авторизуем клиента не автора поста
        self.user = TaskURLTests.author2
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {

            'posts/index.html': reverse('posts:index'),
            'group.html': reverse('posts:group', args=['test-slug']),
            'posts/new_post.html': reverse('posts:new_post'),
        }
        for template, reverse_name in templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_url_exists_for_any_users(self):
        """Главна Страница и стр. с групп. доступна любому пользователю."""
        templates_url_names = [reverse('posts:index'),
                               reverse('posts:group', args=['test-slug']),
                               reverse('posts:profile', args=['testuser1']),
                               reverse('posts:post', args=['testuser1', '1']),
                               ]

        for reverse_name in templates_url_names:
            with self.subTest():
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, 200)

    def test_url_exists_for_authorized_users(self):
        """Страница /new/ и /edit/ доступна авторизованному пользователю,
        автору поста."""
        templates_url_names = [reverse('posts:new_post'),
                               reverse('posts:post_edit',
                               args=['testuser1', '1']),
                               ]

        for reverse_name in templates_url_names:
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, 200)

    def test_task_url_redirect(self):
        """Страница по адресу:  /new/, /testuser1/1/edit/
          перенаправит анонимного пользователя на страницу логина."""
        templates_path_redirection = {
            reverse('posts:new_post'):
            f"/auth/login/?next={reverse('posts:new_post')}",
            reverse('posts:post_edit', args=['testuser1', '1']):
            f"/auth/login/?next="
            f"{reverse('posts:post_edit', args=['testuser1', '1'])}",
        }
        for path, redirection in templates_path_redirection.items():
            with self.subTest():
                response = self.guest_client.get(path)
                self.assertRedirects(response, redirection)

    def test_task_url_edit_not_exist_for_anonymous(self):
        """Ананимный пользователь не сможет редактировать пост."""
        response = self.guest_client.get(reverse('posts:post_edit',
                                         args=['testuser1', '1']))
        self.assertNotEqual(response.status_code, 200)

    def test_task_url_edit_not_exist_for_authorized_not_author(self):
        """Авторизованный пользователь - не автор не может
        редактировать пост."""
        response = self.authorized_client2.get(reverse('posts:post_edit',
                                               args=['testuser1', '1']))
        self.assertNotEqual(response.status_code, 200)

    def test_status_404_if_page_not_found(self):
        """Возвращает ли сервер код 404, если страница не найдена."""
        response = self.authorized_client.get(reverse('posts:profile',
                                              args=['user_not_in_bd']))
        self.assertEqual(response.status_code, 404)
