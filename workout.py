#!/usr/bin/env python3

import argparse
import math
import random
import sys

import numpy as np
import pygame as pg
#from pygame.compat import unicode_
#import locale


LEG_MOVES = ["squats", "lunges"]
AB_MOVES = ["crunches", "flutter kicks", "bicycle kicks", "leg lifts", "side leg lifts", "scissors", "v-up"]
BACK_MOVES = ["swimmer", "plank", "side plank*"]
ARM_MOVES = ["push ups", "dips", "diamond push ups", "archer push ups", "wide push ups", "pike push ups"]
KILLER_MOVES = ["burpees", "mountain climbers", "jumping lunges", "side squats", "pistol squats"]
MOVES = {
    "leg": LEG_MOVES,
    "ab": AB_MOVES,
    "back": BACK_MOVES,
    "arm": ARM_MOVES,
    "killer": KILLER_MOVES,
}
ALL_MOVES = LEG_MOVES + AB_MOVES + BACK_MOVES + ARM_MOVES + KILLER_MOVES

INTENSITY = {
    "test":   {"on": 10, "off": 5,  "sets": 2, "reps": 2},
    "baby":   {"on": 20, "off": 20, "sets": 3, "reps": 5},  # 11 minutes
    "easy":   {"on": 20, "off": 20, "sets": 3, "reps": 7},  # 15 minutes
    "medium": {"on": 30, "off": 20, "sets": 4, "reps": 8},  # 29 minutes
    "hard":   {"on": 40, "off": 15, "sets": 5, "reps": 9},  # 45 minutes
    "insane": {"on": 50, "off": 15, "sets": 5, "reps": 10}, # 60 minutes
}

COLOR_START = (0,   192, 0)
COLOR_MID   = (255, 192, 0)
COLOR_END   = (192, 0,   0)
COLOR_REST  = (0,   0,   192)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0,   0,   0)

QUIT_EVENTS = [pg.QUIT, pg.KEYDOWN, pg.MOUSEBUTTONDOWN]


def _fg_color(bg_color):
    return COLOR_WHITE if bg_color[0] + bg_color[1] + bg_color[2] <= 382 else COLOR_BLACK


def _generate_workout_set(settings, args):
    keys = list(MOVES.keys())

    # Random generation based on relative frequency
    #freq = np.array([args.__getattribute__(k) for k in keys])
    #prob = freq / np.sum(freq)
    #move_types = list(np.random.choice(keys, settings["reps"], p=prob))

    # Non-random generation based on relative frequency.
    items = [[k, args.__getattribute__(k)] for k in keys]
    items.sort(key=lambda i: i[1], reverse=True)
    move_types = []
    while len(move_types) < settings["reps"]:
        count = items[0][1]
        for i,k in enumerate(keys):
            if items[i][1] == count:
                move_types.append(items[i][0])
                items[i][1] -= 1
            else:
                continue
    move_types = move_types[:settings["reps"]]

    # From the types, randomly generate the moves.
    move_type_count = {k:move_types.count(k) for k in keys}
    workout_set = []
    for k,c in move_type_count.items():
        if c == 0:
            continue
        workout_set.extend(list(np.random.choice(MOVES[k], c, replace=False)))
    random.shuffle(workout_set)
    return workout_set


def _init_display(res=None):
    if res is None:
        res = (1400, 800)
    # Initialize display.
    pg.init()
    screen = pg.display.set_mode(res)

    pg.time.set_timer(pg.USEREVENT, 100)
    return screen


