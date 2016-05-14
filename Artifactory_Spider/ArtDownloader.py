import os
import sys
import json
import requests

from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from patoolib import extract_archive
from patoolib.util import PatoolError
from ssl import _create_unverified_context


def ensure_dir(the_dir):
    """
    Check if dir exists and create one if not
    :param the_dir: the directory path
    :return: none
    """
    d = os.path.dirname(the_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return


def inf_check(the_path):
    """
    Enumerate all inf files in given location
    :param the_path: folder path to check
    :return: list of path to inf files inside the given directory
    """
    total_inf = 0

    for root, dirs, files in os.walk(the_path):
        for file in files:
            if file.endswith(".inf"):
                total_inf += 1
    return total_inf


def download_file(dl_url, dl_save_path):
    """
    Download URL to given path
    :param dl_url: URL to download
    :param dl_save_path: path to save URL to
    :param position:
    :return: none
    """
    local_filename = dl_url.split('/')[-1]
    complete_name = os.path.join(dl_save_path, local_filename)
    # Get file information
    r = requests.head(dl_url, auth=('', ''), verify=False)
    file_info = {'size': r.headers['content-length'], 'status_code': int(r.status_code)}
    # Check status code, should be 200
    if file_info['status_code'] != 200:
        print('Something went wrong connecting to:  %s' % dl_url)
        return 0
    # NOTE the stream=True parameter
    r = requests.get(dl_url, stream=True, auth=('', ''), verify=False)
    with open(complete_name, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
            cur_size = os.path.getsize(os.path.join(dl_save_path, local_filename))
            status(percentage(cur_size, file_info['size']))
    return 1


def url_parse(the_url):
    """
    Parse URL to retrive package information: project, platform and release.
    :param the_url: URL to package location
    :return: information is returned as tuple in the following order: project, platform, release
    """
    the_url = the_url.split('/')
    for c in the_url:
        if c == '' or c == ' ' or c.lower() == 'packages':
            the_url.remove(c)
    the_details = the_url[-1].split('-')
    if 'RVP' not in the_details[1]:
        the_platform = ''.join(c for c in the_details[1] if c.isalpha())
    else:
        the_platform = the_details[1]
    the_project = the_details[0]
    the_release = '-'.join(the_details[2:]).lower()
    return the_project, the_platform, the_release


def name_parse(word):
    """
    Parse a driver name for the name and version separately
    :param word: driver name that has it's name and version together (ie: GFX-13.3.500)
    :return: returns the name and version, if the name doesn't contain a version/name it'll be returned empty
    """
    name = ''
    replace_list = ['zip', 'Zip', 'ZIP', '7z', '7Z' 'rar', 'Rar', 'RAR']
    for letter in word:
        if letter.isalpha():
            name += letter
        else:
            break
    try:
        version = word.replace(name, '')
        if any(symbol == version[0] for symbol in ['-', '_', ':', '.']):
            version = version[1:]
            for rep in replace_list:
                version = version.replace(rep, '')
    except IndexError:
        version = 0

    if name == '':
        return version_check(word), version
    else:
        return name, version


def version_check(version_number):
    """
    Match version number with driver name from known drivers
    :param version_number: driver version number to check
    :return: returns best match driver name
    """
    def similar(a, b):
        return SequenceMatcher(None, a, b).ratio()

    try:
        with open(r'./data/versions.json', 'r') as the_infile:
            versions = json.load(the_infile)
    except (ValueError, FileNotFoundError):
        print('Versions file was not found, quiting')
        quit()
        return

    update = True
    average = {}
    version_number = ''.join(c for c in version_number if c.isdigit())

    for driver in versions:
        average[driver] = []
        for ver in versions[driver]:
            #  check if version is already listed
            if any(vers == version_number for vers in versions[driver]):
                average[driver] = 1.0
                update = False
                break
            average[driver].append(similar(version_number, ver))
        else:
            average[driver] = sum(average[driver]) / len(average[driver])
            continue
        break

    if all(average[xa] < 0.75 for xa in average):
        return ''

    if update:  # update versions file with new version to corresponding name
        versions[max(average, key=average.get)].append(version_number)
        with open(r'./data\versions.json', 'w') as outfile_loc:
            json.dump(versions, outfile_loc, sort_keys=True, indent=4, ensure_ascii=False)

    return max(average, key=average.get)


def kit_checker(the_site):
    print(the_site)
    the_package = []
    # the_page = urllib.request.urlopen(the_site, context=context)
    the_page = requests.get(the_site, auth=('', ''), verify=False)
    the_soup = BeautifulSoup(the_page.text, 'html.parser')
    the_site_kits = the_soup.findAll('div', {'class': 'local-repos-list'})
    for the_div in the_site_kits:
        the_links = the_div.findAll('a')
        for the_link in the_links:
            the_package.append(the_link.get_text(strip=True).strip('/'))
    return max(the_package)


def percentage(xi, yi):
    """
    Return x out of y percentage
    :param xi: value to be checked
    :param yi: value to check against
    :return: integer as percentage
    """
    try:
        perc = int(xi) / int(yi)
        return perc*100
    except ZeroDivisionError:
        return 'Error'


def status(percent):
    sys.stdout.write("Downloading %3d%%\r" % percent)
    sys.stdout.flush()

requests.packages.urllib3.disable_warnings()
context = _create_unverified_context()
tmp_path = os.environ['temp']
drivers = {}
urls = []
log = open(r'.\log.txt', 'w')
outdir = r'./Drivers'

package_sites = []


for url in package_sites:

    url = url + '/' + kit_checker(url) + '/Packages'

    page = requests.get(url, auth=('', ''), verify=False)
    soup = BeautifulSoup(page.text, 'html.parser')
    driver_links = soup.findAll('div', {'class': 'local-repos-list'})

    url_info = url_parse(url)
    package_name = '_'.join(url_info)
    print(package_name)
    drivers[package_name] = {'project': url_info[0],
                             'platform': url_info[1],
                             'release': url_info[2],
                             'drivers': {}
                             }

    for div in driver_links:
        links = div.findAll('a')
        total_links = len(links)
        for lnk in links:
            driver_name = name_parse(lnk.get_text(strip=True).replace('/', ''))[0]
            driver_version = name_parse(lnk.get_text(strip=True).replace('/', ''))[1]

            link_page = requests.get(lnk['href'], auth=('', ''), verify=False)
            link_soup = BeautifulSoup(link_page.text, 'html.parser')

            drv_page = link_soup.findAll('div', {'class': 'local-repos-list'})
            for drv_div in drv_page:
                # Skip KSC package
                if any(ver == driver_version for ver in ['1.01', '1.02', '1.03', '1.04',
                                                         '1.20', '1.21', '1.22', '1.23', '1.24', '1.25',
                                                         '1.23v2', ]):
                    break
                elif driver_name in ['IFWI', 'ifwi'] or driver_name in ['ME', 'me', 'CSME', 'csme']:  # Skip Bios/ME files
                    break
                drv_link = drv_div.findAll('a', {'class': 'icon-link jar'})  # Grab driver's zip link
                for lnk2 in drv_link:
                    # Check if version was not found
                    if not driver_version:
                        driver_version = lnk2.get_text(strip=True)
                        for x in ['.zip', '.Zip', '.ZIP', '.7z', '.rar']:
                            driver_version = driver_version.replace(x, '')
                    drivers[package_name]['drivers'][driver_name] = {'link': lnk2['href'],
                                                                     'name': driver_name,
                                                                     'version': driver_version,
                                                                     'manual': 0
                                                                     }
                    log.write('     Driver: %-20s version: %-20s  --  ' % (driver_name, driver_version))
                    driver_save_path = os.path.join(outdir, driver_name, driver_version)
                    if not os.path.exists(os.path.join(outdir, driver_name, driver_version)):
                        print('Need to download %s ver %s' % (driver_name, driver_version))
                        driver_link = lnk2['href']
                        zip_download_path = os.path.join(tmp_path, driver_link.split('/')[-1])
                        if not download_file(driver_link, tmp_path):
                            break
                        # ensure_dir(driver_save_path)
                        try:
                            extract_archive(zip_download_path, outdir=driver_save_path, verbosity=-1)
                        except PatoolError as err:
                            print(err)
                        try:
                            os.remove(zip_download_path)
                        except PermissionError:
                            pass
                        log.write('%-10s downloaded\n' % '')
                    else:
                        log.write('%-10s exists\n' % '')
                    drivers[package_name]['drivers'][driver_name]['manual'] = inf_check(driver_save_path)
        if len(drivers[package_name]['drivers']) > 0:
            with open(os.path.join(outdir, 'MAP_files', '%s.json' % package_name), 'w') as outfile:  # datetime.utcnow().strftime('%d-%m-%y_%H-%M-%S')
                print(os.path.join(outdir, 'MAP_files', '%s.json' % package_name))
                json.dump(drivers[package_name], outfile, sort_keys=True, indent=4, ensure_ascii=False)
        else:
            log.write('%s - NOT DOWNLOADED\n link: %s' % (package_name, url))

log.close()
