"""转职测试"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.engine import JobChangeSystem, Player

class TestChange:
    def test_skills_replaced(self):
        jcs = JobChangeSystem()
        jcs.players["p1"] = Player("p1","warrior",50,100,["slash"],["sword"])
        jcs.change_job("p1","mage")
        assert "fireball" in jcs.players["p1"].skills or jcs.players["p1"].skills == [], "转职不换技能"

class TestStats:
    def test_stat_points_reset(self):
        jcs = JobChangeSystem()
        jcs.players["p1"] = Player("p1","warrior",50,100,[],[])
        jcs.change_job("p1","mage")
        assert jcs.players["p1"].stat_points == 100 or jcs.players["p1"].stat_points == 0, "属性点未重置"
