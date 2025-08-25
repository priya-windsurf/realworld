import http

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from realworld.articles.models import Article

from .models import Comment

User = get_user_model()


class TestAddCommentView(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.author = User(
            email="tester@gmail.com",
            name="tester",
        )
        cls.author.save()

        cls.article = Article.objects.create(
            title="test",
            summary="test",
            content="test",
            author=cls.author,
        )

        cls.url = reverse("add_comment", args=[cls.article.id])

    def test_add_comment(self):
        self.client.force_login(self.author)

        response = self.client.post(self.url, {"content": "test"})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        comment = Comment.objects.get()

        self.assertEqual(comment.article, self.article)
        self.assertEqual(comment.author, self.author)

    def test_add_comment_invalid_form(self):
        self.client.force_login(self.author)

        response = self.client.post(self.url, {"content": ""})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), 0)


class TestEditCommentView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            "tester@gmail.com", name="Test User", password="testpass1"
        )
        cls.article = Article.objects.create(
            title="test",
            summary="test", 
            content="test",
            author=cls.author,
        )
        cls.comment = Comment.objects.create(
            content="Original comment",
            author=cls.author,
            article=cls.article,
        )
        cls.url = reverse("edit_comment", args=[cls.comment.id])

    def test_edit_comment_get(self):
        self.client.force_login(self.author)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(response.context["comment"], self.comment)

    def test_edit_comment_post_valid(self):
        self.client.force_login(self.author)
        response = self.client.post(self.url, {"content": "Updated comment"})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "Updated comment")

    def test_edit_comment_post_invalid(self):
        self.client.force_login(self.author)
        response = self.client.post(self.url, {"content": ""})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "Original comment")


class TestDeleteCommentView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            "tester@gmail.com", name="Test User", password="testpass1"
        )
        cls.article = Article.objects.create(
            title="test",
            summary="test",
            content="test", 
            author=cls.author,
        )

    def test_delete_comment(self):
        comment = Comment.objects.create(
            content="Test comment",
            author=self.author,
            article=self.article,
        )
        url = reverse("delete_comment", args=[comment.id])
        
        self.client.force_login(self.author)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertFalse(Comment.objects.filter(id=comment.id).exists())
