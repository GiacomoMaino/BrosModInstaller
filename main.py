import requests
import urllib3
import constants
import os

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from CollapsingFrame import CollapsingFrame
import re
import shutil
import subprocess
import threading
import string
import random
import concurrent.futures
import json
from ttkbootstrap.dialogs.dialogs import Messagebox
from functools import partial

error_flag = False
done_installing = False

def DBG_print_all(to_print: dict):
    for key in to_print.keys():
        if type(to_print[key]) is list:
            for e in to_print(key):
                print(e)
        elif type(to_print[key]) is dict:
            DBG_print_all(to_print[key])
        else:
            print(key + ":" +str(to_print[key]))

def get_files(folder_id):
    global error_flag
    try:
        request = requests.get(f"https://www.googleapis.com/drive/v3/files?q='{folder_id}'+in+parents&key={constants.API_KEY}")

        data = request.json()
        
        return data["files"]
    except KeyError:
        Messagebox.show_error("Impossibile ottenere informazioni da Drive.\nAccedere al link: https://drive.google.com/drive/folders/12XnVYjQ6pT-mKxYSoQ5_1QaiutJnkw0L\nContattare uno sviluppatore. ;)")
        error_flag = True

def get_folders(files:list):
    dirs = {}
    for file in files:
        if file["mimeType"] == "application/vnd.google-apps.folder":
            dirs[file["name"]] = file["id"]

    return dirs

def filter_files(files):
    out = []
    for file in files:
        if not file["mimeType"] == "application/vnd.google-apps.folder":
            out.append(file)

    return out

def get_files_complete(folder_id:str, dir="", to_disable=[], not_to_include=[]):
    temp = get_files(folder_id)

    dirs = get_folders(temp)

    files = {"main": []}
    for file in filter_files(temp):
        enabled = True
        if dir in to_disable:
            enabled = False
        state = True
        if dir in not_to_include:
            state = False
        files["main"].append({"name": file["name"], "id": file["id"], "enabled": enabled, "state":state})

    for dir in dirs.keys():
        files[dir] = get_files_complete(dirs[dir], dir, to_disable, not_to_include)

    return files

def get_IDs_only(files: dict)->list:
    ids = []
    if "id" in files.keys():
        ids.append(files["id"])
    else:
        for key in files.keys():
            if type(files[key]) is list:
                for file in files[key]:
                    ids.extend(get_IDs_only(file))
            elif type(files[key]) is dict:
                ids.extend(get_IDs_only(files[key]))
    return ids

def get_names_only(files: dict)->list:
    names = []
    if "name" in files.keys():
        names.append(files["name"])
    else:
        for key in files.keys():
            if type(files[key]) is list:
                for file in files[key]:
                    names.extend(get_names_only(file))
            elif type(files[key]) is dict:
                if "name" in files[key].keys():
                    names.append(files[key]["name"])
                else:
                    names.extend(get_names_only(files[key]))
    return names

def generate_quota_user():
    pool = string.ascii_lowercase
    pool += string.digits
    user = ''.join(random.choice(pool) for i in range(20))
    return user

def check_if_corrupt(path):
    try:
        with open(path, "r") as file:
            line = file.readline()
            if re.search("<html>", line):
                return True
        return False
    except UnicodeDecodeError:
        return False

def download_file(url, name):
    http = urllib3.PoolManager()
    r = http.request("GET", url, preload_content=False, headers={"X-Goog-Quota-User": generate_quota_user()})
    with open(os.path.join(constants.TEMP_FOLDER, name), 'wb') as out:
        while True:
            data = r.read(16 * 1024)
            if not data:
                break
            out.write(data)
    return name    
    
