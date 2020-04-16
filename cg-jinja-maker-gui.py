import tkinter as tk
from tkinter import N, E, S, W, END
from tkinter import messagebox, filedialog
from random import randint
from os import system
from platform import system as platform
import yaml
import csv
import sys
import argparse
import re

import yaml
from yaml.loader import SafeLoader
from cloudgenix import API

sdk = API()

##############GLOBALS##############
common_yml_params = [   ###These are the common YML Keys used for the common params checkbox
    'city',
    'country',
    'post_code',
    'state',
    'street',
    'street2',
]

first_site_name = ""
sites_version = ''
elements_version = ''

csv_out_dict = {}

change_list = []
list_box_array = []             ###Contains YML File Original Contents
list_box_array_jinja = []       ###Contains YML File with VALUE replaced with JINJA Variable of YML PATH
element_name_list = []
##################################

def open_yml():
    filename = tk.filedialog.askopenfile(title="Open YML/YAML CloudGenix Config File")
    if (filename):
        alert("OPENED file name: " + str(filename.name) , "File Opened" )
        yml_file = filename.name
        global list_box_array, list_box_array_jinja
        (list_box_array, list_box_array_jinja) = load_yml_file(yml_file)
    else:
        alert("Cancelled File Open", "File Open Cancelled" )

def save_jinja():
    new_csv_params = []
    new_csv_values = []

    jinjafilename = tk.filedialog.asksaveasfilename(initialfile="template-jinja.yml",title="Save JINJA template file")
    if (jinjafilename):
        csvfilename = tk.filedialog.asksaveasfilename(initialfile="template-params.csv",title="Save CSV Parameters file")
        if (csvfilename):
            ### Get CSV Params for things which have changed
            for i in range(len(list_box_array)):
                if ("{{" in lst_Listbox_data.get(i)) and ("}}" in lst_Listbox_data.get(i)):
                    key_param = re.sub("}}.*.", "", lst_Listbox_data.get(i))
                    key_param = re.sub(".*.{{", "", key_param)

                    orig_value = list_box_array[i]['name']
                    orig_value = re.sub(".*.\- ", "", orig_value)
                    orig_value = re.sub(".*.\: ", "", orig_value)
                    orig_value = re.sub("\n", "", orig_value)
                    orig_value = orig_value.replace(":","")
                    orig_value = re.sub("^ *", "", orig_value)
                    
                    new_csv_params.append(key_param)
                    new_csv_values.append(orig_value)   
            with open(csvfilename, 'w', newline='') as csvoutput: #####WRITE the CSV sample file
                linewriter = csv.writer(csvoutput, delimiter=',', quotechar='"')
                linewriter.writerow(new_csv_params)
                linewriter.writerow(new_csv_values)
                print(" SUCCESS: Wrote CSV Parameter file",csvfilename)
            with open(jinjafilename, "w") as jinja_file:
                for i in range(len(list_box_array)): ###write JINJA Template File
                    jinja_file.write(lst_Listbox_data.get(i).replace("\n","") + "\n")
                print(" SUCCESS: Wrote JINJA Parameter file",csvfilename)
        else:
            alert("Cancelled SAVE", "File Save Cancelled" )
    else:
        alert("Cancelled SAVE", "File Save Cancelled" )


def alert(alertmessage, title="Notice"):
    tk.messagebox.showinfo(str(title), str(alertmessage))

def open_api():
    import cloudgenix_config
    from cloudgenix_config import pull
    global sdk
    token = 'testtoken'
    seattle_siteid = "15003264513650067"
    sdk.interactive.use_token(token)
    result_dict = pull.pull_config_sites(seattle_siteid, output_filename=None, passed_sdk=sdk, return_result=True)
    
    win_auth = tk.Toplevel()
    win1.title('Please Authenticate via API')
    win1.geometry("300x150+120+120")
    btn_lift = tk.Button(win1, text="Lift win1")
    btn_lift.pack(padx=30, pady=5)
    btn_lower = tk.Button(win1, text="Lower win1")
    btn_lower.pack(pady=5)
    win1.lift(aboveThis=win)
    win1.grab_set()

def alertme():
    if (chk_selectcommon.get() == 1):
        lst_Listbox_data.selection_set(5)
        lst_Listbox_data.selection_set(6)   
    else:
        lst_Listbox_data.selection_clear(5)
        lst_Listbox_data.selection_clear(6)

