import asyncio, aiohttp
from tkinter import *

__author__ = 'Alan Baumgartner'

def get_proxies():
    proxies = entrybox_box.get(0.0, END)
    proxies = proxies.strip()
    proxies = proxies.split('\n')
    return proxies

def save_proxies():
    #Saves available usernames
    proxies = outputbox_box.get(0.0, END)
    proxies = proxies.strip()
    outputfile = save_entry.get()
    with open(outputfile, "a") as a:
        a.write(proxies)

def update(proxy):
    try:
        outputbox_box.insert(END, proxy+'\n')
        master.update()
        outputbox_box.see(END)
    except Exception:
        pass

async def check_proxies(proxy, orginal_ip, session, sem):
    try:
        async with sem, session.get(URL, proxy=proxy, timeout=3) as resp:
            response = (await resp.read()).decode()
            if response != orginal_ip:
                update(proxy)
    except Exception:
        pass

async def main(conns=50):
    global tasks
    sem = asyncio.BoundedSemaphore(conns)
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as resp:
            orginal_ip = (await resp.read()).decode()
            proxies = get_proxies()
            tasks = [check_proxies(proxy, orginal_ip, session, sem) for proxy in proxies]
            await asyncio.gather(*tasks) 

def start():
    try:
        outputbox_box.delete(0.0, END)
        loop.run_until_complete(main())
    except:
        pass

def stop():
    try:
        tasks.cancel()
    except:
        pass

if __name__ == '__main__':
    URL = 'http://check-host.net/ip'
    loop = asyncio.get_event_loop()

    master = Tk()
    master.wm_title('Proxy Checker')

    entrybox_label = Label(master, text='Proxies to Check')
    outputbox_label = Label(master, text='Working Proxies')
    entrybox_box = Text(master, width=30, height=20, borderwidth=5, relief=SUNKEN, highlightthickness=0)
    outputbox_box = Text(master, width=30, height=20, borderwidth=5, relief=SUNKEN, highlightthickness=0)
    start_button = Button(master, text='Start', command=lambda: start(), width=15, highlightthickness=0)
    stop_button = Button(master, text='Stop', command=lambda: stop(), width=15, highlightthickness=0)
    save_entry = Entry(master, justify='center', width=17, highlightthickness=0)
    save_button = Button(master, text='Save', command=lambda: save_proxies(), width=15, highlightthickness=0)

    save_entry.insert(0, 'filename.txt')

    entrybox_label.grid(row=0,column=0, padx=(10, 5), pady=(10,5))
    outputbox_label.grid(row=0,column=1, padx=(5, 10), pady=(10,5))
    entrybox_box.grid(row=1,column=0, padx=(10, 5), pady=(0,10))
    outputbox_box.grid(row=1,column=1, padx=(5, 10), pady=(0,10))
    start_button.grid(row=2, column=0, pady=(0,10))
    stop_button.grid(row=3, column=0, pady=(0,10))
    save_entry.grid(row=2, column=1, pady=(0,10))
    save_button.grid(row=3, column=1, pady=(0,10))

    mainloop()