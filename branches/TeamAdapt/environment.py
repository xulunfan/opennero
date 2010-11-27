import time
from math import *
from copy import copy
from mazer import Maze
from constants import *
from OpenNero import *
from collections import deque
import TeamAdapt

import observer

class MazeRewardStructure:
    """ This defines the reward that the agents get for running the maze """
    def valid_move(self, state):
        """ a valid move is just a -1 (to reward shorter routes) """
        return 0
    def out_of_bounds(self, state):
        """ reward for running out of bounds of the maze (hitting the outer wall) """
        return 0 #-5
    def hit_wall(self, state):
        """ reward for hitting any other wall """
        return -5
    def goal_reached(self, state):
        """ reward for reaching the goal """
        print 'GOAL REACHED!'
        # reaching a goal is great!
        return 100
    def last_reward(self, state):
        """ reward for ending without reaching the goal """
        (r,c) = state.rc
        print 'EPISODE ENDED AT', r, c
        return 100.0*(r+c)/(ROWS+COLS)

class AgentState:
    """
    State that we keep for each agent
    """
    def __init__(self, maze):
        self.rc = (0, 0)
        self.prev_rc = (0, 0)
        (x,y) = maze.rc2xy(0,0)
        self.pose = (x,y,0)
        self.prev_pose = (x,y,0)
        self.initial_position = Vector3f(x, y, 0)
        self.initial_rotation = Vector3f(0, 0, 0)
        self.goal_reached = False
        self.time = time.time()
        self.start_time = self.time
        self.sensors = True
        self.animation = 'stand'
        self.observation_history = deque([ [x] for x in range(HISTORY_LENGTH)])
        self.action_history = deque([ [x] for x in range(HISTORY_LENGTH)])
        self.reward_history = deque([ 0 for x in range(HISTORY_LENGTH)])
        self.agentType = 0
        
    def reset(self):
        self.rc = (0,0)
        self.prev_rc = (0,0)
        self.goal_reached = False
        self.observation_history = deque([ [x] for x in range(HISTORY_LENGTH)])
        self.action_history = deque([ [x] for x in range(HISTORY_LENGTH)])
        self.reward_history = deque([ 0 for x in range(HISTORY_LENGTH)])

    def update(self, agent, maze):
        """
        Update the state of the agent
        """
        pos = copy(agent.state.position)
        self.prev_rc = self.rc
        self.rc = maze.xy2rc(pos.x, pos.y)
        self.prev_pose = self.pose
        self.pose = (pos.x, pos.y, agent.state.rotation.z + self.initial_rotation.z)
        self.time = time.time()
        
    def record_action(self, action):
        self.action_history.popleft()
        self.action_history.append(action)
        
    def record_observation(self, observation):
        self.observation_history.popleft()
        self.observation_history.append(observation)
    
    def record_reward(self, reward):
        self.reward_history.popleft()
        self.reward_history.append(reward)
        return reward
    
    def is_stuck(self):
        """ for now the only way to get stuck is to have the same state-action pair """
        if not is_uniform(self.action_history):
            return False
        if not is_uniform(self.observation_history):
            return False
        return True
        
    def get_reward(self):
        r0 = self.reward_history.popleft()
        for r in self.reward_history:
            assert(r == r0)
        return r0

class MazeEnvironment(Environment):
    MOVES = [(-1,-1), (0,-1), (1,-1), (1,0), (1,1), (0,1), (-1,1), (0,-1)]

    """
    The environment is a 2-D maze.
    In the discrete version, the agent moves from cell to cell.
     * Actions (1 discrete action)
        * 0 - NW
        * 1 - N
        * 2 - NE
        * 3 - E
        * 4 - SE
        * 5 - S
        * 6 - SW
        * 7 - W

        * 8 - no move
     * Observations (6 discrete observations)
        * o[0] - the current row position
        * o[1] - the current col position
        * o[2] - obstacle in the +r direction?
        * o[3] - obstacle in the -r direction?
        * o[4] - obstacle in the +c direction?
        * o[5] - obstacle in the -c direction?
    """
    def __init__(self):
        """
        generate the maze
        """
        Environment.__init__(self)
        self.maze = Maze.generate(ROWS, COLS, GRID_DX, GRID_DY)
        self.rewards = MazeRewardStructure()
        self.states = {}
        self.objects = {} # dict of ID's referencing Object_state

        '''
        every time an agent is added, the agent's id becomes the 'lastAgent'
        step # is updated during the lastAgent's step
        when stepsDone = STEPS_IN_ROUND, game is reset
        '''

        self.stepsDone = 0
        self.lastAgent = -1

        action_info = FeatureVectorInfo()
        observation_info = FeatureVectorInfo()
        reward_info = FeatureVectorInfo()
        action_info.add_discrete(0, len(MazeEnvironment.MOVES)) # select from the moves we can make

