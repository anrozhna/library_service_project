from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from tests_helpers import sample_user

USER_DATA = {
    "email": "test@test.com",
    "password": "TestPass12345",
}

REGISTER_URL = reverse("users:register")
TOKEN_URL = reverse("users:token_obtain_pair")
TOKEN_REFRESH_URL = reverse("users:token_refresh")
ME_URL = reverse("users:manage")


class PublicUserApiTests(APITestCase):
    def test_create_user(self):
        response = self.client.post(REGISTER_URL, USER_DATA)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], USER_DATA["email"])

    def test_create_token(self):
        sample_user(**USER_DATA)

        response = self.client.post(TOKEN_URL, USER_DATA)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_create_token_invalid_credentials(self):
        sample_user(**USER_DATA)

        response = self.client.post(
            TOKEN_URL,
            {
                "email": "test@test.com",
                "password": "wrongpass",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        user = sample_user(**USER_DATA)

        refresh = RefreshToken.for_user(user)

        response = self.client.post(
            TOKEN_REFRESH_URL,
            {"refresh": str(refresh)},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_auth_required_for_profile(self):
        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(APITestCase):
    def setUp(self):
        self.user = sample_user(**USER_DATA)
        self.client.force_authenticate(self.user)

    def test_retrieve_profile(self):
        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_profile(self):
        data_for_update = {
            "first_name": "First",
            "last_name": "Last",
        }

        response = self.client.patch(ME_URL, data_for_update)

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.first_name, data_for_update["first_name"])
        self.assertEqual(self.user.last_name, data_for_update["last_name"])

    def test_put_profile(self):
        payload = {
            "email": self.user.email,
            "password": self.user.password,
            "first_name": "First",
            "last_name": "Last",
        }

        response = self.client.put(ME_URL, payload)

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.first_name, "First")
        self.assertEqual(self.user.last_name, "Last")
