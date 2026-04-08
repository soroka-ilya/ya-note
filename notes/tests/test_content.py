from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestHomePage(TestCase):

    def test_home_page_returns_200(self):
        """Home page should be accessible to anyone."""
        url = reverse('notes:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_home_page_uses_correct_template(self):
        """Home page should use home.html template."""
        url = reverse('notes:home')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'notes/home.html')


class TestDetailPage(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.note = Note.objects.create(
            title='Запись',
            text='Просто текст.',
            author=cls.author
        )
        cls.detail_url = reverse('notes:detail', args=(cls.note.slug,))

    def test_detail_page_requires_login(self):
        """Detail page should redirect anonymous users to login."""
        response = self.client.get(self.detail_url)
        login_url = reverse('users:login')
        self.assertRedirects(response, f'{login_url}?next={self.detail_url}')

    def test_detail_page_accessible_to_author(self):
        """Author should be able to view their note."""
        self.client.force_login(self.author)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)

    def test_detail_page_shows_correct_note(self):
        """Detail page should display the correct note."""
        self.client.force_login(self.author)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.context['object'], self.note)

    def test_pages_contain_form(self):
        """На страницы создания и редактирования заметки передаются формы."""
        self.client.force_login(self.author)
        urls = (
            reverse('notes:add'),
            reverse('notes:edit', args=(self.note.slug,)),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)


class TestNotesListPage(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='author1')
        cls.other_user = User.objects.create(username='author2')

        for i in range(3):
            Note.objects.create(
                title=f'Author note {i}',
                text=f'Text {i}',
                author=cls.author
            )

        for i in range(2):
            Note.objects.create(
                title=f'Other note {i}',
                text=f'Text {i}',
                author=cls.other_user
            )

    def test_notes_list_requires_login(self):
        """Notes list page should redirect anonymous users."""
        url = reverse('notes:list')
        response = self.client.get(url)
        login_url = reverse('users:login')
        self.assertRedirects(response, f'{login_url}?next={url}')

    def test_notes_list_shows_only_authors_notes(self):
        """User should only see their own notes."""
        self.client.force_login(self.author)
        url = reverse('notes:list')
        response = self.client.get(url)
        notes = response.context['object_list']
        self.assertEqual(notes.count(), 3)
        for note in notes:
            self.assertEqual(note.author, self.author)

    def test_notes_list_uses_correct_template(self):
        """Notes list should use list.html template."""
        self.client.force_login(self.author)
        url = reverse('notes:list')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'notes/list.html')