#        #FOR AVOIDER GAME
#        observation_info.add_continuous(0,1)
#        observation_info.add_continuous(0,1)
#
        #legions
        
        #local [0]
        observation_info.add_discrete(0,1)
        #adjacent [1-8]
        observation_info.add_discrete(0,1)
        observation_info.add_discrete(0,1)
        observation_info.add_discrete(0,1)
        observation_info.add_discrete(0,1)
        observation_info.add_discrete(0,1)
        observation_info.add_discrete(0,1)
        observation_info.add_discrete(0,1)
        observation_info.add_discrete(0,1)

        #radar [9-16]
        observation_info.add_discrete(0,1)
        observation_info.add_discrete(0,1)
        observation_info.add_discrete(0,1)
        observation_info.add_discrete(0,1)
        observation_info.add_discrete(0,1)
        observation_info.add_discrete(0,1)
        observation_info.add_discrete(0,1)
        observation_info.add_discrete(0,1)

#        #legions
#        #local [0]
#        observation_info.add_discrete(0,1)
#        #adjacent [1-8]
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#
#        #radar [9-16]
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#
#        #warbands
#        #local [17]
#        observation_info.add_discrete(0,1)
#        #adjacent [18-25]
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        #radar [26-33]
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#
#        #cities
#        #local [34]
#        observation_info.add_discrete(0,1)
#        #adjacent [35-42]
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        #radar [43-50]
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)
#        observation_info.add_discrete(0,1)

        '''
         OUTPUTS
        #directions NW -> W
        action_info.add_continuous(0,1)
        action_info.add_continuous(0,1)
        action_info.add_continuous(0,1)
        action_info.add_continuous(0,1)
        action_info.add_continuous(0,1)
        action_info.add_continuous(0,1)
        action_info.add_continuous(0,1)
        action_info.add_continuous(0,1)

        #go/stay
        action_info.add_continuous(0,1)
        action_info.add_continuous(0,1)
        '''

        reward_info.add_continuous(-100,100)
        self.agent_info = AgentInitInfo(observation_info, action_info, reward_info)
        self.max_steps = MAX_STEPS
        self.step_delay = STEP_DELAY
        self.speedup = 0
        self.shortcircuit = False
        self.agentList = {}
        print 'Initialized MazeEnvironment'
        
    def get_delay(self):
        return self.step_delay * (1.0 - self.speedup)

    def get_state(self, agent):
        if agent in self.states:
            
            return self.states[agent]
            
        else:
            self.states[agent] = AgentState(self.maze)
            print str(agent) + " state created"
            assert(self.states[agent].sensors)
            if hasattr(agent, 'epsilon'):
                print 'epsilon:', self.epsilon
                agent.epsilon = self.epsilon
            return self.states[agent]

    def get_object_state(self, agent):
        if agent in self.objects:

            return self.objects[agent]

        else:
            self.objects[agent] = AgentState(self.maze)
            print str(agent) + "object state created"
            return self.objects[agent]


    def can_move(self, state, move):
        """
        Figure out if the agent can make the specified move
        """
        (r,c) = state.rc
        (dr,dc) = move
        return self.maze.rc_bounds(r+dc, c+dc) and not self.maze.is_wall(r,c,dr,dc)

    def get_next_rotation(self, move):
        """
        Figure out which way the agent should be facing in order to make the specified move
        """
        return Vector3f(0,0,degrees(atan2(move[1], move[0])))

    def reset(self, agent):
        """
        reset the environment to its initial state
        """
        state = self.get_state(agent.state.id)
        print 'Episode %d complete' % agent.episode
        state.reset()
        agent.state.position = copy(state.initial_position)
        agent.state.rotation = copy(state.initial_rotation)
        return True

    def set_position(self, id, r ,c):
      getSimContext().setObjectPosition(id , Vector3f(r, c, 2))

    def get_other_rc(self,id):
      for key in self.states.iterkeys():
          #if its a legion thats not us
        if key != id and self.states[key].agentType == 0:
          return self.states[key].rc
      return 0

    def cell_occupied(self,r,c,objectType):

      #are we getting an object or agent?

      #agent (anything with a brain)
      if objectType < 2:
        for key in self.states.iterkeys():
          if self.states[key].rc == (r,c) and self.states[key].agentType == objectType:
            print "occupied: " + "(" + str(r) + "," + str(c) + ") " + str(objectType)
            return 1