def select_names():
    global element_name_list
    select = False
    if (chk_selectnames.get() == 1):
        select = True
    ### SELECT Site Name
    change_list.clear()
    match_criteria = " " + first_site_name + ":"
    for i in range(len(list_box_array)):
        if match_criteria in list_box_array[i]['name'].replace("'",""):
            change_list.append(i)

    ### SELECT Element Name
    for i in range(len(list_box_array)):
        key_param = list_box_array[i]['name']
        key_param = re.sub(" ", "", key_param)
        key_param = re.sub("\:.*.", "", key_param)
        key_param = re.sub("\n", "", key_param)
        key_param = key_param.replace(":","")
        if  key_param in element_name_list:
            change_list.append(i)
 
    for index in change_list:
        if select:
            lst_Listbox_data.selection_set(index)
        else:
            lst_Listbox_data.selection_clear(index)


def select_common_yml_params():
    select = False
    first_state_found = False ###a HACK: Used to only change the first instance of the key "state" as in address, not as in element state: bound
    if (chk_selectcommon.get() == 1):
        select = True

    change_list.clear()
    for i in range(len(list_box_array)):
        key_param = list_box_array[i]['name']
        key_param = re.sub(" ", "", key_param)
        key_param = re.sub("\:.*.", "", key_param)
        key_param = re.sub("\n", "", key_param)
        if key_param.replace(":","") in common_yml_params :
            if "state" in key_param:
                if not(first_state_found):
                    first_state_found = True
                    change_list.append(i)
            else:
                change_list.append(i)
    for index in change_list:
        if select:
            lst_Listbox_data.selection_set(index)
        else:
            lst_Listbox_data.selection_clear(index)

def CleanBrackets(item):
    retval = item
    retval = retval.replace("{{ ","")
    retval = retval.replace(" }}","")
    retval = retval.replace("{{","")
    retval = retval.replace("}}","")
    retval = retval.replace(sites_version + ".","")
    retval = retval.replace(sites_version,"")
    retval = retval.replace(" ","_")
    retval = retval.replace(".","_")
    retval = retval.replace("-","_")
    retval = retval.replace("&","_") ##Added support for & character in YML files as JINJA doesnt support this. Thanks Richard Gallagher!
    return retval

### The function of code was modified from Ryder Bush's original YML to JINJA converter
### found at https://github.com/waterswim 
### I have added lines needed to populate the CSV Dict and to permit the ignoring of
### Null parameters
def RecursivelyChangeVals(item, path = ""):
    if ((type(item) == None) or (item is None)) and False:
        return ""
    
    elif (isinstance(item, dict)):
        for key,value in item.items():
            item[key] = RecursivelyChangeVals(value, f"{path}.{key}")
        return item
    elif (isinstance(item, list)):
        for key,value in enumerate(item):
            item[key] = RecursivelyChangeVals(value, f"{path}.{key}")
        return item
    else:
        if (str(item) == "None"):
            csv_out_dict[CleanBrackets(path[1:])] = ""
        else:
            csv_out_dict[CleanBrackets(path[1:])] = str(item)
        path = CleanBrackets(path)
        return f"{{{{{path[1:]}}}}}" 
def revert_selected():
    change_list.clear()
    for i in range(len(list_box_array)):
        if lst_Listbox_data.selection_includes(i):
            change_list.append(i)
    for index in change_list:
        lst_Listbox_data.delete(index)        
        lst_Listbox_data.insert(index, list_box_array[index]['name'])
    if len(change_list) > 0:
        alert("Successfully reverted " + str(len(change_list)) + " items")
    else:
        alert("No items selected to be changed", "Error")

def replace_selected(): 
    change_list.clear()
    for i in range(len(list_box_array)):
        if lst_Listbox_data.selection_includes(i):
            change_list.append(i)
    for index in change_list:
        lst_Listbox_data.delete(index)        
        lst_Listbox_data.insert(index, list_box_array_jinja[index])
    if len(change_list) > 0:
        alert("Successfully changed " + str(len(change_list)) + " items")
    else:
        alert("No items selected to be changed", "Error")

