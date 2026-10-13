"""Uploads (user, 2026-10-08): only JPEG photos, and JPEG or PDF documents - checked by the file's
own bytes, not only its declared type - each at most 5MB, and an oversized request is refused
before the server stores it."""

import asyncio
import io
import unittest

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.testclient import TestClient
from starlette.datastructures import Headers

from app.core.body_limit import BodySizeLimit
from app.core.media import MAX_REQUEST_BYTES, MAX_UPLOAD_BYTES
from app.utils.validators import read_document_upload, read_photo_upload

JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 64
PDF_BYTES = b"%PDF-1.4\n%synthetic"
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def upload(content: bytes, content_type: str) -> UploadFile:
    return UploadFile(io.BytesIO(content), filename="f", headers=Headers({"content-type": content_type}))


def run(coro):
    return asyncio.run(coro)


class OnlyJpegPhotosAndJpegOrPdfDocuments(unittest.TestCase):
    def assertRefused(self, coro, detail):
        with self.assertRaises(HTTPException) as caught:
            run(coro)
        self.assertEqual((caught.exception.status_code, caught.exception.detail), (400, detail))

    def test_a_jpeg_photo_is_accepted(self):
        self.assertEqual(run(read_photo_upload(upload(JPEG_BYTES, "image/jpeg"), size_error_detail="big")), (JPEG_BYTES, "jpg"))

    def test_any_other_photo_type_is_refused(self):
        for content, content_type in ((PNG_BYTES, "image/png"), (JPEG_BYTES, "image/webp"), (JPEG_BYTES, "image/gif"),
                                      (PDF_BYTES, "application/pdf")):
            with self.subTest(content_type=content_type):
                self.assertRefused(read_photo_upload(upload(content, content_type), size_error_detail="big"),
                                   "Only JPG photos are allowed")

    def test_a_document_may_be_jpeg_or_pdf(self):
        self.assertEqual(run(read_document_upload(upload(JPEG_BYTES, "image/jpeg"), size_error_detail="big"))[1], "jpg")
        self.assertEqual(run(read_document_upload(upload(PDF_BYTES, "application/pdf"), size_error_detail="big"))[1], "pdf")
        for content_type in ("application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                             "image/png"):
            with self.subTest(content_type=content_type):
                self.assertRefused(read_document_upload(upload(PDF_BYTES, content_type), size_error_detail="big"),
                                   "Only JPG or PDF files are allowed")

    def test_the_declared_type_must_match_the_files_own_bytes(self):
        for content in (PNG_BYTES, b"<html><script>alert(1)</script>", PDF_BYTES, b""):
            with self.subTest(content=content[:8]):
                self.assertRefused(read_photo_upload(upload(content, "image/jpeg"), size_error_detail="big"),
                                   "Only JPG photos are allowed")
        self.assertRefused(read_document_upload(upload(JPEG_BYTES, "application/pdf"), size_error_detail="big"),
                           "Only JPG or PDF files are allowed")

    def test_exactly_5mb_is_accepted_and_one_byte_more_is_refused_without_reading_the_rest(self):
        at_limit = JPEG_BYTES + b"\x00" * (MAX_UPLOAD_BYTES - len(JPEG_BYTES))
        self.assertEqual(len(run(read_photo_upload(upload(at_limit, "image/jpeg"), size_error_detail="big"))[0]), MAX_UPLOAD_BYTES)

        huge = upload(JPEG_BYTES + b"\x00" * (3 * MAX_UPLOAD_BYTES), "image/jpeg")
        self.assertRefused(read_photo_upload(huge, size_error_detail="Photo must be 5MB or smaller"), "Photo must be 5MB or smaller")
        self.assertEqual(huge.file.tell(), MAX_UPLOAD_BYTES + 1)   # read stopped one byte past the limit


class OversizedRequestsAreRefusedBeforeTheyAreStored(unittest.TestCase):
    LIMIT = 1000

    def setUp(self):
        app = FastAPI()
        self.endpoint_ran = False

        @app.post("/echo")
        async def echo(request: Request):
            body = await request.body()
            self.endpoint_ran = True
            return {"size": len(body)}

        app.add_middleware(BodySizeLimit, max_bytes=self.LIMIT)
        self.client = TestClient(app)

    def test_a_body_within_the_limit_goes_through(self):
        response = self.client.post("/echo", content=b"x" * self.LIMIT)
        self.assertEqual((response.status_code, response.json()), (200, {"size": self.LIMIT}))

    def test_a_declared_size_over_the_limit_is_refused_before_the_endpoint_runs(self):
        response = self.client.post("/echo", content=b"x" * (self.LIMIT + 1))
        self.assertEqual(response.status_code, 413)
        self.assertFalse(self.endpoint_ran)

    def test_a_body_with_no_declared_size_is_counted_as_it_arrives(self):
        chunks = (b"x" * 400 for _ in range(5))   # streamed (chunked): no Content-Length to check up front
        response = self.client.post("/echo", content=chunks)
        self.assertEqual(response.status_code, 413)
        self.assertFalse(self.endpoint_ran)


class TheAppRefusesOversizedRequests(unittest.TestCase):
    def test_the_limit_is_wired_into_the_app(self):
        from app.main import app

        response = TestClient(app).post("/trainees/login", content=b"x" * (MAX_REQUEST_BYTES + 1),
                                        headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 413)


if __name__ == "__main__":
    unittest.main()
