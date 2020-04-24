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
import requests
import yaml
import jinja2
from yaml.loader import SafeLoader
from cloudgenix import API

sdk = API()

##############GLOBALS##############
####Common params takes the dict format of YML_KEY: Depth. Where 0 is any depth. Used to
####specifically match duplicate key names like state which exists both as a key in 
####elements (state: bound) and the site address (state: CA). 
common_yml_params = {   ###These are the common YML Keys used for the common params checkbox
    'city': 0,
    'country': 0,
    'post_code': 0,
    'state': 6, ###Match only the state under the address at depth of 6
    'street': 0,
    'street2': 0,
}

policy_yml_params = {   ###These are the common Policy Keys used for the policy params checkbox
    'nat_policysetstack_id': 4,     ###\
    'network_policysetstack_id': 4, ### }Match only the global policy bindings for the site
    'priority_policysetstack_id': 4,### | at depth '4'
    'security_policyset_id': 4,     ###/
}

first_site_name = '' 
sites_version = ''
elements_version = ''
csv_out_dict = {}

headers = {}
site_name_file = 'site_1'
site_lat_header = "location_latitude"
site_long_header = "location_longitude"

site_street2_header = "address_street2"
site_street_header = "address_street"
site_city_header = "address_city"
site_state_header = "address_state"
site_zipcode_header = "address_post_code"
site_country_header = "address_country"
site_street_column = -1
site_city_column = -1
site_state_column = -1
site_zipcode_column = -1
site_country_column = -1
site_street2_column = -1

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
    global win_jinjatool_main, chk_selectcommon, chk_selectnames, chk_selectpolicybindings
    global chk_selectinterfaces
    global input_frame, options_frame, operation_frame, output_frame
    global lst_Listbox_data

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
                    
                    new_csv_params.append(key_param.strip())
                    new_csv_values.append(orig_value.strip())   
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
    global win_jinjatool_main, chk_selectcommon, chk_selectnames, chk_selectpolicybindings
    global chk_selectinterfaces
    global input_frame, options_frame, operation_frame, output_frame
    global lst_Listbox_data

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
    global win_jinjatool_main, chk_selectcommon, chk_selectnames, chk_selectpolicybindings
    global chk_selectinterfaces
    global input_frame, options_frame, operation_frame, output_frame
    global lst_Listbox_data

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
        print("Your SITE NAME is ",selected_site)

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

def select_names():
    global win_jinjatool_main, chk_selectcommon, chk_selectnames, chk_selectpolicybindings
    global chk_selectinterfaces
    global input_frame, options_frame, operation_frame, output_frame
    global lst_Listbox_data

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
    global win_jinjatool_main, chk_selectcommon, chk_selectnames, chk_selectpolicybindings
    global chk_selectinterfaces
    global input_frame, options_frame, operation_frame, output_frame
    global lst_Listbox_data

    select = False
    if (chk_selectcommon.get() == 1):
        select = True
    change_list.clear()
    for i in range(len(list_box_array)):
        key_param = list_box_array[i]['name']
        key_param = re.sub(" ", "", key_param)
        key_param = re.sub("\:.*.", "", key_param)
        key_param = re.sub("\n", "", key_param)
        if key_param.replace(":","") in common_yml_params.keys() :
            depth = len(list_box_array[i]['name']) - len(list_box_array[i]['name'].lstrip(" "))    
            if (depth == common_yml_params[key_param.replace(":","")] or common_yml_params[key_param.replace(":","")] == 0):
                change_list.append(i)
                print("Selecting Key:",key_param.replace(":","")," at DEPTH:", str(depth))
            else:
                print("IGNORING Key:",key_param.replace(":","")," due to wrong DEPTH:", str(depth))
    for index in change_list:
        if select:
            lst_Listbox_data.selection_set(index)
        else:
            lst_Listbox_data.selection_clear(index)


