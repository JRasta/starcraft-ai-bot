from pysc2.agents import base_agent
from pysc2.env import sc2_env
from pysc2.lib import actions, features, units
from absl import app
import random


def can_do(obs, action):
    return action in obs.observation.available_actions


def get_units_by_type(obs, unit_type):
    return [unit for unit in obs.observation.feature_units
            if unit.unit_type == unit_type]


def unit_type_is_selected(obs, unit_type):
    if (len(obs.observation.single_select) > 0 and
       obs.observation.single_select[0].unit_type == unit_type):
        return True
    if (len(obs.observation.multi_select) > 0 and
       obs.observation.multi_select[0].unit_type == unit_type):
        return True
    else:
        return False


class ZergBOT(base_agent.BaseAgent):
    def __init__(self):
        super(ZergBOT, self).__init__()
        self.attack_coordinates = None

    def step(self, obs):
        super(ZergBOT, self).step(obs)

        if obs.first():
            player_y, player_x = (obs.observation.feature_minimap.player_relative ==
                                  features.PlayerRelative.SELF).nonzero()

            ymean = player_y.mean()
            xmean = player_x.mean()

            if xmean <= 33 and ymean <= 31:
                self.attack_coordinates = (47, 47)
            else:
                self.attack_coordinates = (12, 16)

        zergling_units = get_units_by_type(obs, units.Zerg.Zergling)
        if len(zergling_units) > 0:
            if unit_type_is_selected(obs, units.Zerg.Zergling):
                if can_do(obs, actions.FUNCTIONS.Attack_minimap.id):
                    return actions.FUNCTIONS.Attack_minimap('now', self.attack_coordinates)

        larva_units = get_units_by_type(obs, units.Zerg.Larva)
        print(len(larva_units))

        # Check available larva
        if len(larva_units) == 3:
            larvae_unit = random.choice(larva_units)
            actions.FUNCTIONS.select_point("select_all_type", (larvae_unit.x,
                                                               larvae_unit.y))

            if unit_type_is_selected(obs, units.Zerg.Larva):
                if can_do(obs, actions.FUNCTIONS.Train_Drone_quick.id):
                    return actions.FUNCTIONS.Train_Drone_quick('now')

        # Select Larva and build a zergling
        if unit_type_is_selected(obs, units.Zerg.Larva):
            if can_do(obs, actions.FUNCTIONS.Train_Zergling_quick.id):
                return actions.FUNCTIONS.Train_Zergling_quick('now')

        spawning_pool_count = get_units_by_type(obs, units.Zerg.SpawningPool)

        # If not spawning pool create one
        if len(spawning_pool_count) == 0:
            # Once drone has been selected create a spawning pool
            if unit_type_is_selected(obs, units.Zerg.Drone):
                if can_do(obs, actions.FUNCTIONS.Build_SpawningPool_screen.id):
                    x = random.randint(0, 63)
                    y = random.randint(0, 63)
                    return actions.FUNCTIONS.Build_SpawningPool_screen('now', (x, y))

        drone_units = get_units_by_type(obs, units.Zerg.Drone)
        if len(drone_units) > 0:
            drone_unit = random.choice(drone_units)
            return actions.FUNCTIONS.select_point("select_all_type", (drone_unit.x,
                                                                      drone_unit.y))

        return actions.FUNCTIONS.no_op()


def main(unused_argv):
    agent = ZergBOT()
    # game_map does not require LE at the end
    # current maps 'Acropolis', 'DiscoBloodbath', 'Ephemeron', 'Thunderbird', 'Triton', 'WintersGate', 'WorldofSleepers'
    game_map = 'WintersGate'
    try:
        while True:
            with sc2_env.SC2Env(
                map_name=game_map,
                players=[sc2_env.Agent(sc2_env.Race.zerg),
                         sc2_env.Bot(sc2_env.Race.random,
                                     sc2_env.Difficulty.very_easy)],
                agent_interface_format=features.AgentInterfaceFormat(
                    feature_dimensions=features.Dimensions(screen=84, minimap=64),
                    use_feature_units=True), step_mul=8, game_steps_per_episode=0,
                    # Visualize shows HUD of other display options
                    visualize=False, realtime=True) as env:

                agent.setup(env.observation_spec(), env.action_spec())

                timesteps = env.reset()
                agent.reset()

                while True:
                    step_actions = [agent.step(timesteps[0])]
                    if timesteps[0].last():
                        break
                    timesteps = env.step(step_actions)

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    app.run(main)
