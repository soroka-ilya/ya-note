from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='test_user')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.add_url = reverse('notes:add')
        cls.form_data = {
            'title': 'Test Note',
            'text': 'Test text content',
        }

    def test_anonymous_user_cant_create_note(self):
        """Anonymous users should be redirected to login."""
        initial_count = Note.objects.count()
        response = self.client.post(self.add_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        final_count = Note.objects.count()
        self.assertEqual(final_count, initial_count)

    def test_authenticated_user_can_create_note(self):
        """Authenticated users can create notes."""
        initial_count = Note.objects.count()
        response = self.auth_client.post(self.add_url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        final_count = Note.objects.count()
        self.assertEqual(final_count, initial_count + 1)

        note = Note.objects.latest('id')
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.author, self.user)

    def test_slug_is_generated_automatically(self):
        """Slug should be auto-generated from title if not provided."""
        response = self.auth_client.post(self.add_url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))

        note = Note.objects.latest('id')
        expected_slug = 'test-note'
        self.assertEqual(note.slug, expected_slug)

    def test_cannot_create_note_with_existing_slug(self):
        """Should not allow duplicate slugs."""
        self.auth_client.post(self.add_url, data=self.form_data)

        form_data_with_slug = {
            'title': 'Different Title',
            'text': 'Different text',
            'slug': 'test-note'
        }
        response = self.auth_client.post(self.add_url, data=form_data_with_slug)

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, f'test-note{WARNING}')

        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_slug_validation_with_blank_slug(self):
        """If slug is blank, it should be generated from title."""
        self.auth_client.post(self.add_url, data=self.form_data)

        duplicate_form_data = {
            'title': 'Test Note',
            'text': 'Different text',
            'slug': ''
        }
        response = self.auth_client.post(self.add_url, data=duplicate_form_data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test-note')
        self.assertContains(response, WARNING)


class TestNoteEditDelete(TestCase):
    NEW_NOTE_TEXT = 'Обновлённый текст'
    NEW_NOTE_TITLE = 'Обновлённый заголовок'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        cls.note = Note.objects.create(
            title='Оригинальный заголовок',
            text='Оригинальный текст',
            author=cls.author
        )

        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.detail_url = reverse('notes:detail', args=(cls.note.slug,))
        cls.form_data = {
            'title': cls.NEW_NOTE_TITLE,
            'text': cls.NEW_NOTE_TEXT,
        }

    def test_author_can_delete_note(self):
        """Author should be able to delete their own note."""
        notes_count_before = Note.objects.count()
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, reverse('notes:success'))
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before - 1)

        with self.assertRaises(Note.DoesNotExist):
            self.note.refresh_from_db()

    def test_author_can_edit_note(self):
        """Author should be able to edit their own note."""
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))

        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.NEW_NOTE_TITLE)
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_reader_cant_edit_others_note(self):
        """Non-author should not be able to edit note."""
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        self.note.refresh_from_db()
        self.assertEqual(self.note.title, 'Оригинальный заголовок')
        self.assertEqual(self.note.text, 'Оригинальный текст')

    def test_reader_cant_delete_others_note(self):
        """Non-author should not be able to delete note."""
        notes_count_before = Note.objects.count()
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before)

        self.note.refresh_from_db()
        self.assertEqual(self.note.title, 'Оригинальный заголовок')

    def test_anonymous_cant_edit_note(self):
        """Anonymous users should be redirected to login."""
        self.client.logout()
        response = self.client.post(self.edit_url, data=self.form_data)
        login_url = reverse('users:login')
        self.assertRedirects(response, f'{login_url}?next={self.edit_url}')

    def test_anonymous_cant_delete_note(self):
        """Anonymous users should be redirected to login."""
        self.client.logout()
        response = self.client.delete(self.delete_url)
        login_url = reverse('users:login')
        self.assertRedirects(response, f'{login_url}?next={self.delete_url}')

    def test_edit_note_with_existing_slug(self):
        """Should not allow editing a note to use an existing slug."""
        other_note = Note.objects.create(
            title='Another Note',
            text='Another text',
            author=self.author
        )

        edit_url = reverse('notes:edit', args=(self.note.slug,))
        form_data_with_existing_slug = {
            'title': 'Updated Title',
            'text': 'Updated text',
            'slug': other_note.slug
        }
        response = self.author_client.post(
            edit_url, data=form_data_with_existing_slug)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'{other_note.slug}{WARNING}')

        self.note.refresh_from_db()
        self.assertEqual(self.note.title, 'Оригинальный заголовок')
        self.assertEqual(self.note.text, 'Оригинальный текст')
