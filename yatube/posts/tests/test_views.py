import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

POST_IN_GROUP = 15
POST_OTHER = 12
ALL_POSTS = POST_IN_GROUP + POST_OTHER

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='test group',
            slug='test-slug',
            description='test description',
        )

        post_in_group = (
            Post(
                text='ж' * (100 + i),
                author=cls.user,
                group=cls.group,
                image=SimpleUploadedFile(
                    name='small_' + str(i) + '.gif',
                    content=SMALL_GIF,
                    content_type='image/gif',
                ),
            )
            for i in range(1, POST_IN_GROUP + 1)
        )
        Post.objects.bulk_create(post_in_group)

        post_out_group = (
            Post(
                text='ж' * (100 + i),
                author=cls.user,
                image=SimpleUploadedFile(
                    name='small_' + str(i) + '.gif',
                    content=SMALL_GIF,
                    content_type='image/gif',
                ),
            )
            for i in range(POST_IN_GROUP + 1, ALL_POSTS + 1)
        )
        Post.objects.bulk_create(post_out_group)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': ViewTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': ViewTests.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': 1}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': 1}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""

        response = self.authorized_client.get(reverse('posts:index'))
        objects = response.context['page_obj']
        for object in objects:
            post_author = object.author
            post_text = object.text
            post_pk = object.pk
            post_image = object.image
            self.assertEqual(post_author, ViewTests.user)
            self.assertEqual(post_text, 'ж' * (100 + post_pk))
            self.assertEqual(
                post_image, 'posts/small_' + str(post_pk) + '.gif'
            )

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': ViewTests.group.slug})
        )
        objects = response.context['page_obj']
        objects_group = response.context['group']
        self.assertEqual(objects_group, ViewTests.group)
        for object in objects:
            post_author = object.author
            post_text = object.text
            post_pk = object.pk
            post_group = object.group
            post_image = object.image
            self.assertEqual(post_author, ViewTests.user)
            self.assertEqual(post_text, 'ж' * (100 + post_pk))
            self.assertEqual(post_group, ViewTests.group)
            self.assertEqual(
                post_image, 'posts/small_' + str(post_pk) + '.gif'
            )

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse(
                'posts:profile', kwargs={'username': ViewTests.user.username}
            )
        )
        objects = response.context['page_obj']
        object_count = objects.paginator.count
        self.assertEqual(object_count, ALL_POSTS)
        for object in objects:
            post_author = object.author
            post_text = object.text
            post_pk = object.pk
            post_image = object.image
            self.assertEqual(post_author, ViewTests.user)
            self.assertEqual(post_text, 'ж' * (100 + post_pk))
            self.assertEqual(
                post_image, 'posts/small_' + str(post_pk) + '.gif'
            )

    def test_post_detail_page_auth_user_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""

        for i in range(1, ALL_POSTS + 1):
            response = self.authorized_client.get(
                reverse('posts:post_detail', kwargs={'post_id': i})
            )
            object = response.context['post']
            object_count = response.context['posts_count']
            post_author = object.author
            post_text = object.text
            post_pk = object.pk
            post_image = object.image
            post_form = response.context['form']
            self.assertEqual(post_author, ViewTests.user)
            self.assertEqual(post_text, 'ж' * (100 + post_pk))
            self.assertEqual(object_count, ALL_POSTS)
            self.assertEqual(
                post_image, 'posts/small_' + str(post_pk) + '.gif'
            )
            self.assertTrue(post_form)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': 1})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""

        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_paginator_contains(self):
        """Паджинатор сформирован правильно."""

        pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': ViewTests.group.slug}),
            reverse(
                'posts:profile', kwargs={'username': ViewTests.user.username}
            ),
        ]

        for reverse_name in pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                objects = response.context['page_obj']
                num_pages = objects.paginator.num_pages
                for num in range(1, num_pages + 1):
                    page = objects.paginator.page(num)
                    object_list = len(page.object_list)
                    per_page = objects.paginator.per_page
                    count = objects.paginator.count
                    if num < num_pages:
                        self.assertEqual(object_list, per_page)
                    else:
                        objects_num = count % per_page
                        if objects_num == 0:
                            objects_num = per_page
                        self.assertEqual(object_list, objects_num)

    def test_post_new_group_contains(self):
        """Пост в новой группе создан правильно."""

        group_new = Group.objects.create(
            title='test group new',
            slug='test-slug-new',
            description='test description new',
        )

        post_new = Post.objects.create(
            author=ViewTests.user,
            text='ж' * 100,
            group=group_new,
            image=SimpleUploadedFile(
                name='small.gif',
                content=SMALL_GIF,
                content_type='image/gif',
            ),
        )

        pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': group_new.slug}),
            reverse('posts:profile', kwargs={'username': post_new.author}),
        ]

        for reverse_name in pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                objects = response.context['page_obj']
                self.assertIn(post_new, objects)

        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': ViewTests.group.slug})
        )
        objects = response.context['page_obj']
        self.assertNotIn(post_new, objects)

    def test_post_comment_contains(self):
        """Комментарий к посту отображается правильно."""

        Comment.objects.create(
            author=ViewTests.user,
            text='Тестовый комментарий 1',
            post=Post.objects.get(pk=1),
        )

        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        object = response.context['post']
        object_count = response.context['posts_count']
        post_author = object.author
        post_text = object.text
        post_pk = object.pk
        post_image = object.image
        post_form = response.context['form']
        self.assertEqual(post_author, ViewTests.user)
        self.assertEqual(post_text, 'ж' * (100 + post_pk))
        self.assertEqual(object_count, ALL_POSTS)
        self.assertEqual(post_image, 'posts/small_' + str(post_pk) + '.gif')
        self.assertTrue(post_form)
        self.assertTrue(object.comments.filter(text='Тестовый комментарий 1'))

    def test_cache_index_contains(self):
        """Кеширование главной страницы работает правильно"""

        post_new = Post.objects.create(
            author=ViewTests.user,
            text='Тест кэша',
        )

        response = self.authorized_client.get(reverse('posts:index'))
        objects = response.context['page_obj']
        content_1 = response.content

        post_new.delete()

        response = self.authorized_client.get(reverse('posts:index'))
        content_2 = response.content
        self.assertEqual(content_1, content_2)

        key = make_template_fragment_key('index_page', [objects.number])
        cache.delete(key)

        response = self.authorized_client.get(reverse('posts:index'))
        content_3 = response.content
        self.assertNotEqual(content_1, content_3)

    def test_follow_and_unfollow_correct(self):
        """Подписка работает правильно"""

        def create_posts(author):
            posts = (
                Post(
                    text='ж' * (100 + i),
                    author=author,
                )
                for i in range(10)
            )
            Post.objects.bulk_create(posts)

            return

        author_1 = User.objects.create_user(username='author_1')
        author_2 = User.objects.create_user(username='author_2')

        authors = [author_1, author_2]
        for author in authors:
            create_posts(author)

        follower = User.objects.create_user(username='follower')
        authorized_follower = Client()
        authorized_follower.force_login(follower)

        authorized_follower.get(
            reverse('posts:profile_follow', kwargs={'username': author_1})
        )
        authorized_follower.get(
            reverse('posts:profile_follow', kwargs={'username': author_2})
        )
        response = authorized_follower.get(reverse('posts:follow_index'))

        objects = response.context['page_obj']
        num_pages = objects.paginator.num_pages
        for num in range(1, num_pages + 1):
            page_objects = objects.paginator.page(num)
            for object in page_objects:
                post_author = object.author
                self.assertIn(post_author, [author_1, author_2])

        authorized_follower.get(
            reverse('posts:profile_unfollow', kwargs={'username': author_2})
        )
        response = authorized_follower.get(reverse('posts:follow_index'))

        objects = response.context['page_obj']
        num_pages = objects.paginator.num_pages
        for num in range(1, num_pages + 1):
            page_objects = objects.paginator.page(num)
            for object in page_objects:
                post_author = object.author
                self.assertIn(post_author, [author_1])

    def test_new_post_following_correct(self):
        """Посты у подписчиков отображаются правильно"""

        def create_posts(author):
            posts = (
                Post(
                    text='ж' * (100 + i),
                    author=author,
                )
                for i in range(10)
            )
            Post.objects.bulk_create(posts)

            return

        author_1 = User.objects.create_user(username='author_1')
        author_2 = User.objects.create_user(username='author_2')
        author_3 = User.objects.create_user(username='author_3')

        authors = [author_1, author_2, author_3]
        for author in authors:
            create_posts(author)

        follower_1 = User.objects.create_user(username='follower_1')
        authorized_follower_1 = Client()
        authorized_follower_1.force_login(follower_1)

        authorized_follower_1.get(
            reverse('posts:profile_follow', kwargs={'username': author_1})
        )
        authorized_follower_1.get(
            reverse('posts:profile_follow', kwargs={'username': author_3})
        )

        follower_2 = User.objects.create_user(username='follower_2')
        authorized_follower_2 = Client()
        authorized_follower_2.force_login(follower_2)

        authorized_follower_2.get(
            reverse('posts:profile_follow', kwargs={'username': author_1})
        )
        authorized_follower_2.get(
            reverse('posts:profile_follow', kwargs={'username': author_2})
        )

        post_1 = Post.objects.create(text='Пост author_1', author=author_1)
        post_2 = Post.objects.create(text='Пост author_2', author=author_2)
        post_3 = Post.objects.create(text='Пост author_3', author=author_3)

        response = authorized_follower_1.get(reverse('posts:follow_index'))
        objects = response.context['page_obj']
        self.assertIn(post_1, objects)
        self.assertNotIn(post_2, objects)
        self.assertIn(post_3, objects)

        response = authorized_follower_2.get(reverse('posts:follow_index'))
        objects = response.context['page_obj']
        self.assertIn(post_1, objects)
        self.assertIn(post_2, objects)
        self.assertNotIn(post_3, objects)
