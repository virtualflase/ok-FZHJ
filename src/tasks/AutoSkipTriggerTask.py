from src.tasks.GameTriggerTaskBase import GameTriggerTaskBase


class AutoSkipTriggerTask(GameTriggerTaskBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_task()

    def setup_task(self):
        self.name = "自动跳过"
        self.description = "持续检测跳过和点击继续按钮"
        self.default_config.update({
            "enabled": True,
            "trigger_interval": 0.6,
        })

    def run(self):
        if not self.is_enabled():
            return
        # 每轮只推进一个最高优先级按钮，避免在同一帧里连续点击多个继续/跳过入口。
        self.click_first_present(
            "skip_button",
            "blank_continue_primary",
            "blank_continue_secondary",
            after_sleep=0.2,
        )
