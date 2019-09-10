from lab1.liuvacuum import *
from random import randint
import copy

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

AGENT_STATE_DICT = dict({
    0: AGENT_STATE_UNKNOWN,
    1: AGENT_STATE_WALL,
    2: AGENT_STATE_CLEAR,
    3: AGENT_STATE_DIRT,
    4: AGENT_STATE_HOME
})

AGENT_DIRECTION_DICT = dict({
    0: AGENT_DIRECTION_NORTH,
    1: AGENT_DIRECTION_EAST,
    2: AGENT_DIRECTION_SOUTH,
    3: AGENT_DIRECTION_WEST
})

class Coordinate:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.back_node = None

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, another_C):
        if type(another_C) is not Coordinate:
            return False
        else:
            return True if self.get_y() == another_C.get_y() and self.get_x() == another_C.get_x() else False

    def __repr__(self):
        return "Coordinate(%s, %s)" % (self.x, self.y)

    def set_back_node(self, Coordinate):
        self.back_node = Coordinate

    def get_back_node(self):
        return self.back_node

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y

    def get_north_coordinate(self):
        return Coordinate(self.x, self.y - 1)

    def get_south_coordinate(self):
        return Coordinate(self.x, self.y + 1)

    def get_east_coordinate(self):
        return Coordinate(self.x + 1, self.y)

    def get_west_coordinate(self):
        return Coordinate(self.x - 1, self.y)

    def get_state(self, self_state_world):
        return self_state_world[self.x][self.y]

