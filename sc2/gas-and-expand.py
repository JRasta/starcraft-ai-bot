import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.ids.unit_typeid import *


class TerranBot(sc2.BotAI):
    async def on_step(self, iteration):
        await self.distribute_workers()  # in sc2/bot_ai.py
        await self.build_workers()  # create workers in SC2
        await self.build_sdepots()  # build supply depots
        await self.build_vespene()  # build vespene buildings
        await self.expand_base()  # expand to another location

    async def build_workers(self):
        for cc in self.units(UnitTypeId.COMMANDCENTER).noqueue:
            if self.can_afford(UnitTypeId.SCV) and not self.units(UnitTypeId.SCV).amount == 16:
                await self.do(cc.train(UnitTypeId.SCV))

    async def build_sdepots(self):
        if self.supply_left < 4 and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
            commandc = self.units(UnitTypeId.COMMANDCENTER).ready
            if commandc.exists:
                if self.can_afford(UnitTypeId.SUPPLYDEPOT):
                    await self.build(UnitTypeId.SUPPLYDEPOT, near=commandc.random)

    async def build_vespene(self):
        for cc in self.units(UnitTypeId.COMMANDCENTER).ready:
            gases = self.state.vespene_geyser.closer_than(9.0, cc)
            for gas in gases:
                if not self.can_afford(UnitTypeId.REFINERY):
                    break
                worker = self.select_build_worker(gas.position)
                if worker is None:
                    break
                if not self.units(UnitTypeId.REFINERY).closer_than(1.0, gas).exists:
                    await self.do(worker.build(UnitTypeId.REFINERY, gas))

    async def expand_base(self):
        if self.units(UnitTypeId.COMMANDCENTER).amount < 3 and self.can_afford(UnitTypeId.COMMANDCENTER):
            await self.expand_now()


run_game(maps.get("KingsCoveLE"), [
    Bot(Race.Terran, TerranBot()),
    Computer(Race.Zerg, Difficulty.VeryEasy)
], realtime=True)
