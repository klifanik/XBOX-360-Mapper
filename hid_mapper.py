import tkinter as tk
from tkinter import ttk, messagebox
import threading, time, json, os
import pygame
import vgamepad as vg

POLL = 0.01           # main-loop poll rate (applying to the virtual pad)
CALIB_POLL = 0.02      # poll rate during calibration (lowered so UI/window dragging stays smooth)
ASSIGN_WINDOW = 5      # seconds to wait for input when assigning one button/axis
AXIS_THRESHOLD = 0.5   # threshold for digital axis mode: |value| < threshold -> 0, else +-1

# ---------------------------------------------------------------------------
# Virtual controller profiles. Each profile describes the outputs shown in the
# UI (axes/buttons) and how to translate them into calls on the underlying
# vgamepad object. Axis order is always [LX, LY, RX, RY, left-trigger, right-trigger]
# regardless of the profile, so generic code can address them by position.
# ---------------------------------------------------------------------------
PROFILES = {
    'xbox360': {
        'display': 'Xbox 360',
        'axes': ['LX', 'LY', 'RX', 'RY', 'LT', 'RT'],
        'buttons': ['A', 'B', 'X', 'Y', 'LB', 'RB', 'BACK', 'START', 'LS', 'RS', 'UP', 'DOWN', 'LEFT', 'RIGHT'],
        'has_special_dpad': False,
        'button_enum': {
            'A': vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            'B': vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            'X': vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            'Y': vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            'LB': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            'RB': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
            'BACK': vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
            'START': vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            'LS': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
            'RS': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
            'UP': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
            'DOWN': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
            'LEFT': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
            'RIGHT': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
        },
        'special_enum': {},
        'make_pad': lambda: vg.VX360Gamepad(),
    },
    'ds4': {
        'display': 'DualShock 4',
        'axes': ['LX', 'LY', 'RX', 'RY', 'L2', 'R2'],
        'buttons': ['CROSS', 'CIRCLE', 'SQUARE', 'TRIANGLE', 'L1', 'R1', 'L3', 'R3',
                    'SHARE', 'OPTIONS', 'PS', 'TOUCHPAD', 'UP', 'DOWN', 'LEFT', 'RIGHT'],
        'has_special_dpad': True,   # DS4 reports the D-pad as one 8-way value, not 4 separate bits
        'button_enum': {
            'CROSS': vg.DS4_BUTTONS.DS4_BUTTON_CROSS,
            'CIRCLE': vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE,
            'SQUARE': vg.DS4_BUTTONS.DS4_BUTTON_SQUARE,
            'TRIANGLE': vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE,
            'L1': vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT,
            'R1': vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT,
            'L3': vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT,
            'R3': vg.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT,
            'SHARE': vg.DS4_BUTTONS.DS4_BUTTON_SHARE,
            'OPTIONS': vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS,
        },
        'special_enum': {
            'PS': vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS,
            'TOUCHPAD': vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD,
        },
        'dpad_map': {
            (True, False, False, False): vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH,
            (False, True, False, False): vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH,
            (False, False, True, False): vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST,
            (False, False, False, True): vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST,
            (True, False, False, True): vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHEAST,
            (True, False, True, False): vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST,
            (False, True, False, True): vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHEAST,
            (False, True, True, False): vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHWEST,
        },
        'dpad_none': vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE,
        'make_pad': lambda: vg.VDS4Gamepad(),
    },
}
PROFILE_ORDER = ['xbox360', 'ds4']   # order shown in the dropdown

