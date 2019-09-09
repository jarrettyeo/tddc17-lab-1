from lab1.liuvacuum import *

DEBUG_OPT_DENSEWORLDMAP = False

AGENT_STATE_UNKNOWN = 0
AGENT_STATE_WALL = 1
AGENT_STATE_CLEAR = 2
AGENT_STATE_DIRT = 3
AGENT_STATE_HOME = 4

AGENT_DIRECTION_NORTH = 0
AGENT_DIRECTION_EAST = 1
AGENT_DIRECTION_SOUTH = 2
AGENT_DIRECTION_WEST = 3

def direction_to_string(cdr):
    cdr %= 4
    return  "NORTH" if cdr == AGENT_DIRECTION_NORTH else\
            "EAST"  if cdr == AGENT_DIRECTION_EAST else\
            "SOUTH" if cdr == AGENT_DIRECTION_SOUTH else\
            "WEST" #if dir == AGENT_DIRECTION_WEST

"""
Internal state of a vacuum agent
"""
class MyAgentState:

    def __init__(self, width, height):

        # Initialize perceived world state
        self.world = [[AGENT_STATE_UNKNOWN for _ in range(height)] for _ in range(width)]
        self.world[1][1] = AGENT_STATE_HOME

        # Agent internal state
        self.last_action = ACTION_NOP
        self.direction = AGENT_DIRECTION_EAST
        self.pos_x = 1
        self.pos_y = 1

        self.reason_for_last_action = ""

        # Metadata
        self.world_width = width
        self.world_height = height

    """
    Update perceived agent location
    """
    def update_position(self, bump):
        if not bump and self.last_action == ACTION_FORWARD:
            if self.direction == AGENT_DIRECTION_EAST:
                self.pos_x += 1
            elif self.direction == AGENT_DIRECTION_SOUTH:
                self.pos_y += 1
            elif self.direction == AGENT_DIRECTION_WEST:
                self.pos_x -= 1
            elif self.direction == AGENT_DIRECTION_NORTH:
                self.pos_y -= 1

    """
    Update perceived or inferred information about a part of the world
    """
    def update_world(self, x, y, info):
        self.world[x][y] = info

    """
    Dumps a map of the world as the agent knows it
    """
    def print_world_debug(self):
        for y in range(self.world_height):
            for x in range(self.world_width):
                if self.world[x][y] == AGENT_STATE_UNKNOWN:
                    print("?" if DEBUG_OPT_DENSEWORLDMAP else " ? ", end="")
                elif self.world[x][y] == AGENT_STATE_WALL:
                    print("#" if DEBUG_OPT_DENSEWORLDMAP else " # ", end="")
                elif self.world[x][y] == AGENT_STATE_CLEAR:
                    print("." if DEBUG_OPT_DENSEWORLDMAP else " . ", end="")
                elif self.world[x][y] == AGENT_STATE_DIRT:
                    print("D" if DEBUG_OPT_DENSEWORLDMAP else " D ", end="")
                elif self.world[x][y] == AGENT_STATE_HOME:
                    print("H" if DEBUG_OPT_DENSEWORLDMAP else " H ", end="")

            print() # Newline
        print() # Delimiter post-print

