import tkinter as tk
from tkinter import N, E, S, W, END
from tkinter import messagebox, filedialog
from random import randint
import yaml
import csv
import sys
import argparse
import re

import yaml
from yaml.loader import SafeLoader

common_yml_params = [
    'city',
    'country',
    'post_code',
    'state',
    'street',
    'street2',
]


class SafeLineLoader(SafeLoader):
    def construct_mapping(self, node, deep=False):
        mapping = super(SafeLineLoader, self).construct_mapping(node, deep=deep)
        # Add 1 so line numbering starts at 1
        mapping['__line__'] = node.start_mark.line + 1
        return mapping


yml_file = "/Users/karlschmutz/Documents/PythonDev/ST-TEST.yml"

sites_version = 'sites v4.3'
elements_version = 'elements v2.3'
csv_out_dict = {}
CLIARGS = {}
yml_input = {}

big_list = []
change_list = []
CLIARGS['ignore_nulls'] = False
CLIARGS['Input YML File'] = yml_file
def open_yml():
    filename = tk.filedialog.askopenfile(title="Open YML/YAML CloudGenix Config File")
    if (filename):
        alert("OPENED file name: " + str(filename.name) , "File Opened" )
    else:
        alert("Cancelled File Open", "File Open Cancelled" )
    yml_file = filename.name

def save_jinja():
    jinjafilename = tk.filedialog.asksaveasfilename(initialfile="template-jinja.yml",title="Save JINJA template file")
    if (jinjafilename):
        ymlfilename = tk.filedialog.asksaveasfilename(initialfile="template-params.csv",title="Save CSV Parameters file")
        if (ymlfilename):
            alert("Saved file names: " + str(jinjafilename) + " and " + str(ymlfilename), "File Saved" )
        else:
            alert("Cancelled SAVE", "File Save Cancelled" )
    else:
        alert("Cancelled SAVE", "File Save Cancelled" )


def alert(alertmessage, title="Notice"):
    tk.messagebox.showinfo(str(title), str(alertmessage))

def alertme():
    if (chk_selectcommon.get() == 1):
        lst_Listbox_data.selection_set(5)
        lst_Listbox_data.selection_set(6)
    else:
        lst_Listbox_data.selection_clear(5)
        lst_Listbox_data.selection_clear(6)


def select_common_yml_params():
    select = False
    if (chk_selectcommon.get() == 1):
        select = True

    change_list.clear()
    for i in range(len(big_list)):
        key_param = big_list[i]['name']
        key_param = re.sub(" ", "", key_param)
        key_param = re.sub("\:.*.", "", key_param)
        key_param = re.sub("\n", "", key_param)
        if key_param.replace(":","") in common_yml_params :
            change_list.append(i)
    for index in change_list:
        if select:
            lst_Listbox_data.selection_set(index)
        else:
            lst_Listbox_data.selection_clear(index)


    

def open_files():
    print("OPENING FILE")
    print(" USING INPUT FILE:", CLIARGS['Input YML File'])
    yml_dict = {}
    with open(CLIARGS['Input YML File'], 'r') as stream:
        try:
            print(" Opened file successfully")
            yml_dict = yaml.safe_load(stream)
            #yml_dict = yaml.load(stream, Loader=SafeLineLoader)
            print(" Loaded YML Successfully")        
        except yaml.YAMLError as exc:
            sys.exit(exc)

    if(sites_version not in yml_dict.keys()):
        sys.exit("ERROR: no sites (" + sites_version + ") found in YML input file")

    if len(yml_dict[sites_version]) > 1:
        print(" WARNING: more than 1 site found. It is recommended that a YML with only 1 site be used")
    return yml_dict

yml_input = open_files()
yml_raw_input = open(yml_file, "r")

counter = 0
for i in yml_raw_input:
    if (i != '---\n') and (i[0] != '#'):  ###IGNORE Comments and the starting --- Char
        big_list.append({"name": str(i), "value": False, 'line': counter})
        counter += 1

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
    if ((type(item) == None) or (item is None)) and (CLIARGS['ignore_nulls']):
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

def replace_selected(): 
    change_list.clear()
    for i in range(len(big_list)):
        if lst_Listbox_data.selection_includes(i):
            change_list.append(i)
    for index in change_list:
        lst_Listbox_data.delete(index)        
        lst_Listbox_data.insert(index, replace_big_list[index])
    if len(change_list) > 0:
        alert("Successfully changed " + str(len(change_list)) + " items")
    else:
        alert("No items selected to be changed", "Error")

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

btn_convert = tk.Button(output_frame, text='Convert to JINJA', command=replace_selected)
btn_save = tk.Button(output_frame, text='Save JINJA and CSV Parameters File', command=save_jinja)

lst_Listbox_data = tk.Listbox(operation_frame, selectmode=tk.MULTIPLE)
scrollbar = tk.Scrollbar(operation_frame)
lst_Listbox_data.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=lst_Listbox_data.yview)
for i in big_list:
    lst_Listbox_data.insert(END, str(i['name']))


input_frame.pack( fill="both")
btn_openfile.pack(side="left", fill="both")
lbl_api.pack(side="right", fill="both")

options_frame.pack(fill="both")
lbl_labelcheckdescription = tk.Label(options_frame, text="Optional Settings: ")
lbl_labelcheckdescription.pack(side="left", fill="y")
chk_chkselectcommon = tk.Checkbutton(options_frame, text='Common Parameters', command=select_common_yml_params, variable=chk_selectcommon) 
chk_chkselectcommon.pack(side="left", fill="y", padx=15)
chk_chkselectnames = tk.Checkbutton(options_frame, text='Site/Element Names', command=alertme, variable=chk_selectnames) 
chk_chkselectnames.pack(side="left", fill="y", padx=15)
chk_chkselectwaninterfaces = tk.Checkbutton(options_frame, text='WAN Interfaces', command=alertme, variable=chk_selectwaninterfaces) 
chk_chkselectwaninterfaces.pack(side="left", fill="y", padx=15)

operation_frame.pack(expand=1, fill="both")
scrollbar.pack(side="right", fill="y")
lst_Listbox_data.pack(expand=1, fill="both", side="left")

output_frame.pack(fill="both")
btn_convert.pack(side="left",)
btn_save.pack(side="right")


win.focus_set()

RecursivelyChangeVals(yml_input)
replaced_yml = yaml.dump(yml_input, sort_keys=False)

replace_big_list = []
for i in replaced_yml.split('\n'):
    replace_big_list.append(i)

tk.mainloop()