#        print "NOT occupied: " + "(" + str(r) + "," + str(c) + ") " + str(objectType)
        return 0

      #object
      else:
        for key in self.objects.iterkeys():
          if self.objects[key].rc == (r,c) and self.objects[key].agentType == objectType:
            print "occupied: " + "(" + str(r) + "," + str(c) + ") " + str(objectType)
            return 1
#        print "NOT occupied: " + "(" + str(r) + "," + str(c) + ") " + str(objectType)
        return 0

    def get_object_in_cell(self,r,c,objectType):
      #are we getting an object or agent?

      #agent (anything with a brain)
      if objectType < 2:
        for key in self.states.iterkeys():
          if self.states[key].rc == (r,c) and self.states[key].agentType == objectType:
            print "agentHere : " + "(" + str(r) + "," + str(c) + ") " + str(key)
            return key
#        print "NOT occupied: " + "(" + str(r) + "," + str(c) + ") " + str(objectType)
        return -1

      #object
      else:
        for key in self.objects.iterkeys():
          if self.objects[key].rc == (r,c) and self.objects[key].agentType == objectType:
            print "objectHere : " + "(" + str(r) + "," + str(c) + ") " + str(objectType)
            return key
#        print "NOT occupied: " + "(" + str(r) + "," + str(c) + ") " + str(objectType)
        return -1
    
    def get_round_fitness():
      print "setting fitness"
      return 1

    def get_agent_info(self, agent):
        return self.agent_info

    def set_animation(self, agent, state, animation):
        if state.animation != animation:
            agent.state.setAnimation(animation)
            state.animation = animation

    def step(self, agent, action):
        
        """
        Discrete version
        """
        
        state = self.get_state(agent.state.id)
        state.record_action(action)

        #if were done
        if self.stepsDone == STEPS_IN_ROUND:
          return get_round_fitness()

        if not self.agent_info.actions.validate(action):
            state.prev_rc = state.rc
            return 0
        if agent.step == 0:
            state.initial_position = agent.state.position
            state.initial_rotation = agent.state.rotation
        (r,c) = state.rc

        print "prevPos :" + str(state.prev_rc)
        print "pos: " + str(state.rc)
        
        a = int(round(action[0]))
        state.prev_rc = state.rc

        if a == len(MazeEnvironment.MOVES): # null action
            return 0 #state.record_reward(self.rewards.valid_move(state))
        (dr,dc) = MazeEnvironment.MOVES[a]
        print "agent action:" + str(a)
        print "agent moving:" + str(MazeEnvironment.MOVES[a])
        new_r, new_c = r + dr, c + dc

        #our step is done
        if agent.state.id  == self.lastAgent:
          self.stepsDone += 1
          print "turn complete: " + str(self.stepsDone)

        #reasons not to actually move
        #out of bounds
        if not self.maze.rc_bounds(new_r, new_c):
            print "out of bounds"
            return 0
            #return state.record_reward(self.rewards.out_of_bounds(state))

        #if we are legion
        if state.agentType == 0:
          print "IM LEGION"
          #and there's a legion in our destination cell
          legion =  self.get_object_in_cell(dr, dc, 0)
          print "checking for legion :" + str(new_r) + str (new_c)
          print str(legion)
          if legion != -1:
            #don't move
            print "legion in cell" + str(legion)
            return 0

          #and there's a barb in the cell
          barb =  self.get_object_in_cell(dr, dc, 1)
          if barb != -1:
            #remove that agent
            print "removing agent: " + str(barb)

        #if we are barb
        if state.agentType == 1:
          #and there's any agent in the destination cell
          legion =  self.get_object_in_cell(dr, dc, 0)
          barb =  self.get_object_in_cell(dr, dc, 1)
          if legion != -1 or barb != -1:
            #don't move
            return 0

