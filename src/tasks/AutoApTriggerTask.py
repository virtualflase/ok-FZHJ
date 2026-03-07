from src.tasks.GameTriggerTaskBase import GameTriggerTaskBase


class AutoApTriggerTask(GameTriggerTaskBase):
    non_negative_int_keys = ("max_use_clicks",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_task()

    def setup_task(self):
        self.name = "自动补AP"
        self.description = "检测 AP 提示后执行补药和返回流程"
        self.default_config.update({
            "enabled": True,
            "max_use_clicks": 4,
            "trigger_interval": 0.6,
        })

    def run(self):
        if not self.is_enabled():
            return
        if self.find_feature_box("ap_tip") is None:
            return

        self.log_info("AutoApTriggerTask ap flow start")
        if not self.click_feature("ap_use_entry", after_sleep=0.6):
            return

        max_clicks = self.get_int_setting("max_use_clicks", 4)
        used = 0
        while used < max_clicks:
            if not self.click_feature("ap_use_confirm", after_sleep=0.6):
                break
            used += 1

        for _ in range(2):
            self.click_feature("back_button", after_sleep=0.5)
        self.click_feature("next_stage_button", after_sleep=0.5)
        self.log_info(f"AutoApTriggerTask ap flow finish used={used}")
