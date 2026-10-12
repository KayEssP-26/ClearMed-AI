import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.rag import embedder
from app.rag import retriever


class GeminiEmbedderTests(unittest.TestCase):
    @patch("app.rag.embedder.get_gemini_client")
    def test_embeds_query_with_retrieval_instruction_and_index_dimension(self, mock_client_factory):
        mock_client = mock_client_factory.return_value
        mock_client.models.embed_content.return_value.embeddings = [
            SimpleNamespace(values=[0.25, -0.5])
        ]

        vector = embedder.embed_text("abnormal blood test")

        self.assertAlmostEqual(vector[0], 1 / (5**0.5))
        self.assertAlmostEqual(vector[1], -2 / (5**0.5))
        call = mock_client.models.embed_content.call_args.kwargs
        self.assertEqual(call["model"], "gemini-embedding-001")
        self.assertEqual(call["contents"], "task: search result | query: abnormal blood test")
        self.assertEqual(call["config"].output_dimensionality, 384)
        self.assertEqual(call["config"].task_type, "RETRIEVAL_QUERY")

    @patch("app.rag.embedder.get_gemini_client")
    def test_embeds_corpus_batch_with_matching_configuration(self, mock_client_factory):
        mock_client = mock_client_factory.return_value
        mock_client.models.embed_content.return_value.embeddings = [
            SimpleNamespace(values=[0.1, 0.2]),
            SimpleNamespace(values=[0.3, 0.4]),
        ]

        vectors = embedder.embed_batch(["first abstract", "second abstract"])

        self.assertAlmostEqual(sum(value * value for value in vectors[0]), 1.0)
        self.assertAlmostEqual(sum(value * value for value in vectors[1]), 1.0)
        call = mock_client.models.embed_content.call_args.kwargs
        self.assertEqual(call["model"], "gemini-embedding-001")
        self.assertEqual(call["contents"], ["first abstract", "second abstract"])
        self.assertEqual(call["config"].output_dimensionality, 384)
        self.assertEqual(call["config"].task_type, "RETRIEVAL_DOCUMENT")

    @patch("app.rag.embedder.get_gemini_client")
    def test_empty_batch_does_not_call_provider(self, mock_client_factory):
        self.assertEqual(embedder.embed_batch([]), [])
        mock_client_factory.assert_not_called()

    @patch("app.rag.retriever.Pinecone")
    @patch("app.rag.retriever.embed_text", return_value=[0.1, 0.2])
    def test_retrieval_uses_gemini_embedding_namespace(self, _mock_embed_text, mock_pinecone):
        mock_index = mock_pinecone.return_value.Index.return_value
        mock_index.query.return_value = {
            "matches": [{"metadata": {"text": "retrieved source"}}]
        }

        chunks = retriever.retrieve_chunks("query text", top_k=1)

        self.assertEqual(chunks, ["retrieved source"])
        self.assertEqual(
            mock_index.query.call_args.kwargs["namespace"],
            embedder.PINECONE_NAMESPACE,
        )


if __name__ == "__main__":
    unittest.main()