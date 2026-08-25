English

# HID → Xbox 360 Mapper

A minimalist alternative to x360ce: turns any HID joystick/gamepad into a virtual Xbox 360 controller so that games and programs that only understand XInput can see your device.

Works only on **Windows** (uses the [ViGEmBus](https://github.com/ViGEm/ViGEmBus) driver via the [vgamepad](https://pypi.org/project/vgamepad/) library).

## Features

- Assigning any button/axis/hat (D-pad) of a physical joystick to any output of a virtual Xbox 360 (sticks, triggers, buttons, D-pad).
- Quick calibration of one output or all of them at once, one after another.
- Digital axis mode (values only `0`/`±1`) — enabled via a checkbox.
- Direction inversion for each axis separately.
- The ability to assign an analog stick as a digital D‑pad (for example,  “left push” → LEFT button), without conflicting with the normal axis assignment.
- Several physical sources per output (for example, a stick **and**
  the crosspiece is simultaneously controlled by LX/LY) — what is active right now is working.
- The "Input test" button is a live window for viewing raw data from the joystick,
  to check if the program sees the device at all.
- The "Start" button/Stop" — you can pause the transfer to the virtual
gamepad without closing the program.
- Saving/loading the layout in `controller_mapping.json`.

## Installation

1. Download/clone the repository.
2. Run **`install.bat`** — it will install Python itself (if it is not there) and
all dependencies (`pygame`, `vgamepad'). You may need to confirm
   installing the ViGEmBus driver (separate UAC/installer window).
3. If a virtual gamepad is not created after installation, install
   Driver manually: https://github.com/ViGEm/ViGEmBus/releases

## Launch

Just run **`run.bat`**.

## Usage

1. Select your device from the drop‑down list at the top.
2. Click “Assign” next to the desired output (for example, `LX`) and, within
   5 seconds, move/press the corresponding element on the physical joystick —
   The assignment will happen instantly as soon as the program recognizes the signal.
3. Or click “Calibrate all outputs” and go through all the axes and buttons in sequence.
4. “Input test” will show what the program physically sees — useful for diagnostics if the assignment doesn’t work.
5. “Save”/“Load” — so you don’t have to reconfigure the layout every time.

## License

MIT — do whatever you want with the code, see [LICENSE](LICENSE).





Russian

# HID → Xbox 360 Mapper

Минималистичная альтернатива x360ce: превращает любой HID-джойстик/геймпад
в виртуальный контроллер Xbox 360, чтобы игры и программы, которые понимают
только XInput, видели твоё устройство.

Работает только на **Windows** (используется драйвер [ViGEmBus](https://github.com/ViGEm/ViGEmBus)
через библиотеку [vgamepad](https://pypi.org/project/vgamepad/)).

## Возможности

- Назначение любой кнопки/оси/хэта (D-pad) физического джойстика на любой
  выход виртуального Xbox 360 (стики, триггеры, кнопки, D-pad).
- Быстрая калибровка одного выхода или всех сразу по очереди.
- Цифровой режим осей (значения только `0`/`±1`) — включается чекбоксом.
- Инверсия направления для каждой оси отдельно.
- Возможность назначить аналоговый стик как цифровой D-pad (например
  "толчок влево" → кнопка LEFT), без конфликта с обычным назначением оси.
- Несколько физических источников на один выход (например стик **и**
  крестовина одновременно управляют LX/LY) — работает то, что активно прямо сейчас.
- Кнопка «Тест ввода» — окно живого просмотра сырых данных с джойстика,
  чтобы проверить, видит ли программа устройство вообще.
- Кнопка «Старт/Стоп» — можно приостановить передачу в виртуальный
  геймпад, не закрывая программу.
- Сохранение/загрузка раскладки в `controller_mapping.json`.

## Установка

1. Скачай/склонируй репозиторий.
2. Запусти **`install.bat`** — он сам поставит Python (если его нет) и
   все зависимости (`pygame`, `vgamepad`). Может потребоваться подтвердить
   установку драйвера ViGEmBus (отдельное окно UAC/установщика).
3. Если после установки виртуальный геймпад не создаётся — поставь
   драйвер вручную: https://github.com/ViGEm/ViGEmBus/releases

## Запуск

Просто запускай **`run.bat`**.

## Использование

1. Выбери своё устройство в выпадающем списке вверху.
2. Нажми «Назначить» напротив нужного выхода (например `LX`) и в течение
   5 секунд подвигай/нажми соответствующий элемент на физическом джойстике —
   назначение произойдёт мгновенно, как только программа распознает сигнал.
3. Либо нажми «Калибровка всех выходов» и пройди по очереди все оси и кнопки.
4. «Тест ввода» покажет, что физически видит программа — полезно для
   диагностики, если назначение не срабатывает.
5. «Сохранить»/«Загрузить» — чтобы не настраивать раскладку заново каждый раз.

## Лицензия

MIT — делай с кодом что хочешь, см. [LICENSE](LICENSE).