#        elif self.maze.is_wall(r,c,dr,dc):
#            print "hitting wall"
#            return state.record_reward(self.rewards.hit_wall(state))


        state.rc = (new_r, new_c)
        print "newPos :" + str(state.rc)
        (old_r,old_c) = state.prev_rc
        (old_x,old_y) = self.maze.rc2xy(old_r, old_c)
        pos0 = agent.state.position
        pos0.x = old_x
        pos0.y = old_y
        agent.state.position = pos0
        relative_rotation = self.get_next_rotation((dr,dc))
        agent.state.rotation = state.initial_rotation + relative_rotation


        

        #if this is the final step in the round, assign fitness
        

#        if new_r == 4 - 1 and new_c == COLS - 1:
#            state.goal_reached = True
#            return state.record_reward(self.rewards.goal_reached(state))
          
#        elif agent.step >= self.max_steps - 1:
#            return state.record_reward(self.rewards.last_reward(state))


        #other reward
        return state.record_reward(self.rewards.valid_move(state))



#        (r,c) = state.rc
#        (other_r,other_c) = self.get_other_rc(agent.state.id)
#
#        disOther = ((r - other_r) ** 2) + ((c - other_c)**2)
#        disOther = sqrt(disOther)
#        disGoal = ((r - 3) ** 2) + ((c - COLS - 1)**2)
#        disGoal = sqrt(disGoal)
#        if disGoal != 0:
#          disGoal = 1/disGoal
#        if disOther != 0:
#          disOther = 1/disOther
#        reward = (disGoal) - (disOther)
#        print "agent :" + str(disGoal) + " , " + str(disOther)
#        return reward

    def teleport(self, agent, r, c):
        """
        move the agent to a new location
        """
        state = self.get_state(agent.state.id)
        state.prev_rc = (r,c)
        state.rc = (r,c)
        (x,y) = self.maze.rc2xy(r,c)
        pos0 = agent.state.position
        pos0.x = x
        pos0.y = y
        agent.state.position = pos0

    # returns which direction the agent is relative to self
    def inAngle(self, r, c, agent_r, agent_c ):
        angle = self.getAngle( r, c, agent_r, agent_c )
        if 337.5 >= angle and 292.5 < angle: # NW
            return 0
        if  22.5 >= angle or  337.5 < angle: # N
            return 1
        if  67.5 >= angle and  22.5 < angle: # NE
            return 2
        if 112.5 >= angle and  67.5 < angle: # E
            return 3
        if 157.5 >= angle and 112.5 < angle: # SE
            return 4
        if 202.5 >= angle and 157.5 < angle: # S
            return 5
        if 247.5 >= angle and 202.5 < angle: # SW
            return 6
        if 292.5 >= angle and 247.5 < angle: # W
            return 7

    # return 0-259
    def getAngle(self, r, c, agent_r, agent_c ) :

        x = agent_r - r
        y = agent_c - c

        angle = atan2(x,y)*(360/(2*pi))

        if angle < 0 :
            return 360 + angle
        return angle

    def normalize(self, arr):
        max = 0
        for x in arr:
            if x > max:
                max = x
        for i in range(len(arr)):
            arr[i] /= max

    def sense(self, agent):
        """
        Discrete version
        """
        state = self.get_state(agent.state.id)
        mod = TeamAdapt.module.getMod()
        v = self.agent_info.sensors.get_instance()
        r = state.rc[0]
        c = state.rc[1]

        # sharing sensors #

#        (r,c) = state.rc
#        print str(r) + str(c)
#        (other_r,other_c) = self.get_other_rc(agent.state.id)
#        print str(other_r) + str(other_c)
#        disOther = ((r - other_r) ** 2) + ((c - other_c)**2)
#        print str(disOther)
#        disOther = sqrt(disOther)
#        print str(disOther)
#        disGoal = ((r - 3) ** 2) + ((c - COLS - 1)**2)
#        disGoal = sqrt(disGoal)
#        if disGoal != 0:
#          disGoal = 1/disGoal
#        if disOther != 0:
#          disOther = 1/disOther

#        print "agent :" + str(disGoal) + " , " + str(disOther)
#        v[0] = disGoal
#        v[1] = disOther


        #legions

        #local [0]
        v[0] = self.cell_occupied(r,c,0)
        #adjacent [1-8]
        v[1] = self.cell_occupied(r-1,c-1,0)
        v[2] = self.cell_occupied(r,c-1,0)
        v[3] = self.cell_occupied(r+1,c-1,0)
        v[4] = self.cell_occupied(r+1,c,0)
        v[5] = self.cell_occupied(r+1,c+1,0)
        v[6] = self.cell_occupied(r,c+1,0)
        v[7] = self.cell_occupied(r-1,c+1,0)
        v[8] = self.cell_occupied(r-1,c,0)
