# WAD HANDLER
import math

class map:
    def __init__(self, number, name, desc, trck, data):
        self.number = number
        self.name = name
        self.data = data
        self.trck = trck

        # text description of the map
        self.desc = desc

        # size = [x_size, y_size]
        self.size = [len(data[0]), len(data)]

        # separate these into two distinct
        # size variables, just for convenience
        self.x_size = self.size[0]
        self.y_size = self.size[1]

    def get_BGM(self):
        return self.trck

    def get_player_start(self):

        # make these 0 initially so we will default to (0, 0) coordinates
        # if playerstart is not defined
        playerstart_x = 0
        playerstart_y = 0
        
        for y in range(len(self.data)):
            for x in range(len(self.data[0])):
                if self.data[y][x].playerstart:
                    playerstart_x = x
                    playerstart_y = y

        return [x, y]

    def get_sector(self, x, y):
        
        # sectors are centered at integer coordinates
        # their boundaries are at (integer + 0.5)
        
        if (x - int(x)) >= 0.5:
            x = int(x) + 1
        elif (x - int(x)) <= -0.5:
            x = int(x) - 1
        else:
            x = int(x)

        if (y - int(y)) >= 0.5:
            y = int(y) + 1
        elif (y - int(y)) <= -0.5:
            y = int(y) - 1
        else:
            y = int(y)
            
        return self.data[y][x]

class sector:
    def __init__(self, x, y, wall=False, threat=False, key1=False, key2=False, key3=False, door1=False, door2=False, door3=False, end=False, playerstart=False):
        
        # where the sector is located on the map
        self.x = int(x)
        self.y = int(y)

        # is this a wall? (non-traversable)
        self.wall = bool(wall)

        # is this a threat? (kills player)
        self.threat = bool(threat)

        # is this a key? (can be picked up)
        self.key1 = bool(key1)
        self.key2 = bool(key2)
        self.key3 = bool(key3)

        # is this a door? (can only be traversed with a key)
        self.door1 = bool(door1)
        self.door2 = bool(door2)
        self.door3 = bool(door3)

        # is this the level ending? (finishes map)
        self.end = end

        # is this the starting position for player?
        self.playerstart = playerstart

    def take_key1(self):
        self.key1 = False
    def take_key2(self):
        self.key2 = False
    def take_key3(self):
        self.key3 = False

class player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.orient = [[1,0],
                       [0,1]]
        self.angle = 0
        self.key1 = False
        self.key2 = False
        self.key3 = False

        self.alive = True

        self.lin_speed = 3
        self.rot_speed = 20

    def get_pos(self):
        return [self.x, self.y]

    def is_alive(self):
        return self.alive

    def kill(self):
        self.alive = False

    def rotate(self, rotation):
        # rotations is in angles
        self.angle += rotation * self.rot_speed
        
        rad1 = math.radians(self.angle)
        rad2 = math.radians(self.angle + 90)
        
        self.orient = [[math.cos(rad1), math.sin(rad1)],
                       [math.cos(rad2), math.sin(rad2)]]

    def move(self, movement):
        # this is just matrix calculations
        # Q: Why not use numpy? A: WhY NoT UsE nuMpY!?!?11
        self.x += movement[0] * self.orient[0][0] * self.lin_speed
        self.x += movement[1] * self.orient[1][0] * self.lin_speed

        self.y += movement[0] * self.orient[0][1] * self.lin_speed
        self.y += movement[1] * self.orient[1][1] * self.lin_speed

    def give_key1(self):
        self.key1 = True
    def give_key2(self):
        self.key2 = True
    def give_key3(self):
        self.key3 = True

    def has_key1(self):
        return self.key1
    def has_key2(self):
        return self.key2
    def has_key3(self):
        return self.key3

# we read maps from .wad files
# they are actually just .txt files with a fancy extension
def read_map(map_filename):
    if not map_filename.endswith(".wad"):
        map_filename += ".wad"

    map_file = open(map_filename, "r")
    map_lines = map_file.readlines()

    # read metadata
    for line in map_lines:
        if line.startswith("name = "):
            map_name = line[7:-1]
        elif line.startswith("desc = "):
            map_desc = line[7:-1]
        elif line.startswith("numr = "):
            map_numr = int(line[7:-1])
        elif line.startswith("trck = "):
            map_trck = line[7:-1]

    map_data = []
    y = 0
    # read sectors
    for line in map_lines:
        if line.startswith("D|"):
            map_data.append([])
            line = line[2:-1]
            x = 0
            for char in line:

                # mapping of flags: (x, y, wall, threat, key1, key2, key3, door1, door2, door3, end, playerstart)
                
                # regular traversable sector
                if char == ".":
                    new_sector = sector(x, y)

                # wall
                elif char == "#":
                    new_sector = sector(x, y, wall=True)

                # end
                elif char == "E":
                    new_sector = sector(x, y, end=True)

                # threat
                elif char == "X":
                    new_sector = sector(x, y, threat=True)

                # keys
                elif char == "z":
                    new_sector = sector(x, y, key1=True)

                elif char == "x":
                    new_sector = sector(x, y, key2=True)

                elif char == "c":
                    new_sector = sector(x, y, key3=True)

                # doors
                elif char == "Z":
                    new_sector = sector(x, y, door1=True)

                elif char == "X":
                    new_sector = sector(x, y, door2=True)

                elif char == "C":
                    new_sector = sector(x, y, door3=True)

                # playerstart
                elif char == "P":
                    new_sector = sector(x, y, playerstart=True)
                    
                map_data[y].append(new_sector)
                x += 1
            y += 1

    new_map = map(map_numr, map_name, map_desc, map_trck, map_data)
    return new_map