def select_common_policy_params():
    global win_jinjatool_main, chk_selectcommon, chk_selectnames, chk_selectpolicybindings
    global chk_selectinterfaces
    global input_frame, options_frame, operation_frame, output_frame
    global lst_Listbox_data

    select = False
    if (chk_selectcommon.get() == 1):
        select = True
    change_list.clear()
    for i in range(len(list_box_array)):
        key_param = list_box_array[i]['name']
        key_param = re.sub(" ", "", key_param)
        key_param = re.sub("\:.*.", "", key_param)
        key_param = re.sub("\n", "", key_param)
        if key_param.replace(":","") in policy_yml_params.keys() :
            depth = len(list_box_array[i]['name']) - len(list_box_array[i]['name'].lstrip(" "))    
            if (depth == policy_yml_params[key_param.replace(":","")] or policy_yml_params[key_param.replace(":","")] == 0):
                change_list.append(i)
                print("Selecting Key:",key_param.replace(":","")," at DEPTH:", str(depth))
            else:
                print("IGNORING Key:",key_param.replace(":","")," due to wrong DEPTH:", str(depth))
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
    retval = retval.replace("site_1_","")
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
    global win_jinjatool_main, chk_selectcommon, chk_selectnames, chk_selectpolicybindings
    global chk_selectinterfaces
    global input_frame, options_frame, operation_frame, output_frame
    global lst_Listbox_data


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
    global win_jinjatool_main, chk_selectcommon, chk_selectnames, chk_selectpolicybindings
    global chk_selectinterfaces
    global input_frame, options_frame, operation_frame, output_frame
    global lst_Listbox_data


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
    global win_jinjatool_main, chk_selectcommon, chk_selectnames, chk_selectpolicybindings
    global chk_selectinterfaces
    global input_frame, options_frame, operation_frame, output_frame
    global lst_Listbox_data

    new_value = str(input_box.get())
    old_line = list_box_array_jinja[item_index]
    new_line = re.sub("\{\{.*.\}\}",new_value,old_line)
    list_box_array_jinja[item_index] = new_line
    lst_Listbox_data.delete(item_index)        
    lst_Listbox_data.insert(item_index, list_box_array_jinja[item_index])
    w.destroy()

def replace_selected(): 
    global win_jinjatool_main, chk_selectcommon, chk_selectnames, chk_selectpolicybindings
    global chk_selectinterfaces
    global input_frame, options_frame, operation_frame, output_frame
    global lst_Listbox_data

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
    global win_jinjatool_main, chk_selectcommon, chk_selectnames, chk_selectpolicybindings
    global chk_selectinterfaces
    global input_frame, options_frame, operation_frame, output_frame
    global lst_Listbox_data

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

def csvjinja_csv_get():
    global csv_params_file, template_jinja_var, template_outdir_var, latlong_api_key
    filename = tk.filedialog.askopenfile(title="Open CSV Parameters Config File")
    if (filename):
        #alert("OPENED file name: " + str(filename.name) , "File Opened" )
        csv_params_file.set(filename.name)
    else:
        alert("Cancelled File Open", "File Open Cancelled" )

def csvjinja_jinja_get():
    global csv_params_file, template_jinja_var, template_outdir_var, latlong_api_key
    filename = tk.filedialog.askopenfile(title="Open JINJA Template YML File")
    if (filename):
        #alert("OPENED file name: " + str(filename.name) , "File Opened" )
        template_jinja_var.set(filename.name)
    else:
        alert("Cancelled File Open", "File Open Cancelled" )

def csvjinja_outdir_get():
    global csv_params_file, template_jinja_var, template_outdir_var, latlong_api_key
    filename = tk.filedialog.askdirectory(title="Pick a directory for destination YML Files")
    if (filename):
        #alert("OPENED file name: " + str(filename) , "File Opened" )
        template_outdir_var.set(filename)
    else:
        alert("Cancelled File Open", "File Open Cancelled" )
    pass


def get_lat_long (text_as_str):
    global latlong_api_key
    mapquest_api_key = latlong_api_key.strip()
    #Only do this if an API key is present
    if (len(mapquest_api_key) == 0):
        latitude = ""
        longitude = ""
        return (latitude, longitude)
            
    map_url = f"https://www.mapquestapi.com/geocoding/v1/address?key={mapquest_api_key}&location={address_concat}"
    location = requests.get(url=map_url).json()
    latLng = location['results'][0]['locations'][0]['latLng']
    latitude = latLng['lat']
    longitude = latLng['lng']
    return (latitude, longitude)

