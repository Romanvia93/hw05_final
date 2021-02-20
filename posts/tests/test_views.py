from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from posts.models import Post, Group, Follow, Comment
from django.urls import reverse
from django import forms
import tempfile
from django.conf import settings
import shutil
import tempfile
from django.conf import settings
import shutil
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.forms import PostForm
import time
from django.core.cache import cache

User = get_user_model()


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности
        cls.author = User.objects.create(
            username='testuser'
        )
        cls.group = Group.objects.create(
            title='название группы',
            slug='test-slug',
            description='описание группы'
        )
        Post.objects.create(
            text='тестовый текст',
            pub_date='дата публикации',
            author=cls.author,
            group=cls.group
        )

        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        # Модуль shutil - библиотека Python с прекрасными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение, изменение папок|файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = TaskPagesTests.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        cache.clear()
    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'group.html': reverse('posts:group', kwargs={'slug': 'test-slug'}),
            'posts/new_post.html': reverse('posts:new_post'),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверяем корректность контекста
    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        context = response.context.get('page')[0]

        templates_context_test = {
            context.text: 'тестовый текст',
            context.author.username: 'testuser',
            context.group.title: 'название группы',
        }

        for context, test in templates_context_test.items():
            with self.subTest():
                self.assertEqual(context, test)

    def test_group_page_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:group',
                                              kwargs={'slug': 'test-slug'}))
        context = response.context.get('group')

        templates_context_test = {
            context.title: 'название группы',
            context.slug: 'test-slug',
            context.description: 'описание группы',
        }

        for context, test in templates_context_test.items():
            with self.subTest():
                self.assertEqual(context, test)

    def test_edit_post_page_show_correct_context(self):
        """Шаблон post edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_edit',
                                              kwargs={'username': 'testuser',
                                                      'post_id': '1'
                                                      }))
        form_fields = {'group': forms.fields.ChoiceField,
                       'text': forms.fields.CharField,
                       }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        context = self.authorized_client.get(reverse('posts:profile',
                                             kwargs={'username': 'testuser'
                                                     })).context

        templates_context_test = {
            context.get('author').username: 'testuser',
            context.get('page')[0].text: 'тестовый текст',
            context.get('page')[0].author.username: 'testuser',
            context.get('post_list')[0].text: 'тестовый текст'
        }

        for context, test in templates_context_test.items():
            with self.subTest():
                self.assertEqual(context, test)

    def test_post_page_show_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        context = self.authorized_client.get(reverse('posts:post',
                                             kwargs={'username': 'testuser',
                                                     'post_id': '1'
                                                     })).context
        templates_context_test = {
            context.get('author').username: 'testuser',
            context.get('post').text: 'тестовый текст',
        }

        for context, test in templates_context_test.items():
            with self.subTest():
                self.assertEqual(context, test)

    def test_new_post_page_show_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:new_post'))

        form_fields = {'group': forms.fields.ChoiceField,
                       'text': forms.fields.CharField,
                       }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    # Paginator
    def test_paginator_main_page(self):
        """Paginator displays correct num of pages."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.context.get('paginator').per_page, 10)

    # Imagies tests
    def test_image_context(self):
        """image is in context."""

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
        post = Post.objects.create(
            text='image!',
            author=self.author,
            group=self.group,
            image=uploaded
        )

        aut_client = self.authorized_client
        templates_context = [
            aut_client.get(reverse('posts:index'
                                   )).context.get('page')[0],
            aut_client.get(reverse('posts:group', args=[post.group.slug]
                                   )).context.get('page')[0],
            aut_client.get(reverse('posts:post', args=[post.author, post.id]
                                   )).context.get('post'),
            aut_client.get(reverse('posts:profile', args=[post.author]
                                   )).context.get('page')[0],
        ]

        for context in templates_context:
            with self.subTest():
                image = context.image
                self.assertEqual(image, post.image)

    def test_cache(self):
        # Check response before post creating
        response_zero = self.authorized_client.get(reverse('posts:index'))
        # Create post
        post = Post.objects.create(author=self.author, text='test_text_cash_1')
        response_first = self.authorized_client.get(reverse('posts:index'))
        Post.objects.filter(id=post.id).delete()

        # Response deleted in Database but On page it should be saved
        response_second = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_first.content, response_second.content)

        # Post should be deleted on page with clear cache
        cache.clear()
        response_third = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_zero.content, response_third.content)


class PostCreateTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username='roman'
        )
        cls.author_second = User.objects.create(
            username='author_second'
        )
        cls.group1 = Group.objects.create(
            title='test_title1',
            slug='test_slug1',
            description='test_desc1'
        )

        cls.group2 = Group.objects.create(
            title='test_title2',
            slug='test_slug2',
            description='test_desc2'
        )

        cls.post = Post.objects.create(
            text='test_text',
            author=cls.author,
            group=cls.group1
        )

    def setUp(self):
        self.user = PostCreateTest.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        cache.clear()
    def test_post_in_right_group(self):
        """Проверка, что при создании поста, этот пост появляется
        на главной странице сайта, на странице выбранной группы.
        """
        expected = PostCreateTest.post
        # Check main page
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.context.get('page')[0], expected)
        # Check group page
        response = self.authorized_client.get(
            reverse('posts:group', kwargs={'slug': 'test_slug1'}))
        self.assertEqual(response.context.get('page')[0], expected)

        # Check group page where post dosnot created
        response = self.authorized_client.get(
            reverse('posts:group', kwargs={'slug': 'test_slug2'}))
        self.assertFalse(len(response.context.get('page')))


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username='author'
        )
        cls.author_second = User.objects.create(
            username='author_second'
        )
        cls.group1 = Group.objects.create(
            title='test_title1',
            slug='test_slug1',
            description='test_desc1'
        )

        cls.post = Post.objects.create(
            text='test_text',
            author=cls.author,
            group=cls.group1
        )

        cls.post_second = Post.objects.create(
            text='test_text',
            author=cls.author_second,
        )

    def setUp(self):
        self.user = FollowTest.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.guest = Client()
        
        cache.clear()
    
       
    def test_autuser_can_follow_and_unfollow(self):
        """Авторизованный пользователь может подписываться на 
        других пользователей и удалять их из подписок.
        """
        
        # 1. Check that user doesnot have followings
        followings = Follow.objects.all()
        self.assertEqual(followings.count(), 0)
        
        # 2. User get to posts:profile_follow, then he should have one followings
        response = self.authorized_client.post(
            reverse('posts:profile_follow', args= [self.author_second])) 
        followings = Follow.objects.filter(
            user=self.author,
            author = self.author_second
        )
        self.assertEqual(followings.count(), 1)

        # 2. User get to posts:profile_follow, then he should delete followings
        response = self.authorized_client.post(
            reverse('posts:profile_unfollow', args= [self.author_second])
            ) 
        followings = Follow.objects.filter(
            user=self.author,
            author = self.author_second
        )
        self.assertEqual(followings.count(), 0)

    def test_followpost_for_followuser_and_not_for_not_follow_autuser(self):
        """Новая запись пользователя появляется в ленте тех, кто на 
        него подписан и не появляется в ленте тех, кто не подписан на него.
        """ 
        # 0. Number posts on follow_index before following
        response = self.authorized_client.get(reverse('posts:follow_index'))
        cnt_posts = len(response.context['page'])
        self.assertEqual(cnt_posts, 0)
        
        # 1. Follow to author
        response = self.authorized_client.post(
            reverse('posts:profile_follow', args= [self.author_second])) 
        followings = Follow.objects.filter(
            user=self.author,
            author = self.author_second
        )
        self.assertEqual(followings.count(), 1)

        # 2. Number posts on follow_index after following
        response = self.authorized_client.get(reverse('posts:follow_index'))
        cnt_posts = len(response.context['page'])
        self.assertEqual(cnt_posts, 1)
        
        # 3. unfollow to author
        response = self.authorized_client.post(
            reverse('posts:profile_unfollow', args= [self.author_second])
            ) 
        followings = Follow.objects.filter(
            user=self.author,
            author = self.author_second
        )
        self.assertEqual(followings.count(), 0)
        
        # 4. Number posts on follow_index after unfollowing. So it is unfllowing user
        response = self.authorized_client.get(reverse('posts:follow_index'))
        cnt_posts = len(response.context['page'])
        self.assertEqual(cnt_posts, 0)

    def test_autuser_can_make_comment_and_noautuser_cant_make_comment(self):
        """Только авторизированный пользователь может комментировать посты.
        """   
        # 1. number commnents before commenting
        self.assertEqual(Comment.objects.count(), 0)
        # 2. number commnents after commenting by authorized_client
        response = self.authorized_client.post(reverse('posts:add_comment', 
                                                       args=[self.post.author, 
                                                       self.post.id]),
                                                       {'text': 'comment'})   
        self.assertEqual(Comment.objects.count(), 1)

        # 3. Check correction of comment
        comment = Comment.objects.filter(author=self.post.author, post=self.post.id)
        self.assertEqual(comment[0].text, 'comment')

        # 5. number commnents after commenting by not authorized_client
        Comment.objects.first().delete()

        response = self.guest.post(reverse('posts:add_comment', 
                                                       args=[self.post.author, 
                                                       self.post.id]),
                                                       {'text': 'comment'})   
        self.assertEqual(Comment.objects.count(), 0)