# ---------------------------------------------------------------------------
# UI translations. The console/terminal stays English regardless (see the
# .bat launcher files) - this dict only affects text drawn inside the window.
# ---------------------------------------------------------------------------
STRINGS = {
    'ru': {
        'app_title': 'HID → Xbox 360 Mapper',
        'lang_label': 'Язык',
        'controller_label': 'Виртуальный джойстик',
        'status_virtual_created': 'HID: {n} | Виртуальный {device}: создан',
        'status_virtual_failed': 'Виртуальный {device} НЕ создан: {err}',
        'outputs_header': 'Выходы виртуального джойстика',
        'axis_section': 'ОСИ',
        'button_section': 'КНОПКИ',
        'assign_btn': 'Назначить',
        'clear_btn': 'Очистить',
        'invert_check': 'Инверт',
        'stop_btn': 'Остановить',
        'start_btn': 'Запустить',
        'test_btn': 'Тест ввода',
        'calibrate_btn': 'Калибровка всех выходов',
        'clear_all_btn': 'Очистить всё',
        'save_btn': 'Сохранить',
        'load_btn': 'Загрузить',
        'digital_check': 'Оси только 0/±1 (цифровой режим)',
        'active_started': 'Работа запущена',
        'active_stopped': 'Работа остановлена (виртуальный геймпад обнулён)',
        'assign_prompt': 'Назначение {typ} {name}: двигай/нажми нужный элемент',
        'calib_prompt': '{typ} {name}: двигай/нажми нужный элемент',
        'assigned_status': '{label} → {typ} {name}',
        'skipped_no_input': '{typ} {name}: пропущено — ввода нет',
        'skipped': '{typ} {name}: пропущено',
        'calib_done': 'Калибровка завершена',
        'cleared_all': 'Все назначения очищены',
        'runtime_error': 'Ошибка: {err}',
        'error_title': 'Ошибка',
        'controller_not_found': 'Контроллер не найден',
        'done_title': 'Готово',
        'save_done': 'Сохранено в controller_mapping.json',
        'no_file_title': 'Нет файла',
        'load_missing': 'controller_mapping.json не найден',
        'load_done': 'Конфигурация загружена',
        'confirm_switch_title': 'Смена виртуального джойстика',
        'confirm_switch_msg': 'Это очистит все текущие назначения. Продолжить?',
        'pad_create_error': 'Не удалось создать виртуальный {device}: {err}',
        'test_window_title': 'Тест захвата ввода',
        'test_device_label': 'Устройство: {name}',
        'test_axes_header': 'Оси',
        'test_buttons_header': 'Кнопки',
        'test_hats_header': 'Хэты (D-Pad)',
        'test_axis_row': 'Ось {i}',
        'test_button_row': 'Кнопка {i}',
        'test_hat_row': 'Хэт {i}',
        'test_pressed': 'НАЖАТА',
        'test_not_pressed': '—',
    },
    'en': {
        'app_title': 'HID → Xbox 360 Mapper',
        'lang_label': 'Language',
        'controller_label': 'Virtual gamepad',
        'status_virtual_created': 'HID: {n} | Virtual {device}: created',
        'status_virtual_failed': 'Virtual {device} NOT created: {err}',
        'outputs_header': 'Virtual gamepad outputs',
        'axis_section': 'AXES',
        'button_section': 'BUTTONS',
        'assign_btn': 'Assign',
        'clear_btn': 'Clear',
        'invert_check': 'Invert',
        'stop_btn': 'Stop',
        'start_btn': 'Start',
        'test_btn': 'Input test',
        'calibrate_btn': 'Calibrate all outputs',
        'clear_all_btn': 'Clear all',
        'save_btn': 'Save',
        'load_btn': 'Load',
        'digital_check': 'Axes only 0/±1 (digital mode)',
        'active_started': 'Running',
        'active_stopped': 'Stopped (virtual gamepad reset)',
        'assign_prompt': 'Assigning {typ} {name}: move/press the desired control',
        'calib_prompt': '{typ} {name}: move/press the desired control',
        'assigned_status': '{label} → {typ} {name}',
        'skipped_no_input': '{typ} {name}: skipped — no input',
        'skipped': '{typ} {name}: skipped',
        'calib_done': 'Calibration finished',
        'cleared_all': 'All assignments cleared',
        'runtime_error': 'Error: {err}',
        'error_title': 'Error',
        'controller_not_found': 'Controller not found',
        'done_title': 'Done',
        'save_done': 'Saved to controller_mapping.json',
        'no_file_title': 'No file',
        'load_missing': 'controller_mapping.json not found',
        'load_done': 'Configuration loaded',
        'confirm_switch_title': 'Switch virtual gamepad',
        'confirm_switch_msg': 'This will clear all current assignments. Continue?',
        'pad_create_error': 'Failed to create virtual {device}: {err}',
        'test_window_title': 'Input capture test',
        'test_device_label': 'Device: {name}',
        'test_axes_header': 'Axes',
        'test_buttons_header': 'Buttons',
        'test_hats_header': 'Hats (D-Pad)',
        'test_axis_row': 'Axis {i}',
        'test_button_row': 'Button {i}',
        'test_hat_row': 'Hat {i}',
        'test_pressed': 'PRESSED',
        'test_not_pressed': '—',
    },
}