def csvjinja_process():
    global csv_params_file, template_jinja_var, template_outdir_var, latlong_api_key
    config_parameters = []
    csv_parameters_file = csv_params_file.get()
    print("Read CSV parameter file...",csv_parameters_file)
    with open(csv_parameters_file, newline='') as csvinput:
        lineread = csv.reader(csvinput, delimiter=',', quotechar='"')
        temp_row = next(lineread)
        row = []
        for item in temp_row:
            row.append(item.strip())
        
        for index,item in enumerate(row):    
            headers[index] = item ## This line assignes the index to names for use in the DICT later
            if item == site_street_header:
                site_street_column = index
            if item == site_street2_header:
                site_street2_column = index
            if item == site_city_header:
                site_city_column = index
            if item == site_state_header:
                site_state_column = index
            if item == site_zipcode_header:
                site_zipcode_column = index
            if item == site_country_header:
                site_country_column = index
            if item == site_lat_header:
                latitude_column_index = index
            if item == site_long_header:
                longitude_column_index = index
    
        ##Now Read the remaining rows and assign the dict
        for index,row in enumerate(lineread):
            parameter_dict = dict()
            for i in range(0,len(row)):
                parameter_dict[headers[i]] = row[i]
            if ((site_lat_header in parameter_dict.keys()) and (site_long_header in parameter_dict.keys())):
                if parameter_dict[site_lat_header] == "" and parameter_dict[site_long_header] == "":
                    address_concat = parameter_dict[site_street_header]
                    address_concat += ", " + parameter_dict[site_city_header] 
                    address_concat += ", " + parameter_dict[site_state_header] + " " + parameter_dict[site_zipcode_header]
                    if (parameter_dict[site_country_header] != ""):      #country is optional. if blank, do not use
                        address_concat += ", "
                        address_concat += parameter_dict[site_country_header]
                    address_concat = address_concat.strip()
                    print("     FOUND street address: ", address_concat) 
                    latlon_request = get_lat_long(address_concat)
                    parameter_dict[site_lat_header] = latlon_request[0]
                    parameter_dict[site_long_header] = latlon_request[1]
                    print ("     LAT/LONG:",latlon_request[0],latlon_request[1])
                
            config_parameters.append(parameter_dict)

    # 3. next we need to create the central Jinja2 environment and we will load
    # the Jinja2 template file
    template_file = template_jinja_var.get()
    print("Create Jinja2 environment...")
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath="/"))
    template = env.get_template(template_file)

    # we will make sure that the output directory exists
    output_directory = template_outdir_var.get().strip()
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)

    # 4. now create the templates
    count  =0 
    print("Create templates...")
    for parameter in config_parameters:
        count  += 1 
        result = template.render(parameter)
        result = result.replace(": ''",": ") ##PATCH for do_site as NULL parameters inside of single quotes can break the do_site import script
        f = open(os.path.join(output_directory, parameter[site_name_file] + ".yaml"), "w")
        f.write(result)
        f.close()
        print("Configuration '%s' created..." % (parameter[site_name_file] + ".yaml"))
    alert(str(count) + " Configurations created in folder " + str(output_directory) )


