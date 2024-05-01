import ctypes
import os
import requests
import xml.etree.ElementTree as ET
import subprocess
import xml.etree.ElementTree as ET
import shutil
import sys
from lxml import etree as ET
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
def download_file(url, folder):
    response = requests.get(url)
    filename = os.path.join(folder, url.split("/")[-1])
    with open(filename, 'wb') as file:
        file.write(response.content)

def parse_and_download(xml_file_path):
    with open(xml_file_path, 'rb') as file:
        xml_content = file.read()
        
    root = ET.fromstring(xml_content)
    ns = {'ns': 'http://schemas.microsoft.com/appx/appinstaller/2018'}
    folder = "Temp Arc"
    os.makedirs(folder, exist_ok=True)
    
    main_package = root.find('ns:MainPackage', ns)
    dependencies = root.find('ns:Dependencies', ns)
    
    download_file(main_package.get('Uri'), folder)
    
    for package in dependencies.findall('ns:Package', ns):
        download_file(package.get('Uri'), folder)

def extract_msix(folder):
    output_folder = "ArcFiles"
    os.makedirs(output_folder, exist_ok=True)
    for filename in os.listdir(folder):
        if filename.startswith("Arc") and filename.endswith(".msix"):
            filepath = os.path.join(folder, filename)
            subprocess.run(['./7z', 'x', filepath, '-o'+output_folder])

def delete_files(folder, filenames):
    for filename in filenames:
        filepath = os.path.join(folder, filename)
        if os.path.exists(filepath):
            if os.path.isfile(filepath):
                os.remove(filepath)
            elif os.path.isdir(filepath):
                shutil.rmtree(filepath)
        else:
            print(f"The file {filename} does not exist.")



def edit_xml_file(file_path, new_min_version):
    parser = ET.XMLParser(remove_blank_text=True)
    tree = ET.parse(file_path, parser)
    root = tree.getroot()

    ns = {'ns': 'http://schemas.microsoft.com/appx/manifest/foundation/windows10'}

    target_device_family = root.find(".//ns:TargetDeviceFamily", ns)

    if target_device_family is not None:
        target_device_family.set('MinVersion', new_min_version)

        tree.write(file_path, pretty_print=True, xml_declaration=True, encoding='utf-8')
    else:
        print("Element 'TargetDeviceFamily' non trouvé dans le fichier XML.")


def install_msix(folder):
    for filename in os.listdir(folder):
        if filename.startswith("Microsoft") and filename.endswith(".msix"):
            filepath = os.path.join(os.getcwd(), folder, filename)
            quoted_filepath = f'"{filepath}"'
            subprocess.run(['powershell', 'Add-AppxPackage', '-Path', quoted_filepath])

def prompt_for_dev_mode():
    input("Make sure Developer Mode is enabled in the Settings App: Update And Security > For Developers > Enable Developper Mode. Then press Enter...")

def register_appxmanifest(folder):
    manifest_path = os.path.join(os.getcwd(), folder, "AppxManifest.xml")
    quoted_manifest_path = f'"{manifest_path}"'
    subprocess.run(['powershell', 'Add-AppxPackage', '-Register', quoted_manifest_path])

def install_font(font_name):
    font_path = os.path.join(os.getcwd(), font_name)
    
    fonts_folder = os.path.join(os.environ['WINDIR'], 'Fonts')
    
    shutil.copy(font_path, fonts_folder)


if not is_admin():
    input("Please run this script as an administrator.")
    sys.exit()
input("NOTE 1/4: Before starting, this is an *UNOFFICIAL* installer for the Arc Browser. Press Enter.")
input("NOTE 2/4: I'm not responsible for any damage caused by using this installer. Press Enter.")
input("NOTE 3/4: Take note that The Browser Company will not help if you have any issues with this version. Press Enter.")
input("NOTE 4/4: Finally, make sure that you enabled Developer Mode in the Settings App (temporary). Press Enter to run the installer.")

print("Downloading Arc Files and Dependencies... This may take a while.")
xml_file_path = "Arc.appinstaller"
parse_and_download(xml_file_path)

print("Extracting Arc.msix...")
extract_msix("Temp Arc")

print("Deleting signature files...")
delete_files("ArcFiles", ["[Content_Types].xml", "AppxBlockMap.xml", "AppxSignature.p7x", "AppxMetadata"])

print("Patching ArcManifest.xml...")
edit_xml_file("ArcFiles/AppxManifest.xml", "10.0.19000.0")

print("Installing dependencies via Powershell...")
install_msix("Temp Arc")

print("Installing required fonts...")
install_font("Segoe Fluent Icons.ttf")

prompt_for_dev_mode()
print("Sideloading Arc...")
register_appxmanifest("ArcFiles")
print("Sideloaded Arc!")

input("Arc was successfully installed! Please Disable Developer Mode in the Settings App for security reasons.")
sys.exit()
