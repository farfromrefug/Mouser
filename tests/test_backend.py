import copy
import unittest
from unittest.mock import patch

from core.config import DEFAULT_CONFIG

try:
    from ui.backend import Backend
except ModuleNotFoundError:
    Backend = None


@unittest.skipIf(Backend is None, "PySide6 not installed in test environment")
class BackendDeviceLayoutTests(unittest.TestCase):
    def _make_backend(self):
        with (
            patch("ui.backend.load_config", return_value=copy.deepcopy(DEFAULT_CONFIG)),
            patch("ui.backend.save_config"),
        ):
            return Backend(engine=None)

    def test_defaults_to_generic_layout_without_connected_device(self):
        backend = self._make_backend()

        self.assertEqual(backend.effectiveDeviceLayoutKey, "generic_mouse")
        self.assertFalse(backend.hasInteractiveDeviceLayout)

    def test_disconnected_override_request_does_not_persist(self):
        backend = self._make_backend()
        backend._connected_device_key = "mx_master_3"
        backend.setDeviceLayoutOverride("mx_master")

        overrides = backend._cfg.get("settings", {}).get("device_layout_overrides", {})
        self.assertEqual(overrides, {})


@unittest.skipIf(Backend is None, "PySide6 not installed in test environment")
class BackendAutostartTests(unittest.TestCase):
    def _make_backend(
        self,
        *,
        config=None,
        autostart_supported=True,
        launch_enabled=False,
    ):
        effective_config = copy.deepcopy(config or DEFAULT_CONFIG)
        with (
            patch("ui.backend.load_config", return_value=effective_config),
            patch("ui.backend.save_config") as save_config_mock,
            patch("ui.backend.autostart.is_supported", return_value=autostart_supported),
            patch(
                "ui.backend.autostart.is_launch_at_login_enabled",
                return_value=launch_enabled,
            ),
        ):
            backend = Backend(engine=None)
        return backend, save_config_mock

    def test_syncs_start_at_login_from_existing_launch_agent(self):
        backend, save_config_mock = self._make_backend(
            autostart_supported=True,
            launch_enabled=True,
        )

        self.assertTrue(backend.startAtLogin)
        save_config_mock.assert_called_once()

    def test_set_start_at_login_uses_current_hidden_start_preference(self):
        config = copy.deepcopy(DEFAULT_CONFIG)
        config["settings"]["start_minimized"] = False

        with (
            patch("ui.backend.load_config", return_value=config),
            patch("ui.backend.save_config"),
            patch("ui.backend.autostart.is_supported", return_value=True),
            patch("ui.backend.autostart.is_launch_at_login_enabled", return_value=False),
            patch("ui.backend.autostart.enable_launch_at_login") as enable_mock,
        ):
            backend = Backend(engine=None)
            backend.setStartAtLogin(True)

        enable_mock.assert_called_once_with(start_hidden=False)
        self.assertTrue(backend.startAtLogin)

    def test_set_start_minimized_refreshes_existing_login_item(self):
        config = copy.deepcopy(DEFAULT_CONFIG)
        config["settings"]["start_at_login"] = True
        config["settings"]["start_minimized"] = True

        with (
            patch("ui.backend.load_config", return_value=config),
            patch("ui.backend.save_config"),
            patch("ui.backend.autostart.is_supported", return_value=True),
            patch("ui.backend.autostart.is_launch_at_login_enabled", return_value=True),
            patch("ui.backend.autostart.enable_launch_at_login") as enable_mock,
        ):
            backend = Backend(engine=None)
            backend.setStartMinimized(False)

        enable_mock.assert_called_once_with(start_hidden=False)
        self.assertFalse(backend.startMinimized)


if __name__ == "__main__":
    unittest.main()
