import tkinter as tk
from tkinter import N, E, S, W, END
from tkinter import messagebox, filedialog
from random import randint
from os import system
from platform import system as platform
import os
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
    win_api_auth = tk.Toplevel()
    win_api_auth.title('Please Authenticate via API')
    #win_api_auth.geometry("300x150+120+120")

    auth_method = tk.IntVar(None, 1)

    radio1 = tk.Radiobutton(win_api_auth, text="Auth Token", variable=auth_method, value=1)
    radio1.pack(anchor=W)
    lbl_0 = tk.Label(win_api_auth, text="Auth Token Authentication:" )
    lbl_0.pack()
    
    txt_auth_token = tk.StringVar(win_api_auth, value='... Please paste your Auth Token Here ...')
    input_box_token = tk.Entry(win_api_auth, textvariable=txt_auth_token, width=40)
    input_box_token.pack()

    radio2 = tk.Radiobutton(win_api_auth, text="User/Pass", variable=auth_method, value=2)
    radio2.pack(anchor=W)

    lbl_1 = tk.Label(win_api_auth, text="Username/PW Auth:" )
    lbl_1.pack()

    lbl_2 = tk.Label(win_api_auth, text="Email/User" )
    lbl_2.pack()

    txt_username = tk.StringVar(win_api_auth, value='<username>')
    input_box_username = tk.Entry(win_api_auth, textvariable=txt_username,state="disabled")
    input_box_username.pack()

    lbl_3 = tk.Label(win_api_auth, text="Password" )
    lbl_3.pack()

    txt_password = tk.StringVar(win_api_auth, value='********')
    input_box_password = tk.Entry(win_api_auth, textvariable=txt_password, show="*",state="disabled")
    input_box_password.pack()
    
    btn_ok = tk.Button(win_api_auth, text="OK")
    btn_cancel = tk.Button(win_api_auth, text="CANCEL", command=lambda: subwindow_cancel(win_api_auth))

    btn_cancel.pack(side="right",expand=1, pady=5, padx=10)
    btn_ok.pack(side="left",expand=1, pady=5)
    
    radio1.config(command=lambda: choose_new_auth_method([input_box_token],[input_box_username,input_box_password]))
    radio2.config(command=lambda: choose_new_auth_method( [input_box_username,input_box_password], [input_box_token] ))
    btn_ok.config(command=lambda: auth_and_pick_sites(auth_method.get(),txt_username.get(),txt_password.get(),txt_auth_token.get(),win_api_auth))
    auth_method.set(1)
    radio1.set(1)
    radio1.invoke()
    
    win_api_auth.lift(aboveThis=win_jinjatool_main)
    win_api_auth.grab_set()

def choose_new_auth_method(enable_list, disable_list):
    for widget in enable_list:
        widget.config(state="normal")
    for widget in disable_list:
        widget.config(state="disabled")

def auth_and_pick_sites(auth_method, username, password, auth_token, parent_window):
    ###AUTH_METHOD, 1 = API_TOKEN, 2 = UN/PW
    
    import cloudgenix_config
    from cloudgenix_config import pull
    global sdk
    
    if (auth_method == 1): ###API TOKEN AUTH
        try: auth_status = sdk.interactive.use_token(auth_token)
        except: auth_status = False
    else:
        auth_status = sdk.interactive.login(email=username,password=password)
        try: auth_status
        except: auth_status = False

    if auth_status:
        site_list = sdk.get.sites().cgx_content.get("items")

        win_site_picker = tk.Toplevel()
        win_site_picker.title('Please Select your Site')

        lbl_1 = tk.Label(win_site_picker, text="Choose One Site Below:" )
        lbl_1.pack(side="left",expand=1,pady=5, fill="y")
        

        lst_Listbox_sites = tk.Listbox(win_site_picker)
        site_list_scrollbar = tk.Scrollbar(win_site_picker)
        lst_Listbox_sites.config(yscrollcommand=site_list_scrollbar.set)
        site_list_scrollbar.config(command=lst_Listbox_sites.yview)
        
        site_list_scrollbar.pack(side="right", fill="y")
        lst_Listbox_sites.pack(expand=1, fill="both", side="left")

        btn_ok_sites = tk.Button(win_site_picker, text="OK", command=lambda: load_site([win_site_picker, parent_window], sdk, lst_Listbox_sites, site_list ))
        btn_cancel_sites = tk.Button(win_site_picker, text="CANCEL", command=lambda: kill_windows(win_site_picker))

        btn_cancel_sites.pack(side="right",expand=1, pady=5, padx=10)
        btn_ok_sites.pack(side="left",expand=1, pady=5)

        win_site_picker.lift(aboveThis=parent_window)
        win_site_picker.grab_set()

        for site in site_list:
            lst_Listbox_sites.insert(END, str(site['name']))
    else:
        alert("Authentication Failed, please verify your credentials", "Error")
        



