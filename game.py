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

def play_episode(ep_name):

    def play_map(map_name):
        c_map, c_player = load_map(ep_name, map_name)
        delta_t = 0.01
        end_flag = False

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

            elif player_sector.key2:
                c_player.give_key2()
                player_sector.take_key2()

            elif player_sector.key3:
                c_player.give_key3()
                player_sector.take_key3()

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
            search_radius = 3

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
                    
                    # cos(a) = [(xa * xb + ya * yb) / (√(xa2 + ya2) * √(xb2 + yb2))]
                    right_alignment = (threat_dir[0] * orn[0][0] + threat_dir[1] * orn[0][1])
                    # ^^ no need to divide since the magnitudes of orn[0] and wall_dir are both 1
                    alignment = [(1-right_alignment)/2, (1+right_alignment)/2]
                    volume_mult = getVolumeAtDistance(d)
                    threat_volume[0] += volume_mult * alignment[0]
                    threat_volume[1] += volume_mult * alignment[1]

                # end
                elif source.end:
                    d = dist(c_player.get_pos(), source.get_pos())
                    end_dir = [source.get_pos()[0] - c_player.get_pos()[0], source.get_pos()[1] - c_player.get_pos()[1]]
                    end_dir[0] = end_dir[0]/d
                    end_dir[1] = end_dir[1]/d

                    orn = c_player.get_orient()
                    
                    # cos(a) = [(xa * xb + ya * yb) / (√(xa2 + ya2) * √(xb2 + yb2))]
                    right_alignment = (end_dir[0] * orn[0][0] + end_dir[1] * orn[0][1])
                    # ^^ no need to divide since the magnitudes of orn[0] and wall_dir are both 1
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
                
            # now, actually play the sounds
            if wall_volume[0] or wall_volume[1]:
                if not getChannelBusy(3):
                    playSfx("wall_chime", 3)

                setChannelVolume(3, wall_volume[0], wall_volume[1])

            if threat_volume[0] or threat_volume[1]:
                if not getChannelBusy(2):
                    playSfx("evil", 2)

                setChannelVolume(2, threat_volume[0], threat_volume[1])

            if end_volume[0] or end_volume[1]:
                if not getChannelBusy(1):
                    playSfx("gate", 1)

                setChannelVolume(1, end_volume[0], end_volume[1])

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
        success = play_map(e1_maps[i][1])
        if success:
            i += 1
        else:
            pass

    print("END OF EPISODE.")

def init():
    init_sound()
    play_episode("E1")

init()
