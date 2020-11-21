from absl import app
from pysc2.agents import base_agent
from pysc2.env import sc2_env
from pysc2.lib import actions
from pysc2.lib import features
import time


_BUILD_PYLON = actions.FUNCTIONS.Build_Pylon_screen.id
_BUILD_GATEWAY = actions.FUNCTIONS.Build_Gateway_screen.id
_NOOP = actions.FUNCTIONS.no_op.id
_SELECT_POINT = actions.FUNCTIONS.select_point.id
_TRAIN_ZEALOT = actions.FUNCTIONS.Train_Zealot_quick.id
_RALLY_UNITS_MINIMAP = actions.FUNCTIONS.Rally_Units_minimap.id
_SELECT_ARMY = actions.FUNCTIONS.select_army.id
_ATTACK_MINIMAP = actions.FUNCTIONS.Attack_minimap.id

_PLAYER_RELATIVE = features.SCREEN_FEATURES.player_relative.index  # value [0,4] denoting [background,self,ally,neutral,enemy]
_UNIT_TYPE = features.SCREEN_FEATURES.unit_type.index


_PROTOSS_GATEWAY = 62
_PROTOSS_NEXUS = 59
_PROTOSS_PYLON = 60
_PROTOSS_PROBE = 84

# Parameters
_PLAYER_SELF = 1
_SUPPLY_USED = 3
_SUPPLY_MAX = 4
_SCREEN = [0]
_MINIMAP = [1]
_QUEUED = [1]
_SELECT_ALL = [0]


class RuleBaseAgent(base_agent.BaseAgent):
    nexus_top_left = None
    pylon_built = False
    probe_selected = False
    gateway_built = False
    gateway_selected = False
    gateway_rallied = False
    army_selected = False
    army_rallied = False

    def transform_location(self, x, x_distance, y, y_distance):
        if not self.nexus_top_left:
            return [x - x_distance, y - y_distance]
        else:
            return [x + x_distance, y + y_distance]

    def step(self, obs):
        super(RuleBaseAgent, self).step(obs)
        time.sleep(0.01)
        if self.nexus_top_left is None:
            nexus_y, nexus_x = (obs.observation["feature_minimap"][_PLAYER_RELATIVE] == _PLAYER_SELF).nonzero()
            self.nexus_top_left = nexus_y.mean() <= 31

        # rule 1:
        if not self.pylon_built:
            if not self.probe_selected:
                unit_type = obs.observation["feature_screen"][_UNIT_TYPE]
                probe_y, probe_x = (unit_type == _PROTOSS_PROBE).nonzero()
                target = [probe_x[0], probe_y[0]]
                self.probe_selected = True
                return actions.FunctionCall(_SELECT_POINT, [_SCREEN, target])
            elif _BUILD_PYLON in obs.observation["available_actions"]:
                unit_type = obs.observation["feature_screen"][_UNIT_TYPE]
                nexus_y, nexus_x = (unit_type == _PROTOSS_NEXUS).nonzero()
                target = self.transform_location(int(nexus_x.mean()), 0, int(nexus_y.mean()), 20)
                self.pylon_built = True
                return actions.FunctionCall(_BUILD_PYLON, [_SCREEN, target])

        # rule 2:
        elif not self.gateway_built:
            if _BUILD_GATEWAY in obs.observation["available_actions"]:
                unit_type = obs.observation["feature_screen"][_UNIT_TYPE]
                pylon_y, pylon_x = (unit_type == _PROTOSS_PYLON).nonzero()
                target = self.transform_location(int(pylon_x.mean()), 10, int(pylon_y.mean()), 0)
                if (unit_type == _PROTOSS_GATEWAY).any():
                    self.gateway_built = True
                return actions.FunctionCall(_BUILD_GATEWAY, [_SCREEN, target])

        # rule 3:
        elif not self.gateway_rallied:
            if not self.gateway_selected:
                unit_type = obs.observation["feature_screen"][_UNIT_TYPE]
                gateway_y, gateway_x = (unit_type == _PROTOSS_GATEWAY).nonzero()

                if gateway_y.any():
                    target = [int(gateway_x.mean()), int(gateway_y.mean())]
                    self.gateway_selected = True
                    return actions.FunctionCall(_SELECT_POINT, [_SCREEN, target])
            else:
                self.gateway_rallied = True
                if self.nexus_top_left:
                    return actions.FunctionCall(_RALLY_UNITS_MINIMAP, [_MINIMAP, [29, 21]])
                else:
                    return actions.FunctionCall(_RALLY_UNITS_MINIMAP, [_MINIMAP, [29, 46]])

        # rule 4:
        elif obs.observation["player"][_SUPPLY_USED] < obs.observation["player"][_SUPPLY_MAX] and \
                _TRAIN_ZEALOT in obs.observation["available_actions"]:
            return actions.FunctionCall(_TRAIN_ZEALOT, [_QUEUED])

        # rule 5:
        elif not self.army_rallied:
            if not self.army_selected:
                if _SELECT_ARMY in obs.observation["available_actions"]:
                    self.army_selected = True
                    return actions.FunctionCall(_SELECT_ARMY, [_SELECT_ALL])
            elif _ATTACK_MINIMAP in obs.observation["available_actions"]:
                self.army_rallied = True
                if self.nexus_top_left:
                    self.army_selected = False
                    self.army_rallied = False
                    return actions.FunctionCall(_ATTACK_MINIMAP, [_MINIMAP, [39, 45]])
                else:
                    self.army_selected = False
                    self.army_rallied = False
                    return actions.FunctionCall(_ATTACK_MINIMAP, [_MINIMAP, [21, 24]])

        return actions.FunctionCall(_NOOP, [])


def main(unused_argv):
    agent = RuleBaseAgent()
    # game_map does not require LE at the end
    game_map = 'Triton'
    try:
        while True:
            with sc2_env.SC2Env(
                map_name=game_map,
                players=[sc2_env.Agent(sc2_env.Race.protoss),
                         sc2_env.Bot(sc2_env.Race.zerg,
                                     sc2_env.Difficulty.very_easy)],
                agent_interface_format=features.AgentInterfaceFormat(
                    feature_dimensions=features.Dimensions(screen=84, minimap=64),
                    use_feature_units=True), step_mul=16, game_steps_per_episode=0,
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