def load_site(window_list, sdk, site_list_box, site_list):
    selected_site = site_list_box.get('active')
    site_id = ""
    site_name = ""
    for site in site_list:
        if selected_site == site['name']:
            site_id = site['id']
            site_name = site['id']
    if site_id != "":
        print("Your SITE ID is ", site_id)
        print("Your SITE NAME is ", site_name, " VS ", selected_site)

        tmp_file_name = "CGX-" + str(randint(111111,999999)) + ".yml"
        print("Your TEMP FileName is ", tmp_file_name)
        from cloudgenix_config import pull
        pull.pull_config_sites(sites=site_id,output_filename=tmp_file_name, passed_sdk=sdk)#, return_result=True)
        
        global list_box_array, list_box_array_jinja
        (list_box_array, list_box_array_jinja) = load_yml_file(tmp_file_name)
        os.remove(tmp_file_name)
        kill_windows(window_list)


def kill_windows(window_list):
    if type(window_list) is list:
        for window in window_list:
            window.destroy()
    else:
        window_list.destroy()

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

def modify_item_jinja_var(self):
    item = lst_Listbox_data.get('active')
    item_index = (lst_Listbox_data.index('active'))
    
    input_key = ""

    current_key = list_box_array_jinja[item_index]
    current_key = re.sub(".*.{{","",current_key)
    
    current_key = re.sub("}}.*.","",current_key)
    
    old_line = list_box_array_jinja[item_index]
    new_line = re.sub("\{\{.*.\}\}",input_key,old_line)

    win_custom_key = tk.Toplevel()
    win_custom_key.title('Customize the Key')
    #win_custom_key.geometry("300x150+120+120")

    lbl_current_key = tk.Label(win_custom_key, text="Current Key : {{ " + current_key + " }}" )
    txt_input = tk.StringVar(win_custom_key, value='{{ ' + current_key + ' }}')
    input_box = tk.Entry(win_custom_key, textvariable=txt_input)

    btn_ok = tk.Button(win_custom_key, text="OK", command=lambda: custom_jinja_key_ok_replace(win_custom_key,input_box,item_index))
    btn_cancel = tk.Button(win_custom_key, text="CANCEL", command=lambda: subwindow_cancel(win_custom_key))

    lbl_current_key.pack(fill="both", expand=1, pady=5, padx=10)
    input_box.pack(fill="both", expand=1, pady=5, padx=10)
    btn_cancel.pack(side="right",expand=1, pady=5, padx=10)
    btn_ok.pack(side="left",expand=1, pady=5)
    
    win_custom_key.lift(aboveThis=win_jinjatool_main)
    win_custom_key.grab_set()
    
def subwindow_cancel(w):
    w.destroy()

def custom_jinja_key_ok_replace(w,input_box,item_index):
    new_value = str(input_box.get())
    old_line = list_box_array_jinja[item_index]
    new_line = re.sub("\{\{.*.\}\}",new_value,old_line)
    list_box_array_jinja[item_index] = new_line
    lst_Listbox_data.delete(item_index)        
    lst_Listbox_data.insert(item_index, list_box_array_jinja[item_index])
    w.destroy()

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
win_jinjatool_main = tk.Tk()

chk_selectcommon = tk.IntVar()
chk_selectnames = tk.IntVar()
chk_selectwaninterfaces = tk.IntVar()

win_jinjatool_main.title('Jinja TOOL')
win_jinjatool_main.geometry('900x700') # Size 200, 200

input_frame = tk.Frame(win_jinjatool_main)
options_frame = tk.Frame(win_jinjatool_main, bd="2", highlightbackground="black", highlightthickness=1)
operation_frame = tk.Frame(win_jinjatool_main)
output_frame = tk.Frame(win_jinjatool_main)

lbl_api = tk.Label(input_frame, text=" ")
btn_openfile = tk.Button(input_frame, text='Select YML File to OPEN', command=open_yml)
btn_openapi = tk.Button(input_frame, text='Load YML via API', command=open_api, ) ###state="disabled"

btn_convert = tk.Button(output_frame, text='Convert to JINJA', command=replace_selected)
btn_revert = tk.Button(output_frame, text='Revert Selection to YAML', command=revert_selected)
btn_save = tk.Button(output_frame, text='Save JINJA and CSV Parameters File', command=save_jinja)

lst_Listbox_data = tk.Listbox(operation_frame, selectmode=tk.MULTIPLE)
scrollbar = tk.Scrollbar(operation_frame)
lst_Listbox_data.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=lst_Listbox_data.yview)
lst_Listbox_data.bind("<Double-Button-1>", modify_item_jinja_var)

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

win_jinjatool_main.focus_set()

if platform() == 'Darwin':  # How Mac OS X is identified by Python
    system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')

tk.mainloop()
