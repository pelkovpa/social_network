from django.urls import path
from . import views

app_name = "posts"


urlpatterns = [
    path("", views.HomePageView.as_view(), name="index"),
    path(
        "group/<slug:slug>/", views.GroupPageView.as_view(), name="group_posts"
    ),
    path(
        "profile/<str:username>/",
        views.ProfilePageView.as_view(),
        name="profile",
    ),
    path(
        "posts/<int:post_id>/",
        views.PostDetailView.as_view(),
        name="post_detail",
    ),
    path("create/", views.PostCreateView.as_view(), name="post_create"),
    path(
        "posts/<int:post_id>/edit/",
        views.PostUpdateView.as_view(),
        name="post_edit",
    ),
    path(
        "posts/<int:post_id>/comment/", views.add_comment, name="add_comment"
    ),
    path("follow/", views.follow_index, name="follow_index"),
    path(
        "profile/<str:username>/follow/",
        views.profile_follow,
        name="profile_follow",
    ),
    path(
        "profile/<str:username>/unfollow/",
        views.profile_unfollow,
        name="profile_unfollow",
    ),
]