def download_files_from_IDs(ids: list, names:list, gauge):

    global error_flag
    urls = []
    for i in range(len(ids)):
        urls.append((f"https://www.googleapis.com/drive/v3/files/{ids[i]}?alt=media&key={constants.API_KEY}", names[i]))
    
    done = 0
    with concurrent.futures.ThreadPoolExecutor() as exeutor:
        future_to_url = {exeutor.submit(download_file, url[0], url[1]): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            done += 1
            if check_if_corrupt(os.path.join(constants.TEMP_FOLDER, future.result())):
                error_flag = True
            #gauge.configure(value=done/(len(ids)*2) * 100)

def get_file_from_id(files, id):
    for file in files:
        if file["id"] == id:
            return file


def select_mod(selected:list, id, files):
    if get_file_from_id(files, id) in selected:
        selected.remove(get_file_from_id(files, id))
    else:
        selected.append(get_file_from_id(files, id))

def save_old_mods(file_names):
    prev_mods = [mod for mod in os.listdir(constants.MODS_FOLDER) if re.search(".jar", mod)]
    in_folder =[]
    os.makedirs(os.path.join(constants.MODS_FOLDER, "old"), exist_ok=True)
    for mod in prev_mods:
        if mod not in file_names:
            try:
                os.rename(os.path.join(constants.MODS_FOLDER, mod),os.path.join(constants.MODS_FOLDER, "old", mod))
            except:
                os.remove(os.path.join(constants.MODS_FOLDER, mod))
        else:
            in_folder.append(mod)
    return in_folder

def install(files, gauge):
    to_download = []
    names = []
    for file in files:
        names.append(file["name"])
    already_have = save_old_mods(names)

    already_have = []
    for file in files:
        if os.path.isfile(os.path.join(constants.TEMP_FOLDER, file["name"])) and not check_if_corrupt(os.path.join(constants.TEMP_FOLDER, file["name"])):
            shutil.copy(os.path.join(constants.TEMP_FOLDER, file["name"]), os.path.join(constants.MODS_FOLDER, file["name"]))
            already_have.append(file["name"])
    versions = []
    for version in [version for _, _, version in os.walk(constants.VERSION_FOLDER)]:
        versions.extend(version)
    already_have.extend(version)

    to_download = [file for file in files if file["name"] not in already_have]
    ids = []
    for file in to_download:
        ids.append(file["id"])
    names = []
    for file in to_download:
        names.append(file["name"])

    download_files_from_IDs(ids, names, gauge)

    forge = ""
    threads = []
    for name in names:
        if not re.search("^forge", name) and not check_if_corrupt(os.path.join(constants.TEMP_FOLDER, name)):
            threads.append(threading.Thread(target=lambda: shutil.copy(os.path.join(constants.TEMP_FOLDER, name), os.path.join(constants.MODS_FOLDER, name))))
            threads[-1].start()
    names.extend(already_have)
    for name in names:
        if re.search("^forge", name):
            t = name
            data = t.split("-")
            version_name = ''.join(data[1] + '-' + data[0] + '-' + data[2][:-4])
            version_pattern = ""
            for letter in version_name:
                if letter == ".":
                    version_pattern += "\."
                else:
                    version_pattern += letter
            print(f"{version_pattern}: {[file for file in versions if re.search(version_pattern, file)]}")
            if not len([file for file in versions if re.search(version_pattern, file)]) >0:
                forge = name

    for thread in threads:
        thread.join()
    if forge != "":
        cmd = ["java", "-jar",os.path.join(constants.TEMP_FOLDER, forge)]
        proc = subprocess.call(cmd)
    global done_installing
    done_installing= True

    with open(constants.PROFILES_FILE, "r") as file:
        data = json.load(file)
    profiles = data["profiles"].keys()
    if not "serata-gaming" in profiles:
        data["profiles"]["serata-gaming"] = {
      "javaArgs" : "-Xmx4G -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M",
      "lastUsed" : "2023-08-31T11:17:06.042Z",
      "lastVersionId" : version_name,
      "name" : "Serata Gaming",
      "type" : "custom"
    }
    with open(constants.PROFILES_FILE, "w") as file:
        data = json.dump(data, file)

    pass

def launch_install(files, gauge):
    global done_installing 
    done_installing = False
    gauge.pack(fill='x', expand='yes')
    gauge.start()
    t= threading.Thread(target=lambda: install(files, gauge))
    t.start()

class little_helper():
    def __init__(self):
        self.has_to_run = True
    
    def set_has_to_run(self, value):
        self.has_to_run = value

def app_show(app, files, styles={}):
    widgets = {}
    selected=[]
    sf = ScrolledFrame(app)
    label = ttk.Label(sf, text="SERATA GAMING INSTALLER", style="light", font=("Arial", 25))
    label.pack(side= "top", pady=5, ipadx = 5, expand="yes")
    cf = CollapsingFrame(sf)
    sf.pack(fill='both', expand="yes")
    cf.pack(fill='both')
    selected_id = ""
    for section in files.keys():
        if section in styles:
            style = styles[section]
        else:
            style = "primary"
        if len(files[section]) > 0:
            widgets[section] = ttk.Frame(cf, padding=10)
            if section == "main":
                for file in files[section]:
                    selected_id = file["id"]
                    if file["enabled"]:
                        state = "normal"
                    else:
                        state = "disabled"
                    res = re.findall("[A-Z|a-z| |-|_]*", file["name"])
                    text = [i for i in res if i][0]
                    widgets[file["name"]] = ttk.Checkbutton(widgets[section], text=text, command=lambda: partial(select_mod, selected, selected_id, files[section]["main"]), font=("Arial", 20))
                    widgets[file["name"]].pack(fill='x')
                    if file["state"]:
                        widgets[file["name"]].invoke()
                    else:
                        widgets[file["name"]].invoke()
                        widgets[file["name"]].invoke()
                    widgets[file["name"]]['state'] = state   
            else:
                for file in files[section]["main"]:
                    selected_id = file["id"]
                    if file["enabled"]:
                        state = "normal"
                    else:
                        state = "disabled"
                    res = re.findall("[A-Z|a-z| |-|_]*", file["name"])
                    text = [i for i in res if i][0]
                    widgets[file["name"]] = ttk.Checkbutton(widgets[section], text=text, command=partial(select_mod, selected, selected_id, files[section]["main"]))
                    if file["state"]:
                        widgets[file["name"]].invoke()
                    else:
                        widgets[file["name"]].invoke()
                        widgets[file["name"]].invoke()
                    widgets[file["name"]].pack(fill='x')
                    widgets[file["name"]]['state'] = state
            cf.add(widgets[section], title=section, style=style+'.TButton')
    gauge = ttk.Floodgauge(master = sf, bootstyle="info",font=(None, 24, 'bold'), text="Installazione in corso...")
    widgets["install_button"] = ttk.Button(sf, text="Installa", command=lambda: launch_install(selected, gauge), style="success")
    widgets["install_button"].pack(fill="x")
    has_to_run = True
    global error_flag
    global done_installing
    ltl_helper = little_helper()
    app.protocol("WM_DELETE_WINDOW", lambda: ltl_helper.set_has_to_run(False))
    while has_to_run:
        app.update_idletasks()
        has_to_run = ltl_helper.has_to_run
        if error_flag or done_installing:
            gauge.stop()
            gauge.pack_forget()
        if done_installing:
            Messagebox.ok("Installazione terminata")
            done_installing = False
        if error_flag:
            Messagebox.show_error("Una o più mod si sono corrotte durante il download. \nRiprovare più tardi. \nSe urgente andarea al link: https://drive.google.com/drive/folders/12XnVYjQ6pT-mKxYSoQ5_1QaiutJnkw0L", "File corrotto")
            error_flag = False
        app.update()


    

def main():
    app = ttk.Window("Serata Gaming Mod Installer", themename = "darkly")
    app.geometry("920x1080")
    files = get_files_complete(constants.MAIN_FOLDER, to_disable=["API", "Content", "Optimization"], not_to_include=["Server Only"])
    os.makedirs(constants.TEMP_FOLDER, exist_ok=True)
    os.makedirs(constants.MODS_FOLDER, exist_ok=True)
    #download_files_from_IDs(, )
    app_show(app, files, styles={"API": "warning", "Forge": "light", "Client": "success", "Server Only": "danger", "Content": "primary"})
    


if __name__ == "__main__":
    main()