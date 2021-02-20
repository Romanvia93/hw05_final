from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Post, Group


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username='testuser'
        )
        cls.group = Group.objects.create(
            title='название группы',
            slug='слаг',
            description='описание группы'
        )
        cls.post = Post.objects.create(
            text='тестовый текст',
            pub_date='дата публикации',
            author=cls.author,
            group=cls.group
        )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Запись',
            'group': 'Группа'
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Сделайте запись Вашего поста',
            'group': 'Выбирите группу, куда попадет пост'
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_display_str(self):
        """В поле __str__  объектов group и post записаны поля title и text"""
        post = PostModelTest.post
        group = PostModelTest.group

        field_names = {post: post.text,
                       group: group.title
                       }

        for value, expected in field_names.items():
            with self.subTest(value=value):
                self.assertEqual(
                    str(value), expected)
