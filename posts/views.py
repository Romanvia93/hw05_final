from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from django.core.paginator import Paginator
from django.http import Http404


# Main page
def index(request):
    """Main page"""
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    # Из URL извлекаем номер запрошенной страницы - это значение параметра page
    page_number = request.GET.get('page')
    # Получаем набор записей для страницы с запрошенным номером
    page = paginator.get_page(page_number)
    index = True
    return render(request,
                  'posts/index.html',
                  {'page': page,
                   'paginator': paginator,
                   'index': index}
                  )


# Cтраницы сообщества
def group_posts(request, slug):
    """Group page"""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.filter(group=group)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, 'group.html', {'group': group,
                                          'page': page,
                                          'paginator': paginator})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if (request.method == 'POST' and form.is_valid()):
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:index')
    return render(request, 'posts/new_post.html', {'form': form})


def profile(request, username):
    """Profile page"""
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=author)
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    followers_count = Follow.objects.filter(author=author).count()
    followings_count = Follow.objects.filter(user=author).count()
    following = Follow.objects.filter(user__username = request.user, author=author)

    return render(request,
                  'posts/profile.html',
                  {'author': author,
                   'page': page,
                   'post_list': post_list,
                   'paginator': paginator,
                   'followers_count': followers_count,
                   'followings_count': followings_count,
                   'following': following
                   })


def post_view(request, username, post_id):
    """Post page"""
    form = CommentForm(request.POST or None)
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id, author__username=username)
    comments = post.comments.all()
    #Follow
    followers_count = Follow.objects.filter(author=author).count()
    followings_count = Follow.objects.filter(user=author).count()
    following = Follow.objects.filter(user__username = request.user, author=author)
    context = {
        'form': form,
        'author': author,
        'post': post,
        'comments': comments,
        'followers_count': followers_count,
        'followings_count': followings_count,
        'following': following
    }
    return render(request, 'posts/post.html', context)


@login_required
def post_edit(request, username, post_id):
    guest = get_object_or_404(User, username=username)
    post = Post.objects.filter(author__username=username).get(id=post_id)
    form = PostForm(request.POST, instance=post, files=request.FILES or None)

    if request.user != guest:
        raise Http404('You are not allowed to edit this post')
    else:
        if (request.method == 'POST' and form.is_valid()):
            edit_post = form.save(commit=False)
            post.text = edit_post.text
            post.group = edit_post.group
            post.save()
            return redirect('posts:post', username, post_id)
    form = PostForm(instance=post)
    return render(request, 'posts/new_post.html', {'form': form,
                                                   'post': post,
                                                   })


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        # return redirect('posts:profile', post.author)
    return redirect('posts:post', post.author, post_id)


@login_required
def follow_index(request):
    """Favorite authors"""
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    follow = True
    return render(request,
                  'posts/follow.html',
                  {'page': page,
                   'paginator': paginator,
                   'follow': follow}
                  )



@login_required
def profile_follow(request, username):
    """Def for author following"""
    author = get_object_or_404(User, username=username)
    if request.user != author and not Follow.objects.filter(user = request.user,
                                                            author = author
                                                            ).exists():
        Follow.objects.create(user = request.user, author = author)
    
    return redirect('posts:profile', username)
    
    


@login_required
def profile_unfollow(request, username):
    """Def for author unfollowing"""
    author = get_object_or_404(User, username=username)
    follower = Follow.objects.filter(user = request.user, author = author)
    if follower.exists():
        follower.delete()
    
    return redirect('posts:profile', username)
    # ...
    pass 





def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
