import keyboard as kbd
import time
import os

from wad import *
from sound import *

def load_episode(episode_name):
    c_maplist = os.listdir("episodes/" + episode_name)
    arranged_list = []
    
    for mapfile in c_maplist:
        map_numr = read_map("episodes/" + episode_name + "/" + mapfile).get_number()
        arranged_list.append([map_numr, mapfile])

    arranged_list = sorted(arranged_list)
    return arranged_list

def load_map(ep_name, map_filename):
    map_full_filename = "episodes/" + ep_name + "/" + map_filename

    # load map data
    current_map = read_map(map_full_filename)

    # play map BGM
    playBGM(current_map.get_BGM())

    # initialize player
    playerstart = current_map.get_player_start()
    current_player = player(playerstart[0], playerstart[1])

    return current_map, current_player

def play_episode(ep_name, difficulty):

    def play_map(map_name, difficulty):
        c_map, c_player = load_map(ep_name, map_name)
        delta_t = 0.01
        end_flag = False
        search_radius = 3

        def draw_map():
            if os.name == "nt":
                os.system("cls")
            else:
                os.system("clear")
            
            ascii_map_str = ""
            
            if difficulty == 1:
                for y in c_map.get_data():
                    ascii_map_str += "\n"
                    for x in y:
                        if x.wall:
                            ascii_map_str += "#"
                        elif x.end:
                            ascii_map_str += "E"
                        elif x.threat:
                            ascii_map_str += "X"
                        elif x.playerstart:
                            ascii_map_str += "P"
                        elif x.key1:
                            ascii_map_str += "a"
                        elif x.key2:
                            ascii_map_str += "b"
                        elif x.key3:
                            ascii_map_str += "c"
                        elif x.door1:
                            ascii_map_str += "A"
                        elif x.door2:
                            ascii_map_str += "B"
                        elif x.door3:
                            ascii_map_str += "C"
                        else:
                            ascii_map_str += "."

            print(c_map.get_name(), "\n")
            print(ascii_map_str, "\n")
            print(c_map.get_desc())
            print("Hearing radius:", str(search_radius), "units")

        draw_map()

        def dist(coord1, coord2):
            return ((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)**0.5

        while c_player.is_alive():

            cycle_start = time.perf_counter()

            cmd_move_y = 0
            cmd_move_x = 0
            cmd_rotate = 0

            # linear movement input
            if kbd.is_pressed("w"):
                cmd_move_y -= 1
            if kbd.is_pressed("s"):
                cmd_move_y += 1
            if kbd.is_pressed("d"):
                cmd_move_x += 1
            if kbd.is_pressed("a"):
                cmd_move_x -= 1

            # rotation input
            if kbd.is_pressed("k"):
                cmd_rotate += 1
            if kbd.is_pressed("l"):
                cmd_rotate -= 1

            # increase - decrease hearing radius
            if kbd.is_pressed("y") and search_radius < 6:
                search_radius += 1
                time.sleep(0.2)
                draw_map()
            if kbd.is_pressed("t") and search_radius > 2:
                search_radius -= 1
                time.sleep(0.2)
                draw_map()

            cmd_rotate *= delta_t
            cmd_move_x *= delta_t
            cmd_move_y *= delta_t

            # do the actual player moving
            c_player.rotate(cmd_rotate)
            c_player.move([cmd_move_x, cmd_move_y])

            try:
                player_sector = c_map.get_sector(c_player.get_pos()[0], c_player.get_pos()[1])
            except IndexError:
                # prevent the player from travelling out-of-bounds
                # (which is a guaranteed insta-crash)
                c_player.move([-cmd_move_x, -cmd_move_y])

            # we cannot have the player moving through walls, just revert the movement that's
            # already applied (rotation shall stay)
            # combined with good map design, this should prevent out-of-bounds too
            if player_sector.wall:
                c_player.move([-cmd_move_x, -cmd_move_y])

            # if the sector has a key, give it to the player
            # and remove it from the sector
            elif player_sector.key1:
                c_player.give_key1()
                player_sector.take_key1()
                print("KEY-A ACQUIRED!")
                time.sleep(1)
                draw_map()

            elif player_sector.key2:
                c_player.give_key2()
                player_sector.take_key2()
                print("KEY-B ACQUIRED!")
                time.sleep(1)
                draw_map()

            elif player_sector.key3:
                c_player.give_key3()
                player_sector.take_key3()
                print("KEY-C ACQUIRED!")
                time.sleep(1)
                draw_map()

            # no moving thru doors without keys
            elif player_sector.door1 and not c_player.has_key1():
                c_player.move([-cmd_move_x, -cmd_move_y])

            elif player_sector.door2 and not c_player.has_key2():
                c_player.move([-cmd_move_x, -cmd_move_y])

            elif player_sector.door3 and not c_player.has_key3():
                c_player.move([-cmd_move_x, -cmd_move_y])

            # stepped on a threat sector? too bad.
            elif player_sector.threat:
                c_player.kill()
                playSfx("death", 10)
                print("YOU HAVE DIED - RESTARTING LEVEL...")
                time.sleep(2)
                draw_map()

            elif player_sector.end:
                end_flag = True

            # Channels:
            # 0 -- bgm
            # 1 -- end
            # 2 -- threat
            # 3 -- wall
            # 4 -- key1
            # 5 -- key2
            # 6 -- key3
            # 7 -- door1
            # 8 -- door2
            # 9 -- door3
            sectors_nearby = []

            search_start_x = max(int(c_player.get_pos()[0]) - search_radius, 0)
            search_start_y = max(int(c_player.get_pos()[1]) - search_radius, 0)

            search_end_x = min(search_start_x + search_radius*2, c_map.get_size()[0])
            search_end_y = min(search_start_y + search_radius*2, c_map.get_size()[1])

            sound_sources = []
            for y in range(search_start_y, search_end_y):
                for x in range(search_start_x, search_end_x):
                    if c_map.get_data()[y][x].has_flags():
                        sound_sources.append(c_map.get_data()[y][x])

            wall_volume = [0,0]
            threat_volume = [0,0]
            end_volume = [0,0]
            key1_volume = [0,0]
            key2_volume = [0,0]
            key3_volume = [0,0]
            door1_volume = [0,0]
            door2_volume = [0,0]
            door3_volume = [0,0]

            # OKAY so I made these all separately so that it will be easier to give a special effect to any
            # kind of sound source sector that we want. the computer should have to make nearly the same amount
            # of work whether I write this all in a for loop or separately by hand
            for source in sound_sources:

                # walls (there can be multiple!!)
                if source.wall:
                    d = dist(c_player.get_pos(), source.get_pos())
                    wall_dir = [source.get_pos()[0] - c_player.get_pos()[0], source.get_pos()[1] - c_player.get_pos()[1]]
                    wall_dir[0] = wall_dir[0]/d
                    wall_dir[1] = wall_dir[1]/d

                    orn = c_player.get_orient()
                    
                    # cos(a) = [(xa * xb + ya * yb) / (√(xa2 + ya2) * √(xb2 + yb2))]
                    right_alignment = (wall_dir[0] * orn[0][0] + wall_dir[1] * orn[0][1])
                    # ^^ no need to divide since the magnitudes of orn[0] and wall_dir are both 1
                    alignment = [(1-right_alignment)/2, (1+right_alignment)/2]
                    volume_mult = getVolumeAtDistance(d)

                    wall_volume[0] += alignment[0]*volume_mult
                    wall_volume[1] += alignment[1]*volume_mult

                # threats (there can be multiple!!)
                elif source.threat:
                    d = dist(c_player.get_pos(), source.get_pos())
                    threat_dir = [source.get_pos()[0] - c_player.get_pos()[0], source.get_pos()[1] - c_player.get_pos()[1]]
                    threat_dir[0] = threat_dir[0]/d
                    threat_dir[1] = threat_dir[1]/d

                    orn = c_player.get_orient()
                    
                    right_alignment = (threat_dir[0] * orn[0][0] + threat_dir[1] * orn[0][1])
                    alignment = [(1-right_alignment)/2, (1+right_alignment)/2]
                    volume_mult = getVolumeAtDistance(d)
                    threat_volume[0] += volume_mult * alignment[0]
                    threat_volume[1] += volume_mult * alignment[1]

                # door1 (there can be multiple!!)
                elif source.door1:
                    d = dist(c_player.get_pos(), source.get_pos())
                    door1_dir = [source.get_pos()[0] - c_player.get_pos()[0], source.get_pos()[1] - c_player.get_pos()[1]]
                    door1_dir[0] = door1_dir[0]/d
                    door1_dir[1] = door1_dir[1]/d

                    orn = c_player.get_orient()
                    
                    right_alignment = (door1_dir[0] * orn[0][0] + door1_dir[1] * orn[0][1])
                    alignment = [(1-right_alignment)/2, (1+right_alignment)/2]
                    volume_mult = getVolumeAtDistance(d)
                    door1_volume[0] += volume_mult * alignment[0]
                    door1_volume[1] += volume_mult * alignment[1]

                # door2 (there can be multiple!!)
                elif source.door2:
                    d = dist(c_player.get_pos(), source.get_pos())
                    door2_dir = [source.get_pos()[0] - c_player.get_pos()[0], source.get_pos()[1] - c_player.get_pos()[1]]
                    door2_dir[0] = door2_dir[0]/d
                    door2_dir[1] = door2_dir[1]/d

                    orn = c_player.get_orient()
                    
                    right_alignment = (door2_dir[0] * orn[0][0] + door2_dir[1] * orn[0][1])
                    alignment = [(1-right_alignment)/2, (1+right_alignment)/2]
                    volume_mult = getVolumeAtDistance(d)
                    door2_volume[0] += volume_mult * alignment[0]
                    door2_volume[1] += volume_mult * alignment[1]

                # door3 (there can be multiple!!)
                elif source.door3:
                    d = dist(c_player.get_pos(), source.get_pos())
                    door3_dir = [source.get_pos()[0] - c_player.get_pos()[0], source.get_pos()[1] - c_player.get_pos()[1]]
                    door3_dir[0] = door3_dir[0]/d
                    door3_dir[1] = door3_dir[1]/d

                    orn = c_player.get_orient()
                    
                    right_alignment = (door3_dir[0] * orn[0][0] + door3_dir[1] * orn[0][1])
                    alignment = [(1-right_alignment)/2, (1+right_alignment)/2]
                    volume_mult = getVolumeAtDistance(d)
                    door3_volume[0] += volume_mult * alignment[0]
                    door3_volume[1] += volume_mult * alignment[1]

                # key1
                elif source.key1:
                    d = dist(c_player.get_pos(), source.get_pos())
                    key1_dir = [source.get_pos()[0] - c_player.get_pos()[0], source.get_pos()[1] - c_player.get_pos()[1]]
                    key1_dir[0] = key1_dir[0]/d
                    key1_dir[1] = key1_dir[1]/d

                    orn = c_player.get_orient()
                    
                    right_alignment = (key1_dir[0] * orn[0][0] + key1_dir[1] * orn[0][1])
                    alignment = [(1-right_alignment)/2, (1+right_alignment)/2]
                    volume_mult = getVolumeAtDistance(d)
                    key1_volume = [volume_mult * alignment[0], volume_mult * alignment[1]]

                # key2
                elif source.key2:
                    d = dist(c_player.get_pos(), source.get_pos())
                    key2_dir = [source.get_pos()[0] - c_player.get_pos()[0], source.get_pos()[1] - c_player.get_pos()[1]]
                    key2_dir[0] = key2_dir[0]/d
                    key2_dir[1] = key2_dir[1]/d

                    orn = c_player.get_orient()
                    
                    right_alignment = (key2_dir[0] * orn[0][0] + key2_dir[1] * orn[0][1])
                    alignment = [(1-right_alignment)/2, (1+right_alignment)/2]
                    volume_mult = getVolumeAtDistance(d)
                    key2_volume = [volume_mult * alignment[0], volume_mult * alignment[1]]

                # key3
                elif source.key3:
                    d = dist(c_player.get_pos(), source.get_pos())
                    key3_dir = [source.get_pos()[0] - c_player.get_pos()[0], source.get_pos()[1] - c_player.get_pos()[1]]
                    key3_dir[0] = key3_dir[0]/d
                    key3_dir[1] = key3_dir[1]/d

                    orn = c_player.get_orient()
                    
                    right_alignment = (key3_dir[0] * orn[0][0] + key3_dir[1] * orn[0][1])
                    alignment = [(1-right_alignment)/2, (1+right_alignment)/2]
                    volume_mult = getVolumeAtDistance(d)
                    key3_volume = [volume_mult * alignment[0], volume_mult * alignment[1]]

                # end
                elif source.end:
                    d = dist(c_player.get_pos(), source.get_pos())
                    end_dir = [source.get_pos()[0] - c_player.get_pos()[0], source.get_pos()[1] - c_player.get_pos()[1]]
                    end_dir[0] = end_dir[0]/d
                    end_dir[1] = end_dir[1]/d

                    orn = c_player.get_orient()
                    
                    right_alignment = (end_dir[0] * orn[0][0] + end_dir[1] * orn[0][1])
                    alignment = [(1-right_alignment)/2, (1+right_alignment)/2]
                    volume_mult = getVolumeAtDistance(d)
                    end_volume = [volume_mult * alignment[0], volume_mult * alignment[1]]

            # normalize wall sound       
            if wall_volume[0] > 1:
                wall_volume[1] = 1/wall_volume[0]
                wall_volume[0] = 1
            elif wall_volume[1] > 1:
                wall_volume[0] = 1/wall_volume[1]
                wall_volume[1] = 1

            # normalize threat sound      
            if threat_volume[0] > 1:
                threat_volume[1] = 1/threat_volume[0]
                threat_volume[0] = 1
            elif threat_volume[1] > 1:
                threat_volume[0] = 1/threat_volume[1]
                threat_volume[1] = 1

            # normalize door1 sound
            if door1_volume[0] > 1:
                door1_volume[1] = 1/door1_volume[0]
                door1_volume[0] = 1
            elif door1_volume[1] > 1:
                door1_volume[0] = 1/door1_volume[1]
                door1_volume[1] = 1

            # normalize door2 sound
            if door2_volume[0] > 1:
                door2_volume[1] = 1/door2_volume[0]
                door2_volume[0] = 1
            elif door2_volume[1] > 1:
                door2_volume[0] = 1/door2_volume[1]
                door2_volume[1] = 1

            # normalize door3 sound
            if door3_volume[0] > 1:
                door3_volume[1] = 1/door3_volume[0]
                door3_volume[0] = 1
            elif door3_volume[1] > 1:
                door3_volume[0] = 1/door3_volume[1]
                door3_volume[1] = 1
                
            # now, actually play the sounds
            if wall_volume[0] or wall_volume[1]:
                if not getChannelBusy(3):
                    playSfx("wall_chime", 3)

                setChannelVolume(3, wall_volume[0], wall_volume[1])
            elif getChannelBusy(3):
                stopChannel(3)

            if threat_volume[0] or threat_volume[1]:
                if not getChannelBusy(2):
                    playSfx("evil", 2)

                setChannelVolume(2, threat_volume[0], threat_volume[1])
            elif getChannelBusy(2):
                stopChannel(2)

            if end_volume[0] or end_volume[1]:
                if not getChannelBusy(1):
                    playSfx("gate", 1)

                setChannelVolume(1, end_volume[0], end_volume[1])
            elif getChannelBusy(1):
                stopChannel(1)

            if door1_volume[0] or door1_volume[1]:
                if not getChannelBusy(7):
                    playSfx("door1", 7)

                setChannelVolume(7, door1_volume[0], door1_volume[1])
            elif getChannelBusy(7):
                stopChannel(7)

            if door2_volume[0] or door2_volume[1]:
                if not getChannelBusy(8):
                    playSfx("door2", 8)

                setChannelVolume(8, door2_volume[0], door2_volume[1])
            elif getChannelBusy(8):
                stopChannel(8)

            if door3_volume[0] or door3_volume[1]:
                if not getChannelBusy(9):
                    playSfx("door3", 9)

                setChannelVolume(9, door3_volume[0], door3_volume[1])
            elif getChannelBusy(9):
                stopChannel(9)

            if key1_volume[0] or key1_volume[1]:
                if not getChannelBusy(4):
                    playSfx("key1", 4)

                setChannelVolume(4, key1_volume[0], key1_volume[1])
            elif getChannelBusy(4):
                stopChannel(4)

            if key2_volume[0] or key2_volume[1]:
                if not getChannelBusy(5):
                    playSfx("key2", 5)

                setChannelVolume(5, key2_volume[0], key2_volume[1])
            elif getChannelBusy(5):
                stopChannel(5)

            if key3_volume[0] or key3_volume[1]:
                if not getChannelBusy(6):
                    playSfx("key3", 6)

                setChannelVolume(6, key3_volume[0], key3_volume[1])
            elif getChannelBusy(6):
                stopChannel(6)

            # make sure we have a consistent update rate
            cycle_dt = time.perf_counter() - cycle_start

            if delta_t > cycle_dt:
                time.sleep(delta_t - cycle_dt)

            if end_flag:
                print("CONGRATS!", c_map.get_name(), "completed!")
                time.sleep(3)
                return 1

        return 0
                
    ## --- END OF play_map() ---
                
    e1_maps = load_episode(ep_name)
    number_of_maps = len(e1_maps)

    i = 0
    
    while i < number_of_maps:
        success = play_map(e1_maps[i][1], difficulty)
        if success:
            i += 1
        else:
            pass

    print("END OF EPISODE.")
    time.sleep(5)

def init():
    init_sound()
    difficulty = int(input("Select difficulty (1 or 2):"))
    play_episode("E1", difficulty)

init()
