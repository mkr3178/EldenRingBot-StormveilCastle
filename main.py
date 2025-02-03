import time
from datetime import datetime
import mss
import win32api, win32con
import keyboard
from pynput import keyboard as pyn
import numpy as np
import cv2
import logging
from logging.handlers import RotatingFileHandler
import os


class ElapsedFilter(logging.Filter): # inspired from the following post: https://stackoverflow.com/questions/25194864/python-logging-time-since-start-of-program
    def __init__(self):
        self.start_time = time.time()

    def filter(self, record):
        elapsed_seconds = record.created - self.start_time
        cm_seconds = int((round(elapsed_seconds, 2)*100)%100)
        centi_seconds = ""
        if cm_seconds != 0:
            centi_seconds = f".{cm_seconds}"
        elapsed = (f"{int(elapsed_seconds//3600)}h {int((elapsed_seconds//60)%60)}m {int((elapsed_seconds%60)//1)}"
                   f"{centi_seconds}s")
        record.elapsed = elapsed
        return True


log_dir = "Log"
os.makedirs(log_dir, exist_ok=True)



f = ElapsedFilter()
logging.basicConfig(level=logging.ERROR,
                    format="%(name)s, %(levelname)s: %(message)s | %(elapsed)s",
                    datefmt='%m/%d/%Y %H:%M:%S')


info_logger = logging.getLogger("Infos")
info_logger.addFilter(f)
info_logger.setLevel(logging.DEBUG)
Info_handler = RotatingFileHandler('Log\\Debug.log', maxBytes=20000000, backupCount=3)
Info_formatter = logging.Formatter('%(asctime)s, Elapsed time:%(elapsed)s | %(levelname)s: %(message)s', datefmt='%m/%d/%Y %H:%M:%S')
Info_handler.setFormatter(Info_formatter)
info_logger.addHandler(Info_handler)
info_logger.propagate = False # To see it on the console set boolean to true


warning_logger = logging.getLogger("Warnings")
warning_logger.addFilter(f)
warning_logger.setLevel(logging.DEBUG)
Warning_handler = RotatingFileHandler('Log\\Debug.log', maxBytes=20000000, backupCount=3)
Warning_formatter = logging.Formatter('%(levelname)s: %(message)s | Time running: %(elapsed)s | %(asctime)s', datefmt='%m/%d/%Y %H:%M:%S')
Warning_handler.setFormatter(Warning_formatter)
warning_logger.addHandler(Warning_handler)
warning_logger.propagate = False # To see it on the console set boolean to true

keys_clicked = logging.getLogger("Press record")
keys_clicked.addFilter(f)
keys_clicked.setLevel(logging.DEBUG)
Keys_clicked_handler = RotatingFileHandler('Log\\Keyboard_Inputs.log', maxBytes=2000000, backupCount=3)
Keys_clicked_formatter = logging.Formatter('%(asctime)s | Time running: %(elapsed)s | %(message)s')
Keys_clicked_handler.setFormatter(Keys_clicked_formatter)
keys_clicked.addHandler(Keys_clicked_handler)
keys_clicked.propagate = False # To see it on the console set boolean to true


def press_key(s):
    keyboard.press(s)
    time.sleep(0.2)
    keyboard.release(s)
    time.sleep(0.2)


def Check_surroundings_pics(png, confidence = 0.8, custom_prompt = "") -> bool: # 99% of this function was made by ChatGPT
    # Load the template image
    new_png = f"Templates\\{png}"
    template = cv2.imread(new_png, cv2.IMREAD_UNCHANGED)

    # Capture the screen
    with mss.mss() as sct:
        screenshot = np.array(sct.grab(sct.monitors[1]))  # Capture full screen

    # Convert screenshot to grayscale (better for matching)
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    # Match template (TM_CCOEFF_NORMED is the best method)
    result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    # Confidence threshold (adjust based on testing)
    if max_val > confidence:
        # print(f"Found at: {max_loc}")  # x, y position of the match
        info_logger.debug(f"Confidence val accepted {round(max_val, 4)} {custom_prompt}")
        return True
    else:
        info_logger.debug(f"Confidence val denied {round(max_val, 4)} {custom_prompt}")
        return False


def press_key_win32(s):
    win32api.keybd_event(s, 0, 0, 0)
    time.sleep(0.3)
    win32api.keybd_event(s, 0, win32con.KEYEVENTF_KEYUP, 0)

def mouse_click_left(t = 0.2):
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)  # Left button down
    time.sleep(t)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)  # Left button up
    time.sleep(0.2)

def attack_end_stamina(a = 6):
    for i in range(a):
        mouse_click_left()
        time.sleep(0.6)
    info_logger.debug(f"Attacked {a} times")

def right_click(t = 0.3):
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)  # Left button down
    time.sleep(t)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)  # Left button up

def check_fp_bar() -> bool: # 99% of this function was made by ChatGPT
    with mss.mss() as sct:
        fp_region = {"left": 310, "top": 131, "width": 200, "height": 20}  # Adjust coordinates
        screenshot = sct.grab(fp_region)
        img = np.array(screenshot)
        mss.tools.to_png(screenshot.rgb, screenshot.size, output="region_screenshot.png")
        blue_pixels = np.count_nonzero(img[:, :, 2] > 150)  # Count blue pixels
        info_logger.debug(f"Check fp found {blue_pixels} blue pixels on the screen")
        return blue_pixels > 100  # If low, return False

