#
# Bouncing ball simulator for Blender game engine
#
# Copyright(c) 2016 M. Roohian. All rights reserved.
#

import bge
import math

# Constants
DEBUG = False
MASS = 1.0
RADIUS = 0.5
GRAVITY = -9.8
DELTATIME = 0.1
SQUEEZESPEED = 0.006 # 14 (m/s) / 0.7
STRETCHSPEED = 0.00008 # 98 (E) / 0.7
BOUNCEENERGYREMAINING = 0.56 # Saves 56% of energy

# Sphere states object
class ObjectStatus:
    def __init__(self, speedZ, Z):
        self.speedZ = speedZ
        self.Z = Z
        self.energy = 0.0
        self.remainingTime = 0.0

    def setDeltaTime(self):
        self.remainingTime = DELTATIME

    def setTimeTo(self, time):
        self.remainingTime = time

    def spendTime(self, spentTime):
        self.remainingTime -= spentTime


# Get the bge objects
cont = bge.logic.getCurrentController()
sphere = cont.owner

# Initialize variables
time = sphere.get("time", None)
if time is None:
    time = sphere["time"] = 0.0
else:
    time = sphere["time"] = time + DELTATIME
    
phase = sphere.get("phase", None)
if phase is None:
    # assume simulation starts with ball over ground
    phase = sphere["phase"] = "freefall"

sphereStatus = sphere.get("sphereStatus", None)
if sphereStatus is None:
    sphereStatus = ObjectStatus(0.0, sphere.worldPosition.z)

# Helper functions
def timeOfAccelaratedTravelByDistance(acceleration, currentSpeed, distance):
    if DEBUG:
        print ("speed: %f, acceleration: %f, distance: %f" % (currentSpeed, acceleration, distance))
    return (- currentSpeed - math.sqrt(2 * acceleration * distance + currentSpeed * currentSpeed)) / acceleration

# Logic functions

# freefall phase
def freefall(currentStatus):
    # if object is still on the ground return
    if currentStatus.Z - RADIUS < 0.00001 and currentStatus.speedZ < 0.00001:
        if DEBUG:
            print ( "- still")
        currentStatus.setTimeTo(0)
        return "freefall"

    newSpeedZ = currentStatus.speedZ + GRAVITY * currentStatus.remainingTime
    newZ = currentStatus.Z + 0.5 * (newSpeedZ + currentStatus.speedZ) * currentStatus.remainingTime

    # if next move will not collide the ground the move is allowed
    if newZ - RADIUS > 0:
        currentStatus.speedZ = newSpeedZ
        currentStatus.Z = newZ
        currentStatus.setTimeTo(0)
        return "freefall"

    # time until the ball collides the ground
    deltaTimeToColide = timeOfAccelaratedTravelByDistance(GRAVITY, currentStatus.speedZ, RADIUS - currentStatus.Z)
    if DEBUG:
        print ( "- deltaTimeToColide: %f, speed: %f, distance: %f" % (deltaTimeToColide, currentStatus.speedZ, RADIUS - currentStatus.Z) )

    # position and speed at collision point
    newSpeedZColide = currentStatus.speedZ + GRAVITY * deltaTimeToColide
    newZColide = currentStatus.Z + 0.5 * (newSpeedZColide + currentStatus.speedZ) * deltaTimeToColide
    if DEBUG: 
        print ( "- newSpeedZColide: %f newZColide: %f" % (newSpeedZColide, newZColide) )

    # update current status 
    currentStatus.speedZ = newSpeedZColide
    currentStatus.Z = newZColide
    currentStatus.spendTime(deltaTimeToColide)

    return "squeeze"

# Squeeze phase
def squeeze(currentStatus):
    currentSpeedZ = currentStatus.speedZ
    newSpeedZ = 0

    # time to fully squeeze the ball
    timeToSqueeze = SQUEEZESPEED * math.fabs(currentSpeedZ)

    # check if we have enough time to fully squeeze
    if timeToSqueeze >= currentStatus.remainingTime:
        timeToSqueeze = currentStatus.remainingTime
        newSpeedZ = currentSpeedZ + (timeToSqueeze / SQUEEZESPEED)
        
    # calculate the reduced energy
    energyDiff = 0.5 * MASS * (currentSpeedZ * currentSpeedZ - newSpeedZ * newSpeedZ)

    # update the speed and energy
    currentStatus.speedZ = newSpeedZ
    currentStatus.energy += energyDiff * BOUNCEENERGYREMAINING
    currentStatus.spendTime(timeToSqueeze)

    # start stretching when speed is zero
    if newSpeedZ == 0:
        return "stretch"

    return "squeeze"

# Stretch phase
def stretch(currentStatus):
    currentEnergy = currentStatus.energy
    newEnergy = 0

    # time to fully stretch the ball
    timeToStretch = STRETCHSPEED * currentEnergy

    # check if we have enough time to fully stretch
    if timeToStretch >= currentStatus.remainingTime:
        timeToStretch = currentStatus.remainingTime
        newEnergy = currentEnergy - (timeToStretch / STRETCHSPEED)
        
    # calculate the increase speed
    currentSpeedZ = currentStatus.speedZ
    newSpeedZ = math.sqrt((4 * (currentEnergy - newEnergy) + MASS * currentSpeedZ * currentSpeedZ) / (2 * MASS))
    currentStatus.energy = newEnergy
    currentStatus.speedZ = newSpeedZ
    currentStatus.spendTime(timeToStretch)

    # start stretching when speed is zero
    if newEnergy == 0:
        return "freefall"

    return "stretch"

# Phase function map
phaseActions = {"freefall": freefall, "squeeze": squeeze, "stretch": stretch}

# Update loop
sphereStatus.setDeltaTime()

while sphereStatus.remainingTime > 0:
    phase = phaseActions[phase](sphereStatus)
    if DEBUG: 
        print ( "time: %f, phase: %s, energy: %f, locationZ: %f speed: %f" % (time, phase, sphereStatus.energy, sphereStatus.Z, sphereStatus.speedZ) )

# Move objects in the scene
sphere.worldPosition = [sphere.worldPosition.x, sphere.worldPosition.y, sphereStatus.Z]

# Update status variables
sphere["phase"] = phase
sphere["sphereStatus"] = sphereStatus