class Path:
    def __init__(self, C1, C2):
        self.C1 = C1
        self.C2 = C2

    def get_C1(self):
        return self.C1

    def get_C2(self):
        return self.C2

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

        # Additional variables
        self.reason_for_last_action = ""
        # self.backtracking_path = []
        # self.nodes_to_visit = []
        # self.index = 0
        # self.node_network = [[None for _ in range(height)] for _ in range(width)]

        # self.visited_coordinates = []
        self.unvisited_coordinates = []
        # self.last_coordinate = None

        self.action_queue = []

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
        algo = "DFS"  # "new lane" # "snake"

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
            what_is_ahead = get_what_is_ahead(self.state.world, self.state.pos_x, self.state.pos_y, self.state.direction)
            print("get_what_is_ahead", what_is_ahead)
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
                elif self.state.world[self.state.pos_x][self.state.pos_y - 1] != AGENT_STATE_UNKNOWN and self.state.world[self.state.pos_x][self.state.pos_y + 1] != AGENT_STATE_UNKNOWN and self.state.world[self.state.pos_x - 1][self.state.pos_y] != AGENT_STATE_UNKNOWN and self.state.world[self.state.pos_x + 1][self.state.pos_y] != AGENT_STATE_UNKNOWN:
                    print("== 0")
                    print("so RANDOM now")
                    self.state.reason_for_last_action = "== 0"
                    random_number = randint(0, 3)
                    if random_number == 0:
                        direction = ACTION_TURN_RIGHT
                    elif random_number == 1:
                        direction = ACTION_TURN_LEFT
                    else:
                        direction = ACTION_FORWARD
                    self.state.last_action = direction
                    self.state.direction = get_new_direction(self.state.direction, direction)
                    return direction
                elif what_is_ahead != AGENT_STATE_UNKNOWN and what_is_ahead != AGENT_STATE_HOME:
                    print("elif")
                    print("so ACTION_TURN_RIGHT now")
                    self.state.reason_for_last_action = "elif"
                    self.state.last_action = ACTION_TURN_RIGHT
                    self.state.direction = get_new_direction(self.state.direction, ACTION_TURN_RIGHT)
                    return ACTION_TURN_RIGHT
                else:
                    print("else-else")
                    print("so ACTION_FORWARD now")
                    self.state.reason_for_last_action = "else-else"
                    self.state.last_action = ACTION_FORWARD
                    return ACTION_FORWARD

        elif algo == "DFS":

            C = Coordinate(self.state.pos_x, self.state.pos_y)
            # self.state.visited_coordinates.append(C)

            # Step -2: Scan all unvisited nodes for updates
            for X in self.state.unvisited_coordinates:
                if X.get_state(self.state.world) != AGENT_STATE_UNKNOWN:
                    self.state.unvisited_coordinates.remove(X)

            # Step -1: Remove all paths to unreachable areas
            # Not necessary to maintain state
            # pass

            # Step 0: Scan NSEW
            def insert_unvisited_coordinates(C):
                N = C.get_north_coordinate()
                S = C.get_south_coordinate()
                E = C.get_east_coordinate()
                W = C.get_west_coordinate()
                NSEW_list = [N, S, E, W]
                for X in NSEW_list:
                    if X.get_state(self.state.world) == AGENT_STATE_UNKNOWN and X not in self.state.unvisited_coordinates:
                        self.state.unvisited_coordinates.insert(0, X)

            # Step 1: If unvisited_coordinates is empty, add all unvisited NSEW of current node to list
            if self.state.action_queue == []:
                insert_unvisited_coordinates(C)

            # Step 2: Add path to unvisited node
            # Not necessary to maintain state
            # pass
            print("current position: (%s, %s)" % (self.state.pos_x, self.state.pos_y))
            print("current direction: %s" % (direction_to_string(self.state.direction)))

            print("(before) action_queue:", self.state.action_queue)
            print("(before) unvisited_coordinates:", self.state.unvisited_coordinates)

            # Step 2B: Handle the LAST action of the action queue
            if dirt:
                print("dirt")
                print("so ACTION_SUCK now")
                self.state.last_action = ACTION_SUCK
                return ACTION_SUCK
            elif bump:
                print("bump")
                print("so ACTION_NOP now")
                self.state.last_action = ACTION_NOP
                return ACTION_NOP
            else:
                # Step 3: If action queue is not empty, do the action
                if self.state.action_queue != []:
                    # ========================================================================= #
                    action = self.state.action_queue.pop(0)
                    print("action available")
                    print("so just took a %s" % action)
                    self.state.last_action = action
                    self.state.direction = get_new_direction(self.state.direction, action)
                    return action
                    # ========================================================================= #
                # Else if action queue is empty and there are still unvisited nodes, pop next node to visit
                elif self.state.action_queue == [] and self.state.unvisited_coordinates != []:
                    target_C = self.state.unvisited_coordinates.pop(0)
                    print("no actions in queue")
                    print("so go to %s now" % target_C)

                    # Step 4: Get path to next node via visited nodes
                    def NSEW_coordinates(C):
                        return Coordinate(C.get_x() + 1, C.get_y()), Coordinate(C.get_x() - 1, C.get_y()), \
                               Coordinate(C.get_x(), C.get_y() + 1), Coordinate(C.get_x(), C.get_y() - 1)

                    def get_path_to_next_node(start_C, target_C, self_state_world):
                        START_C = copy.deepcopy(start_C)
                        TARGET_C = copy.deepcopy(target_C)
                        START_C.set_back_node(None)
                        TARGET_C.set_back_node(None)

                        unvisited_nodes = [START_C]
                        visited_nodes = []

                        back_node_world = [[None for _ in range(self.state.world_height)] for _ in range(self.state.world_width)]

                        while unvisited_nodes != []:
                            this_C = unvisited_nodes.pop(0)
                            visited_nodes.append(this_C)
                            # if the node to visit is our target node, exit while loop
                            if this_C == TARGET_C:
                                # return path of Coordinates
                                C_path = []
                                while back_node_world[this_C.get_x()][this_C.get_y()] != None and this_C != START_C:
                                    C_path.append(Coordinate(this_C.get_x(), this_C.get_y()))
                                    this_C = Coordinate(back_node_world[this_C.get_x()][this_C.get_y()].get_x(), back_node_world[this_C.get_x()][this_C.get_y()].get_y())
                                    # C_path.append(this_C.get_back_node()) # does not work because local variable
                                # finally add START_C as the final node
                                C_path.append(START_C)
                                return C_path
                            # otherwise, loop through NSEW and add CLEAR nodes to visit
                            else:
                                N, S, E, W = NSEW_coordinates(this_C)
                                for P in [N, S, E, W]:
                                    # visited_nodes.append(P)
                                    if P == TARGET_C or (self_state_world[P.get_x()][P.get_y()] == AGENT_STATE_CLEAR and Coordinate(P.get_x(), P.get_y()) not in visited_nodes):
                                        unvisited_nodes.append(P)
                                        back_node_world[P.get_x()][P.get_y()] = Coordinate(this_C.get_x(), this_C.get_y())
                                        # back_node_dict[P] = this_C
                                        # P.set_back_node(this_C) # does not work because local variable

                    def get_actions_from_path(C_path, current_direction):
                        actions = []
                        current_C = C_path.pop(-1)

                        while C_path != []:
                            next_C = C_path.pop(-1)

                            if next_C.get_y() - current_C.get_y() == 1:
                                # need to go down
                                if current_direction == AGENT_DIRECTION_NORTH:
                                    actions.extend([ACTION_TURN_RIGHT, ACTION_TURN_RIGHT, ACTION_FORWARD])
                                elif current_direction == AGENT_DIRECTION_SOUTH:
                                    actions.extend([ACTION_FORWARD])
                                elif current_direction == AGENT_DIRECTION_EAST:
                                    actions.extend([ACTION_TURN_RIGHT, ACTION_FORWARD])
                                elif current_direction == AGENT_DIRECTION_WEST:
                                    actions.extend([ACTION_TURN_LEFT, ACTION_FORWARD])
                                current_direction = AGENT_DIRECTION_SOUTH

                            elif next_C.get_y() - current_C.get_y() == -1:
                                # need to go up
                                if current_direction == AGENT_DIRECTION_NORTH:
                                    actions.extend([ACTION_FORWARD])
                                elif current_direction == AGENT_DIRECTION_SOUTH:
                                    actions.extend([ACTION_TURN_RIGHT, ACTION_TURN_RIGHT, ACTION_FORWARD])
                                elif current_direction == AGENT_DIRECTION_EAST:
                                    actions.extend([ACTION_TURN_LEFT, ACTION_FORWARD])
                                elif current_direction == AGENT_DIRECTION_WEST:
                                    actions.extend([ACTION_TURN_RIGHT, ACTION_FORWARD])
                                current_direction = AGENT_DIRECTION_NORTH

                            elif next_C.get_x() - current_C.get_x() == 1:
                                # need to go right
                                if current_direction == AGENT_DIRECTION_NORTH:
                                    actions.extend([ACTION_TURN_RIGHT, ACTION_FORWARD])
                                elif current_direction == AGENT_DIRECTION_SOUTH:
                                    actions.extend([ACTION_TURN_LEFT, ACTION_FORWARD])
                                elif current_direction == AGENT_DIRECTION_EAST:
                                    actions.extend([ACTION_FORWARD])
                                elif current_direction == AGENT_DIRECTION_WEST:
                                    actions.extend([ACTION_TURN_RIGHT, ACTION_TURN_RIGHT, ACTION_FORWARD])
                                current_direction = AGENT_DIRECTION_EAST

                            elif next_C.get_x() - current_C.get_x() == -1:
                                # need to go left
                                if current_direction == AGENT_DIRECTION_NORTH:
                                    actions.extend([ACTION_TURN_LEFT, ACTION_FORWARD])
                                elif current_direction == AGENT_DIRECTION_SOUTH:
                                    actions.extend([ACTION_TURN_RIGHT, ACTION_FORWARD])
                                elif current_direction == AGENT_DIRECTION_EAST:
                                    actions.extend([ACTION_TURN_RIGHT, ACTION_TURN_RIGHT, ACTION_FORWARD])
                                elif current_direction == AGENT_DIRECTION_WEST:
                                    actions.extend([ACTION_FORWARD])
                                current_direction = AGENT_DIRECTION_WEST

                            current_C = next_C

                        return actions

                    C_path = get_path_to_next_node(C, target_C, self.state.world)
                    actions = get_actions_from_path(C_path, self.state.direction)
                    self.state.action_queue.extend(actions)
                    print("(after) action_queue:", self.state.action_queue)
                    print("(after) unvisited_coordinates:", self.state.unvisited_coordinates)

                    # ========================================================================= #
                    action = self.state.action_queue.pop(0)
                    print("action available")
                    print("so just took a %s" % action)
                    self.state.last_action = action
                    self.state.direction = get_new_direction(self.state.direction, action)
                    return action
                    # ========================================================================= #

                # Else if no more nodes to visit, terminate
                else:
                    self.iteration_counter = 0
                    return


            # ========================================

            # Initialize self.state.backtracking_path
            # if self.state.backtracking_path == []:
                # self.state.backtracking_path.append([self.state.pos_x, self.state.pos_y])
                # self.state.network['']
            # elif [self.state.pos_x, self.state.pos_y] not in self.state.backtracking_path:
                # self.state.backtracking_path.append([self.state.pos_x, self.state.pos_y])
                # self.state.index += 1

            # # Check that every node which are not ? is removed from unvisited_nodes_list
            # for node in self.state.nodes_to_visit:
            #     if self.state.world[node[0]][node[1]] != AGENT_STATE_UNKNOWN:
            #         self.state.nodes_to_visit.remove(node)
            #         self.state.node_network[node[0]][node[1]] = None
            #
            # # Look around NSEW to find unvisited nodes
            # unvisited_nodes_list = get_NSEW_ahead(self.state.world, self.state.pos_x, self.state.pos_y)
            # for ahead in unvisited_nodes_list:
            #     if ahead not in self.state.nodes_to_visit:
            #         x = ahead[0]
            #         y = ahead[1]
            #         self.state.nodes_to_visit.insert([x,y], 0)
            #         self.state.node_network[x][y] = [self.state.pos_x, self.state.pos_y]
            #
            # # =========================================================================================================
            # # If action_queue is empty, check front of unvisited_nodes_list
            # if len(self.state.nodes_to_visit) > 0:
            #     next_node_to_visit = self.state.nodes_to_visit[0]
            #     self.state.nodes_to_visit.remove(0)
            #
            #     # Queue new actions from current position to next_node_to_visit
            #     # get_actions_to_take([self.state.pos_x, self.state.pos_y], next_node_to_visit)
            #
            # # Else if action_queue and unvisited_nodes_list is empty, terminate!
            # else:
            #     return
            # # =========================================================================================================
            #
            # what_is_ahead = get_what_is_ahead(self.state.world, self.state.pos_x, self.state.pos_y, self.state.direction)
            # print("get_what_is_ahead", what_is_ahead)
            # print("self.state.direction", self.state.direction)
            # print("self.state.last_action:", self.state.last_action)
            # print("self.state.reason_for_last_action:", self.state.reason_for_last_action)
            # if dirt:
            #     print("dirt")
            #     print("so ACTION_SUCK now")
            #     self.state.reason_for_last_action = "dirt"
            #     self.state.last_action = ACTION_SUCK
            #     return ACTION_SUCK
            # elif bump:
            #     print("bump")
            #     print("so ACTION_NOP now")
            #     self.state.reason_for_last_action = "bump"
            #     self.state.last_action = ACTION_NOP
            #     return ACTION_NOP
            # else:
            #     pass

    def get_actions_to_take(self, current_node, next_node_to_visit):
        # nodes are in [x,y]
        node_network = [[None for _ in range(self.state.world_height)] for _ in range(self.state.world_width)]
        visited_nodes = []
        queue = []

        # Initialize queue
        if self.state.world[current_node[0]][current_node[1] + 1] == AGENT_STATE_CLEAR and \
                [current_node[0]][current_node[1] + 1] not in visited_nodes:
            queue.append(self.state.world[current_node[0]][current_node[1] + 1])
            node_network[current_node[0]][current_node[1]] = [current_node[0], current_node[1] + 1]
            node_network[current_node[0]][current_node[1] + 1] = [current_node[0], current_node[1]]
        if self.state.world[current_node[0]][current_node[1] - 1] == AGENT_STATE_CLEAR and \
                [current_node[0]][current_node[1] - 1] not in visited_nodes:
            queue.append(self.state.world[current_node[0]][current_node[1] - 1])
            node_network[current_node[0]][current_node[1]] = [current_node[0], current_node[1] - 1]
            node_network[current_node[0]][current_node[1] - 1] = [current_node[0], current_node[1]]
        if self.state.world[current_node[0] + 1][current_node[1]] == AGENT_STATE_CLEAR and \
                [current_node[0] + 1][current_node[1]] not in visited_nodes:
            queue.append(self.state.world[current_node[0] + 1][current_node[1]])
            node_network[current_node[0]][current_node[1]] = [current_node[0] + 1, current_node[1]]
            node_network[current_node[0] + 1][current_node[1]] = [current_node[0], current_node[1]]
        if self.state.world[current_node[0] - 1][current_node[1]] == AGENT_STATE_CLEAR and \
                [current_node[0] - 1][current_node[1]] not in visited_nodes:
            queue.append(self.state.world[current_node[0] - 1][current_node[1]])
            node_network[current_node[0]][current_node[1]] = [current_node[0] - 1, current_node[1]]
            node_network[current_node[0] - 1][current_node[1]] = [current_node[0], current_node[1]]

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


