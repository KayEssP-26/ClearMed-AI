import unittest
from unittest.mock import patch

from app.pipeline import simplifier


class SimplifierProviderFallbackTests(unittest.TestCase):
    @patch("app.pipeline.simplifier.retrieve_chunks", return_value=["context chunk"])
    @patch("app.pipeline.simplifier._load_prompt", return_value="Context:\n{retrieved_context}\nInput:\n{input_text}")
    @patch("app.pipeline.simplifier.get_gemini_client")
    def test_uses_gemini_when_available(
        self,
        mock_client_factory,
        _mock_prompt,
        _mock_retriever,
    ):
        mock_client = mock_client_factory.return_value
        mock_client.interactions.create.return_value.output_text = "This is a clear explanation."

        simplified, sources = simplifier.simplify_text("Symptoms include chest pain.")

        self.assertEqual(simplified, "This is a clear explanation.")
        self.assertEqual(sources, ["context chunk"])
        mock_client.interactions.create.assert_called_once()
        self.assertEqual(
            mock_client.interactions.create.call_args.kwargs["model"],
            "gemini-3.5-flash-lite",
        )
        self.assertFalse(mock_client.interactions.create.call_args.kwargs["store"])

    @patch("app.pipeline.simplifier.retrieve_chunks", return_value=["context chunk"])
    @patch("app.pipeline.simplifier._load_prompt", return_value="Context:\n{retrieved_context}\nInput:\n{input_text}")
    @patch("app.pipeline.simplifier.get_gemini_client")
    def test_raises_friendly_error_when_gemini_is_unavailable(
        self,
        mock_client_factory,
        _mock_prompt,
        _mock_retriever,
    ):
        mock_client = mock_client_factory.return_value
        mock_client.interactions.create.side_effect = Exception("403 forbidden secret-value")

        with self.assertRaises(RuntimeError) as context:
            simplifier.simplify_text("Symptoms include chest pain.")

        message = str(context.exception).lower()
        self.assertIn("temporarily unavailable", message)
        self.assertIn("gemini", message)
        self.assertNotIn("secret-value", message)


if __name__ == "__main__":
    unittest.main()