#        radar [9-16]s
        #loop through all

        directions = [[],[],[],[],[],[],[],[]]
        for agent_id in mod.agent_map.values():
            agent_state = self.get_state(agent_id)
            if agent_id != agent.state.id and agent_state.rc != (r,c):
                agent_r, agent_c = agent_state.rc
                dir_i = self.inAngle( r, c, agent_r, agent_c )
                directions[dir_i].append((agent_r,agent_c))

        distances = [0]*8
        for i in range(len(directions)):
            for point in directions[i]:
                dist = sqrt(pow(r-point[0],2)+pow(c-point[1],2))
                distances[i] += float(1)/dist

        self.normalize(distances)

        for i in range(len(distances)):
            v[i+9] = distances[i]


#        if state.agentType == 0:
#            #legions
#            #local [0]
#            v[0] = self.cell_occupied(r,c,0)
#            #adjacent [1-8]
#            v[1] = self.cell_occupied(r-1,c-1,0)
#            v[2] = self.cell_occupied(r,c-1,0)
#            v[3] = self.cell_occupied(r+1,c-1,0)
#            v[4] = self.cell_occupied(r+1,c,0)
#            v[5] = self.cell_occupied(r+1,c+1,0)
#            v[6] = self.cell_occupied(r,c+1,0)
#            v[7] = self.cell_occupied(r-1,c+1,0)
#            v[8] = self.cell_occupied(r-1,c,0)
#            #radar [9-16]
#        elif state.agentType == 1:
#            #warbands
#            #local [17]
#            v[0] = 1#self.cell_occupied(r,c,0)
#            #adjacent [18-25]
#            v[1] = self.cell_occupied(r-1,c-1,0)
#            v[2] = self.cell_occupied(r,c-1,0)
#            v[3] = self.cell_occupied(r+1,c-1,0)
#            v[4] = self.cell_occupied(r+1,c,0)
#            v[5] = self.cell_occupied(r+1,c+1,0)
#            v[6] = self.cell_occupied(r,c+1,0)
#            v[7] = self.cell_occupied(r-1,c+1,0)
#            v[8] = self.cell_occupied(r-1,c,0)
#            #radar [26-33]
#        elif state.agentType == 2:
#            #cities
#            #local [34]
#            v[34] = self.cell_occupied(r,c,0)
#            #adjacent [35-42]
#            v[35] = self.cell_occupied(r-1,c-1,0)
#            v[36] = self.cell_occupied(r,c-1,0)
#            v[37] = self.cell_occupied(r+1,c-1,0)
#            v[38] = self.cell_occupied(r+1,c,0)
#            v[39] = self.cell_occupied(r+1,c+1,0)
#            v[40] = self.cell_occupied(r,c+1,0)
#            v[41] = self.cell_occupied(r-1,c+1,0)
#            v[42] = self.cell_occupied(r-1,c,0)
#            #radar [43-50]

#        offset = GRID_DX/10.0
#        p0 = agent.state.position
#        for i, (dr, dc) in enumerate(MazeEnvironment.MOVES):
#            direction = Vector3f(dr, dc, 0)
#            ray = (p0 + direction * offset, p0 + direction * GRID_DX)
#            # we only look for objects of type 1, which means walls
#            objects = getSimContext().findInRay(ray[0], ray[1], 1, True)
#            v[2 + i] = int(len(objects) > 0)
        state.record_observation(v)
        return v

    def is_active(self, agent):
        state = self.get_state(agent.state.id)
        # here, we interpolate between state.prev_rc and state.rc
        (r0,c0) = state.prev_rc
        (r1,c1) = state.rc
        dr, dc = r1 - r0, c1 - c0
        if dr != 0 or dc != 0:
            (x0,y0) = self.maze.rc2xy(r0,c0)
            (x1,y1) = self.maze.rc2xy(r1,c1)
            pos = agent.state.position
            fraction = 1.0
            if self.get_delay() != 0:
                fraction = min(1.0,float(time.time() - state.time)/self.get_delay())
            pos.x = x0 * (1 - fraction) + x1 * fraction
            pos.y = y0 * (1 - fraction) + y1 * fraction
            agent.state.position = pos
            self.set_animation(agent, state, 'run')
        else:
            self.set_animation(agent, state, 'stand')
        if time.time() - state.time > self.get_delay():
            state.time = time.time()
            return True # call the sense/act/step loop
        else:
            return False

    def is_episode_over(self, agent):
        state = self.get_state(agent.state.id)
        if self.max_steps != 0 and agent.step >= self.max_steps:
            return True
        elif state.goal_reached:
            return True
        #elif self.shortcircuit and state.is_stuck():
        #    return False
        else:
            return False

    def cleanup(self):
        pass

