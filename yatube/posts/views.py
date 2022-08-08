from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.functional import cached_property
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

User = get_user_model()


class IndexView(ListView):

    template_name = 'posts/index.html'
    model = Post
    paginate_by = 10
    context_object_name = 'posts'


class GroupView(ListView):

    template_name = 'posts/group_list.html'
    paginate_by = 10
    context_object_name = 'posts'

    @cached_property
    def group(self):
        return get_object_or_404(Group, slug=self.kwargs['slug'])

    def get_queryset(self):
        return self.group.posts.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = self.group
        return context


class ProfileView(ListView):

    template_name = 'posts/profile.html'
    paginate_by = 10
    context_object_name = 'posts'

    @cached_property
    def author(self):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_queryset(self):
        return self.author.posts.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            user = self.request.user
            if user.follower.filter(author=self.author).exists():
                context['following'] = True
            if user == self.author:
                context['user_author'] = True
        context['author'] = self.author
        return context


class PostDetailView(DetailView):

    model = Post
    template_name = 'posts/post_detail.html'
    context_object_name = 'post'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['posts_count'] = Post.objects.filter(
            author=context['post'].author
        ).count()
        context['form'] = CommentForm(self.request.POST or None)
        context['comments'] = (
            context['post'].comments.all().order_by('-created')
        )
        return context


class PostCreateView(LoginRequiredMixin, CreateView):

    template_name = 'posts/create_post.html'
    model = Post
    form_class = PostForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.save()
        return super(PostCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'posts:profile', kwargs={'username': self.request.user}
        )


class PostEditView(LoginRequiredMixin, UpdateView):

    template_name = 'posts/create_post.html'
    model = Post
    form_class = PostForm
    pk_url_kwarg = 'post_id'

    def get(self, request, *args, **kwargs):
        if request.user != self.get_object().author:
            return redirect(self.get_success_url())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context

    def get_success_url(self):
        return reverse_lazy(
            'posts:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )


class CommentCreateView(LoginRequiredMixin, CreateView):

    form_class = CommentForm

    def get(self, request, *args, **kwargs):
        if request.method == "GET":
            return redirect(self.get_success_url())
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        self.object.save()
        return super(CommentCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'posts:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )


class FollowIndexView(LoginRequiredMixin, ListView):

    template_name = 'posts/follow.html'
    paginate_by = 10
    context_object_name = 'posts'

    def get_queryset(self):
        return Post.objects.filter(author__following__user=self.request.user)


class ProfileFollowView(LoginRequiredMixin, ListView):
    def get(self, *args, **kwargs):
        user = self.request.user
        author = get_object_or_404(User, username=self.kwargs['username'])
        if user != author:
            Follow.objects.get_or_create(user=user, author=author)

        return redirect('posts:profile', self.kwargs['username'])


class ProfileUnfollowView(LoginRequiredMixin, ListView):
    def get(self, *args, **kwargs):
        user = self.request.user
        Follow.objects.filter(
            user=user, author__username=self.kwargs['username']
        ).delete()

        return redirect('posts:profile', self.kwargs['username'])
