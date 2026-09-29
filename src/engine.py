"""转职觉醒系统 - 修复版"""
import time
from dataclasses import dataclass, field

MIN_CHANGE_LEVEL = 50
CHANGE_COOLDOWN = 7 * 24 * 3600  # 7天冷却
AWAKENING_BONUS = 100
BACKPACK_CAPACITY = 50

JOB_SKILLS = {
    "warrior": ["slash", "shield_block"],
    "mage": ["fireball", "frostbolt"],
    "priest": ["heal", "smite"],
    "archer": ["aimed_shot", "multishot"],
}

SKILL_REFUND_POINTS = 1  # 每个旧技能返还的技能点

ITEM_TYPES = {
    "sword": "weapon_melee", "shield": "shield", "heavy_armor": "heavy_armor",
    "staff": "weapon_caster", "wand": "weapon_caster", "robe": "cloth_armor",
    "bow": "weapon_ranged", "leather_armor": "leather_armor",
}

JOB_EQUIPMENT_TYPES = {
    "warrior": {"weapon_melee", "shield", "heavy_armor"},
    "mage": {"weapon_caster", "cloth_armor"},
    "priest": {"weapon_caster", "cloth_armor"},
    "archer": {"weapon_ranged", "leather_armor"},
}

AWAKENING_TASKS = ["awaken_trial_1", "awaken_trial_2", "awaken_trial_3"]


@dataclass
class Player:
    pid: str
    job: str
    level: int
    stat_points: int
    skills: list
    equipment: list
    allocated_stats: dict = field(default_factory=dict)
    skill_points: int = 0
    inventory: list = field(default_factory=list)
    mail: list = field(default_factory=list)
    awakened: bool = False
    awakening_done: set = field(default_factory=set)
    last_change_time: float = 0.0
    change_count: int = 0


class JobChangeSystem:
    def __init__(self, clock=time.time):
        self.players: dict[str, Player] = {}
        self.history: list[dict] = []  # 转职记录
        self._clock = clock

    # bug3 修复: 等级 + 时间冷却双重条件
    def can_change(self, pid):
        p = self.players[pid]
        if p.level < MIN_CHANGE_LEVEL:
            return False
        return self._clock() - p.last_change_time >= CHANGE_COOLDOWN

    # bug1/bug2/bug5/bug6 修复
    def change_job(self, pid, new_job, reason=""):
        if not self.can_change(pid):
            return False
        p = self.players[pid]
        if new_job == p.job or new_job not in JOB_SKILLS:
            return False
        old_job = p.job

        # bug1: 替换为新职业技能树, 旧技能按规则返还技能点
        p.skill_points += len(p.skills) * SKILL_REFUND_POINTS
        p.skills = list(JOB_SKILLS[new_job])

        # bug2: 已分配属性点回收, 全部重置为未分配
        p.stat_points += sum(p.allocated_stats.values())
        p.allocated_stats = {}

        # bug5: 不兼容装备自动卸下, 背包满则进邮件
        allowed = JOB_EQUIPMENT_TYPES[new_job]
        kept, removed = [], []
        for item in p.equipment:
            if ITEM_TYPES.get(item) in allowed:
                kept.append(item)
            else:
                removed.append(item)
        p.equipment = kept
        for item in removed:
            if len(p.inventory) < BACKPACK_CAPACITY:
                p.inventory.append(item)
            else:
                p.mail.append(item)

        # bug6: 保存转职记录(历史职业/时间/原因)
        now = self._clock()
        self.history.append({
            "pid": pid, "from_job": old_job, "to_job": new_job,
            "time": now, "reason": reason,
        })
        p.job = new_job
        p.last_change_time = now
        p.change_count += 1
        return True

    def get_history(self, pid):
        return [h for h in self.history if h["pid"] == pid]

    # bug4 修复: 觉醒需完成任务链
    def complete_awakening_task(self, pid, task_id):
        p = self.players[pid]
        if task_id in AWAKENING_TASKS:
            p.awakening_done.add(task_id)
            return True
        return False

    def unlock_awakening(self, pid):
        p = self.players[pid]
        return all(t in p.awakening_done for t in AWAKENING_TASKS)

    # bug7 修复: 觉醒只能一次, 重复觉醒无效
    def awaken(self, pid):
        p = self.players[pid]
        if p.awakened or not self.unlock_awakening(pid):
            return False
        p.awakened = True
        p.stat_points += AWAKENING_BONUS
        return True
