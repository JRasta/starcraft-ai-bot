import pysc2
from pysc2 import run_game, maps, Race, Difficulty
from pysc2.player import Bot, Computer
from pysc2.ids.unit_typeid import *


class TerranBot(sc2.BotAI):
    def on_step(self, iteration):
        self.distribute_workers()  # in sc2/bot_ai.py
        self.build_workers()  # create workers in SC2
        self.build_sdepots()  # build supply depots
        self.build_vespene()  # build vespene buildings
        self.expand_base()  # expand to another location
        self.offensive_force_buildings()  # build army producing units
        self.build_offensive_force()  # build an army

    def build_workers(self):
        for cc in self.units(UnitTypeId.COMMANDCENTER).noqueue:
            if self.can_afford(UnitTypeId.SCV) and not self.units(UnitTypeId.SCV).amount == 16:
                self.do(cc.train(UnitTypeId.SCV))

    def build_sdepots(self):
        if self.supply_left < 4 and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
            commandc = self.units(UnitTypeId.COMMANDCENTER).ready
            if commandc.exists:
                if self.can_afford(UnitTypeId.SUPPLYDEPOT):
                    self.build(UnitTypeId.SUPPLYDEPOT, near=commandc.random)

    def build_vespene(self):
        for cc in self.units(UnitTypeId.COMMANDCENTER).ready:
            gases = self.state.vespene_geyser.closer_than(9.0, cc)
            for gas in gases:
                if not self.can_afford(UnitTypeId.REFINERY):
                    break
                worker = self.select_build_worker(gas.position)
                if worker is None:
                    break
                if not self.units(UnitTypeId.REFINERY).closer_than(1.0, gas).exists:
                    self.do(worker.build(UnitTypeId.REFINERY, gas))

    def expand_base(self):
        if self.units(UnitTypeId.COMMANDCENTER).amount < 3 and self.can_afford(UnitTypeId.COMMANDCENTER):
            self.expand_now()

    def offensive_force_buildings(self):
        commandc = self.units(UnitTypeId.COMMANDCENTER).ready
        if not self.units(UnitTypeId.BARRACKS).ready.exists:
            if self.can_afford(UnitTypeId.BARRACKS) and not self.already_pending(UnitTypeId.BARRACKS):
                self.build(UnitTypeId.BARRACKS, near=commandc.random)

    def build_offensive_force(self):
        for barracks in self.units(UnitTypeId.BARRACKS).ready.noqueue:
            if self.can_afford(UnitTypeId.MARINE) and self.supply_left > 0:
                self.do(barracks.train(UnitTypeId.MARINE))


run_game(maps.get("KingsCoveLE"), [
    Bot(Race.Terran, TerranBot()),
    Computer(Race.Zerg, Difficulty.VeryEasy)
], realtime=True)
