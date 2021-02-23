from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from posts.models import Post, Group
from django.urls import reverse
import tempfile
from django.conf import settings
import shutil
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.forms import PostForm
from django.core.cache import cache

User = get_user_model()


class PostCreateTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        cls.author = User.objects.create(username='roman')
        cls.group = Group.objects.create(
            title='test_title',
            slug='test_slug',
            description='test_desc'
        )

        cls.post = Post.objects.create(
            text='test_text',
            author=cls.author,
            group=cls.group
        )

        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = PostCreateTest.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        cache.clear()

    def test_form_edit_post(self):
        """при редактировании поста через форму на странице
        /<username>/<post_id>/edit/
        изменяется соответствующая запись в базе данных"""
        form_data = {'group': self.group.id,
                     'text': 'modified-post',
                     }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'username': self.user,
                                               'post_id': self.post.id}),
            data=form_data,
            follow=True
        )

        self.post.refresh_from_db()
        self.assertEqual(self.post.text, form_data['text'])

    def test_create_post_with_image(self):
        """Валидная форма создает запись в Post with image."""
        # Подсчитаем количество записей в Task
        tasks_count = Post.objects.count()
        # Для тестирования загрузки изображений
        # берём байт-последовательность картинки,
        # состоящей из двух пикселей: белого и чёрного
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        form_data = {'group': PostCreateTest.group.id,
                     'text': 'test_text',
                     'image': uploaded,
                     }

        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('posts:index'))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), tasks_count + 1)
        self.assertTrue(Post.objects.filter(
            group=PostCreateTest.group).exists())

    def test_downloat_not_image(self):
        """Тест загрузки формата изображения"""

        not_image = SimpleUploadedFile(
            name='test.txt',
            content=b'test',
            content_type='text/plain'
        )
        form_data = {'group': PostCreateTest.group.id,
                     'text': 'test_text',
                     'image': not_image,
                     }
        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )

        self.assertFormError(response, 'form',
                             'image',
                             errors=['Upload a valid image. The file you'
                                     ' uploaded was either not an image or'
                                     ' a corrupted image.'])
