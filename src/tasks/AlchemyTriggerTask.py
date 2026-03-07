from src.tasks.GameTriggerTaskBase import GameTriggerTaskBase


class AlchemyTriggerTask(GameTriggerTaskBase):
    non_negative_int_keys = ("max_rounds",)
    MODE_OPTION_POINT = (0.59375, 0.27778)
    ALCHEMY_START_POINT = (0.78125, 0.83333)
    ALCHEMY_OBTAIN_POINT = (0.9375, 0.97222)
    WHITE_MATERIAL_STOP_THRESHOLD = (0.34375, 0.41667)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_task()

    def setup_task(self):
        self.name = "自动炼金"
        self.description = "切换炼金模式并按轮数自动炼金"
        self.change_mode = getattr(self, "change_mode", False)
        self.round_count = getattr(self, "round_count", 0)
        self.default_config.update({
            "enabled": True,
            "max_rounds": 1,
            "trigger_interval": 0.6,
        })

    def run(self):
        if not self.is_enabled():
            return

        max_rounds = self.get_int_setting("max_rounds", 1)

        if self.handle_obtain(max_rounds):
            return

        if self.round_count >= max_rounds:
            self.finish_alchemy_run("max_rounds_reached")
            return

        if self.click_feature("alchemy_entry", after_sleep=0.4):
            return

        if not self.change_mode and self.find_feature_box("alchemy_one_click_select") is not None:
            if self.click_feature("alchemy_mode_switch", after_sleep=0.6):
                self.click_relative(*self.MODE_OPTION_POINT, after_sleep=0.6)
                self.change_mode = True
                self.log_info("AlchemyTriggerTask switched to item-count mode")
                return

        if self.find_feature_box("alchemy_item_count_mode") is None:
            return

        if self.should_stop_for_white_material():
            self.finish_alchemy_run("white_material_threshold")
            return

        if not self.click_feature("alchemy_one_click_select", after_sleep=2.0):
            return
        if not self.click_feature("alchemy_confirm", after_sleep=0.4):
            return

        self.round_count += 1
        self.log_info(f"AlchemyTriggerTask round start={self.round_count}")
        self.click_relative(*self.ALCHEMY_START_POINT, after_sleep=2.0)

    def handle_obtain(self, max_rounds: int) -> bool:
        if self.find_feature_box("alchemy_obtain") is None:
            return False
        self.click_relative(*self.ALCHEMY_OBTAIN_POINT, after_sleep=0.6)
        self.log_debug("AlchemyTriggerTask clicked obtain")
        if self.round_count >= max_rounds:
            self.finish_alchemy_run("obtain_after_max_rounds")
        return True

    def should_stop_for_white_material(self) -> bool:
        white_material = self.find_feature_box("alchemy_white_material")
        if white_material is None:
            return False
        center_x, center_y = white_material.center()
        screen_width = getattr(self, "screen_width", 1) or 1
        screen_height = getattr(self, "screen_height", 1) or 1
        return (
            center_x / screen_width < self.WHITE_MATERIAL_STOP_THRESHOLD[0]
            and center_y / screen_height < self.WHITE_MATERIAL_STOP_THRESHOLD[1]
        )

    def finish_alchemy_run(self, reason: str):
        self.log_info(f"AlchemyTriggerTask finish reason={reason}")
        if self.click_feature("alchemy_cancel", after_sleep=0.6):
            self.click_feature("back_button", after_sleep=2.0)
