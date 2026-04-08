import pytest

from django.urls import reverse

from notes.forms import NoteForm


@pytest.mark.parametrize(
    'client_fixture_name, note_in_list',
    (
        ('author_client', True),
        ('not_author_client', False),
    )
)
def test_notes_list_for_different_users(
    note, client_fixture_name, note_in_list, request
):
    parametrized_client = request.getfixturevalue(client_fixture_name)
    url = reverse('notes:list')
    response = parametrized_client.get(url)
    object_list = response.context['object_list']
    assert (note in object_list) is note_in_list


def test_create_note_page_contains_form(author_client):
    url = reverse('notes:add')
    response = author_client.get(url)
    assert 'form' in response.context
    assert isinstance(response.context['form'], NoteForm)


def test_edit_note_page_contains_form(slug_for_args, author_client):
    url = reverse('notes:edit', args=slug_for_args)
    response = author_client.get(url)
    assert 'form' in response.context
    assert isinstance(response.context['form'], NoteForm)


@pytest.mark.parametrize(
    'name, args_fixture_name',
    (
        ('notes:add', None),
        ('notes:edit', 'slug_for_args')
    )
)
def test_pages_contains_form(author_client, name, args_fixture_name, request):
    # Получаем аргументы из фикстуры если они нужны
    if args_fixture_name:
        args = request.getfixturevalue(args_fixture_name)
    else:
        args = None

    url = reverse(name, args=args)
    response = author_client.get(url)
    assert 'form' in response.context
    assert isinstance(response.context['form'], NoteForm)
