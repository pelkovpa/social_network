from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404

from django.views.generic import ListView, DetailView, CreateView, UpdateView
from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow

NUM_OF_ENTRIES = 10


class HomePageView(ListView):
    template_name = "posts/index.html"
    paginate_by = NUM_OF_ENTRIES

    def get_queryset(self):
        return Post.objects.all()


class GroupPageView(ListView):
    template_name = "posts/group_list.html"
    paginate_by = NUM_OF_ENTRIES

    def get_queryset(self, **kwargs):
        group = get_object_or_404(Group, slug=self.kwargs["slug"])
        return group.posts.all()


class ProfilePageView(ListView):
    template_name = "posts/profile.html"
    paginate_by = NUM_OF_ENTRIES

    def get_queryset(self, **kwargs):
        author = get_object_or_404(User, username=self.kwargs["username"])
        return author.posts.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        author = get_object_or_404(User, username=self.kwargs["username"])
        context["posts"] = author.posts.all()
        context["author"] = author
        user = self.request.user
        context["user"] = user
        context["following"] = False
        if user.id in author.following.values_list("user", flat=True):
            context["following"] = True
        return context


class PostDetailView(DetailView):
    model = Post
    pk_url_kwarg = "post_id"
    template_name = "posts/post_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = get_object_or_404(Post, id=self.kwargs["post_id"])
        context["comments"] = post.comments.all()
        context["post"] = post
        context["form"] = CommentForm()
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "posts/create_post.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        post = form.save()
        return redirect("posts:profile", username=post.author.username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = False
        return context


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "posts/create_post.html"

    def get_object(self, queryset=None):
        return Post.objects.get(id=self.kwargs.get("post_id"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context

    def form_valid(self, form):
        post = form.save()
        return redirect("posts:post_detail", post_id=post.id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    authors = user.follower.values_list("author", flat=True)
    posts = Post.objects.filter(author__in=authors)
    template = "posts/follow.html"
    paginator = Paginator(posts, NUM_OF_ENTRIES)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {"page_obj": page_obj}
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    user = request.user
    follow = Follow.objects.filter(user=user, author=author)
    if user != author and not follow.exists():
        Follow.objects.create(user=user, author=author)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.get(user=request.user, author__username=username).delete()
    return redirect("posts:profile", username=username)