def get_what_is_ahead(self_state_world, self_state_pos_x, self_state_pos_y, self_state_direction):

    global AGENT_STATE_UNKNOWN, AGENT_STATE_WALL, AGENT_STATE_CLEAR, AGENT_STATE_DIRT, AGENT_STATE_HOME

    if self_state_direction == AGENT_DIRECTION_NORTH:
        return self_state_world[self_state_pos_x][self_state_pos_y - 1]
    if self_state_direction == AGENT_DIRECTION_SOUTH:
        return self_state_world[self_state_pos_x][self_state_pos_y + 1]
    if self_state_direction == AGENT_DIRECTION_EAST:
        return self_state_world[self_state_pos_x + 1][self_state_pos_y]
    if self_state_direction == AGENT_DIRECTION_WEST:
        return self_state_world[self_state_pos_x - 1][self_state_pos_y]

def get_what_is_right(self_state_world, self_state_pos_x, self_state_pos_y, self_state_direction):

    global AGENT_STATE_UNKNOWN, AGENT_STATE_WALL, AGENT_STATE_CLEAR, AGENT_STATE_DIRT, AGENT_STATE_HOME

    if self_state_direction == AGENT_DIRECTION_NORTH:
        return self_state_world[self_state_pos_x + 1][self_state_pos_y]
    if self_state_direction == AGENT_DIRECTION_SOUTH:
        return self_state_world[self_state_pos_x - 1][self_state_pos_y]
    if self_state_direction == AGENT_DIRECTION_EAST:
        return self_state_world[self_state_pos_x][self_state_pos_y - 1]
    if self_state_direction == AGENT_DIRECTION_WEST:
        return self_state_world[self_state_pos_x][self_state_pos_y + 1]

