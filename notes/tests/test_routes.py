from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username='author', password='password'
        )
        cls.reader = User.objects.create_user(
            username='reader', password='password'
        )

        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
        )

    def test_pages_availability_for_anonymous(self):
        """Test which pages are accessible to anonymous users."""
        urls = (
            ('notes:home', None, HTTPStatus.OK),
            ('users:login', None, HTTPStatus.OK),
            ('users:signup', None, HTTPStatus.OK),
            ('notes:detail', (self.note.slug,), HTTPStatus.FOUND),
            ('notes:edit', (self.note.slug,), HTTPStatus.FOUND),
            ('notes:delete', (self.note.slug,), HTTPStatus.FOUND),
            ('notes:list', None, HTTPStatus.FOUND),
            ('notes:add', None, HTTPStatus.FOUND),
        )
        for name, args, expected_status in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, expected_status)

    def test_pages_availability_for_author(self):
        """Test which pages are accessible to the note author."""
        self.client.force_login(self.author)

        urls = (
            ('notes:home', None, HTTPStatus.OK),
            ('notes:detail', (self.note.slug,), HTTPStatus.OK),
            ('notes:edit', (self.note.slug,), HTTPStatus.OK),
            ('notes:delete', (self.note.slug,), HTTPStatus.OK),
            ('notes:list', None, HTTPStatus.OK),
            ('notes:add', None, HTTPStatus.OK),
            ('users:login', None, HTTPStatus.OK),
            ('users:signup', None, HTTPStatus.OK),
            ('notes:success', None, HTTPStatus.OK),
        )
        for name, args, expected_status in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, expected_status)

    def test_reader_cannot_access_authors_notes(self):
        """Reader should not be able to access author's notes."""
        self.client.force_login(self.reader)

        urls = (
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_redirect_for_anonymous_client(self):
        """Test that anonymous users are redirected to login page."""
        login_url = reverse('users:login')

        protected_urls = (
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:list', None),
            ('notes:add', None),
        )

        for name, args in protected_urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
