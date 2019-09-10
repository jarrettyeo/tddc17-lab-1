# ==================================================================================================================== #
# We use DFS to determine the next node we want to visit, but use BFS via Dijkstra's Algorithm to find out path to target node.
# ==================================================================================================================== #

from lab1.liuvacuum import *
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
        self.unvisited_coordinates = []
        self.action_queue = []
        self.home = None
        self.commence_return_home = False

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

        # ====================== #
        # START HELPER FUNCTIONS #
        # ====================== #

        def get_new_direction(self_state_direction, new_action):
            """
            This function gets new direction given the current direction and new action
            """
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

        def insert_unvisited_coordinates(C):
            """
            This function inserts unvisited nodes into state
            """
            N = C.get_north_coordinate()
            S = C.get_south_coordinate()
            E = C.get_east_coordinate()
            W = C.get_west_coordinate()
            NSEW_list = [N, S, E, W]
            for X in NSEW_list:
                if X.get_state(self.state.world) in [AGENT_STATE_UNKNOWN, AGENT_STATE_HOME] and X not in self.state.unvisited_coordinates:
                    self.state.unvisited_coordinates.insert(0, X)

        def NSEW_coordinates(C):
            """
            This function returns the Coordinates of nodes to the N, S, E, W of current position
            """
            return Coordinate(C.get_x() + 1, C.get_y()), Coordinate(C.get_x() - 1, C.get_y()), \
                   Coordinate(C.get_x(), C.get_y() + 1), Coordinate(C.get_x(), C.get_y() - 1)

        def get_path_to_next_node(start_C, target_C, self_state_world):
            """
            This function finds path to target node using BfS implemented with Dijkstra's Algorithm
            """
            START_C = copy.deepcopy(start_C)
            TARGET_C = copy.deepcopy(target_C)
            START_C.set_back_node(None)
            TARGET_C.set_back_node(None)

            unvisited_nodes = [START_C]
            visited_nodes = []

            back_node_world = [[None for _ in range(self.state.world_height)] for _ in
                               range(self.state.world_width)]

            while unvisited_nodes != []:
                this_C = unvisited_nodes.pop(0)
                visited_nodes.append(this_C)
                # if the node to visit is our target node, exit while loop
                if this_C == TARGET_C:
                    # return path of Coordinates
                    C_path = []
                    while back_node_world[this_C.get_x()][this_C.get_y()] != None and this_C != START_C:
                        C_path.append(Coordinate(this_C.get_x(), this_C.get_y()))
                        this_C = Coordinate(back_node_world[this_C.get_x()][this_C.get_y()].get_x(),
                                            back_node_world[this_C.get_x()][this_C.get_y()].get_y())
                        # C_path.append(this_C.get_back_node()) # does not work because local variable
                    # finally add START_C as the final node
                    C_path.append(START_C)
                    return C_path
                # otherwise, loop through NSEW and add CLEAR nodes to visit
                else:
                    N, S, E, W = NSEW_coordinates(this_C)
                    for P in [N, S, E, W]:
                        # visited_nodes.append(P)
                        if P == TARGET_C or (self_state_world[P.get_x()][P.get_y()] in [AGENT_STATE_CLEAR,
                                                                                        AGENT_STATE_HOME] and Coordinate(
                                P.get_x(), P.get_y()) not in visited_nodes):
                            unvisited_nodes.append(P)
                            visited_nodes.append(P)
                            # SPECIAL: if node is H, then jot it down
                            if self_state_world[P.get_x()][P.get_y()] == AGENT_STATE_HOME:
                                self.state.home = Coordinate(P.get_x(), P.get_y())
                                print("*********************************************************")
                                print("HOME FOUND!")
                                print("*********************************************************")
                            back_node_world[P.get_x()][P.get_y()] = Coordinate(this_C.get_x(), this_C.get_y())
                            # back_node_dict[P] = this_C
                            # P.set_back_node(this_C) # does not work because local variable

        def get_actions_from_path(C_path, current_direction):
            """
            This function determines the actions to take to travel between all nodes in C_path given a current direction
            """
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

        # ==================== #
        # END HELPER FUNCTIONS #
        # ==================== #

        C = Coordinate(self.state.pos_x, self.state.pos_y)
        # self.state.visited_coordinates.append(C)

        # Step -3: Sanity check for edge case - sometimes start position = H, and H becomes . immediately
        # In this case, we scan the world for H first. If H exists, do nothing because algorithm can find it
        # However, if H cannot be found (and starting coordinate is 1,1), then we have to set H as (1,1)
        H_exists = False
        for row in self.state.world:
            for element in row:
                if element == AGENT_STATE_HOME:
                    H_exists = True
                    break
            if H_exists:
                break
        if not H_exists:
            self.state.home = Coordinate(1, 1)

        # Step -2: Scan all unvisited nodes for updates
        for X in self.state.unvisited_coordinates:
            if X.get_state(self.state.world) not in [AGENT_STATE_UNKNOWN, AGENT_STATE_HOME]:
                self.state.unvisited_coordinates.remove(X)

        # Step -1: Remove all paths to unreachable areas
        # Not necessary to maintain state
        # pass

        # Step 1: Scan NSEW of current node
        # If unvisited_coordinates is empty, add all unvisited NSEW of current node to list
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
                print("THERE ARE NO MORE NODES OR ACTIONS TO TAKE!")
                print("RETURNING TO H...")

                # If at home, terminate
                if self.state.home == Coordinate(self.state.pos_x, self.state.pos_y):
                    self.iteration_counter = 0
                    # Because visiting H will override it with . we must put H back into the world
                    self.state.world[self.state.home.get_x()][self.state.home.get_y()] = AGENT_STATE_HOME
                    self.state.print_world_debug()
                    return

                # Else, do a 1-time finding of path back home
                if not self.state.commence_return_home:
                    C_path = get_path_to_next_node(Coordinate(self.state.pos_x, self.state.pos_y), self.state.home, self.state.world)
                    actions = get_actions_from_path(C_path, self.state.direction)
                    self.state.action_queue.extend(actions)
                    print("(after) action_queue:", self.state.action_queue)
                    print("(after) unvisited_coordinates:", self.state.unvisited_coordinates)
                    self.state.commence_return_home = True

                # ========================================================================= #
                if self.state.action_queue != []:
                    action = self.state.action_queue.pop(0)
                    print("action available")
                    print("so just took a %s" % action)
                    self.state.last_action = action
                    self.state.direction = get_new_direction(self.state.direction, action)
                    return action
                # ========================================================================= #
