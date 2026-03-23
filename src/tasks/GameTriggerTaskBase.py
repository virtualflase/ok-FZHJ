from __future__ import annotations

from typing import Any

from ok import TriggerTask


class GameTriggerTaskBase(TriggerTask):
    # 这四个迁移任务都走同一套配置兜底、找图和点击辅助，避免每个任务重复写样板代码。
    non_negative_int_keys: tuple[str, ...] = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_base_task()

    def init_base_task(self):
        if not hasattr(self, "default_config"):
            self.default_config = {}
        if not hasattr(self, "config_type"):
            self.config_type = {}
        self._missing_features_logged = set()

    def get_setting(self, key: str, default: Any = None) -> Any:
        # 运行时配置优先，其次才退回默认配置；这样界面里改过的值会立刻生效。
        task_config = getattr(self, "config", None)
        if isinstance(task_config, dict) and key in task_config:
            return task_config[key]
        if key in self.default_config:
            return self.default_config[key]
        return default

    def get_int_setting(self, key: str, default: int) -> int:
        value = self.get_setting(key, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            self.log_error(f"{self.__class__.__name__} invalid int config: {key}={value!r}")
            return default

    def is_enabled(self) -> bool:
        return bool(self.get_setting("enabled", True))

    def validate_config(self, key, value):
        if key in self.non_negative_int_keys and (not isinstance(value, int) or value < 0):
            return f"{key} must be a non-negative integer"
        return None

    def find_feature_box(self, feature_name: str):
        # 触发任务会高频运行，缺失特征如果每轮都报错会把日志刷满，所以这里只记录一次。
        if not self.feature_exists(feature_name):
            if feature_name not in self._missing_features_logged:
                self._missing_features_logged.add(feature_name)
                self.log_error(f"{self.__class__.__name__} missing feature: {feature_name}")
            return None
        return self.find_one(feature_name)

    def click_feature(self, feature_name: str, *, after_sleep: float = 0.0, relative_x: float = 0.5,
                      relative_y: float = 0.5) -> bool:
        box = self.find_feature_box(feature_name)
        if box is None:
            return False
        self.click_box(box, relative_x=relative_x, relative_y=relative_y, after_sleep=after_sleep)
        self.log_debug(f"{self.__class__.__name__} clicked {feature_name}")
        return True

    def click_first_present(self, *feature_names: str, after_sleep: float = 0.0) -> str | None:
        for feature_name in feature_names:
            if self.click_feature(feature_name, after_sleep=after_sleep):
                return feature_name
        return None