def get_what_is_left(self_state_world, self_state_pos_x, self_state_pos_y, self_state_direction):

    global AGENT_STATE_UNKNOWN, AGENT_STATE_WALL, AGENT_STATE_CLEAR, AGENT_STATE_DIRT, AGENT_STATE_HOME

    if self_state_direction == AGENT_DIRECTION_NORTH:
        return self_state_world[self_state_pos_x - 1][self_state_pos_y]
    if self_state_direction == AGENT_DIRECTION_SOUTH:
        return self_state_world[self_state_pos_x + 1][self_state_pos_y]
    if self_state_direction == AGENT_DIRECTION_EAST:
        return self_state_world[self_state_pos_x][self_state_pos_y + 1]
    if self_state_direction == AGENT_DIRECTION_WEST:
        return self_state_world[self_state_pos_x][self_state_pos_y - 1]

def get_NSEW_ahead(self_state_world, self_state_pos_x, self_state_pos_y):

    global AGENT_STATE_UNKNOWN, AGENT_STATE_WALL, AGENT_STATE_CLEAR, AGENT_STATE_DIRT, AGENT_STATE_HOME

    unvisited_nodes_list = []

    if self_state_world[self_state_pos_x][self_state_pos_y + 1] == AGENT_STATE_UNKNOWN:
        unvisited_nodes_list.append([self_state_pos_x, self_state_pos_y + 1])
    if self_state_world[self_state_pos_x][self_state_pos_y - 1] == AGENT_STATE_UNKNOWN:
        unvisited_nodes_list.append([self_state_pos_x, self_state_pos_y - 1])
    if self_state_world[self_state_pos_x + 1][self_state_pos_y] == AGENT_STATE_UNKNOWN:
        unvisited_nodes_list.append([self_state_pos_x + 1, self_state_pos_y])
    if self_state_world[self_state_pos_x - 1][self_state_pos_y] == AGENT_STATE_UNKNOWN:
        unvisited_nodes_list.append([self_state_pos_x - 1, self_state_pos_y])

    return unvisited_nodes_list

