from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

        cls.user_1 = User.objects.create_user(username='auth_1')
        cls.authorized_client_1 = Client()
        cls.authorized_client_1.force_login(cls.user_1)

        cls.user_2 = User.objects.create_user(username='auth_2')
        cls.authorized_client_2 = Client()
        cls.authorized_client_2.force_login(cls.user_2)

        cls.group = Group.objects.create(
            title='test group',
            slug='test-slug',
            description='test description',
        )

        cls.post = Post.objects.create(
            author=cls.user_1,
            text='ж' * 100,
            group=cls.group,
        )

        cls.urls_dict_all = {
            reverse('posts:index'): 200,
            reverse(
                'posts:group_list', kwargs={'slug': URLTests.group.slug}
            ): 200,
            reverse(
                'posts:profile', kwargs={'username': URLTests.user_1.username}
            ): 200,
            reverse(
                'posts:post_detail', kwargs={'post_id': URLTests.post.pk}
            ): 200,
            reverse(
                'posts:add_comment', kwargs={'post_id': URLTests.post.pk}
            ): 302,
            '/unexisting_page/': 404,
            reverse(
                'posts:profile_follow',
                kwargs={'username': URLTests.user_1.username},
            ): 302,
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': URLTests.user_1.username},
            ): 302,
        }

        cls.urls_templates_all = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': URLTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': URLTests.user_1.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': URLTests.post.pk}
            ): 'posts/post_detail.html',
        }

    def test_urls_guest_client(self):
        """Страница доступна неавторизованному пользователю."""

        urls_dict_local = {
            reverse(
                'posts:post_edit', kwargs={'post_id': URLTests.post.pk}
            ): 302,
            reverse('posts:post_create'): 302,
            reverse('posts:follow_index'): 302,
        }
        urls_dict = {**URLTests.urls_dict_all, **urls_dict_local}
        for address, status in urls_dict.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_urls_auth_1(self):
        """Страница доступна авторизованному пользователю атвору поста."""

        urls_dict_local = {
            reverse(
                'posts:post_edit', kwargs={'post_id': URLTests.post.pk}
            ): 200,
            reverse('posts:post_create'): 200,
            reverse('posts:follow_index'): 200,
        }
        urls_dict = {**URLTests.urls_dict_all, **urls_dict_local}
        for address, status in urls_dict.items():
            with self.subTest(address=address):
                response = self.authorized_client_1.get(address)
                self.assertEqual(response.status_code, status)

    def test_urls_auth_2(self):
        """Страница доступна авторизованному пользователю."""

        urls_dict_local = {
            reverse(
                'posts:post_edit', kwargs={'post_id': URLTests.post.pk}
            ): 302,
            reverse('posts:post_create'): 200,
            reverse('posts:follow_index'): 200,
        }
        urls_dict = {**URLTests.urls_dict_all, **urls_dict_local}
        for address, status in urls_dict.items():
            with self.subTest(address=address):
                response = self.authorized_client_2.get(address)
                self.assertEqual(response.status_code, status)

    def test_template_guest_client(self):
        """URL-адрес использует соответствующий шаблон для неавторизованного
        пользователя."""

        urls_templates_local = {
            reverse(
                'posts:post_edit', kwargs={'post_id': URLTests.post.pk}
            ): 'users/login.html',
            reverse('posts:post_create'): 'users/login.html',
            reverse(
                'posts:add_comment', kwargs={'post_id': URLTests.post.pk}
            ): 'users/login.html',
            reverse('posts:follow_index'): 'users/login.html',
            reverse(
                'posts:profile_follow',
                kwargs={'username': URLTests.user_1.username},
            ): 'users/login.html',
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': URLTests.user_1.username},
            ): 'users/login.html',
        }
        urls_templates = {
            **URLTests.urls_templates_all,
            **urls_templates_local,
        }
        for address, template in urls_templates.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertTemplateUsed(response, template)

    def test_template_auth_1(self):
        """URL-адрес использует соответствующий шаблон для авторизованного
        пользователя автора поста."""

        urls_templates_local = {
            reverse(
                'posts:post_edit', kwargs={'post_id': URLTests.post.pk}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:add_comment', kwargs={'post_id': URLTests.post.pk}
            ): 'posts/post_detail.html',
            reverse('posts:follow_index'): 'posts/follow.html',
            reverse(
                'posts:profile_follow',
                kwargs={'username': URLTests.user_1.username},
            ): 'posts/profile.html',
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': URLTests.user_1.username},
            ): 'posts/profile.html',
        }
        urls_templates = {
            **URLTests.urls_templates_all,
            **urls_templates_local,
        }
        for address, template in urls_templates.items():
            with self.subTest(address=address):
                response = self.authorized_client_1.get(address, follow=True)
                self.assertTemplateUsed(response, template)

    def test_template_auth_2(self):
        """URL-адрес использует соответствующий шаблон для авторизованного
        пользователя."""

        urls_templates_local = {
            reverse(
                'posts:post_edit', kwargs={'post_id': URLTests.post.pk}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:add_comment', kwargs={'post_id': URLTests.post.pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts:profile_follow',
                kwargs={'username': URLTests.user_1.username},
            ): 'posts/profile.html',
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': URLTests.user_1.username},
            ): 'posts/profile.html',
        }
        urls_templates = {
            **URLTests.urls_templates_all,
            **urls_templates_local,
        }
        for address, template in urls_templates.items():
            with self.subTest(address=address):
                response = self.authorized_client_2.get(address, follow=True)
                self.assertTemplateUsed(response, template)
