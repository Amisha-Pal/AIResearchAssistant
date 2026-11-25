from unittest import TestCase, mock

import requests

from ai_engine import device
from ai_engine.config import AIConfig
from ai_engine.llm.ollama_client import OllamaClient, OllamaError


class AIConfigTests(TestCase):
    def test_candidate_models_deduplicated(self):
        config = AIConfig(llm_model="qwen2.5:3b", llm_fallback_models=("qwen2.5:3b", "qwen2.5:1.5b"))
        self.assertEqual(config.candidate_models, ["qwen2.5:3b", "qwen2.5:1.5b"])

    def test_invalid_chunking_rejected(self):
        with self.assertRaises(ValueError):
            AIConfig(rag_chunk_size=100, rag_chunk_overlap=100)

    def test_invalid_device_rejected(self):
        with self.assertRaises(ValueError):
            AIConfig(compute_device="tpu")

    def test_django_settings_produce_valid_config(self):
        from ai_engine.config import get_ai_config

        config = get_ai_config()
        self.assertTrue(config.llm_model)
        self.assertFalse(config.ollama_base_url.endswith("/"))


class DeviceTests(TestCase):
    def test_cpu_when_torch_missing(self):
        with mock.patch.object(device, "torch_installed", return_value=False):
            self.assertEqual(device.resolve_device("auto"), "cpu")
            self.assertEqual(device.resolve_device("cuda"), "cpu")

    def test_explicit_cpu(self):
        self.assertEqual(device.resolve_device("cpu"), "cpu")

    def test_cuda_when_available(self):
        fake_torch = mock.MagicMock()
        fake_torch.cuda.is_available.return_value = True
        with mock.patch.object(device, "torch_installed", return_value=True), mock.patch.dict(
            "sys.modules", {"torch": fake_torch}
        ):
            self.assertEqual(device.resolve_device("auto"), "cuda")

    def test_cpu_fallback_when_cuda_unavailable(self):
        fake_torch = mock.MagicMock()
        fake_torch.cuda.is_available.return_value = False
        with mock.patch.object(device, "torch_installed", return_value=True), mock.patch.dict(
            "sys.modules", {"torch": fake_torch}
        ):
            self.assertEqual(device.resolve_device("cuda"), "cpu")


class OllamaClientTests(TestCase):
    def _session(self, payloads):
        session = mock.MagicMock()

        def get(url, timeout):
            response = mock.MagicMock()
            response.json.return_value = payloads[url.rsplit("/api", 1)[1]]
            return response

        session.get.side_effect = get
        return session

    def test_status(self):
        session = self._session({"/version": {"version": "0.5.1"}, "/tags": {"models": [{"name": "qwen2.5:3b"}]}})
        client = OllamaClient("http://ollama:11434/", session=session)
        self.assertEqual(client.status(), {"version": "0.5.1", "models": ["qwen2.5:3b"]})

    def test_connection_error_wrapped(self):
        session = mock.MagicMock()
        session.get.side_effect = requests.ConnectionError("refused")
        with self.assertRaises(OllamaError):
            OllamaClient("http://ollama:11434", session=session).version()