def take_screenshot(subdirectory = "Screenshots", filename ="", custom_prompt =""):
    with mss.mss() as sct:
        now = datetime.now()
        formatted = now.strftime("%H-%M-%S")
        texted = f"{subdirectory}\\{filename}{formatted}.png"
        sct.shot(output=texted)
        info_logger.debug(f"Screenshot {custom_prompt}")

def teleport(time_start = 0, repetitions = 0):
    ts = time.time()
    rep = repetitions
    if time_start != 0:
        ts = time_start
    info_logger.debug("Teleporting")
    press_key('g')
    press_key('f')
    press_key('e')
    if not Check_surroundings_pics("TemplateMap.png", custom_prompt="Map finding"):
        warning_logger.warning("Enemy did not die")
        if not Check_surroundings_pics("Sample_Lock-in.png", confidence=0.95, custom_prompt="Locked in"):
            press_key('q')
            if Check_surroundings_pics("Sample_Lock-in.png", confidence=0.95, custom_prompt="Locked in"):
                if not check_fp_bar():
                    regain_mana()
            attack_end_stamina()
            rep += 1
            if ts-time.time() > 10:
                warning_logger.error(f"Same process repeated {rep} times for {round(ts-time.time(), 2)}s")
            teleport(ts, rep)
        else:
            if Check_surroundings_pics("TemplateWrongLockIn.png", confidence=0.6, custom_prompt="Wrong guy locked in"):
                info_logger.info("Locked-in on the wrong enemy")
                press_key('q')
                time.sleep(0.3)
                press_key('q')
            if not check_fp_bar():
                regain_mana()
            attack_end_stamina()
            time.sleep(1)
            rep += 1
            if ts-time.time() > 10:
                warning_logger.error(f"Same process repeated {rep} times for {round(ts-time.time(), 2)}s")
            teleport(ts, rep)
    else:
        info_logger.debug(f"Teleporting finished in {round(time.time()-ts, 2)}s")
        press_key('e')


def walk_forward(t):
    keyboard.press('w')
    time.sleep(t)
    keyboard.release('w')


def backward_move(t):
    keyboard.press('s')
    time.sleep(t)
    keyboard.release('s')


def move_left(t):
    keyboard.press('a')
    time.sleep(t)
    keyboard.release('a')

def move_right(t):
    keyboard.press('d')
    time.sleep(t)
    keyboard.release('d')

def move_mouse(d = 0, y = 0):
    win32api.mouse_event(0x0001, d, y, 0, 0)  # MOUSEEVENTF_MOVE


def regain_mana():
    press_key('r')
    time.sleep(2.5)
    info_logger.info('potion refilled')


def pressed(key):
    try:
        keys_clicked.debug(f"pressed {key.char}")
    except AttributeError:
        keys_clicked.debug(f"Special key {key} pressed")


def Released(key):
    global Quit_
    if key == pyn.Key.shift:
        info_logger.debug("Quitting")
        Quit_ = True

def backward_left_relative():
    start_mov = time.time()
    info_logger.debug("backward-left Move")
    move_left(.2)
    keyboard.press('s')
    time.sleep(3)
    if not Check_surroundings_pics("TemplateMoveLeft.png", custom_prompt="Left Movement"):
        move_left(.2)
    time.sleep(1)
    while (not Check_surroundings_pics("TemplateMoveBack.png", confidence=.55, custom_prompt="Back Movement")
           or not Check_surroundings_pics("TemplateBackM.png", confidence=.55, custom_prompt="Torch BM")):
        time.sleep(0.1)
    keyboard.release('s')
    info_logger.debug(f"Moved back for {round(time.time()-start_mov, 2)}s")


keyboard_listener = pyn.Listener(on_press=pressed, on_release=Released)
keyboard_listener.start()
Quit_ = False
CountLoops = 0
sum_time = float(0)
x, y = win32api.GetCursorPos()
info_logger.debug(f"Lets start the show x:{x} y:{y}")
win32api.SetCursorPos((10, 10))
mouse_click_left()
time.sleep(3)


while not Quit_:
    start_loop = time.time()
    teleport()
    time.sleep(4)
    while not Check_surroundings_pics("templateLSCut.png", custom_prompt="Loaded Screen"):
        time.sleep(0.5)
    time.sleep(1)
    walk_forward(2.5)
    move_mouse(-1200, 0)
    time.sleep(0.5)
    press_key('q')
    walk_forward(5)
    attack_end_stamina()
    backward_left_relative()
    attack_end_stamina()
    time.sleep(2.83)
    attack_end_stamina()
    regain_mana()
    time.sleep(20.6)
    if Check_surroundings_pics("TemplateSuccessBf(2).png", custom_prompt="Look Down"):
        move_mouse(-75, 150)
    attack_end_stamina()
    time.sleep(1)
    sum_time += (time.time()-start_loop)
    CountLoops += 1
    info_logger.debug(f"Run no.{CountLoops}, Loop-time: {round(time.time()-start_loop, 2)}s")

info_logger.info(f"Runes Earned: {CountLoops*1210} this session\nLooped {CountLoops} times"
      f"\nAverage time per loop: {round(sum_time/CountLoops, 2)}s")
