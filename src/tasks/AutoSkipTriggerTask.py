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
        self.click_first_present(
            "skip_button",
            "blank_continue_primary",
            "blank_continue_secondary",
            after_sleep=0.2,
        )
