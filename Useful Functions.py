from win32com.client import Dispatch
from winreg import *


def create_shortcut(path, target='', w_dir='', icon=''):
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = w_dir
    if icon == '':
        pass
    else:
        shortcut.IconLocation = icon
    shortcut.save()
    return

# create_shortcut(r'D:/test.lnk', r'C:\IT Spider\IT_Spider.exe', r'C:\IT Spider', r'C:\IT Spider\IT_Spider.exe')

reg_dic = {'hkxx': HKEY_LOCAL_MACHINE, 'reg_key': r'SYSTEM\CurrentControlSet\Control\test', 'key_child': 'child_test',
           'value': 'this-is-a-test', 'child_type': REG_SZ}


def reg_write(hkxx, reg_path, reg_key, value):
    hk = 0
    if hkxx.lower() == "hklm":
        hk = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
    elif hkxx.lower() == "khlu":
        hk = ConnectRegistry(None, HKEY_CURRENT_USER)
    key = OpenKey(hk, reg_path)
    SetValueEx(key, "Start Page", 0, REG_SZ, value)
    CloseKey(key)
    return


def reg_read(hkxx, reg_path, reg_key):
    hk = 0
    if hkxx.lower() == "hklm":
        hk = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
    elif hkxx.lower() == "khlu":
        hk = ConnectRegistry(None, HKEY_CURRENT_USER)
    key = OpenKey(hk, reg_path, KEY_READ)
    value = QueryValueEx(key, reg_key)[0]
    return value


'''
#  start same function multiple times
with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
    executor.map(download_file, links)
'''


print(reg_read('HKLM', r'HARDWARE\DESCRIPTION\System\BIOS', 'BaseBoardProduct'))
