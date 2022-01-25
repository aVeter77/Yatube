from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
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

    def get_queryset(self):
        group = get_object_or_404(Group, slug=self.kwargs['slug'])
        return group.posts.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = context['posts'][0].group
        return context


class ProfileView(ListView):

    template_name = 'posts/profile.html'
    paginate_by = 10
    context_object_name = 'posts'

    def get_queryset(self):
        author = get_object_or_404(User, username=self.kwargs['username'])
        return author.posts.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        author = get_object_or_404(User, username=self.kwargs['username'])
        if self.request.user.is_authenticated:
            user = User.objects.get(username=self.request.user)
            author = User.objects.get(username=self.kwargs['username'])
            if user.follower.filter(author=author):
                context['following'] = True
        context['author'] = author
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
        user = get_object_or_404(User, username=self.request.user)
        posts = Post.objects.filter(
            author__in=[following.author for following in user.follower.all()]
        )
        return posts


class ProfileFollowView(LoginRequiredMixin, ListView):
    def get(self, *args, **kwargs):
        user = get_object_or_404(User, username=self.request.user)
        author = get_object_or_404(User, username=self.kwargs['username'])
        if not user.follower.filter(author=author) and user != author:
            Follow.objects.create(user=user, author=author)
        return redirect('posts:profile', self.kwargs['username'])


class ProfileUnfollowView(LoginRequiredMixin, ListView):
    def get(self, *args, **kwargs):
        user = get_object_or_404(User, username=self.request.user)
        author = get_object_or_404(User, username=self.kwargs['username'])
        if user.follower.filter(author=author):
            Follow.objects.filter(user=user, author=author).delete()
        return redirect('posts:profile', self.kwargs['username'])
