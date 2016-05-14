from platform import release
from winreg import *
import os
import pywinauto
import subprocess
from time import sleep
from multiprocessing.pool import ThreadPool

_pool = ThreadPool(processes=1)


def percentage(x, y):
    """
    Return x out of y percentage
    :param x: value to be checked
    :param y: value to check against
    :return: integer as percentage
    """
    try:
        perc = (int(x) / int(y)) * 100
        return int(perc)
    except ZeroDivisionError:
        return 'Error'


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
    """
    Read key value from local registry
    :param hkxx: Hive name (HKLM, HKCU)
    :param reg_path: registry key path
    :param reg_key: key value data
    :return: value as string
    """
    try:
        hk = 0
        if hkxx.lower() == "hklm":
            hk = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
        elif hkxx.lower() == "khlu":
            hk = ConnectRegistry(None, HKEY_CURRENT_USER)
        key = OpenKey(hk, reg_path, KEY_READ)
        value = QueryValueEx(key, reg_key)[0]
    except FileNotFoundError:
        return '0'
    return value


def restart(timeout):
    # subprocess.call(['shutdown', '/r', '/t', timeout], shell=True)
    os.system('shutdown /r /t 3')
    return 1


def my_platform():
    return reg_read('HKLM', r'HARDWARE\DESCRIPTION\System\BIOS', 'BaseBoardProduct')


def get_platform():
    """
    Parse motherboard name from registry according to projects
    :return: dictionary {'SKL': 'RVP3', 'KBL': 'Y'}
    """
    replace_words = ['Kabylake', 'Skylake', 'DDR3L', 'LPDDR3L', 'LPDDR3', 'DDR4']
    the_platform = my_platform()
    # the_platform = 'Skylake S RVP8 DDR4'

    if 'RVP' not in the_platform:
        return the_platform

    for rep in replace_words:
        the_platform = the_platform.replace(rep, '')

    the_platform = the_platform.split(' ')
    the_platform_skl = list(filter(None, the_platform))[1]
    the_platform_kbl = list(filter(None, the_platform))[0]

    if the_platform_kbl.upper() == 'HALO':
        the_platform_kbl = 'H'
    elif the_platform_kbl.upper == 'AIO' or the_platform_kbl.upper() == 'DT':
        the_platform_kbl = 'S'

    if the_platform_skl.upper() == 'RVP5':
        the_platform_skl = 'RVP7'
    elif the_platform_skl.upper() == 'RVP9' or the_platform_skl == 'RVP11' or the_platform_skl.upper() == 'RVP16':
        the_platform_skl = 'RVP10'
    elif the_platform_skl == 'RVP15':
        the_platform_skl = 'RVP7'
    return {'SKL': the_platform_skl, 'KBL': the_platform_kbl}


def get_win_ver(packages, project, platform):
    """
    Get windows version
    :param packages: dictionary
    :param project: string
    :param platform: string
    :return: return windows version according to available kits
    """
    available_win_ver = [packages[package]['win_ver'] for package in packages if project in package and platform in package]
    available_win_ver = list(set(available_win_ver))

    my_win_ver = release()
    if my_win_ver == '7':
        my_win_ver = 'win7'
    elif my_win_ver == '8' or my_win_ver == '8.1':
        my_win_ver = 'win8.1'
    elif my_win_ver == '10':
        my_win_ver = 'win10'

    if my_win_ver in available_win_ver:
        return my_win_ver
    elif len(available_win_ver) < 2:
        return available_win_ver[0]
    elif my_win_ver == 'win7':
        if 'win8.1' in available_win_ver:
            return 'win8.1'
        else:
            return 'win10'
    elif my_win_ver == 'win8.1':
        if 'win10' in available_win_ver:
            return 'win10'
        else:
            return 'win7'
    elif my_win_ver == 'win10':
        if 'win8.1' in available_win_ver:
            return 'win8.1'
        else:
            return 'win7'


