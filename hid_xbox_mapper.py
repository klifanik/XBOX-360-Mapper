import tkinter as tk
from tkinter import ttk, messagebox
import threading, time, json, os
import pygame
import vgamepad as vg

POLL = 0.01           # частота опроса в главном цикле (применение к виртуальному пэду)
CALIB_POLL = 0.02      # частота опроса во время калибровки (снижена, чтобы не тормозило UI/перетаскивание окна)
ASSIGN_WINDOW = 5      # сколько секунд ждём ввод при назначении одной кнопки/оси
AXIS_THRESHOLD = 0.5   # порог для цифрового режима осей: |значение| < порога → 0, иначе ±1

AXES = ['LX','LY','RX','RY','LT','RT']
BUTTONS = ['A','B','X','Y','LB','RB','BACK','START','LS','RS','UP','DOWN','LEFT','RIGHT']
VBUTTON = {n:getattr(vg.XUSB_BUTTON,'XUSB_GAMEPAD_'+({'A':'A','B':'B','X':'X','Y':'Y','LB':'LEFT_SHOULDER','RB':'RIGHT_SHOULDER','BACK':'BACK','START':'START','LS':'LEFT_THUMB','RS':'RIGHT_THUMB','UP':'DPAD_UP','DOWN':'DPAD_DOWN','LEFT':'DPAD_LEFT','RIGHT':'DPAD_RIGHT'}[n])) for n in BUTTONS}

TRANSLATIONS = {
    'ru': {
        'title': 'HID → Xbox 360 Mapper',
        'stop': 'Остановить',
        'start': 'Запустить',
        'test_input': 'Тест ввода',
        'calib_all': 'Калибровка всех выходов',
        'clear_all': 'Очистить всё',
        'save': 'Сохранить',
        'load': 'Загрузить',
        'digital_axes': 'Оси только 0/±1 (цифровой режим)',
        'outputs_title': 'Выходы виртуального Xbox 360',
        'assign': 'Назначить',
        'clear': 'Очистить',
        'invert': 'Инверт',
        'error': 'Ошибка',
        'no_ctrl': 'Контроллер не найден',
        'calib_done': 'Калибровка завершена',
        'all_cleared': 'Все назначения очищены',
        'virt_created': 'Виртуальный Xbox 360: создан',
        'virt_not_created': 'Виртуальный Xbox 360 НЕ создан: ',
        'running': 'Работа запущена',
        'stopped': 'Работа остановлена (виртуальный геймпад обнулён)',
        'assigning': 'Назначение',
        'move_press': 'двигай/нажми нужный элемент',
        'skipped': 'пропущено',
        'no_input': 'ввода нет',
        'saved_to': 'Сохранено в controller_mapping.json',
        'done': 'Готово',
        'no_file': 'controller_mapping.json не найден',
        'cfg_loaded': 'Конфигурация загружена',
        'test_title': 'Тест захвата ввода',
        'device': 'Устройство',
        'axes': 'Оси',
        'axis': 'Ось',
        'buttons': 'Кнопки',
        'button': 'Кнопка',
        'pressed': 'НАЖАТА',
        'hats': 'Хэты (D-Pad)',
        'hat': 'Хэт',
        'lang_btn': 'English',
        'none': '—'
    },
    'en': {
        'title': 'HID → Xbox 360 Mapper',
        'stop': 'Stop',
        'start': 'Start',
        'test_input': 'Input Test',
        'calib_all': 'Calibrate All',
        'clear_all': 'Clear All',
        'save': 'Save',
        'load': 'Load',
        'digital_axes': 'Axes only 0/±1 (Digital Mode)',
        'outputs_title': 'Virtual Xbox 360 Outputs',
        'assign': 'Assign',
        'clear': 'Clear',
        'invert': 'Invert',
        'error': 'Error',
        'no_ctrl': 'Controller not found',
        'calib_done': 'Calibration complete',
        'all_cleared': 'All bindings cleared',
        'virt_created': 'Virtual Xbox 360: created',
        'virt_not_created': 'Virtual Xbox 360 NOT created: ',
        'running': 'Running',
        'stopped': 'Stopped (virtual gamepad reset)',
        'assigning': 'Assigning',
        'move_press': 'move/press the element',
        'skipped': 'skipped',
        'no_input': 'no input',
        'saved_to': 'Saved to controller_mapping.json',
        'done': 'Done',
        'no_file': 'controller_mapping.json not found',
        'cfg_loaded': 'Configuration loaded',
        'test_title': 'Input Capture Test',
        'device': 'Device',
        'axes': 'Axes',
        'axis': 'Axis',
        'buttons': 'Buttons',
        'button': 'Button',
        'pressed': 'PRESSED',
        'hats': 'Hats (D-Pad)',
        'hat': 'Hat',
        'lang_btn': 'Русский',
        'none': '—'
    }
}

