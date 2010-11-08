from common import *
from OpenNero import getSimContext
from Blocksworld.BlocksEnvironment import *
from Blocksworld.RTNEATAgent import *
from Blocksworld.Turret import *
from constants import *
import subprocess
import os
import sys

import random

class BlocksworldModule:
    def __init__(self):
        global rtneat, rtneat2
        rtneat = RTNEAT("data/ai/neat-params.dat", NEAT_SENSORS, NEAT_ACTIONS, pop_size, 1.0)
        rtneat2 = RTNEAT("data/ai/neat-params.dat", NEAT_SENSORS, NEAT_ACTIONS, pop_size,1.0)
        self.environment = None
        self.speedup = 100
        self.agent_id = None
        self.agent_map = {}
        self.weights = Fitness()
        self.lt = 150
        self.dta = 50
        self.dtb = 50
        self.dtc = 50
        self.ff =  0
        self.ee =  0
        self.hp = 50
        self.currTeam = 1
        self.coin_nears = [{0:0, 1:0, 2:0},{0:0,1:0,2:0}]
        self.coin_locs = {0:Vector3f(XDIM/2,YDIM/2,0), 1:Vector3f(XDIM/2,YDIM/3,0), 2:Vector3f(XDIM/2,2*YDIM/3,0)}
        self.coin_ids = {}
        self.coins = [[0,1,2],[],[]]
        self.fitness = {1:.05,2:.05}
        self.capture = {1:.05,2:.05}
        self.curr_id = 3
        self.num_to_add = pop_size

    def setup_map(self):
        """
        setup the test environment
        """
        global XDIM, YDIM, HEIGHT, OFFSET
        if self.environment:
            error("Environment already created")
            return
        
        #Test for wx python
        try:
            import wx
        except ImportError:
            print "Please install wx"
            openWiki('wx')()
            return False

        startScript('Blocksworld/menu.py')
        
        self.environment = BlocksEnvironment()

        set_environment(self.environment)
        
        # coin placement
        for coin in self.coin_locs:
         self.coin_ids[coin] = addObject("data/shapes/cube/BlueCube.xml", self.coin_locs[coin], label="Coin")

        # world walls
        addObject("data/shapes/cube/Cube.xml", Vector3f(XDIM/2,0,HEIGHT+OFFSET), Vector3f(0, 0, 90), scale=Vector3f(1,XDIM,HEIGHT), label="World Wall0", type = OBSTACLE )
        addObject("data/shapes/cube/Cube.xml", Vector3f(0, YDIM/2, HEIGHT + OFFSET), Vector3f(0, 0, 0), scale=Vector3f(1,YDIM,HEIGHT), label="World Wall1", type = OBSTACLE )
        addObject("data/shapes/cube/Cube.xml", Vector3f(XDIM, YDIM/2, HEIGHT + OFFSET), Vector3f(0, 0, 0), scale=Vector3f(1,YDIM,HEIGHT), label="World Wall2", type = OBSTACLE )
        addObject("data/shapes/cube/Cube.xml", Vector3f(XDIM/2, YDIM, HEIGHT +OFFSET), Vector3f(0, 0, 90), scale=Vector3f(1,XDIM,HEIGHT), label="World Wall3", type = OBSTACLE )

        # Add the surrounding Environment
        addObject("data/terrain/NeroWorld.xml", Vector3f(XDIM/2, YDIM/2, 0), scale=Vector3f(1, 1, 1), label="NeroWorld")
        
        return True
    
    def change_coin(self, new_loc, id):
        self.coin_locs[id] = Vector3f(new_loc[0],new_loc[1],new_loc[2])
        
        removeObject(self.coin_ids[id])

        self.coin_ids[id] = addObject("data/shapes/cube/BlueCube.xml", self.coin_locs[id], label="Coin")

    def add_coin(self, new_loc):
        
        self.coin_locs[self.curr_id] = (Vector3f(new_loc[0],new_loc[1],new_loc[2]))
        
        self.coin_ids[self.curr_id] = addObject("data/shapes/cube/BlueCube.xml", self.coin_locs[self.curr_id], label="Coin")

        self.coin_nears[0][self.curr_id] = 0
        self.coin_nears[1][self.curr_id] = 0

        self.coins[0].append(self.curr_id)

        self.curr_id += 1

    #The following is run when the Deploy button is pressed
    def start_rtneat(self):
        """ start the rtneat learning stuff"""
        global rtneat, rtneat2
        disable_ai()

        # Create RTNEAT Objects
        set_ai("neat1",rtneat)
        set_ai("neat2", rtneat2)
        enable_ai()
        # Generate all initial rtNEAT Agents
        dx = random.randrange(XDIM/20) - XDIM/40
        dy = random.randrange(XDIM/20) - XDIM/40
        for i in range(0, DEPLOY_SIZE):
            dx = random.randrange(XDIM/20) - XDIM/40
            dy = random.randrange(XDIM/20) - XDIM/40
            id = None
            if i % 2 == 0:
                self.currTeam = 1
                id = addObject("data/shapes/character/steve_red_armed.xml",Vector3f(TEAM_1_SL_X + dx,TEAM_1_SL_Y + dy,2),type = AGENT)
            else:
                self.currTeam = 2
                id = addObject("data/shapes/character/steve_red_armed.xml",Vector3f(TEAM_2_SL_X + dx,TEAM_2_SL_Y + dy ,2),type = AGENT)
            self.agent_map[(0,i)] = id

   #The following is run when the Save button is pressed

    def save_rtneat(self, location, pop):
        import os
        location = os.path.relpath("/") + location
        global rtneat, rtneat2
        if pop == 1: rtneat.save_population(str(location))
        if pop == 2: rtneat2.save_population(str(location))

    #The following is run when the Load button is pressed
    def load_rtneat(self, location , pop):
        import os
        global rtneat, rtneat2
        location = os.path.relpath("/") + location
        if os.path.exists(location):
            if pop == 1: rtneat = RTNEAT(str(location), "data/ai/neat-params.dat", pop_size)
            if pop == 2: rtneat2= RTNEAT(str(location), "data/ai/neat-params.dat", pop_size)
    
    def set_speedup(self, speedup):
        self.speedup = speedup
        if self.environment:
            self.environment.speedup = speedup
    
    #The following functions are used to let the client update the fitness function
    def set_weight(self, key, value):
        self.weights[key] = (value-100.0)/100.0
        print key, value
        
    def ltChange(self,value):
        self.lt = value
        print 'lifetime:',value

    def dtaChange(self,value):
        self.dta = value
        print 'Distance to approach A:',value

    def dtbChange(self,value):
        self.dtb = value
        print 'Distance to approach B:',value

    def dtcChange(self,value):
        self.dtc = value
        print 'Distance to approach C:',value

    def ffChange(self,value):
        self.ff = value
        print 'Friendly fire:',value

    def eeChange(self,value):
        self.ee = value
        print 'Explore/exploit:',value

    def hpChange(self,value):
        self.hp = value
        print 'Hit points:',value

    def fitChange(self,team,value):
        value = value/100.0
        self.fitness[team] = value
        print 'Team:', team, "fitness =",value

    def capChange(self,team,value):
        value = value/100.0
        self.capture[team] = value
        print 'Team:', team, "fitness =",value


    def getNumToAdd(self):
        return self.num_to_add

    #This is the function ran when an agent already in the field causes the generation of a new agent
    def addAgent(self,pos):
        self.num_to_add -= 1
        self.currTeam += 1
        if self.currTeam == 3: self.currTeam = 1
        addObject("data/shapes/character/steve_red_armed.xml",Vector3f(pos[0],pos[1],pos[2]),type = AGENT)

gMod = None

def delMod():
    global gMod
    gMod = None

def getMod():
    global gMod
    if not gMod:
        gMod = BlocksworldModule()
    return gMod

def parseInput(strn):
    if strn == "deploy": return
    if len(strn) < 2: return
    mod = getMod()
    loc,val = strn.split(' ')
    vali = 1
    if strn.isupper(): vali = int(val)
    if loc == "F1": mod.fitChange(1,vali)
    if loc == "F2": mod.fitChange(2,vali)
    if loc == "C1": mod.capChange(1,vali)
    if loc == "C2": mod.capChange(2,vali)
    if loc == "EE": mod.eeChange(vali)
    if loc == "HP": mod.hpChange(vali)
    if loc == "SP": mod.set_speedup(vali)
    if loc == "save1": mod.save_rtneat(val,1)
    if loc == "load1": mod.load_rtneat(val,1)
    if loc == "save2": mod.save_rtneat(val,2)
    if loc == "load2": mod.load_rtneat(val,2)

def ServerMain():
    print "Starting mod Blocksworld"
