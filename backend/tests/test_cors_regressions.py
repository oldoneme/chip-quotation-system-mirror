import os
import sys
import unittest
import importlib
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, '/home/qixin/projects/chip-quotation-system/backend')

class CorsRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app.main import app

        cls.client = TestClient(app)

    def assert_preflight_allows_origin(self, origin: str):
        response = self.client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("access-control-allow-origin"), origin)

    def test_preflight_allows_wecom_dev_origin(self):
        self.assert_preflight_allows_origin("https://wecom-dev.chipinfos.com.cn")

    def test_preflight_allows_localhost_origin(self):
        self.assert_preflight_allows_origin("http://localhost:3000")

    def test_cors_origins_include_configured_production_host(self):
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",
                "FRONTEND_BASE_URL": "https://wecom-quote.chipinfos.com.cn",
                "WECOM_BASE_URL": "https://wecom-quote.chipinfos.com.cn",
                "API_BASE_URL": "https://wecom-quote.chipinfos.com.cn/api",
            },
            clear=False,
        ):
            from app.config import get_cors_origins

            origins = get_cors_origins()

        self.assertIn("https://wecom-quote.chipinfos.com.cn", origins)
        self.assertNotIn("http://localhost:3000", origins)

    def test_production_env_initializes_cors_middleware_for_wecom_host(self):
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",
                "FRONTEND_BASE_URL": "https://wecom-quote.chipinfos.com.cn",
                "WECOM_BASE_URL": "https://wecom-quote.chipinfos.com.cn",
                "API_BASE_URL": "https://wecom-quote.chipinfos.com.cn/api",
            },
            clear=False,
        ):
            import app.config as config_module
            import app.main as main_module

            config_module = importlib.reload(config_module)
            main_module = importlib.reload(main_module)
            try:
                client = TestClient(main_module.app)
                response = client.options(
                    "/api/v1/auth/login",
                    headers={
                        "Origin": "https://wecom-quote.chipinfos.com.cn",
                        "Access-Control-Request-Method": "GET",
                    },
                )
            finally:
                importlib.reload(config_module)
                importlib.reload(main_module)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "https://wecom-quote.chipinfos.com.cn",
        )


if __name__ == "__main__":
    unittest.main()
