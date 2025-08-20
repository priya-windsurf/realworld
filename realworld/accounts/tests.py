import http

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse, reverse_lazy

from .forms import UserCreationForm, SettingsForm

User = get_user_model()


class TestUserModel(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            "tester@gmail.com", name="Test User", password="testpass1"
        )
        self.assertEqual(user.email, "tester@gmail.com")
        self.assertTrue(user.check_password("testpass1"))

    def test_create_user_without_password(self):
        user = User.objects.create_user(
            "tester@gmail.com", name="Test User", password=None
        )
        self.assertEqual(user.email, "tester@gmail.com")
        self.assertTrue(user.password)
        self.assertFalse(user.check_password("testpass1"))

    def test_get_full_name(self):
        self.assertEqual(User(name="Test User").get_full_name(), "Test User")

    def test_get_short_name(self):
        self.assertEqual(User(name="Test User").get_short_name(), "Test User")


class TestUserCreationForm(TestCase):
    form_data = {
        "name": "Tester",
        "email": "tester@gmail.com",
        "password": "testpass1",
    }

    def test_save(self):
        form = UserCreationForm(self.form_data)
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertTrue(user.check_password("testpass1"))

    def test_save_commit_false(self):
        form = UserCreationForm(self.form_data)
        self.assertTrue(form.is_valid())

        user = form.save(commit=False)
        self.assertTrue(user.check_password("testpass1"))
        self.assertIsNone(user.pk)


class TestFollowView(TestCase):
    password = "testpass"

    @classmethod
    def setUpTestData(cls):

        cls.user = User(
            email="tester1@gmail.com",
            name="tester1",
        )
        cls.user.set_password(cls.password)
        cls.user.save()

        cls.other_user = User(
            email="tester2@gmail.com",
            name="tester2",
        )
        cls.other_user.set_password(cls.password)
        cls.other_user.save()

        cls.url = reverse("follow", args=[cls.user.id])

    def test_follow(self):
        self.client.force_login(self.other_user)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(self.user.followers.filter(pk=self.other_user.id).exists())

    def test_same_user(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)
        self.assertFalse(self.user.followers.filter(pk=self.user.id).exists())

    def test_unfollow(self):
        self.client.force_login(self.other_user)
        self.user.followers.add(self.other_user)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertFalse(self.user.followers.filter(pk=self.other_user.id).exists())


class TestRegisterView(TestCase):
    url = reverse_lazy("register")

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

    def test_post_invalid(self):
        response = self.client.post(self.url, {"email": "invalid"})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

    def test_post_valid(self):
        response = self.client.post(
            self.url,
            {
                "name": "Tester",
                "email": "tester@gmail.com",
                "password": "testpass1",
            },
        )
        self.assertEqual(response.headers["HX-Redirect"], reverse("home"))
        self.assertTrue(User.objects.filter(email="tester@gmail.com").exists())


class TestCheckEmailView(TestCase):
    url = reverse_lazy("check_email")

    def test_not_exists(self):
        response = self.client.get(self.url, {"email": "tester@gmail.com"})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertNotContains(response, "Email is in use")

    def test_exists(self):
        User.objects.create_user(
            "tester@gmail.com", name="Test User", password="testpass1"
        )

        response = self.client.get(self.url, {"email": "tester@gmail.com"})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, "This email is in use")

    def test_no_email_parameter(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(response.content.decode(), "")

    def test_empty_email_parameter(self):
        response = self.client.get(self.url, {"email": ""})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(response.content.decode(), "")


class TestSettingsForm(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "tester@gmail.com", name="Test User", password="testpass1"
        )

    def test_save_with_password(self):
        form_data = {
            "name": "Updated Name",
            "email": "updated@gmail.com",
            "bio": "Updated bio",
            "password": "newpassword123",
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertEqual(user.name, "Updated Name")
        self.assertEqual(user.email, "updated@gmail.com")
        self.assertEqual(user.bio, "Updated bio")
        self.assertTrue(user.check_password("newpassword123"))

    def test_save_without_password(self):
        form_data = {
            "name": "Updated Name",
            "email": "updated@gmail.com",
            "bio": "Updated bio",
            "password": "",
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertEqual(user.name, "Updated Name")
        self.assertTrue(user.check_password("testpass1"))

    def test_save_commit_false(self):
        form_data = {
            "name": "Updated Name",
            "email": "updated@gmail.com",
            "password": "newpassword123",
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

        user = form.save(commit=False)
        self.assertEqual(user.name, "Updated Name")
        self.assertTrue(user.check_password("newpassword123"))


class TestProfileView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "tester@gmail.com", name="Test User", password="testpass1"
        )
        self.other_user = User.objects.create_user(
            "other@gmail.com", name="Other User", password="testpass1"
        )

    def test_profile_view(self):
        url = reverse("profile", args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, self.user.name)

    def test_profile_view_with_favorites_filter(self):
        url = reverse("profile", args=[self.user.id])
        response = self.client.get(url, {"favorites": "true"})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.context["favorites"])

    def test_profile_view_following_status(self):
        self.user.followers.add(self.other_user)
        self.client.force_login(self.other_user)
        
        url = reverse("profile", args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)


class TestSettingsView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "tester@gmail.com", name="Test User", password="testpass1"
        )
        self.url = reverse("settings")

    def test_get_settings(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

    def test_post_valid_settings(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {
            "name": "Updated Name",
            "email": "updated@gmail.com",
            "bio": "Updated bio",
        })
        self.assertEqual(response.headers.get("HX-Redirect"), self.user.get_absolute_url())

    def test_post_invalid_settings(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {
            "name": "",
            "email": "invalid-email",
        })
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, "form")