pygame.init(); pygame.joystick.init()

def init_joysticks():
    out = []
    for i in range(pygame.joystick.get_count()):
        try:
            j = pygame.joystick.Joystick(i); j.init(); out.append(j)
        except: pass
    return out

class App:
    def __init__(self, root):
        self.root = root; self.root.title('HID → Xbox 360 Mapper'); self.root.geometry('980x740')
        self.lang = 'ru'
        self.js = init_joysticks(); self.mapping = {}; self.calibrating = False; self.running = True
        self.active = True   # whether input is currently forwarded to the virtual gamepad (Start/Stop)
        self.digital_axes = tk.BooleanVar(value=True)   # True = axes are only -1/0/1, no in-between values
        self.invert = {}      # per-axis inversion, rebuilt for the active profile
        self._i18n_static = []    # (widget, key) - permanent chrome, never rebuilt
        self._i18n_dynamic = []   # (widget, key) - output rows, rebuilt on profile switch
        self.vars = {}
        self.pad = None; self.virtual = False; self.verror = ''
        self.profile_key = 'xbox360'
        self.status = tk.StringVar(value='')
        self.count = tk.StringVar(value='')
        self._ui()
        self._activate_profile(self.profile_key)
        self.root.after(10, self.loop)

    # ---------------------------------------------------------- translations
    def tr(self, key, **kwargs):
        s = STRINGS[self.lang][key]
        return s.format(**kwargs) if kwargs else s

    def reg(self, widget, key, dynamic=False):
        (self._i18n_dynamic if dynamic else self._i18n_static).append((widget, key))
        widget.config(text=self.tr(key))
        return widget

    def set_language(self, lang):
        if lang not in STRINGS or lang == self.lang: return
        self.lang = lang
        for widget, key in self._i18n_static + self._i18n_dynamic:
            try: widget.config(text=self.tr(key))
            except Exception: pass
        self.refresh_status()

    # ------------------------------------------------------------------- UI
    def _ui(self):
        top = ttk.Frame(self.root, padding=10); top.pack(side='top', fill='x')
        ttk.Label(top, text='HID → Xbox 360 Mapper', font=('Segoe UI', 18, 'bold')).pack(side='left')

        lang_frame = ttk.Frame(top); lang_frame.pack(side='right', padx=(0, 10))
        self.reg(ttk.Label(lang_frame, text=''), 'lang_label').pack(side='left', padx=(0, 5))
        self.lang_combo = ttk.Combobox(lang_frame, state='readonly', width=6, values=['RU', 'EN'])
        self.lang_combo.current(0)
        self.lang_combo.bind('<<ComboboxSelected>>', lambda e: self.set_language('ru' if self.lang_combo.get() == 'RU' else 'en'))
        self.lang_combo.pack(side='left')

        self.device = ttk.Combobox(top, state='readonly', width=30, values=[f'[{i}] {j.get_name()}' for i, j in enumerate(self.js)])
        if self.js: self.device.current(0)
        self.device.pack(side='right', padx=10)

        ctrl_frame = ttk.Frame(top); ctrl_frame.pack(side='right', padx=10)
        self.reg(ttk.Label(ctrl_frame, text=''), 'controller_label').pack(side='left', padx=(0, 5))
        self.profile_combo = ttk.Combobox(ctrl_frame, state='readonly', width=14,
                                           values=[PROFILES[k]['display'] for k in PROFILE_ORDER])
        self.profile_combo.current(PROFILE_ORDER.index(self.profile_key))
        self.profile_combo.bind('<<ComboboxSelected>>', self._on_profile_selected)
        self.profile_combo.pack(side='left')

        ttk.Label(self.root, textvariable=self.status, padding=(10, 0)).pack(side='top', anchor='w')

        # Control panel and counter are pinned to the BOTTOM of the window and
        # packed BEFORE the expanding canvas - so they stay visible always,
        # even if the axis/button list grows too tall to fit.
        row = ttk.Frame(self.root, padding=(10, 0, 10, 10)); row.pack(side='bottom', fill='x')
        self.active_btn = ttk.Button(row, text='', command=self.toggle_active)
        self.reg(self.active_btn, 'stop_btn')
        self.active_btn.pack(side='left', padx=(0, 5))
        self.reg(ttk.Button(row, command=self.open_test), 'test_btn').pack(side='left', padx=5)
        self.reg(ttk.Button(row, command=self.calibrate_all), 'calibrate_btn').pack(side='left', padx=5)
        self.reg(ttk.Button(row, command=self.clear), 'clear_all_btn').pack(side='left', padx=5)
        self.reg(ttk.Button(row, command=self.save), 'save_btn').pack(side='left', padx=5)
        self.reg(ttk.Button(row, command=self.load), 'load_btn').pack(side='left', padx=5)
        self.reg(ttk.Checkbutton(row, variable=self.digital_axes), 'digital_check').pack(side='left', padx=10)

        bot = ttk.Frame(self.root, padding=(10, 0, 10, 0)); bot.pack(side='bottom', fill='x')
        ttk.Label(bot, textvariable=self.count, font=('Segoe UI', 13, 'bold')).pack(anchor='w')

        box = ttk.Frame(self.root); box.pack(side='top', fill='both', expand=True, padx=10, pady=10)
        self.canvas = tk.Canvas(box, highlightthickness=0); sb = ttk.Scrollbar(box, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y'); self.canvas.pack(side='left', fill='both', expand=True)
        self.inner = ttk.Frame(self.canvas); self.win = self.canvas.create_window((0, 0), window=self.inner, anchor='nw')
        self.inner.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfigure(self.win, width=e.width))
        self.canvas.bind_all('<MouseWheel>', lambda e: self.canvas.yview_scroll(-int(e.delta / 120), 'units'))
        self.canvas.bind_all('<Button-4>', lambda e: self.canvas.yview_scroll(-3, 'units'))
        self.canvas.bind_all('<Button-5>', lambda e: self.canvas.yview_scroll(3, 'units'))

    def rebuild_output_rows(self):
        """(Re)builds the AXIS/BUTTON rows in the scrollable list for whichever
        profile (Xbox 360 / DualShock 4) is currently active."""
        for child in self.inner.winfo_children():
            child.destroy()
        self._i18n_dynamic = []
        self.vars = {}
        prof = PROFILES[self.profile_key]
        self.invert = {n: tk.BooleanVar(value=False) for n in prof['axes']}

        self.reg(ttk.Label(self.inner, font=('Segoe UI', 14, 'bold')), 'outputs_header', dynamic=True).pack(anchor='w', pady=(5, 10))
        for typ, names, header_key in [('AXIS', prof['axes'], 'axis_section'), ('BUTTON', prof['buttons'], 'button_section')]:
            self.reg(ttk.Label(self.inner, font=('Segoe UI', 11, 'bold')), header_key, dynamic=True).pack(anchor='w', pady=(8, 3))
            for n in names:
                r = ttk.Frame(self.inner); r.pack(fill='x', pady=2)
                ttk.Label(r, text=n, width=9).pack(side='left')
                v = tk.StringVar(value='—'); self.vars[(typ, n)] = v
                ttk.Label(r, textvariable=v, width=28).pack(side='left')
                self.reg(ttk.Button(r, command=lambda t=typ, n=n: self.assign(t, n)), 'assign_btn', dynamic=True).pack(side='left', padx=5)
                self.reg(ttk.Button(r, command=lambda t=typ, n=n: self.remove_output(t, n)), 'clear_btn', dynamic=True).pack(side='left')
                if typ == 'AXIS':
                    self.reg(ttk.Checkbutton(r, variable=self.invert[n]), 'invert_check', dynamic=True).pack(side='left', padx=8)

    # ------------------------------------------------------------- profiles
    def _on_profile_selected(self, event=None):
        new_key = PROFILE_ORDER[self.profile_combo.current()]
        if new_key == self.profile_key: return
        if self.mapping:
            if not messagebox.askyesno(self.tr('confirm_switch_title'), self.tr('confirm_switch_msg')):
                self.profile_combo.current(PROFILE_ORDER.index(self.profile_key))
                return
        self._activate_profile(new_key)

    def _activate_profile(self, profile_key):
        if self.pad is not None:
            try: self.pad.reset(); self.pad.update()
            except Exception: pass
        self.pad = None
        self.profile_key = profile_key
        self.mapping = {}
        self.profile_combo.current(PROFILE_ORDER.index(profile_key))
        try:
            self.pad = PROFILES[profile_key]['make_pad'](); self.virtual = True; self.verror = ''
        except Exception as e:
            self.pad = None; self.virtual = False; self.verror = str(e)
        self.rebuild_output_rows()
        self.refresh_status()
        self.count.set('')

    def refresh_status(self):
        device = PROFILES[self.profile_key]['display']
        if self.virtual: self.status.set(self.tr('status_virtual_created', n=len(self.js), device=device))
        else: self.status.set(self.tr('status_virtual_failed', device=device, err=self.verror))

    def toggle_active(self):
        self.active = not self.active
        new_key = 'start_btn' if not self.active else 'stop_btn'
        self.active_btn.config(text=self.tr(new_key))
        for i, (w, k) in enumerate(self._i18n_static):
            if w is self.active_btn: self._i18n_static[i] = (w, new_key)
        if not self.active and self.pad:
            try: self.pad.reset(); self.pad.update()
            except: pass
        self.status.set(self.tr('active_started' if self.active else 'active_stopped'))

    # --------------------------------------------------------- joystick I/O
    def joy(self):
        if not self.js: return None
        i = self.device.current(); return self.js[i if i >= 0 else 0]

    def state(self):
        pygame.event.pump(); j = self.joy()
        if not j: return ([], [], [])
        return ([j.get_axis(i) for i in range(j.get_numaxes())],
                [j.get_button(i) for i in range(j.get_numbuttons())],
                [j.get_hat(i) for i in range(j.get_numhats())])

    def detect(self, a, b):
        aa, ab, ah = a; ba, bb, bh = b
        for i, (x, y) in enumerate(zip(ab, bb)):
            if x != y and y: return ('button', i), f'BUTTON {i}'
        for i, (x, y) in enumerate(zip(ah, bh)):
            if x != y and y != (0, 0):
                dx, dy = y; d = 'UP' if dy > 0 else 'DOWN' if dy < 0 else 'LEFT' if dx < 0 else 'RIGHT'
                return ('hat', i, d), f'HAT {i} {d}'
        for i, (x, y) in enumerate(zip(aa, ba)):
            if abs(y - x) >= .35:
                sign = 'POS' if y > 0 else 'NEG'
                return ('axis', i, sign), f'AXIS {i} ({y:+.2f})'
        return None

    def wait_for_trigger(self, label, seconds=ASSIGN_WINDOW, poll=CALIB_POLL):
        """Listens to the joystick for the whole time window and returns the
        result IMMEDIATELY as soon as input is recognized - it does not wait
        for the countdown to finish."""
        before = self.state(); end = time.monotonic() + seconds; shown = None
        while time.monotonic() < end:
            remaining = end - time.monotonic()
            s = max(1, int(remaining) + 1)
            if s != shown:
                self.root.after(0, self.count.set, f'{label} — {s}')
                shown = s
            now = self.state(); d = self.detect(before, now)
            if d: return d
            time.sleep(poll)
        return None

    def normalize_key(self, key, target_typ):
        # If an axis is assigned to a real AXIS output (LX/LY/...), direction is
        # not baked into the key - the axis should work continuously both ways.
        # If an axis is assigned to a BUTTON output (e.g. LEFT/RIGHT as a D-pad),
        # direction stays part of the key - so "stick left" and "stick right"
        # become two distinct physical sources and don't overwrite each other.
        if key[0] == 'axis' and target_typ == 'AXIS':
            return (key[0], key[1])
        return key

    def assign(self, typ, name):
        if self.calibrating: return
        if not self.js: return messagebox.showerror(self.tr('error_title'), self.tr('controller_not_found'))
        self.calibrating = True
        def worker():
            try:
                d = self.wait_for_trigger(self.tr('assign_prompt', typ=typ, name=name))
                if d:
                    key, label = d; key = self.normalize_key(key, typ); self.remove_output(key=key)
                    self.mapping.setdefault(key, []).append((typ, name)); self.root.after(0, self.refresh)
                    self.root.after(0, self.status.set, self.tr('assigned_status', label=label, typ=typ, name=name))
                else:
                    self.root.after(0, self.status.set, self.tr('skipped_no_input', typ=typ, name=name))
            finally:
                self.calibrating = False; self.root.after(0, self.count.set, '')
        threading.Thread(target=worker, daemon=True).start()

    def calibrate_all(self):
        if self.calibrating: return
        self.calibrating = True
        prof = PROFILES[self.profile_key]
        targets = [('AXIS', x) for x in prof['axes']] + [('BUTTON', x) for x in prof['buttons']]
        def worker():
            try:
                for typ, name in targets:
                    d = self.wait_for_trigger(self.tr('calib_prompt', typ=typ, name=name))
                    if d:
                        key, label = d; key = self.normalize_key(key, typ); self.remove_output(typ=typ, name=name)
                        self.mapping.setdefault(key, []).append((typ, name)); self.root.after(0, self.refresh)
                        self.root.after(0, self.status.set, self.tr('assigned_status', label=label, typ=typ, name=name))
                    else:
                        self.root.after(0, self.status.set, self.tr('skipped', typ=typ, name=name))
                    time.sleep(.15)
                self.root.after(0, self.count.set, self.tr('calib_done'))
            finally:
                self.calibrating = False
        threading.Thread(target=worker, daemon=True).start()

    def remove_output(self, typ=None, name=None, key=None):
        if key is not None and typ is None and name is None:
            # Full reset of this physical source (used when (re)assigning):
            # clear ALL of its old bindings, otherwise repeated calibration
            # would stack them up and one physical element (e.g. a D-pad)
            # could end up driving several axes/buttons at once ("breaks").
            if key in self.mapping: del self.mapping[key]
            self.refresh(); return
        for k in list(self.mapping):
            if key is not None and k != key: continue
            self.mapping[k] = [o for o in self.mapping[k] if o != (typ, name)]
            if not self.mapping[k]: del self.mapping[k]
        self.refresh()

    def clear(self):
        self.mapping.clear(); self.refresh(); self.status.set(self.tr('cleared_all'))

    def keytext(self, k):
        return f'{k[0]}:{k[1]}' + (f':{k[2]}' if len(k) > 2 else '')

    def refresh(self):
        rev = {}
        for k, outs in self.mapping.items():
            for o in outs: rev[o] = self.keytext(k)
        for o, v in self.vars.items(): v.set(rev.get(o, '—'))

    def loop(self):
        if not self.running: return
        if self.virtual and not self.calibrating and self.active:
            try: self.apply(*self.state())
            except Exception as e: self.status.set(self.tr('runtime_error', err=str(e)))
        self.root.after(10, self.loop)

    def dpad_direction(self, prof, up, down, left, right):
        if up and down: up = down = False
        if left and right: left = right = False
        return prof['dpad_map'].get((up, down, left, right), prof['dpad_none'])

    def apply(self, axes, buttons, hats):
        if not self.pad: return
        self.pad.reset()
        prof = PROFILES[self.profile_key]
        digital = self.digital_axes.get()
        axis_names = prof['axes']; button_names = prof['buttons']
        # Collect ALL contributions from every physical source per output,
        # rather than just overwriting - so a stick and a D-pad both mapped
        # to the same LX/LY don't mute each other.
        axis_contrib = {n: [] for n in axis_names}; btnvals = {n: False for n in button_names}
        for k, outs in self.mapping.items():
            val = 0.; pressed = False
            if k[0] == 'axis' and k[1] < len(axes):
                raw = float(axes[k[1]])
                if len(k) == 3:
                    # direction-specific binding (axis assigned as a button, e.g.
                    # "stick left" -> DPAD LEFT): pressed state is determined by
                    # sign, so the opposite direction won't trigger this button
                    sign = k[2]
                    pressed = (raw >= AXIS_THRESHOLD) if sign == 'POS' else (raw <= -AXIS_THRESHOLD)
                    val = 1.0 if pressed else 0.0
                else:
                    pressed = abs(raw) > .5
                    if digital:
                        val = 0.0 if abs(raw) < AXIS_THRESHOLD else (1.0 if raw > 0 else -1.0)
                    else:
                        val = raw
            elif k[0] == 'button' and k[1] < len(buttons):
                pressed = bool(buttons[k[1]]); val = 1.0 if pressed else 0.
            elif k[0] == 'hat' and k[1] < len(hats):
                x, y = hats[k[1]]
                pressed = (k[2] == 'UP' and y > 0) or (k[2] == 'DOWN' and y < 0) or (k[2] == 'LEFT' and x < 0) or (k[2] == 'RIGHT' and x > 0)
                # sign: LEFT/UP -> -1, RIGHT/DOWN -> +1 (matches the usual
                # "up = -1, down = +1" convention a stick reports)
                sign = -1.0 if k[2] in ('LEFT', 'UP') else 1.0
                val = sign if pressed else 0.
            for typ, n in outs:
                if typ == 'AXIS': axis_contrib.setdefault(n, []).append(val)
                else: btnvals[n] = btnvals.get(n, False) or pressed
        # if several values arrive for one output (e.g. stick + D-pad), whatever
        # is currently actually "active" wins (largest magnitude)
        axisvals = {n: (max(vs, key=abs) if vs else 0.0) for n, vs in axis_contrib.items()}
        for n in axis_names:
            if self.invert.get(n) and self.invert[n].get(): axisvals[n] = -axisvals[n]

        lx, ly, rx, ry, lt, rt = axis_names
        self.pad.left_joystick_float(axisvals[lx], axisvals[ly])
        self.pad.right_joystick_float(axisvals[rx], axisvals[ry])
        self.pad.left_trigger_float(max(0, min(1, axisvals[lt])))
        self.pad.right_trigger_float(max(0, min(1, axisvals[rt])))

        skip = {'UP', 'DOWN', 'LEFT', 'RIGHT'} if prof['has_special_dpad'] else set()
        for n, p in btnvals.items():
            if n in skip: continue
            if n in prof['special_enum']:
                ev = prof['special_enum'][n]
                (self.pad.press_special_button if p else self.pad.release_special_button)(special_button=ev)
            elif n in prof['button_enum']:
                ev = prof['button_enum'][n]
                (self.pad.press_button if p else self.pad.release_button)(button=ev)
        if prof['has_special_dpad']:
            direction = self.dpad_direction(prof, btnvals.get('UP'), btnvals.get('DOWN'), btnvals.get('LEFT'), btnvals.get('RIGHT'))
            self.pad.directional_pad(direction=direction)
        self.pad.update()

    # -------------------------------------------------------------- testing
    def open_test(self):
        """Live raw joystick data viewer - to check whether the program is
        actually seeing input at all, independent of assignments or the
        currently selected virtual gamepad type."""
        if not self.js: return messagebox.showerror(self.tr('error_title'), self.tr('controller_not_found'))
        j = self.joy()
        win = tk.Toplevel(self.root); win.title(self.tr('test_window_title')); win.geometry('380x560')
        frm = ttk.Frame(win, padding=10); frm.pack(fill='both', expand=True)
        ttk.Label(frm, text=self.tr('test_device_label', name=j.get_name()), font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 8))

        axes_box = ttk.LabelFrame(frm, text=self.tr('test_axes_header')); axes_box.pack(fill='x', pady=4)
        axis_vars = []
        for i in range(j.get_numaxes()):
            r = ttk.Frame(axes_box); r.pack(fill='x')
            ttk.Label(r, text=self.tr('test_axis_row', i=i), width=10).pack(side='left')
            v = tk.StringVar(value='0.00'); axis_vars.append(v)
            ttk.Label(r, textvariable=v, width=10).pack(side='left')

        btn_box = ttk.LabelFrame(frm, text=self.tr('test_buttons_header')); btn_box.pack(fill='both', expand=True, pady=4)
        btn_canvas = tk.Canvas(btn_box, highlightthickness=0); bsb = ttk.Scrollbar(btn_box, orient='vertical', command=btn_canvas.yview)
        btn_canvas.configure(yscrollcommand=bsb.set); bsb.pack(side='right', fill='y'); btn_canvas.pack(side='left', fill='both', expand=True)
        btn_inner = ttk.Frame(btn_canvas); bwin = btn_canvas.create_window((0, 0), window=btn_inner, anchor='nw')
        btn_inner.bind('<Configure>', lambda e: btn_canvas.configure(scrollregion=btn_canvas.bbox('all')))
        btn_labels = []
        for i in range(j.get_numbuttons()):
            r = ttk.Frame(btn_inner); r.pack(fill='x')
            ttk.Label(r, text=self.tr('test_button_row', i=i), width=12).pack(side='left')
            lbl = ttk.Label(r, text='—', width=10); lbl.pack(side='left')
            btn_labels.append(lbl)

        hat_box = ttk.LabelFrame(frm, text=self.tr('test_hats_header')); hat_box.pack(fill='x', pady=4)
        hat_vars = []
        for i in range(j.get_numhats()):
            r = ttk.Frame(hat_box); r.pack(fill='x')
            ttk.Label(r, text=self.tr('test_hat_row', i=i), width=10).pack(side='left')
            v = tk.StringVar(value='(0, 0)'); hat_vars.append(v)
            ttk.Label(r, textvariable=v, width=10).pack(side='left')

        state = {'on': True}
        def close():
            state['on'] = False; win.destroy()
        win.protocol('WM_DELETE_WINDOW', close)

        pressed_text = self.tr('test_pressed'); not_pressed_text = self.tr('test_not_pressed')
        def update():
            if not state['on']: return
            try:
                pygame.event.pump()
                for i, v in enumerate(axis_vars): v.set(f'{j.get_axis(i):+.2f}')
                for i, lbl in enumerate(btn_labels):
                    pressed = j.get_button(i)
                    lbl.config(text=pressed_text if pressed else not_pressed_text, foreground='#1a8a1a' if pressed else 'black')
                for i, v in enumerate(hat_vars): v.set(str(j.get_hat(i)))
            except Exception:
                pass
            win.after(50, update)
        update()

    # ---------------------------------------------------------- persistence
    def save(self):
        data = {self.keytext(k): v for k, v in self.mapping.items()}
        data['_profile'] = self.profile_key
        with open('controller_mapping.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        messagebox.showinfo(self.tr('done_title'), self.tr('save_done'))

    def load(self):
        if not os.path.exists('controller_mapping.json'):
            return messagebox.showinfo(self.tr('no_file_title'), self.tr('load_missing'))
        try:
            raw = json.load(open('controller_mapping.json', encoding='utf-8'))
            saved_profile = raw.pop('_profile', self.profile_key)
            if saved_profile in PROFILES and saved_profile != self.profile_key:
                self._activate_profile(saved_profile)
            m = {}
            for s, outs in raw.items():
                p = s.split(':')
                k = (p[0], int(p[1])) if len(p) == 2 else (p[0], int(p[1]), p[2])
                m[k] = [tuple(x) for x in outs]
            self.mapping = m; self.refresh(); self.status.set(self.tr('load_done'))
        except Exception as e:
            messagebox.showerror(self.tr('error_title'), str(e))

    def close(self):
        self.running = False
        try:
            if self.pad: self.pad.reset(); self.pad.update()
        except: pass
        pygame.quit(); self.root.destroy()

root = tk.Tk(); app = App(root); root.protocol('WM_DELETE_WINDOW', app.close); root.mainloop()