from django.db import models
from django.contrib.auth import get_user_model
from .validators import validate_not_empty

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title[:100]


class Post(models.Model):
    text = models.TextField(verbose_name='Запись',
                            help_text='Сделайте запись Вашего поста')
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='posts')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL,
                              blank=True,
                              null=True,
                              related_name='posts',
                              verbose_name='Группа',
                              help_text='Выбирите группу, куда попадет пост',
                              validators=[validate_not_empty])
    # поле для картинки
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    class Meta:
        ordering = ['-pub_date']

    # выводим текст поста
    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             related_name='comments')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comments')
    text = models.TextField(validators=[validate_not_empty])
    created = models.DateTimeField('date published', auto_now_add=True)

class Follow(models.Model):
    user = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='follower')
    author = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='following')
    