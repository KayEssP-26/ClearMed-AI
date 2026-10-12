import asyncio
import unittest
from io import BytesIO
from unittest.mock import AsyncMock, patch

from fastapi import BackgroundTasks, HTTPException, UploadFile

from app import main
from app.models import SimplifyRequest


class ApiOffloadingTests(unittest.TestCase):
    @patch("app.main.log_request")
    @patch("app.main.run_in_threadpool", new_callable=AsyncMock)
    def test_text_pipeline_runs_in_threadpool(self, mock_threadpool, _mock_log_request):
        mock_threadpool.return_value = ("plain explanation", [], 30.0, 70.0, 100)

        response = asyncio.run(
            main.simplify(
                SimplifyRequest(text="clinical text"),
                BackgroundTasks(),
            )
        )

        self.assertEqual(response.simplified, "plain explanation")
        mock_threadpool.assert_awaited_once_with(main._run_pipeline, "clinical text")

    @patch("app.main.log_request")
    @patch("app.main.run_in_threadpool", new_callable=AsyncMock)
    def test_report_ocr_and_pipeline_run_in_threadpool(
        self,
        mock_threadpool,
        _mock_log_request,
    ):
        mock_threadpool.side_effect = [
            "extracted clinical text",
            ("plain explanation", [], 30.0, 70.0, 100),
        ]
        upload = UploadFile(file=BytesIO(b"image bytes"), filename="report.png")

        response = asyncio.run(main.simplify_report(BackgroundTasks(), upload))

        self.assertEqual(response.simplified, "plain explanation")
        self.assertEqual(mock_threadpool.await_count, 2)
        self.assertEqual(mock_threadpool.await_args_list[0].args[0], main.extract_text_from_file)
        self.assertEqual(mock_threadpool.await_args_list[1].args[0], main._run_pipeline)

    @patch("app.main.run_in_threadpool", new_callable=AsyncMock, return_value="  \n")
    def test_report_rejects_image_without_readable_text(self, mock_threadpool):
        upload = UploadFile(file=BytesIO(b"image bytes"), filename="blank.png")

        with self.assertRaises(HTTPException) as context:
            asyncio.run(main.simplify_report(BackgroundTasks(), upload))

        self.assertEqual(context.exception.status_code, 422)
        self.assertEqual(mock_threadpool.await_count, 1)