class ContMazeEnvironment(MazeEnvironment):
    TURN_BY = 30 # how many degrees to turn by every time
    WALK_BY = 2.5 # how many units to advance by every step forward
    ACTIONS = {'FWD':0, 'CW':1, 'CCW':2, 'BCK':3}
    N_ACTIONS = 4 # number of actions
    N_RAYS = 4 # number of rays around the agent, starting from the front
    MAX_DISTANCE = hypot(ROWS*GRID_DX, COLS*GRID_DY) # max distance within the maze
    """
    The environment is a 2-D maze.
    This is a slightly more continous version
     * Actions (1 discrete action)
        * 0 - move forward by WALK_BY
        * 1 - turn CW by TURN_BY and move forward by WALK_BY
        * 2 - turn CCW by TURN_BY and move forward by WALK_BY
        * 3 - move backward by WALK_BY
     * Observations ()
        * o[0] - the current x position
        * o[1] - the current y position
        * o[2] - the angle to the target
        * o[3] - the distance to the target
        * o[4] - o[7] - ray sensors cast around the agent (starting with straight ahead and going clockwise)
    """
    def __init__(self):
        """
        generate the maze
        """
        MazeEnvironment.__init__(self)
        action_info = FeatureVectorInfo() # describes the actions
        observation_info = FeatureVectorInfo() # describes the observations
        reward_info = FeatureVectorInfo() # describes the rewards
        action_info.add_discrete(0, ContMazeEnvironment.N_ACTIONS-1) # action
        ( (xmin, ymin), (xmax, ymax) ) = self.maze.xy_limits()
        print 'MAZE LIMITS', ( (xmin, ymin), (xmax, ymax) )
        observation_info.add_continuous(xmin, xmax) # x-coord
        observation_info.add_continuous(ymin, ymax) # y-coord
        observation_info.add_continuous(0, ContMazeEnvironment.MAX_DISTANCE ) # distance to target
        observation_info.add_continuous(-180, 180) # angle to target
        for i in range(ContMazeEnvironment.N_RAYS):
            observation_info.add_continuous(0,1) # ray sensor
        reward_info.add_continuous(-100,100)
        self.agent_info = AgentInitInfo(observation_info, action_info, reward_info)
        self.max_steps = MAX_STEPS * 15 # allow 15 actions per cell
        self.step_delay = STEP_DELAY/10.0 # smaller actions, but faster
        print 'Initialized ContMazeEnvironment'

    def get_next_rotation(self, move):
        """
        Figure out which way the agent should be facing in order to make the specified move
        """
        return Vector3f(0,0,degrees(atan2(move[1], move[0])))

    def reset(self, agent):
        """
        reset the environment to its initial state
        """
        state = self.get_state(agent.state.id)
        state.pose = (state.initial_position.x, state.initial_position.y, state.initial_rotation.z)
        agent.state.position = copy(state.initial_position)
        agent.state.rotation = copy(state.initial_rotation)
        state.goal_reached = False
        print 'Episode %d complete' % agent.episode
        return True

    def step(self, agent, action):
        """
        Continuous version
        """
        state = self.get_state(agent.state.id)
        state.record_action(action)
        if not self.agent_info.actions.validate(action):
            return 0
        a = int(round(action[0]))
        (x,y,heading) = state.pose # current pose
        new_x, new_y, new_heading = x, y, heading # pose to be computed
        dx, dy = None, None
        if a == ContMazeEnvironment.ACTIONS['CW']: # clockwise
            new_heading = wrap_degrees(heading, -ContMazeEnvironment.TURN_BY)
        elif a == ContMazeEnvironment.ACTIONS['CCW']: # counter-clockwise
            new_heading = wrap_degrees(heading, ContMazeEnvironment.TURN_BY)
        elif a == ContMazeEnvironment.ACTIONS['FWD']: # forward
            dx = ContMazeEnvironment.WALK_BY * cos(radians(new_heading))
            dy = ContMazeEnvironment.WALK_BY * sin(radians(new_heading))
        elif a == ContMazeEnvironment.ACTIONS['BCK']: # backward
            dx = -ContMazeEnvironment.WALK_BY * cos(radians(new_heading))
            dy = -ContMazeEnvironment.WALK_BY * sin(radians(new_heading))
        if dx or dy:
            test_x, test_y = x + 1.5 * dx, y + 1.5 * dy # leave a buffer of space
            new_x, new_y = x + dx, y + dy
            if not self.maze.xy_bounds(test_x, test_y):
                # could not move, out of bounds
                self.set_animation(agent, state, 'stand')
                return self.rewards.out_of_bounds(state)
            elif not self.maze.xy_valid(x,y,test_x,test_y):
                # could not move, hit a wall
                self.set_animation(agent, state, 'stand')
                return self.rewards.hit_wall(state)
            if new_x != x or new_y != y:
                self.set_animation(agent, state, 'run')
        if agent.step == 0:
            state.initial_position = agent.state.position
            state.initial_rotation = agent.state.rotation
        # move the agent
        agent.state.rotation = state.initial_rotation + Vector3f(0,0,new_heading)
        pos0 = agent.state.position
        pos0.x = new_x
        pos0.y = new_y
        agent.state.position = pos0
        # update agent state
        state.update(agent, self.maze)
        (new_r, new_c) = state.rc
        if new_r == ROWS - 1 and new_c == COLS - 1:
            state.goal_reached = True
            return self.rewards.goal_reached(state)
        elif agent.step >= self.max_steps - 1:
            return self.rewards.last_reward(state)
        return self.rewards.valid_move(state)

    def sense(self, agent):
        """
        Continuous version
        """
        state = self.get_state(agent.state.id)
        v = self.agent_info.sensors.get_instance()
        (x,y,heading) = state.pose # current agent pose
        v[0] = x # the agent can observe its position
        v[1] = y # the agent can observe its position
        (tx, ty) = self.maze.rc2xy(ROWS-1,COLS-1) # coordinates of target
        tx, ty = tx - x, ty - y # line to target
        v[2] = hypot(tx, ty) # distance to target
        angle_to_target = degrees(atan2(ty, tx)) # angle to target from +x, in degrees
        angle_to_target = wrap_degrees(angle_to_target, -heading) # heading to target relative to us
        v[3] = angle_to_target
        d_angle = 360.0 / ContMazeEnvironment.N_RAYS
        p0 = agent.state.position
        for i in range(ContMazeEnvironment.N_RAYS):
            angle = radians(heading + i * d_angle)
            direction = Vector3f(cos(angle), sin(angle), 0) # direction of ray
            ray = (p0, p0 + direction * GRID_DX)
            # we only look for objects of type 1, which means walls
            result = getSimContext().findInRay(ray[0], ray[1], 1, True)
            # we can now return a continuous sensor since FindInRay returns the hit point
            if len(result) > 0:
                (sim, hit) = result
                len1 = (ray[1] - ray[0]).getLength() # max extent
                len2 = (hit - ray[0]).getLength() # actual extent
                if len1 != 0:
                    v[4+i] = len2/len1
                else:
                    v[4+i] = 0
            else:
                v[4+i] = 1
        if not self.agent_info.sensors.validate(v):
            print 'ERROR: incorect observation!', v
            print '       should be:', self.agent_info.sensors
        state.record_observation(v)
        return v

    def is_active(self, agent):
        state = self.get_state(agent.state.id)
        # TODO: interpolate
        fraction = min(1.0,float(time.time() - state.time)/self.get_delay())
        if time.time() - state.time > self.get_delay():
            state.time = time.time()
            return True # call the sense/act/step loop
        else:
            return False

def is_uniform(vv):
    """ return true iff all the feature vectors in v are identical """
    l = len(vv)
    if l == 0:
        return False
    v0 = [x for x in vv[0]]
    for i in range(1, len(vv)):
        vi = [x for x in vv[i]]
        if v0 != vi:
            return False
    return True

def wrap_degrees(a,da):
    a2 = a + da
    if a2 > 180:
        a2 = -180 + (a2 % 180)
    elif a2 < -180:
        a2 = 180 - (abs(a2) % 180)
    return a2