def wait_for_net(local_path, network_path):
    """
    Check if network location is mapped, map if not.
    :param local_path: local path no network location (X:\myshare)
    :param network_path: remote server hostname or IP (\\myserver01\share, \\192.168.0.1\share)
    :return: 1 if successful
    """
    while True:
        if os.path.exists(local_path):
            return 1
        else:  # map network location if doesn't exist
            subprocess.Popen(['net', 'use', 'Y:', '/DELETE'], shell=True)
            subprocess.Popen(['net', 'use', 'Y:', network_path, '/PERSISTENT:YES', '/N'], shell=True)
            sleep(1.5)
            continue


def renamer(hostname, log_out):

    regs_local = {'reg1': ('HKLM\SYSTEM\CurrentControlSet\Control\ComputerName\ComputerName', 'ComputerName',),
                  'reg2': ('HKLM\SYSTEM\CurrentControlSet\Control\ComputerName\ActiveComputerName', 'ComputerName',),
                  'reg3': ('HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters', 'Hostname',),
                  'reg4': ('HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters', 'NV Hostname',)
                  }

    regs_remote = {'reg1': ('HKLM\TempHive\CurrentControlSet\Control\ComputerName\ComputerName', 'ComputerName',),
                   'reg2': ('HKLM\TempHive\CurrentControlSet\Control\ComputerName\ActiveComputerName', 'ComputerName',),
                   'reg3': ('HKLM\TempHive\CurrentControlSet\Services\Tcpip\Parameters', 'Hostname',),
                   'reg4': ('HKLM\TempHive\CurrentControlSet\Services\Tcpip\Parameters', 'NV Hostname',)
                   }
    # Set Hostname for current OS
    log_out('Changing hostname')

    for reg in regs_local:
        subprocess.Popen(['reg', 'add', regs_local[reg][0],  '/v', regs_local[reg][1], '/d', hostname, '/f'], shell=True).wait()

    # Get list of available drives (C: drive is omitted)
    drives = ['%s:' % d for d in 'ABDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.exists(r'%s:' % d)]

    for d in drives:  # Check if drive has windows OS installed, if True start setting new Hostname
        if os.path.exists(d + r'\Windows\System32\config'):
            log_out('Loading %s drive registry' % d)
            subprocess.Popen(['reg', 'load', r'HKLM\TempHive', r'%s\Windows\System32\config\SYSTEM' % d], shell=True).wait()
            sleep(3)
            log_out('Changing hostname at %s' % d)
            for reg in regs_remote:
                subprocess.Popen(['reg', 'add', regs_remote[reg][0],  '/v', regs_remote[reg][1], '/d', hostname, '/f'], shell=True).wait()
            sleep(3)
            subprocess.Popen(['reg', 'unload', r'HKLM\TempHive'], shell=True)
    return 1


def driver_installer(path, drivers, log_out, progress):

    def auto_accept():
        """Auto accept windows security warning"""
        while click:
            try:
                app = pywinauto.Application()
                app.window_(title='Windows Security').SetFocus()
                app.window_(title='Windows Security').TypeKeys("%i")
            except (pywinauto.findwindows.WindowNotFoundError, pywinauto.timings.TimeoutError):
                pass
        return

    click = 1
    done = 1
    log = open(r'.\log.txt', 'w')
    total = sum([drivers[driver]['manual'] for driver in drivers])
    click_thread = _pool.apply_async(auto_accept)

    for name in drivers:
        log_out('Installing %s' % name)
        for root, dirs, files in os.walk(os.path.join(path, drivers[name]['name'], drivers[name]['version'])):
            for file in files:
                if file.endswith('.inf'):
                    inf = os.path.join(root, file)
                    progress(percentage(done, total))
                    task = subprocess.Popen(['C:\\Windows\\SYSNATIVE\\PNPUTIL.exe', '-i', '-a', inf], shell=True,
                                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    task.wait()
                    log.flush()
                    out = task.stdout.read()
                    log.write(out.decode('utf-8'))
                    log.write('\n-----------------------------------\n')
                    done += 1
    click = 0
    log.close()
    return 1

