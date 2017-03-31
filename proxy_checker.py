import asyncio, aiohttp, sys, threading
from tkinter import *
from tkinter import messagebox, ttk

__author__ = 'Alan Baumgartner'

class App():
    def __init__(self, root):
        master = root
        master.wm_title('Proxy Checker')
        master.resizable(False, False)

        self.entrybox_label = Label(master, text='Proxies to Check')
        self.outputbox_label = Label(master, text='Working Proxies')
        self.entrybox_box = Text(master, width=30, height=20, borderwidth=5, relief=SUNKEN, highlightthickness=0)
        self.outputbox_box = Text(master, width=30, height=20, borderwidth=5, relief=SUNKEN, highlightthickness=0)
        self.start_button = Button(master, text='Start', command=self.start, width=15, highlightthickness=0)
        self.stop_button = Button(master, text='Stop', command=self.stop, width=15, highlightthickness=0)
        self.save_entry = Entry(master, justify='center', width=17, highlightthickness=0)
        self.save_button = Button(master, text='Save', command=self.save_proxies, width=15, highlightthickness=0)

        s = ttk.Style()
        s.theme_use('default')
        s.configure("skin.Horizontal.TProgressbar")#, background='green')
        self.progress = ttk.Progressbar(master, style="skin.Horizontal.TProgressbar", orient="horizontal", mode="determinate", length=450)

        self.save_entry.insert(0, 'filename.txt')

        self.entrybox_label.grid(row=0,column=0, padx=(10, 5), pady=(10,5))
        self.outputbox_label.grid(row=0,column=1, padx=(5, 10), pady=(10,5))
        self.entrybox_box.grid(row=1,column=0, padx=(10, 5), pady=(0,10))
        self.outputbox_box.grid(row=1,column=1, padx=(5, 10), pady=(0,10))
        self.start_button.grid(row=2, column=0, pady=(0,10))
        self.stop_button.grid(row=3, column=0, pady=(0,10))
        self.save_entry.grid(row=2, column=1, pady=(0,10))
        self.save_button.grid(row=3, column=1, pady=(0,10))
        self.progress.grid(row=4,column=0, columnspan=2, pady=(0,10))
        

        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.URL = 'http://check-host.net/ip'
        self.running = False
        self.count = 0
        

    def get_proxies(self):
        proxies = self.entrybox_box.get(0.0, END)
        proxies = proxies.strip()
        proxies = proxies.split('\n')
        return proxies

    def save_proxies(self):
        proxies = self.outputbox_box.get(0.0, END)
        proxies = proxies.strip()
        outputfile = self.save_entry.get()
        with open(outputfile, "a") as a:
            a.write(proxies)

    async def check_proxies(self, proxy, orginal_ip, session, sem, lock):
        async with sem:
            if self.running:
                try:
                    async with session.get(self.URL, proxy=proxy, timeout=3) as resp:
                        response = (await resp.read()).decode()
                        if response != orginal_ip:
                            self.outputbox_box.insert(END, proxy+'\n')
                            self.outputbox_box.see(END)
                            
                except:
                    pass

                finally:
                    with await lock:
                        self.count += 1
                    self.progress['value'] = self.count

    async def main(self):
        sem = asyncio.BoundedSemaphore(50)
        lock = asyncio.Lock()
        async with aiohttp.ClientSession() as session:
            async with session.get(self.URL) as resp:
                orginal_ip = (await resp.read()).decode()
                proxies = self.get_proxies()
                self.progress['maximum'] = len(proxies)
                tasks = [self.check_proxies(proxy, orginal_ip, session, sem, lock) for proxy in proxies]
                await asyncio.gather(*tasks)
                self.running = False

    def start(self):
        if not self.running:
            self.count = 0
            self.progress['value'] = self.count
            self.running = True
            self.startcheck()

    def stop(self):
        self.running = False

    def startcheck(self):
        newthread = threading.Thread(target=self.check)
        newthread.daemon = True
        newthread.start()

    def check(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            self.outputbox_box.delete(0.0, END)
            loop.run_until_complete(self.main())
        finally:
            loop.close()
    
    def on_closing(self):
        if messagebox.askyesno("Quit", "Are you sure you want to quit?"):
            sys.exit()

if __name__ == '__main__':
    root = Tk()
    app = App(root)
    root.mainloop()