def _render_centered(screen, font, text, yoff, bg=COLOR_WHITE):
    ren = font.render(text, 0, _fg_color(bg), bg)
    size = font.size(text)
    screen.blit(ren, ((screen.get_width() - size[0]) // 2, yoff))
    yoff += size[1]
    return yoff

def _introduce_workout(screen, workout_set, settings):
    screen.fill(COLOR_WHITE)
    yoff = 10
    workout_text = ""

    # Load font
    lg_font = pg.font.Font(None, 100)
    sm_font = pg.font.Font(None, 70)

    #yoff = _render_centered(screen, font, "this workout is:", yoff)
    #yoff = _render_centered(screen, font, "", yoff)

    text = "{} on x {} off x {} sets".format(
        settings["on"],
        settings["off"],
        settings["sets"],
    )
    yoff = _render_centered(screen, lg_font, text, yoff)
    yoff = _render_centered(screen, lg_font, "", yoff)
    workout_text += text + "\n"

    for w in workout_set:
        yoff = _render_centered(screen, sm_font, w, yoff)
        workout_text += w + "\n"

    total_duration = (
        settings["on"] * (settings["reps"] + 1) + settings["off"] * settings["reps"]
    ) * settings["sets"]
    total_duration_min = total_duration // 60
    total_duration_sec = total_duration - (total_duration_min * 60)
    duration_text = "duration: {}:{:02d}".format(
        total_duration_min, total_duration_sec,
    )
    yoff = _render_centered(
        screen, sm_font, duration_text, yoff,
    )
    workout_text += duration_text + "\n"

    yoff = _render_centered(screen, lg_font, "", yoff)
    yoff = _render_centered(screen, lg_font, "press a key to start!", yoff)

    pg.display.flip()
    return workout_text


def _wait_for_user():
    while 1:
        # use event.wait to keep from polling 100% cpu
        if pg.event.wait().type in QUIT_EVENTS:
            break

def _countdown(
    screen, duration, this_text, init_color=COLOR_BLACK,
    half_time=None, half_color=None, next_text=None, other_text=None,
):
    if half_color is None:
        half_color = init_color

    if half_time is None:
        half_time = 0.5

    if isinstance(half_time, float):
        assert half_time < 1.0
        assert half_time > 0.0
        half_time = duration * half_time

    if other_text is None:
        other_text = ""

    med_font = pg.font.Font(None, 200)
    sm_font = pg.font.Font(None, 60)
    lg_font = pg.font.Font(None, 550)

    round_up = True
    def _countdown_text(time):
        if round_up:
            text = "{:.0f}".format(math.ceil(time))
        else:
            text = "{:.1f}".format(time)
        return text

    countdown_time = duration
    paused = False
    while countdown_time > 0:
        if countdown_time <= half_time:
            bg = half_color
        else:
            bg = init_color
        screen.fill(bg)
        #fg = _fg_color(bg)

        yoff = 10
        yoff = _render_centered(screen, sm_font, other_text, yoff, bg)
        yoff += 50
        yoff = _render_centered(screen, med_font, this_text, yoff, bg)
        yoff += 20
        timer_text = _countdown_text(countdown_time)
        yoff = _render_centered(screen, lg_font, timer_text, yoff, bg)
        if paused:
            yoff = _render_centered(screen, sm_font, "<PAUSED>", yoff, bg)
        yoff += 20
        if next_text is not None:
            yoff = _render_centered(screen, sm_font, "next: {}".format(next_text), yoff, bg)
        pg.display.flip()

        while 1:
            event = pg.event.wait()
            if event.type in QUIT_EVENTS:
                if event.type == pg.KEYDOWN and event.key == ord(" "):
                    paused = not paused
                else:
                    return False
            elif event.type == pg.USEREVENT:
                break

        if not paused:
            countdown_time -= 0.1

    return True

def _finish(screen):
    screen.fill(COLOR_WHITE)
    yoff = 200

    lg_font = pg.font.Font(None, 300)

    yoff = _render_centered(screen, lg_font, "all done!", yoff)
    yoff = _render_centered(screen, lg_font, "nice job!", yoff)

    pg.display.flip()

def _do_workout(workout_set, settings, print_only=False):
    screen = _init_display()
    workout_text = _introduce_workout(screen, workout_set, settings)
    print(workout_text)
    if print_only:
        return

    _wait_for_user()
    cont = _countdown(screen, 10, "get ready!", half_time=5, half_color=COLOR_END, next_text=workout_set[0])
    if not cont:
        return
    for i in range(settings["sets"]):
        set_count = i + 1
        for j, (move, next_move) in enumerate(zip(workout_set, workout_set[1:] + ["break"])):
            move_count = j + 1
            status_text = "set {}/{} | rep {}/{}".format(
                set_count, settings["sets"],
                move_count, len(workout_set),
            )
            print("{} | {}".format(status_text, move))
            next_text = "rest" if j < len(workout_set) - 1 else "break"
            cont = _countdown(
                screen,
                settings["on"],
                move,
                init_color=COLOR_START,
                half_color=COLOR_MID,
                next_text=next_text,
                other_text=status_text,
            )
            if not cont:
                return
            if next_text == "rest":
                cont = _countdown(
                    screen,
                    settings["off"],
                    "rest",
                    init_color=COLOR_REST,
                    half_time=5,
                    half_color=COLOR_END,
                    next_text=next_move,
                    other_text=status_text,
                )
                if not cont:
                    return
        if set_count < settings["sets"]:
            cont = _countdown(
                screen,
                settings["on"] + settings["off"],
                "break",
                init_color=COLOR_REST,
                half_color=COLOR_END,
                next_text=workout_set[0],
                other_text=status_text,
            )
            if not cont:
                return

    _finish(screen)
    _wait_for_user()


def main(args):
    intensity_settings = INTENSITY[args.level]
    intensity_settings["on"] = args.on if args.on is not None else intensity_settings["on"]
    intensity_settings["off"] = args.off if args.off is not None else intensity_settings["off"]
    intensity_settings["sets"] = args.sets if args.sets is not None else intensity_settings["sets"]
    intensity_settings["reps"] = args.reps if args.reps is not None else intensity_settings["reps"]
    workout_set = _generate_workout_set(intensity_settings, args)
    _do_workout(workout_set, intensity_settings, args.print_only)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l", "--level",
        choices=list(INTENSITY.keys()), default="easy",
        help="workout intensity level",
    )
    parser.add_argument(
        "-p", "--print_only",
        action="store_true",
        help="only print the workout, don't actually run it",
    )
    for k in MOVES.keys():
        parser.add_argument(
            "--{}".format(k),
            type=int, default=1,
            help="set the relative frequency of {} moves in the workout".format(k),
        )
    parser.add_argument(
        "--on",
        type=int,
        help="override workout ON time",
    )
    parser.add_argument(
        "--off",
        type=int,
        help="override workout OFF time",
    )
    parser.add_argument(
        "--sets",
        type=int,
        help="override workout SETS count",
    )
    parser.add_argument(
        "--reps",
        type=int,
        help="override workout REPS count",
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = _parse_args()
    main(args)