def load_yml_file(yml_filename):
    list_box_array = []
    list_box_array_jinja = []
    yml_dict = {}
    global elements_version, sites_version, first_site_name, element_name_list
    
    print("OPENING FILE")
    print(" USING INPUT FILE:", yml_filename)
    
    with open(yml_filename, 'r') as stream:
        try:
            print(" Opened file successfully")
            yml_dict = yaml.safe_load(stream)
            #yml_dict = yaml.load(stream, Loader=SafeLineLoader)
            print(" Loaded YML Successfully")        
        except yaml.YAMLError as exc:
            sys.exit(exc)

    ###Detect Sites Version
    yml_root_keys = yml_dict.keys()
    for key in yml_root_keys:
        if "sites v" in key:
            sites_version = key
            print("Detected Sites version in use:",sites_version)
    
    first_site_name = next(iter(yml_dict[sites_version]))
    ###Detect Elements Version
    yml_site_keys = yml_dict[sites_version][first_site_name].keys()
    for key in yml_site_keys:
        if "elements v" in key:
            elements_version = key
            print("Detected Elements version in use:",elements_version)
    if elements_version == "":
        print("Warning, no Elements detected in YML")
        
    element_name_list = list(yml_dict[sites_version][first_site_name][elements_version].keys())

    if(sites_version == ""):
        sys.exit("ERROR: no sites version found in YML input file(Is this a CGX YML FILE?)")

    if len(yml_dict[sites_version]) > 1:
        print(" WARNING: more than 1 site found. It is recommended that a YML with only 1 site be used")

    ###Replace Site Name with placeholder: site_1
    yml_dict[sites_version]["{{ site_1 }}"] = yml_dict[sites_version].pop(first_site_name)

    ###Replace ELEMENT Name with placeholder: element_1
    if (len(element_name_list) > 0):
        counter = 0
        for element in element_name_list:
            counter += 1
            new_element_name = "{{ element_" + str(counter) + " }}"
            yml_dict[sites_version]["{{ site_1 }}"][elements_version][new_element_name] = yml_dict[sites_version]["{{ site_1 }}"][elements_version].pop(element)

    

    yml_raw_input = open(yml_filename, "r")

    counter = 0
    for i in yml_raw_input:
        if (i != '---\n') and (i[0] != '#'):  ###IGNORE Comments and the starting --- Char
            list_box_array.append({"name": str(i), "value": False, 'line': counter})
            counter += 1

    for i in list_box_array:
        lst_Listbox_data.insert(END, str(i['name']))

    RecursivelyChangeVals(yml_dict)
    replaced_yml = yaml.dump(yml_dict, sort_keys=False)
    
    for i in replaced_yml.split('\n'):
        list_box_array_jinja.append(i)

    return(list_box_array, list_box_array_jinja)


################################################
##############   BUILD the GUI  ################
################################################
win = tk.Tk()

chk_selectcommon = tk.IntVar()
chk_selectnames = tk.IntVar()
chk_selectwaninterfaces = tk.IntVar()

win.title('Jinja TOOL')
win.geometry('900x700') # Size 200, 200

input_frame = tk.Frame(win)
options_frame = tk.Frame(win, bd="2", highlightbackground="black", highlightthickness=1)
operation_frame = tk.Frame(win)
output_frame = tk.Frame(win)

lbl_api = tk.Label(input_frame, text=" ")
btn_openfile = tk.Button(input_frame, text='Select YML File to OPEN', command=open_yml)
btn_openapi = tk.Button(input_frame, text='Load YML via API', command=open_api, state="disabled")

btn_convert = tk.Button(output_frame, text='Convert to JINJA', command=replace_selected)
btn_revert = tk.Button(output_frame, text='Revert Selection to YAML', command=revert_selected)
btn_save = tk.Button(output_frame, text='Save JINJA and CSV Parameters File', command=save_jinja)

lst_Listbox_data = tk.Listbox(operation_frame, selectmode=tk.MULTIPLE)
scrollbar = tk.Scrollbar(operation_frame)
lst_Listbox_data.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=lst_Listbox_data.yview)

input_frame.pack( fill="both")
btn_openfile.pack(side="left", fill="both")
btn_openapi.pack(side="right", fill="both")
lbl_api.pack(side="right", fill="both")

options_frame.pack(fill="both")
lbl_labelcheckdescription = tk.Label(options_frame, text="Optional Settings: ")
lbl_labelcheckdescription.pack(side="left", fill="y")
chk_chkselectcommon = tk.Checkbutton(options_frame, text='Common Parameters', command=select_common_yml_params, variable=chk_selectcommon) 
chk_chkselectcommon.pack(side="left", fill="y", padx=15)
chk_chkselectnames = tk.Checkbutton(options_frame, text='Site/Element Names', command=select_names, variable=chk_selectnames) 
chk_chkselectnames.pack(side="left", fill="y", padx=15)
chk_chkselectwaninterfaces = tk.Checkbutton(options_frame, text='WAN Interfaces', command=select_names, variable=chk_selectwaninterfaces) 
chk_chkselectwaninterfaces.pack(side="left", fill="y", padx=15)

operation_frame.pack(expand=1, fill="both")
scrollbar.pack(side="right", fill="y")
lst_Listbox_data.pack(expand=1, fill="both", side="left")

output_frame.pack(fill="both")
btn_convert.pack(side="left",)
btn_revert.pack(side="left",)
btn_save.pack(side="right")

win.focus_set()

if platform() == 'Darwin':  # How Mac OS X is identified by Python
    system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')

tk.mainloop()
