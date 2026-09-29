"""转职觉醒 - 带7个bug"""
from dataclasses import dataclass, field

@dataclass class Player:
    pid: str
    job: str
    level: int
    stat_points: int
    skills: list
    equipment: list

class JobChangeSystem:
    def __init__(self):
        self.players: dict[str, Player] = {}
        self.cooldown = {}  # bug3: 只看等级
        self.awakening_tasks = {}  # bug4: 不看任务
        self.history = []  # bug6: 无记录

    def change_job(self, pid, new_job):
        p = self.players[pid]
        # bug1: 只换名称不换技能
        p.job = new_job
        # bug2: 属性点不重置
        # bug5: 装备不处理
        return True

    def can_change(self, pid):
        p = self.players[pid]
        # bug3: 只看等级
        return p.level >= 50

    def unlock_awakening(self, pid):
        # bug4: 只看转职次数
        return True

    def awaken(self, pid):
        p = self.players[pid]
        # bug7: 可重复觉醒
        p.stat_points += 100
        return True