def launch_csvjinjaparmstool():
    win_csvparmtool_main = tk.Toplevel()
    
    win_csvparmtool_main.title("YML Config Generator")

    is_json_var = tk.BooleanVar()
    global csv_params_file, template_jinja_var, template_outdir_var, latlong_api_key
    csv_params_file = tk.StringVar()
    template_jinja_var = tk.StringVar()
    template_outdir_var = tk.StringVar()
    latlong_api_key = tk.StringVar(value="")
    
    datafile_label = tk.StringVar()

    json_header_frame = tk.Frame(win_csvparmtool_main)
    path_entry_frame = tk.Frame(win_csvparmtool_main)
    process_exit = tk.Frame(win_csvparmtool_main)
    extra_options = tk.Frame(win_csvparmtool_main)

    tk.Label(json_header_frame, text="Fill out the below to generate YML Config Files").grid(row=0, column=0, sticky=W)
    json_header_frame.grid(row=0, column=0, pady=12, padx=20)

    # add CSV data file entry
    data_label = tk.Label(path_entry_frame, text="CSV Parameters file:")
    data_label.grid(row=1, column=0, sticky=W)
    datafile_entry = tk.Entry(path_entry_frame, textvariable=csv_params_file, width=65)
    datafile_entry.grid(row=1, column=1)
    browse_csv_button = tk.Button(path_entry_frame, text="Browse", command=csvjinja_csv_get)
    browse_csv_button.grid(row=1, column=2)
    

    # add JINJA template file entry
    tk.Label(path_entry_frame, text="JINJA Template filename:").grid(row=2, column=0, sticky=W)
    template_entry = tk.Entry(path_entry_frame, textvariable=template_jinja_var, width=65)
    template_entry.grid(row=2, column=1, sticky=W)
    browse_jinja_button = tk.Button(path_entry_frame, text="Browse", command=csvjinja_jinja_get)
    browse_jinja_button.grid(row=2, column=2)

    # add OUTPUT Directory
    tk.Label(path_entry_frame, text="YML Output Directory").grid(row=3, column=0, sticky=W)
    template_outdir = tk.Entry(path_entry_frame, textvariable=template_outdir_var, width=65)
    template_outdir.grid(row=3, column=1, sticky=W)
    browse_outdir_button = tk.Button(path_entry_frame, text="Browse", command=csvjinja_outdir_get)
    browse_outdir_button.grid(row=3, column=2)
    path_entry_frame.grid(row=10, column=0, pady=12, padx=20)

    #Additional Options
    opt_label = tk.Label(extra_options, text="MAP API Key:")
    opt_label.grid(row=0, column=0, sticky=W)
    input_api_key = tk.Entry(extra_options, textvariable=latlong_api_key, width=65)
    input_api_key.grid(row=0, column=1, sticky=W)
    extra_options.grid(row=30, column=0, pady=12, padx=20)
    extra_options.grid_remove()
    
    # add process/exit
    tk.Button(process_exit, text="Process", command=csvjinja_process).grid(row=0, column=0, padx=2)
    tk.Button(process_exit, text="Optional Params", command=lambda: csvparmtool_toggle_opts(extra_options)).grid(row=0, column=1, padx=2)
    tk.Button(process_exit, text="Exit", command=lambda: kill_windows(win_csvparmtool_main)).grid(row=0, column=2, padx=2)
    process_exit.grid(row=20, column=0,  pady=12)

    win_csvparmtool_main.lift(aboveThis=win_launchermain)
    win_csvparmtool_main.grab_set()

def csvparmtool_toggle_opts(w):
    if len(w.grid_info()) > 0:
        w.grid_remove()
    else:
        w.grid()

def launch_jinjatool():
    global win_jinjatool_main, chk_selectcommon, chk_selectnames, chk_selectpolicybindings
    global chk_selectinterfaces
    global input_frame, options_frame, operation_frame, output_frame
    global lst_Listbox_data

    win_jinjatool_main = tk.Toplevel()
    chk_selectcommon = tk.IntVar()
    chk_selectnames = tk.IntVar()
    chk_selectpolicybindings = tk.IntVar()
    chk_selectinterfaces = tk.IntVar()
    input_frame = tk.Frame(win_jinjatool_main)
    options_frame = tk.Frame(win_jinjatool_main, bd="2", highlightbackground="black", highlightthickness=1)
    operation_frame = tk.Frame(win_jinjatool_main)
    output_frame = tk.Frame(win_jinjatool_main)
    lst_Listbox_data = tk.Listbox(operation_frame, selectmode=tk.MULTIPLE)

    win_jinjatool_main.title('Jinja TOOL')
    win_jinjatool_main.geometry('900x700') # Size 200, 200



    lbl_api = tk.Label(input_frame, text=" ")
    btn_openfile = tk.Button(input_frame, text='Select YML File to OPEN', command=open_yml)
    btn_openapi = tk.Button(input_frame, text='Load YML via API', command=open_api, ) ###state="disabled"

    btn_convert = tk.Button(output_frame, text='Convert to JINJA', command=replace_selected)
    btn_revert = tk.Button(output_frame, text='Revert Selection to YAML', command=revert_selected)
    btn_save = tk.Button(output_frame, text='Save JINJA and CSV Parameters File', command=save_jinja)

    scrollbar = tk.Scrollbar(operation_frame)
    lst_Listbox_data.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=lst_Listbox_data.yview)
    lst_Listbox_data.bind("<Double-Button-1>", modify_item_jinja_var)

    input_frame.pack( fill="both")
    btn_openfile.pack(side="left", fill="both")
    btn_openapi.pack(side="right", fill="both")
    lbl_api.pack(side="right", fill="both")

    options_frame.pack(fill="both")
    lbl_labelcheckdescription = tk.Label(options_frame, text="Quick Select: ")
    lbl_labelcheckdescription.pack(side="left", fill="y")
    chk_chkselectcommon = tk.Checkbutton(options_frame, text='Site Location ', command=select_common_yml_params, variable=chk_selectcommon) 
    chk_chkselectcommon.pack(side="left", fill="y", padx=15)
    chk_chkselectnames = tk.Checkbutton(options_frame, text='Site/Element Names', command=select_names, variable=chk_selectnames) 
    chk_chkselectnames.pack(side="left", fill="y", padx=15)
    chk_chkpolicybindings = tk.Checkbutton(options_frame, text='Policy Bindings', command=select_common_policy_params, variable=chk_selectpolicybindings) 
    chk_chkpolicybindings.pack(side="left", fill="y", padx=15)

    chk_chkselectinterfaces = tk.Checkbutton(options_frame, text='Interfaces', command=select_names, variable=chk_selectinterfaces) 
    chk_chkselectinterfaces.pack(side="left", fill="y", padx=15)

    operation_frame.pack(expand=1, fill="both")
    scrollbar.pack(side="right", fill="y")
    lst_Listbox_data.pack(expand=1, fill="both", side="left")

    output_frame.pack(fill="both")
    btn_convert.pack(side="left",)
    btn_revert.pack(side="left",)
    btn_save.pack(side="right")
    
    win_jinjatool_main.lift(aboveThis=win_launchermain)
    win_jinjatool_main.grab_set()