pygame.init(); pygame.joystick.init()

def init_joysticks():
    out=[]
    for i in range(pygame.joystick.get_count()):
        try:
            j=pygame.joystick.Joystick(i); j.init(); out.append(j)
        except Exception as e:
            print(f"Failed to init joystick {i}: {e}")
    return out

def load_lang():
    if os.path.exists('settings.json'):
        try:
            data = json.load(open('settings.json', encoding='utf-8'))
            lang = data.get('lang', 'ru')
            if lang in TRANSLATIONS: return lang
        except: pass
    return 'ru'

def save_lang(lang):
    try:
        json.dump({'lang': lang}, open('settings.json', 'w', encoding='utf-8'))
    except Exception as e:
        print(f"Failed to save language: {e}")

class App:
    def __init__(self, root):
        self.root=root; self.root.geometry('900x700')
        self.lang = load_lang()
        self.js=init_joysticks(); self.mapping={}; self.calibrating=False; self.running=True
        self.active=True
        self.digital_axes=tk.BooleanVar(value=True)
        self.invert={n:tk.BooleanVar(value=False) for n in AXES}
        try:
            self.pad=vg.VX360Gamepad(); self.virtual=True
        except Exception as e:
            self.pad=None; self.virtual=False; self.verror=str(e)
        self.status=tk.StringVar(value='')
        self.count=tk.StringVar(value='')
        self._ui(); self.refresh_status(); self.root.after(10,self.loop)

    def switch_lang(self):
        self.lang = 'en' if self.lang == 'ru' else 'ru'
        save_lang(self.lang)
        for widget in self.root.winfo_children():
            widget.destroy()
        self._ui()
        self.refresh_status()
        self.refresh()
        t = TRANSLATIONS[self.lang]
        self.status.set(t['running'] if self.active else t['stopped'])

    def _ui(self):
        t = TRANSLATIONS[self.lang]
        self.root.title(t['title'])
        
        top=ttk.Frame(self.root,padding=10); top.pack(side='top',fill='x')
        ttk.Label(top,text=t['title'],font=('Segoe UI',18,'bold')).pack(side='left')
        
        ttk.Button(top, text=t['lang_btn'], command=self.switch_lang).pack(side='right', padx=10)
        
        self.device=ttk.Combobox(top,state='readonly',width=35,values=[f'[{i}] {j.get_name()}' for i,j in enumerate(self.js)])
        if self.js:self.device.current(0)
        self.device.pack(side='right')
        ttk.Label(self.root,textvariable=self.status,padding=(10,0)).pack(side='top',anchor='w')

        row=ttk.Frame(self.root,padding=(10,0,10,10)); row.pack(side='bottom',fill='x')
        self.active_btn=ttk.Button(row,text=t['stop'] if self.active else t['start'],command=self.toggle_active)
        self.active_btn.pack(side='left',padx=(0,5))
        ttk.Button(row,text=t['test_input'],command=self.open_test).pack(side='left',padx=5)
        ttk.Button(row,text=t['calib_all'],command=self.calibrate_all).pack(side='left',padx=5)
        ttk.Button(row,text=t['clear_all'],command=self.clear).pack(side='left',padx=5)
        ttk.Button(row,text=t['save'],command=self.save).pack(side='left',padx=5)
        ttk.Button(row,text=t['load'],command=self.load).pack(side='left',padx=5)
        ttk.Checkbutton(row,text=t['digital_axes'],variable=self.digital_axes).pack(side='left',padx=10)

        bot=ttk.Frame(self.root,padding=(10,0,10,0)); bot.pack(side='bottom',fill='x')
        ttk.Label(bot,textvariable=self.count,font=('Segoe UI',13,'bold')).pack(anchor='w')

        box=ttk.Frame(self.root); box.pack(side='top',fill='both',expand=True,padx=10,pady=10)
        self.canvas=tk.Canvas(box,highlightthickness=0); sb=ttk.Scrollbar(box,orient='vertical',command=self.canvas.yview); self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side='right',fill='y'); self.canvas.pack(side='left',fill='both',expand=True)
        self.inner=ttk.Frame(self.canvas); self.win=self.canvas.create_window((0,0),window=self.inner,anchor='nw')
        self.inner.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>',lambda e:self.canvas.itemconfigure(self.win,width=e.width))
        self.canvas.bind_all('<MouseWheel>',lambda e:self.canvas.yview_scroll(-int(e.delta/120),'units'))
        self.canvas.bind_all('<Button-4>',lambda e:self.canvas.yview_scroll(-3,'units')); self.canvas.bind_all('<Button-5>',lambda e:self.canvas.yview_scroll(3,'units'))
        ttk.Label(self.inner,text=t['outputs_title'],font=('Segoe UI',14,'bold')).pack(anchor='w',pady=(5,10))
        self.vars={}
        for typ,names in [('AXIS',AXES),('BUTTON',BUTTONS)]:
            ttk.Label(self.inner,text=typ,font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(8,3))
            for n in names:
                r=ttk.Frame(self.inner); r.pack(fill='x',pady=2)
                ttk.Label(r,text=n,width=9).pack(side='left')
                v=tk.StringVar(value=t['none']); self.vars[(typ,n)]=v
                ttk.Label(r,textvariable=v,width=28).pack(side='left')
                ttk.Button(r,text=t['assign'],command=lambda ty=typ,na=n:self.assign(ty,na)).pack(side='left',padx=5)
                ttk.Button(r,text=t['clear'],command=lambda ty=typ,na=n:self.remove_output(ty,na)).pack(side='left')
                if typ=='AXIS':
                    ttk.Checkbutton(r,text=t['invert'],variable=self.invert[n]).pack(side='left',padx=8)
        self.refresh()

    def refresh_status(self):
        t = TRANSLATIONS[self.lang]
        if self.virtual:self.status.set(f"HID: {len(self.js)} | {t['virt_created']}")
        else:self.status.set(t['virt_not_created']+self.verror)

    def toggle_active(self):
        t = TRANSLATIONS[self.lang]
        self.active=not self.active
        self.active_btn.config(text=t['stop'] if self.active else t['start'])
        if not self.active and self.pad:
            try:self.pad.reset(); self.pad.update()
            except:pass
        self.status.set(t['running'] if self.active else t['stopped'])

    def joy(self):
        if not self.js:return None
        i=self.device.current(); return self.js[i if i>=0 else 0]

    def state(self):
        pygame.event.pump(); j=self.joy()
        if not j:return ([],[],[])
        return ([j.get_axis(i) for i in range(j.get_numaxes())],[j.get_button(i) for i in range(j.get_numbuttons())],[j.get_hat(i) for i in range(j.get_numhats())])

    def detect(self,a,b):
        aa,ab,ah=a; ba,bb,bh=b
        for i,(x,y) in enumerate(zip(ab,bb)):
            if x!=y and y:return ('button',i),f'BUTTON {i}'
        for i,(x,y) in enumerate(zip(ah,bh)):
            if x!=y and y!=(0,0):
                dx,dy=y; d='UP' if dy>0 else 'DOWN' if dy<0 else 'LEFT' if dx<0 else 'RIGHT'; return ('hat',i,d),f'HAT {i} {d}'
        for i,(x,y) in enumerate(zip(aa,ba)):
            if abs(y-x)>=.35:
                sign='POS' if y>0 else 'NEG'
                return ('axis',i,sign),f'AXIS {i} ({y:+.2f})'
        return None

    def wait_for_trigger(self,label,seconds=ASSIGN_WINDOW,poll=CALIB_POLL):
        before=self.state(); end=time.monotonic()+seconds; shown=None
        while time.monotonic()<end:
            remaining=end-time.monotonic()
            s=max(1,int(remaining)+1)
            if s!=shown:
                self.root.after(0,self.count.set,f'{label} — {s}')
                shown=s
            now=self.state(); d=self.detect(before,now)
            if d:return d
            time.sleep(poll)
        return None

    def normalize_key(self,key,target_typ):
        if key[0]=='axis' and target_typ=='AXIS':
            return (key[0],key[1])
        return key

    def assign(self,typ,name):
        if self.calibrating:return
        t = TRANSLATIONS[self.lang]
        if not self.js:return messagebox.showerror(t['error'], t['no_ctrl'])
        self.calibrating=True
        def worker():
            try:
                d=self.wait_for_trigger(f"{t['assigning']} {typ} {name}: {t['move_press']}")
                if d:
                    key,label=d; key=self.normalize_key(key,typ); self.remove_output(key=key)
                    self.mapping.setdefault(key,[]).append((typ,name)); self.root.after(0,self.refresh)
                    self.root.after(0,self.status.set,f'{label} → {typ} {name}')
                else:self.root.after(0,self.status.set,f"{typ} {name}: {t['skipped']} — {t['no_input']}")
            finally:self.calibrating=False; self.root.after(0,self.count.set,'')
        threading.Thread(target=worker,daemon=True).start()

    def calibrate_all(self):
        if self.calibrating:return
        t = TRANSLATIONS[self.lang]
        self.calibrating=True
        targets=[('AXIS',x) for x in AXES]+[('BUTTON',x) for x in BUTTONS]
        def worker():
            try:
                for typ,name in targets:
                    d=self.wait_for_trigger(f"{typ} {name}: {t['move_press']}")
                    if d:
                        key,label=d; key=self.normalize_key(key,typ); self.remove_output(typ=typ,name=name)
                        self.mapping.setdefault(key,[]).append((typ,name)); self.root.after(0,self.refresh)
                        self.root.after(0,self.status.set,f'{label} → {typ} {name}')
                    else:self.root.after(0,self.status.set,f"{typ} {name}: {t['skipped']}")
                    time.sleep(.15)
                self.root.after(0,self.count.set,t['calib_done'])
            finally:self.calibrating=False
        threading.Thread(target=worker,daemon=True).start()

    def remove_output(self,typ=None,name=None,key=None):
        if key is not None and typ is None and name is None:
            if key in self.mapping:del self.mapping[key]
            self.refresh(); return
        for k in list(self.mapping):
            if key is not None and k!=key:continue
            self.mapping[k]=[o for o in self.mapping[k] if o!=(typ,name)]
            if not self.mapping[k]:del self.mapping[k]
        self.refresh()

    def clear(self):
        t = TRANSLATIONS[self.lang]
        self.mapping.clear();self.refresh();self.status.set(t['all_cleared'])

    def keytext(self,k):return f'{k[0]}:{k[1]}'+(f':{k[2]}' if len(k)>2 else '')
    
    def refresh(self):
        t = TRANSLATIONS[self.lang]
        rev={}
        for k,outs in self.mapping.items():
            for o in outs:rev[o]=self.keytext(k)
        for o,v in self.vars.items():
            # Если словарь vars перестроился при смене языка, ключа может не быть, но мы защищены .get
            v.set(rev.get(o, t['none']))

    def loop(self):
        if not self.running:return
        if self.virtual and not self.calibrating and self.active:
            try:self.apply(*self.state())
            except Exception as e:
                t = TRANSLATIONS[self.lang]
                self.status.set(f"{t['error']}: {str(e)}")
        self.root.after(10,self.loop)

    def apply(self,axes,buttons,hats):
        if not self.pad:return
        self.pad.reset()
        digital=self.digital_axes.get()
        axis_contrib={n:[] for n in AXES}; btnvals={n:False for n in BUTTONS}
        for k,outs in self.mapping.items():
            val=0.; pressed=False
            if k[0]=='axis' and k[1]<len(axes):
                raw=float(axes[k[1]])
                if len(k)==3:
                    sign=k[2]
                    pressed=(raw>=AXIS_THRESHOLD) if sign=='POS' else (raw<=-AXIS_THRESHOLD)
                    val=1.0 if pressed else 0.0
                else:
                    pressed=abs(raw)>.5
                    if digital:
                        val=0.0 if abs(raw)<AXIS_THRESHOLD else (1.0 if raw>0 else -1.0)
                    else:
                        val=raw
            elif k[0]=='button' and k[1]<len(buttons):
                pressed=bool(buttons[k[1]]); val=1.0 if pressed else 0.
            elif k[0]=='hat' and k[1]<len(hats):
                x,y=hats[k[1]]
                pressed=(k[2]=='UP' and y>0) or (k[2]=='DOWN' and y<0) or (k[2]=='LEFT' and x<0) or (k[2]=='RIGHT' and x>0)
                sign=-1.0 if k[2] in ('LEFT','UP') else 1.0
                val=sign if pressed else 0.
            for typ,n in outs:
                if typ=='AXIS':axis_contrib[n].append(val)
                else:btnvals[n]=btnvals[n] or pressed
        axisvals={n:(max(vs,key=abs) if vs else 0.0) for n,vs in axis_contrib.items()}
        for n in AXES:
            if self.invert[n].get():axisvals[n]=-axisvals[n]
        self.pad.left_joystick_float(axisvals['LX'],axisvals['LY']); self.pad.right_joystick_float(axisvals['RX'],axisvals['RY'])
        self.pad.left_trigger_float(max(0,min(1,axisvals['LT']))); self.pad.right_trigger_float(max(0,min(1,axisvals['RT'])))
        for n,p in btnvals.items():
            if p:self.pad.press_button(button=VBUTTON[n])
            else:self.pad.release_button(button=VBUTTON[n])
        self.pad.update()

    def open_test(self):
        t = TRANSLATIONS[self.lang]
        if not self.js:return messagebox.showerror(t['error'], t['no_ctrl'])
        j=self.joy()
        win=tk.Toplevel(self.root); win.title(t['test_title']); win.geometry('380x560')
        frm=ttk.Frame(win,padding=10); frm.pack(fill='both',expand=True)
        ttk.Label(frm,text=f"{t['device']}: {j.get_name()}",font=('Segoe UI',10,'bold')).pack(anchor='w',pady=(0,8))

        axes_box=ttk.LabelFrame(frm,text=t['axes']); axes_box.pack(fill='x',pady=4)
        axis_vars=[]
        for i in range(j.get_numaxes()):
            r=ttk.Frame(axes_box); r.pack(fill='x')
            ttk.Label(r,text=f"{t['axis']} {i}",width=10).pack(side='left')
            v=tk.StringVar(value='0.00'); axis_vars.append(v)
            ttk.Label(r,textvariable=v,width=10).pack(side='left')

        btn_box=ttk.LabelFrame(frm,text=t['buttons']); btn_box.pack(fill='both',expand=True,pady=4)
        btn_canvas=tk.Canvas(btn_box,highlightthickness=0); bsb=ttk.Scrollbar(btn_box,orient='vertical',command=btn_canvas.yview)
        btn_canvas.configure(yscrollcommand=bsb.set); bsb.pack(side='right',fill='y'); btn_canvas.pack(side='left',fill='both',expand=True)
        btn_inner=ttk.Frame(btn_canvas); bwin=btn_canvas.create_window((0,0),window=btn_inner,anchor='nw')
        btn_inner.bind('<Configure>',lambda e:btn_canvas.configure(scrollregion=btn_canvas.bbox('all')))
        btn_labels=[]
        for i in range(j.get_numbuttons()):
            r=ttk.Frame(btn_inner); r.pack(fill='x')
            ttk.Label(r,text=f"{t['button']} {i}",width=12).pack(side='left')
            lbl=ttk.Label(r,text=t['none'],width=10); lbl.pack(side='left')
            btn_labels.append(lbl)

        hat_box=ttk.LabelFrame(frm,text=t['hats']); hat_box.pack(fill='x',pady=4)
        hat_vars=[]
        for i in range(j.get_numhats()):
            r=ttk.Frame(hat_box); r.pack(fill='x')
            ttk.Label(r,text=f"{t['hat']} {i}",width=10).pack(side='left')
            v=tk.StringVar(value='(0, 0)'); hat_vars.append(v)
            ttk.Label(r,textvariable=v,width=10).pack(side='left')

        state={'on':True}
        def close():
            state['on']=False; win.destroy()
        win.protocol('WM_DELETE_WINDOW',close)

        def update():
            if not state['on']:return
            try:
                pygame.event.pump()
                for i,v in enumerate(axis_vars):v.set(f'{j.get_axis(i):+.2f}')
                for i,lbl in enumerate(btn_labels):
                    pressed=j.get_button(i)
                    lbl.config(text=t['pressed'] if pressed else t['none'],foreground='#1a8a1a' if pressed else 'black')
                for i,v in enumerate(hat_vars):v.set(str(j.get_hat(i)))
            except Exception as e:
                print(f"Update test error: {e}")
            win.after(50,update)
        update()

    def save(self):
        t = TRANSLATIONS[self.lang]
        data={self.keytext(k):v for k,v in self.mapping.items()}
        with open('controller_mapping.json','w',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
        messagebox.showinfo(t['done'], t['saved_to'])

    def load(self):
        t = TRANSLATIONS[self.lang]
        if not os.path.exists('controller_mapping.json'):return messagebox.showinfo(t['error'], t['no_file'])
        try:
            raw=json.load(open('controller_mapping.json',encoding='utf-8')); m={}
            for s,outs in raw.items():
                p=s.split(':'); k=(p[0],int(p[1])) if len(p)==2 else (p[0],int(p[1]),p[2]); m[k]=[tuple(x) for x in outs]
            self.mapping=m; self.refresh(); self.status.set(t['cfg_loaded'])
        except Exception as e:messagebox.showerror(t['error'],str(e))

    def close(self):
        self.running=False
        try:
            if self.pad:self.pad.reset();self.pad.update()
        except:pass
        pygame.quit();self.root.destroy()

if __name__ == '__main__':
    root=tk.Tk(); app=App(root); root.protocol('WM_DELETE_WINDOW',app.close); root.mainloop()