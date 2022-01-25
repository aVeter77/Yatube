from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='ж' * 100,
        )

    def test_models_have_correct_object_names(self):
        """У моделей корректно работает __str__."""

        post = PostModelTest.post
        group = PostModelTest.group
        post_group_fields = {
            post.text[:15]: str(post),
            group.title: str(group),
        }
        for test_field, model_field in post_group_fields.items():
            with self.subTest(test_field=test_field):
                self.assertEqual(test_field, model_field)

    def test_verbose_name(self):
        """verbose_name в полях совпадает c ожидаемым."""

        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Имя группы',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEquals(
                    post._meta.get_field(value).verbose_name, expected
                )

    def test_help_text(self):
        """help_text в полях совпадает c ожидаемым."""

        post = PostModelTest.post
        field_help_texts = {
            'text': 'Текст нового поста',
            'group': 'Выберите группу',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEquals(
                    post._meta.get_field(value).help_text, expected
                )
