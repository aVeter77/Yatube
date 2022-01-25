import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormTests(TestCase):
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

        cls.post = Post.objects.create(
            author=cls.user,
            text='ж' * 100,
            image=SimpleUploadedFile(
                name='small_1.gif',
                content=SMALL_GIF,
                content_type='image/gif',
            ),
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Новый пост создаётся правильно"""

        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст 2',
            'group': FormTests.group.pk,
            'image': SimpleUploadedFile(
                name='small_2.gif',
                content=SMALL_GIF,
                content_type='image/gif',
            ),
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile', kwargs={'username': FormTests.user.username}
            ),
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст 2',
                group=FormTests.group,
                image='posts/small_2.gif',
            ).exists()
        )

    def test_edit_post(self):
        """Пост редактируется правильно"""

        group = Group.objects.create(
            title='test group new',
            slug='test-slug-new',
            description='test description new',
        )

        form_data = {
            'text': 'Тестовый текст 3',
            'group': group.pk,
            'image': SimpleUploadedFile(
                name='small_3.gif',
                content=SMALL_GIF,
                content_type='image/gif',
            ),
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': FormTests.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': FormTests.post.pk},
            ),
        )

        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст 3',
                group=group,
                image='posts/small_3.gif',
            ).exists()
        )

    def test_comment_post(self):
        """Комментарий авторизованного пользователя создается правильно"""

        Comment.objects.create(
            author=FormTests.user,
            text='Тестовый комментарий 1',
            post=FormTests.post,
        )

        comment_count = Comment.objects.filter(post=FormTests.post).count()

        form_data = {
            'text': 'Тестовый комментарий 2',
            'post': FormTests.post.pk,
        }

        response = self.authorized_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': FormTests.post.pk}
            ),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail', kwargs={'post_id': FormTests.post.pk}
            ),
        )
        self.assertEqual(
            Comment.objects.filter(post=FormTests.post).count(),
            comment_count + 1,
        )

        self.assertTrue(
            FormTests.post.comments.filter(text='Тестовый комментарий 2')
        )