"""
Vacuum agent
"""
class MyVacuumAgent(Agent):

    def __init__(self, world_width, world_height, log):
        super().__init__(self.execute)
        self.initial_random_actions = 10
        self.iteration_counter = 1000 # 10
        self.state = MyAgentState(world_width, world_height)
        self.log = log

    def move_to_random_start_position(self, bump):
        action = random()

        self.initial_random_actions -= 1
        self.state.update_position(bump)

        if action < 0.1666666:   # 1/6 chance
            self.state.direction = (self.state.direction + 3) % 4
            self.state.last_action = ACTION_TURN_LEFT
            return ACTION_TURN_LEFT
        elif action < 0.3333333: # 1/6 chance
            self.state.direction = (self.state.direction + 1) % 4
            self.state.last_action = ACTION_TURN_RIGHT
            return ACTION_TURN_RIGHT
        else:                    # 4/6 chance
            self.state.last_action = ACTION_FORWARD
            return ACTION_FORWARD

    def execute(self, percept):

        ###########################
        # DO NOT MODIFY THIS CODE #
        ###########################

        bump = percept.attributes["bump"]
        dirt = percept.attributes["dirt"]
        home = percept.attributes["home"]

        # Move agent to a randomly chosen initial position
        if self.initial_random_actions > 0:
            self.log("Moving to random start position ({} steps left)".format(self.initial_random_actions))
            return self.move_to_random_start_position(bump)

        # Finalize randomization by properly updating position (without subsequently changing it)
        elif self.initial_random_actions == 0:
            self.initial_random_actions -= 1
            self.state.update_position(bump)
            self.state.last_action = ACTION_SUCK
            self.log("Processing percepts after position randomization")
            return ACTION_SUCK


        ########################
        # START MODIFYING HERE #
        ########################

        # Max iterations for the agent
        if self.iteration_counter < 1:
            if self.iteration_counter == 0:
                self.iteration_counter -= 1
                self.log("Iteration counter is now 0. Halting!")
                self.log("Performance: {}".format(self.performance))
            return ACTION_NOP

        self.log("Position: ({}, {})\t\tDirection: {}".format(self.state.pos_x, self.state.pos_y,
                                                              direction_to_string(self.state.direction)))

        self.iteration_counter -= 1

        # Track position of agent
        self.state.update_position(bump)

        if bump:
            # Get an xy-offset pair based on where the agent is facing
            offset = [(0, -1), (1, 0), (0, 1), (-1, 0)][self.state.direction]

            # Mark the tile at the offset from the agent as a wall (since the agent bumped into it)
            self.state.update_world(self.state.pos_x + offset[0], self.state.pos_y + offset[1], AGENT_STATE_WALL)

        # Update perceived state of current tile
        if dirt:
            self.state.update_world(self.state.pos_x, self.state.pos_y, AGENT_STATE_DIRT)
        else:
            self.state.update_world(self.state.pos_x, self.state.pos_y, AGENT_STATE_CLEAR)

        # Debug
        self.state.print_world_debug()

        # Decide action
        algo = "new lane" # "snake"

        if algo == "snake":
            if dirt:
                self.log("DIRT -> choosing SUCK action!")
                self.state.last_action = ACTION_SUCK
                return ACTION_SUCK
            if home and self.state.world[1][2] == AGENT_STATE_CLEAR:
                self.state.last_action = ACTION_NOP
                return ACTION_NOP
            if bump and self.state.direction == AGENT_DIRECTION_SOUTH:
                self.state.last_action = ACTION_TURN_RIGHT
                return ACTION_TURN_RIGHT
            if bump and self.state.direction == AGENT_DIRECTION_NORTH:
                self.state.last_action = ACTION_TURN_LEFT
                return ACTION_TURN_LEFT
            if self.state.direction == AGENT_DIRECTION_WEST \
                    and self.state.world[self.state.pos_x][self.state.pos_y + 1] == AGENT_STATE_WALL \
                    and self.state.world[self.state.pos_x - 1][self.state.pos_y] == AGENT_STATE_WALL:
                self.state.last_action = ACTION_TURN_RIGHT
                return ACTION_TURN_RIGHT
            if (self.state.last_action == ACTION_TURN_RIGHT or self.state.last_action == ACTION_TURN_LEFT) \
                    and self.state.direction == AGENT_DIRECTION_WEST:
                self.state.last_action = ACTION_FORWARD
                return ACTION_FORWARD
            if (self.state.last_action == ACTION_FORWARD or self.state.last_action == ACTION_SUCK) \
                    and self.state.direction == AGENT_DIRECTION_WEST:
                if self.state.world[self.state.pos_x + 1][self.state.pos_y + 1] == AGENT_STATE_WALL:
                    self.state.last_action = ACTION_TURN_RIGHT
                    return ACTION_TURN_RIGHT
                else:
                    self.state.last_action = ACTION_TURN_LEFT
                    return ACTION_TURN_LEFT
            if not bump:
                self.state.last_action = ACTION_FORWARD
                return ACTION_FORWARD
            self.state.last_action = ACTION_NOP
            return ACTION_NOP

        elif algo == "new lane":
            print("self.state.direction", self.state.direction)
            print("self.state.last_action:", self.state.last_action)
            print("self.state.reason_for_last_action:", self.state.reason_for_last_action)
            if dirt:
                print("dirt")
                print("so ACTION_SUCK now")
                self.state.reason_for_last_action = "dirt"
                self.state.last_action = ACTION_SUCK
                return ACTION_SUCK
            elif bump:
                print("bump")
                print("so ACTION_NOP now")
                self.state.reason_for_last_action = "bump"
                self.state.last_action = ACTION_NOP
                return ACTION_NOP
            else:
                if self.state.last_action == ACTION_NOP and self.state.reason_for_last_action == "bump":
                    print("else-if")
                    print("so ACTION_TURN_RIGHT now")
                    self.state.reason_for_last_action = "else-if"
                    self.state.last_action = ACTION_TURN_RIGHT
                    self.state.direction = get_new_direction(self.state.direction, ACTION_TURN_RIGHT)
                    return ACTION_TURN_RIGHT
                else:
                    print("else-else")
                    print("so ACTION_FORWARD now")
                    self.state.reason_for_last_action = "else-else"
                    self.state.last_action = ACTION_FORWARD
                    return ACTION_FORWARD


def get_new_direction(self_state_direction, new_action):

    if new_action == ACTION_TURN_RIGHT:
        if self_state_direction == AGENT_DIRECTION_NORTH:
            self_state_direction = AGENT_DIRECTION_EAST
        elif self_state_direction == AGENT_DIRECTION_EAST:
            self_state_direction = AGENT_DIRECTION_SOUTH
        elif self_state_direction == AGENT_DIRECTION_SOUTH:
            self_state_direction = AGENT_DIRECTION_WEST
        elif self_state_direction == AGENT_DIRECTION_WEST:
            self_state_direction = AGENT_DIRECTION_NORTH

    elif new_action == ACTION_TURN_LEFT:
        if self_state_direction == AGENT_DIRECTION_NORTH:
            self_state_direction = AGENT_DIRECTION_WEST
        elif self_state_direction == AGENT_DIRECTION_WEST:
            self_state_direction = AGENT_DIRECTION_SOUTH
        elif self_state_direction == AGENT_DIRECTION_SOUTH:
            self_state_direction = AGENT_DIRECTION_EAST
        elif self_state_direction == AGENT_DIRECTION_EAST:
            self_state_direction = AGENT_DIRECTION_NORTH

    return self_state_direction
