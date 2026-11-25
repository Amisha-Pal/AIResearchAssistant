from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.core.testing import IsolatedAPITestCase

from .models import ResearchProject

User = get_user_model()


class ResearchProjectAPITests(IsolatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.ada = User.objects.create_user("ada", "ada@example.com", "s3cure-Passw0rd!")
        self.grace = User.objects.create_user("grace", "grace@example.com", "s3cure-Passw0rd!")
        self.client.force_authenticate(self.ada)
        self.list_url = reverse("project-list")

    def detail_url(self, project):
        return reverse("project-detail", args=[project.pk])

    def test_create_sets_owner_and_cleans_tags(self):
        response = self.client.post(
            self.list_url,
            {"title": "  Efficient RAG ", "description": "Survey", "tags": ["RAG", "rag", " LLM "]},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        project = ResearchProject.objects.get()
        self.assertEqual(project.owner, self.ada)
        self.assertEqual(project.title, "Efficient RAG")
        self.assertEqual(project.tags, ["rag", "llm"])

    def test_owner_cannot_be_overridden(self):
        self.client.post(self.list_url, {"title": "Mine", "owner": self.grace.pk}, format="json")
        self.assertEqual(ResearchProject.objects.get().owner, self.ada)

    def test_list_only_shows_own_projects(self):
        ResearchProject.objects.create(owner=self.ada, title="A")
        ResearchProject.objects.create(owner=self.grace, title="G")
        body = self.client.get(self.list_url).json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["title"], "A")

    def test_other_users_project_is_404(self):
        project = ResearchProject.objects.create(owner=self.grace, title="G")
        self.assertEqual(self.client.get(self.detail_url(project)).status_code, 404)
        self.assertEqual(self.client.patch(self.detail_url(project), {"title": "x"}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(self.detail_url(project)).status_code, 404)
        self.assertTrue(ResearchProject.objects.filter(pk=project.pk).exists())

    def test_update_and_delete(self):
        project = ResearchProject.objects.create(owner=self.ada, title="A")
        response = self.client.patch(self.detail_url(project), {"status": "archived"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "archived")
        self.assertEqual(self.client.delete(self.detail_url(project)).status_code, 204)
        self.assertFalse(ResearchProject.objects.exists())

    def test_duplicate_title_per_owner_rejected_case_insensitive(self):
        ResearchProject.objects.create(owner=self.ada, title="Graph Neural Nets")
        ResearchProject.objects.create(owner=self.grace, title="Shared Title")
        dup = self.client.post(self.list_url, {"title": "graph neural nets"}, format="json")
        self.assertEqual(dup.status_code, 400)
        self.assertIn("title", dup.json()["error"]["fields"])
        other_users_title = self.client.post(self.list_url, {"title": "Shared Title"}, format="json")
        self.assertEqual(other_users_title.status_code, 201)

    def test_rename_to_same_title_allowed(self):
        project = ResearchProject.objects.create(owner=self.ada, title="A")
        response = self.client.put(self.detail_url(project), {"title": "A", "status": "completed"}, format="json")
        self.assertEqual(response.status_code, 200, response.content)

    def test_filter_search_and_ordering(self):
        ResearchProject.objects.create(owner=self.ada, title="Vision transformers", status="active")
        ResearchProject.objects.create(owner=self.ada, title="Speech", description="transformers for audio", status="archived")
        ResearchProject.objects.create(owner=self.ada, title="Bandits", status="active")
        titles = lambda q: [p["title"] for p in self.client.get(self.list_url + q).json()["results"]]  # noqa: E731
        self.assertEqual(sorted(titles("?status=active")), ["Bandits", "Vision transformers"])
        self.assertEqual(sorted(titles("?search=transformers")), ["Speech", "Vision transformers"])
        self.assertEqual(titles("?ordering=title"), ["Bandits", "Speech", "Vision transformers"])

    def test_validation(self):
        self.assertEqual(self.client.post(self.list_url, {"title": "   "}, format="json").status_code, 400)
        self.assertEqual(self.client.post(self.list_url, {"title": "T", "status": "bogus"}, format="json").status_code, 400)
        self.assertEqual(self.client.post(self.list_url, {"title": "T", "tags": "notalist"}, format="json").status_code, 400)

    def test_pagination_page_size(self):
        for i in range(5):
            ResearchProject.objects.create(owner=self.ada, title=f"P{i}")
        body = self.client.get(self.list_url + "?page_size=2").json()
        self.assertEqual(body["count"], 5)
        self.assertEqual(len(body["results"]), 2)
        self.assertIsNotNone(body["next"])

    def test_requires_auth(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "not_authenticated")


class ResearchProjectModelTests(IsolatedAPITestCase):
    def test_null_tags_saved_as_empty_list(self):
        owner = User.objects.create_user("ada", "ada@example.com", "s3cure-Passw0rd!")
        project = ResearchProject.objects.create(owner=owner, title="P", tags=None)
        project.refresh_from_db()
        self.assertEqual(project.tags, [])
