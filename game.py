import keyboard as kbd
import time

from wad import *
from sound import *

def load_map(map_filename):
    map_full_filename = "maps/" + map_filename + ".wad"

    # load map data
    current_map = read_map(map_full_filename)

    # play map BGM
    playBGM(current_map.get_BGM())

    # initialize player
    playerstart = current_map.get_player_start()
    current_player = player(playerstart[0], playerstart[1])

    return current_map, current_player

def play_map(map_name):
    c_map, c_player = load_map(map_name)
    delta_t = 0.01

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
            cmd_move_x -= 1
        if kbd.is_pressed("a"):
            cmd_move_x += 1

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
            pass

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
        search_radius = 5

        # make sure we have a consistent update rate
        cycle_dt = time.perf_counter() - cycle_start

        if delta_t > cycle_dt:
            time.sleep(delta_t - cycle_dt)

def init():
    init_sound()
    play_map("level1")

init()
