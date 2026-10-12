import unittest
from unittest.mock import Mock, call, patch

from app.rag import ingest


class CorpusIngestBatchTests(unittest.TestCase):
    @patch("app.rag.ingest.time.sleep")
    @patch("app.rag.ingest.embed_batch", return_value=[[0.1, 0.2]])
    def test_upserts_stable_ids_into_gemini_namespace(self, _mock_embed_batch, _mock_sleep):
        index = Mock()

        result = ingest._flush(index, ["same corpus chunk"], 1, None)

        first_records = index.upsert.call_args.kwargs["vectors"]
        ingest._flush(index, ["same corpus chunk"], 1, None)
        second_records = index.upsert.call_args.kwargs["vectors"]

        self.assertIsInstance(result, float)
        self.assertEqual(first_records[0]["id"], second_records[0]["id"])
        self.assertEqual(
            index.upsert.call_args.kwargs["namespace"],
            ingest.PINECONE_NAMESPACE,
        )

    @patch("app.rag.ingest.time.sleep")
    @patch("app.rag.ingest.embed_batch", side_effect=[RuntimeError("429 quota exceeded"), [[0.1]]])
    def test_retries_after_quota_response(self, mock_embed_batch, mock_sleep):
        index = Mock()

        ingest._flush(index, ["corpus chunk"], 1, None)

        self.assertEqual(mock_embed_batch.call_count, 2)
        mock_sleep.assert_called_once_with(ingest._EMBEDDING_WINDOW_SECONDS)
        self.assertEqual(index.upsert.call_count, 1)


if __name__ == "__main__":
    unittest.main()