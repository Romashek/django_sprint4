from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.urls import reverse, reverse_lazy
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.views import View
from django.http import Http404
from django.conf import settings

# Локальные импорты
from .forms import PostForm, CommentForm
from .models import Post, Category, Comment
from .mixins import OnlyAuthorMixin


User = get_user_model()


def get_published_posts():
    return Post.objects.filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    )


def paginate_func(queryset, request, items_per_page=settings.PAGINATE_BY):
    paginator = Paginator(queryset, items_per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


class IndexListView(ListView):
    ordering = 'id'
    paginate_by = settings.PAGINATE_BY
    template_name = 'blog/index.html'

    def get_queryset(self):
        return get_published_posts()


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:

        if (not post.is_published
                or post.pub_date > timezone.now()
                or not post.category.is_published):
            raise Http404('You do not have permission to view this post.')

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect('blog:post_detail', post_id=post.id)
        else:
            comments = post.comments.all()
            context = {
                'post': post,
                'form': form,
                'comments': comments,
            }
            return render(request, 'blog/detail.html', context)

    else:
        form = CommentForm()

    comments = post.comments.all()

    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }

    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True
    )
    post_list = get_published_posts().filter(
        category=category
    )

    context = {
        'category': category,
        'post_list': post_list,
        'page_obj': paginate_func(post_list, request)
    }

    return render(request, 'blog/category.html', context)


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        username = self.request.user.username
        return reverse('blog:profile', kwargs={'username': username})


class ProfileView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    paginate_by = settings.PAGINATE_BY

    def get_object(self, queryset=None):
        username = self.kwargs.get('username')
        return get_object_or_404(User, username=username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        post_list = self.object.posts.all()

        context['page_obj'] = paginate_func(post_list, self.request)

        return context


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['username', 'first_name', 'last_name', 'email']
    template_name = 'blog/user.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        username = self.object.username
        return reverse('blog:profile', kwargs={'username': username})


class PostUpdateView(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.object.author.username}
        )

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def dispatch(self, request, *args, **kwargs):
        # Проверяем, что пользователь авторизован и является автором поста
        post = self.get_object()
        if not request.user.is_authenticated or post.author != request.user:
            return redirect('blog:post_detail', post_id=post.id)
        return super().dispatch(request, *args, **kwargs)


class PostDeleteView(LoginRequiredMixin, OnlyAuthorMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.object.author.username}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        form = PostForm(instance=post)
        context['form'] = form
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)


class AddCommentView(LoginRequiredMixin, View):
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect('blog:post_detail', post_id=post.id)

        comments = post.comments.all()
        context = {
            'post': post,
            'form': form,
            'comments': comments,
        }
        return render(request, 'blog/detail.html', context)


class EditCommentView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.id}
        )

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author

    def get_object(self, queryset=None):
        post_id = self.kwargs.get('post_id')
        comment_id = self.kwargs.get('comment_id')
        return get_object_or_404(Comment, id=comment_id, post__id=post_id)


class DeleteCommentView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.id}
        )

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author

    def get_object(self, queryset=None):
        post_id = self.kwargs.get('post_id')
        comment_id = self.kwargs.get('comment_id')
        return get_object_or_404(Comment, id=comment_id, post__id=post_id)