win_launchermain = tk.Tk()
win_launchermain.title('Select Something to RUN')

lbl_current_key = tk.Label(win_launchermain, text="Select the tool to use:")

Main_window_height = 10
Main_window_width = 30

frame_opt1 = tk.Frame(height=1, bd=2, relief="sunken")
btn_jinja_tool = tk.Button(frame_opt1, text="1. JINJA/YML Maker Tool", height=Main_window_height, width=Main_window_width,highlightthickness = 0, bd = 0, command=launch_jinjatool)
lbl_desc_opt1 = tk.Label(frame_opt1, wraplength=Main_window_width*9,justify='left',text="Use this tool to get or manipulate a YML from Pull_Site and convert it into a JINJA and CSV Params file",  borderwidth=2, relief="ridge")

frame_opt2 = tk.Frame(height=1, bd=2, relief="sunken")
btn_csvmerge = tk.Button(frame_opt2, text="2. JINJA CSV Params Merge Tool", height=Main_window_height, width=Main_window_width,highlightthickness = 0, bd = 0, command=launch_csvjinjaparmstool)
lbl_desc_opt2 = tk.Label(frame_opt2, wraplength=Main_window_width*9,justify='left',text="Use this tool to combine a JINJA Template and CSV Parameters file into resulting YML Branch site files",  borderwidth=2, relief="ridge")

frame_opt3 = tk.Frame(height=1, bd=2, relief="sunken")
btn_dosite = tk.Button(frame_opt3, text="3. YML 'do_site' upload tool", height=Main_window_height, width=Main_window_width,highlightthickness = 0, bd = 0, )
lbl_desc_opt3 = tk.Label(frame_opt3, wraplength=Main_window_width*9,justify='left',text="Use this tool to upload a YML Site file to CloudGenix",  borderwidth=2, relief="ridge")

btn_jinja_tool.pack (expand=1, pady=5,  fill="both")
lbl_desc_opt1.pack()
btn_csvmerge.pack   (expand=1, pady=5,  fill="both")
lbl_desc_opt2.pack()
btn_dosite.pack     (expand=1, pady=5,  fill="both")
lbl_desc_opt3.pack()

frame_opt1.pack(fill="both", padx=5, pady=5,side="left")
frame_opt2.pack(fill="both", padx=5, pady=5,side="left")
frame_opt3.pack(fill="both", padx=5, pady=5,side="left")

win_launchermain.focus_set()

if platform() == 'Darwin':  # How Mac OS X is identified by Python
    system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')



tk.mainloop()
