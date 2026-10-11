import unittest
from unittest.mock import patch

from app.pipeline import simplifier


class SimplifierProviderFallbackTests(unittest.TestCase):
    @patch("app.pipeline.simplifier.retrieve_chunks", return_value=["context chunk"])
    @patch("app.pipeline.simplifier._load_prompt", return_value="Context:\n{retrieved_context}\nInput:\n{input_text}")
    @patch("app.pipeline.simplifier.InferenceClient")
    def test_raises_friendly_error_when_hf_provider_is_unavailable(
        self,
        mock_client,
        _mock_prompt,
        _mock_retriever,
    ):
        mock_client.return_value.chat_completion.side_effect = Exception(
            "402 Client Error: Payment Required"
        )

        with self.assertRaises(RuntimeError) as context:
            simplifier.simplify_text("Symptoms include chest pain.")

        message = str(context.exception).lower()
        self.assertIn("temporarily unavailable", message)
        self.assertIn("hugging face", message)


if __name__ == "__main__":
    unittest.main()
