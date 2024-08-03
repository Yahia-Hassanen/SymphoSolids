#File: SymphoSolidsConfiguration
import asyncio
import customtkinter as ctk
import keyboard
import struct
import time
from customtkinter import *
from customtkinter import filedialog
import math
import numpy
import re
import itertools
import threading
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError, BleakDeviceNotFoundError

# BLE Definitions ------------------------------------------------------------------------------------------------
WRITE_CHARACTERISTIC_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
NOTIFICATION_CHARACTERISTIC_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

# GUI Root -----------------------------------------------------------------------------------------------------------
root = ctk.CTk()
root.geometry("1030x770")
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("dark-blue")
root.title("SymphoSolids Configuration")
root.resizable(0, 0)

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
root.aspect(1, 1, 1, 1)

root.after(201, lambda: root.iconbitmap(
    'C:/Users/1yahi/Desktop/Dr Chan Summer 24/Musical instruments/Accessory Code/music.ico'))

frame = ctk.CTkFrame(root, fg_color="#f2f2f7")
frame.grid(row=0, column=0, sticky='nsew')
frame.grid_rowconfigure(0, weight=1)
frame.grid_rowconfigure(1, weight=100)
frame.grid_rowconfigure(2, weight=100)
frame.grid_rowconfigure(3, weight=20)
frame.grid_rowconfigure(4, weight=1)

frame.grid_columnconfigure(0, weight=1)
frame.grid_columnconfigure(1, weight=1000)

# Console Frame-----------------------------------------------------------------------------------------------------------
f_console = ctk.CTkFrame(master=frame, fg_color="#f2f2f7")
f_console.grid(row=5, column=0, padx=25, pady=25, columnspan=2, sticky='nsew')

label_console = ctk.CTkLabel(master=f_console, text='Serial Monitor', font=('Bahnschrift SemiBold', 12))
label_console.grid(row=0, column=0, sticky='nswe')

console_text = ctk.CTkTextbox(master=f_console, height=85, width=965, state='disabled', font=('arial', 7))
console_text.grid(row=1, column=0, padx=10, pady=0, sticky='nswe')

version_text = ctk.CTkLabel(master=f_console, text='v1.0', font=('Bahnschrift SemiBold', 12), anchor='center')
version_text.grid(row=2, column=0, sticky='nswe')

f_console.grid_rowconfigure(1, weight=3)
f_console.grid_rowconfigure(2, weight=0)

# Variable Definitions-------------------------------------------------------------------------------------------
device_addresses = {}
selected_address = ctk.StringVar(value="      Select Device")
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
record_lock = threading.Lock()

global current_xyz
current_xyz = None


faces = [f"Face {i}" for i in range(1, 21)]
number_of_controls = ctk.IntVar(value=4)  # Default value
device_name = ctk.StringVar(value='')  # Default value
angle_vars = [ctk.StringVar() for i in faces]


accel_X = [0] * 20
accel_Y = [0] * 20
accel_Z = [0] * 20


# List to accumulate received face data
received_faces = []
client = None
debounce_timer = None


# Function Definitions----------------------------------------------------------------------------------------------
def print_to_console(text):
    console_text.configure(state='normal')
    console_text.insert('end', text + '\n')
    console_text.configure(state='disabled')
    console_text.see('end')  # Auto-scroll to the end


def create_popup(msg):
    popup = ctk.CTkToplevel(root)
    popup.title("Scanning for Devices")
    popup.geometry("300x100")
    popup.transient(root)
    popup.grab_set()

    label = ctk.CTkLabel(popup, text=msg, font=('Bahnschrift SemiBold', 16))
    label.pack(pady=20)

    def update_label():
        dots = itertools.cycle(["", ".", "..", "..."])

        def run_update():
            if popup.winfo_exists():
                label.configure(text=f"{msg}{next(dots)}")
                root.after(500, run_update)  # Schedule the next update

        run_update()

    threading.Thread(target=update_label, daemon=True).start()
    return popup


async def scan_devices():
    popup = create_popup("Scanning")
    try:
        print("Scanning for devices...")
        print_to_console("Scanning for devices...")
        devices = await BleakScanner.discover()
        device_addresses.clear()
        for device in devices:
            if device.name:  # Ensure the device has a name
                print(f"Found device: {device.name} - Address: {device.address}")
                print_to_console(f"Found device: {device.name} - Address: {device.address}")
                device_addresses[device.name] = device.address
        root.after(0, update_device_menu)  # Schedule update_device_menu to run in the main thread
    except BleakError as e:
        print(f"Bleak error: {e}")
        print_to_console(f"Bleak error: {e}")
    finally:
        popup.destroy()


def update_device_menu():
    options = [name for name in device_addresses.keys() if name]  # Filter out None values
    print(f"Updating device menu with options: {options}")
    print_to_console(f"Updating device menu with options: {options}")
    device_menu.configure(values=options)


def confirm_selection():
    choice = selected_address.get()
    address = device_addresses.get(choice)
    if address:
        asyncio.run_coroutine_threadsafe(connect_to_device(address), loop)
    else:
        print("No device selected or device address not found")
        print_to_console("No device selected or device address not found")


async def send_data(client, data):
    try:
        print(f"Sending data: {data}")
        print_to_console(f"Sending data: {data}")
        await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, bytearray(data, 'utf-8'))
        print("Data sent successfully.")
        print_to_console("Data sent successfully.")
    except Exception as e:
        print(f"Failed to send data: {e}")
        print_to_console(f"Failed to send data: {e}")


def disconnect():
    global client
    if client:
        asyncio.run_coroutine_threadsafe(client.disconnect(), loop)
        client = None
    print(f"Disconnected")
    print_to_console(f"Disconnected")

    # Reset the button back to original state
    button_connect.configure(text="Connect", command=confirm_selection, fg_color='#6ac4dc', hover_color='#24cc44')


def confirm_sides(sides):
    sides=int(sides)
    global debounce_timer
    if debounce_timer is not None:
        root.after_cancel(debounce_timer)
    debounce_timer = root.after(3000, lambda: [update_face_buttons_and_entries(sides, tabs)])



def parse_accelerometer_data(data):
    try:
        accelX, accelY, accelZ = struct.unpack('fff', data)
        accelX = round(accelX, 2)
        accelY = round(accelY, 2)
        accelZ = round(accelZ, 2)

        if test_toggle.get() == 1:
            current_xyz = {'X': accelX, 'Y': accelY, 'Z': accelZ}
            print(f"Current Orientation: {current_xyz}")
            print_to_console(f"Current Orientation: {current_xyz}")
            angle_between(current_xyz)
            print(f"Sent to angle calc")
        else:
            parsed_data = {'X': accelX, 'Y': accelY, 'Z': accelZ}
            print(f"Parsed data: X={parsed_data['X']}, Y={parsed_data['Y']}, Z={parsed_data['Z']}")
            print_to_console(f"Parsed data: X={parsed_data['X']}, Y={parsed_data['Y']}, Z={parsed_data['Z']}")
            update_entries(last_selected_face, parsed_data)
    except struct.error as e:
        print(f"Failed to parse data: {e}")
        print_to_console(f"Failed to parse data: {e}")
        return {}



def angle_between(current_xyz):
    print("Calculating...")
    for i in faces:
        face_index = faces.index(face)
        data = {
            'X': float(accel_X[face_index]),
            'Y': float(accel_Y[face_index]),
            'Z': float(accel_Z[face_index])
        }
        angle = math.acos(numpy.vecdot(face,current_xyz)/(numpy.linalg.vectornorm(face)*numpy.linalg.vector_norm(current_xyz)))
        print(f"Angle between current orientation and Face {i} is:",round(angle,3))
        highlight_closest()


async def notification_handler(sender, data):
    global record_message_sent, current_xyz
    try:
        print(f"Received data: {data}")
        print_to_console(f"Received data: {data}")

        if len(data) == 12:
            parsed_data = parse_accelerometer_data(data)
            print("Data sent to parse")
            print_to_console("Data send to parse")
    except Exception as e:
        print(f"Error in notification handler: {e}")
        print_to_console(f"Error in notification handler: {e}")

    record_message_sent = False

def highlight_closest():
    smallest_angle = min(abs(angles))
    smallest_angle_index = angles.index(smallest_angle)
    print(f"The closest face value to {current_xyz} is {smallest_angle_index}")

    for label, value in zip(entries_mode1[' Angle'], angle_values):
        if value == smallest_angle:
            label.configure(fg_color="yellow")  # Highlight smallest value
            print("highlighted!")
        else:
            label.configure(fg_color="#e5e5ea")  # Reset color for other labels

def update_entries(face, data):
    col_index = faces.index(face)
    for entries in [entries_mode1, entries_mode2, entries_mode3]:
        for key in ['X', 'Y', 'Z']:
            value = data.get(key, '0')


            entries[key][col_index].configure(text=str(value))

            # Update the corresponding list with the new value
            if key == 'X':
                accel_X[col_index] = value
            elif key == 'Y':
                accel_Y[col_index] = value
            elif key == 'Z':
                accel_Z[col_index] = value

        for key in entries:
            if key == 'Note':
                entries[key][col_index].configure(state="normal")
                entries[key][col_index].delete(0, 'end')
                if key in data:
                    entries[key][col_index].insert(0, str(data[key]))
                else:
                    entries[key][col_index].insert(0, '0')

        if 'Note' in data:
            note_value = data['Note']
            note_widget = entries['Note'][col_index]
            note_widget.bind("<Key>", restrict_space_key)
            note_widget.bind("<Key>", restrict_input)
            print(f"Updating Note widget at column {col_index} with value: {note_value}")
            note_widget.configure(state="normal")
            note_widget.delete(0, 'end')
            note_widget.insert(0, str(note_value))
            print(f"Note widget updated with value: {note_widget.get()}")




def indicate_limit(label):
    def update_color():
        sides = number_of_controls.get()
        if sides == 4 or sides == 20:
            label.configure(text_color='#ff375f')
        else:
            label.configure(text_color='black')
        root.after(100, update_color)

    update_color()


# Add a flag to debounce the "Record" message
record_message_sent = False


async def record_face(selected_face):
   global last_selected_face
   global record_message_sent


   with record_lock:
       if not record_message_sent:
           await send_data(client, f"Record")
           record_message_sent = True


       last_selected_face = selected_face


def save_file():
    file_path = filedialog.asksaveasfilename(
        initialdir="C://Users//1yahi//Desktop",
        defaultextension=".h",
        filetypes=[("Header files", "*.h"), ("All files", "*.*")]
    )

    if not file_path:
        print("Save operation cancelled")
        return

    try:
        with open(file_path, 'w') as file:
            file.write("#ifndef CONFIG_H\n#define CONFIG_H\n\n")
            file.write('#define DEVICE_NAME "blablabla"\n')
            file.write('#define NUM_SIDES "20"\n\n\n')

            # Write X, Y, Z and DotProduct values once for each face
            for i in range(20):
                file.write(f"#define Face {i+1}_X {accel_X[i]}\n")
                file.write(f"#define Face {i+1}_Y {accel_Y[i]}\n")
                file.write(f"#define Face {i+1}_Z {accel_Z[i]}\n")

            # Write Notes for each mode separately
            for mode in ['MODE1', 'MODE2', 'MODE3']:
                for i in range(20):
                    file.write(f"#define {mode}_Face {i+1}_NOTE {entries_mode1['Note'][i].get() if mode == 'MODE1' else entries_mode2['Note'][i].get() if mode == 'MODE2' else entries_mode3['Note'][i].get()}\n")

            file.write("\n#endif // CONFIG_H\n")

        print("File saved successfully")
        print_to_console("File saved successfully")
    except Exception as e:
        print(f"Failed to save file: {e}")
        print_to_console(f"Failed to save file: {e}")


def restrict_space_key(event):
    if event.keysym == 'space':
        return "break"

def restrict_input(event):
    allowed_keys = ['BackSpace', 'Left', 'Right', 'Up', 'Down', 'Delete', 'Tab', 'Return']
    if event.keysym in allowed_keys:
        return
    elif event.char.isdigit():
        current_value = event.widget.get()
        # Check if the current input plus the new character is within the range
        new_value = current_value + event.char
        if int(new_value) > 127:
            return "break"
    else:
        return "break"


def parse_h_file(file_path):
    print("Initiating parse_h_file")  # Debugging statement

    # Initialize dictionaries to store accelerometer data
    modes = {'MODE1': {'X': [0] * 25, 'Y': [0] * 25, 'Z': [0] * 25, 'NOTE': ['0'] * 20},
             'MODE2': {'X': [0] * 25, 'Y': [0] * 25, 'Z': [0] * 25, 'NOTE': ['0'] * 20},
             'MODE3': {'X': [0] * 25, 'Y': [0] * 25, 'Z': [0] * 25, 'NOTE': ['0'] * 20}}

    # Regular expression to match lines with data
    pattern = re.compile(r'#define\s+(\w+)_Face\s+(\d+)_([XYZ]|NOTE)\s+([0-9.-]+)')

    with open(file_path, 'r') as file:
        for line in file:
            match = pattern.match(line)
            if match:
                mode = match.group(1)
                face_num = int(match.group(2))
                key = match.group(3)
                value = match.group(4)

                print(f"Matched - Mode: {mode}, Face Number: {face_num}, Key: {key}, Value: {value}")

                if mode in modes:
                    if key in modes[mode]:
                        modes[mode][key][face_num - 1] = value
                    else:
                        print("Unexpected key:", key)
                else:
                    print("Unexpected mode:", mode)
            elif '#define' in line and 'DEVICE_NAME' in line:
                device_name = line.split()[2].strip('"')
                print("Device Name:", device_name)
                name_entry.delete(0, 'end')  # Clear the current value
                name_entry.insert(0, device_name)  # Insert the new value
            elif '#define' in line and 'NUM_SIDES' in line:
                rec_sides=line.split()[2].strip('"')
                print("Number of Sides:", rec_sides)
                confirm_sides(rec_sides)
                print("Called confirm_sides")
                number_of_controls.set(rec_sides)
                print("Counter updated")

            else:
                print("Skipping line:", line.strip())

    print("Finished parsing file")  # Debugging statement

    # Process all faces and modes
    for mode in modes:
        for face_num in range(1, 21):  # Faces 1 to 20
            face = f'Face {face_num}'
            data = {axis: modes[mode][axis][face_num - 1] for axis in ['X', 'Y', 'Z']}
            data['Note'] = modes[mode]['NOTE'][face_num - 1]

            # Debugging: print the data to be passed to update_entries
            print(f"Updating entries for {face} in {mode} with data: {data}")

            update_entries(face, data)

def import_file():
    print("Initiating import_file")  # Debugging statement
    print_to_console("Initiating import_file")
    file_path = filedialog.askopenfilename(filetypes=[("Header files", "*.h")])
    if file_path:
        data = parse_h_file(file_path)
    print("Finished import_file")  # Debugging statement
    print_to_console("Finished import_file")  # Debugging statement


def create_face_layout(parent_frame, entries):
    for col_index, face in enumerate(faces):
        face_button = ctk.CTkButton(
            master=parent_frame,
            text=face,
            command=lambda v=face: asyncio.run_coroutine_threadsafe(record_face(v), loop),
            height=25,
            width=50,
            fg_color="#6ac4dc",
            text_color="#302c2c",
            hover_color="#008299",
            font=('Bahnschrift SemiBold', 10),
            text_color_disabled='grey'
        )
        if col_index < 10:
            face_button.grid(row=0, column=col_index + 1, padx=5, pady=5, sticky='nsew')
        else:
            face_button.grid(row=7, column=col_index - 9, padx=5, pady=5, sticky='nsew')

    for row_index, label in enumerate(['Note', 'X', 'Y', 'Z'], start=2):
        ctk.CTkLabel(master=parent_frame, text=label, font=('Bahnschrift SemiBold', 12)).grid(row=row_index, column=0,
                                                                                              padx=5, pady=5,
                                                                                              sticky='nsew')
        for col_index in range(1, 11):
            if label in ['X', 'Y', 'Z']:
                entry = ctk.CTkLabel(master=parent_frame, text="0", font=('Bahnschrift SemiBold', 12))
                entry.grid(row=row_index, column=col_index, padx=5, pady=5, sticky='nsew')
                entries[label].append(entry)
            else:
                entry = ctk.CTkEntry(master=parent_frame, width=50, height=5)
                entry.configure(state="normal")
                entry.bind("<Key>", restrict_space_key)
                entry.bind("<Key>", restrict_input)
                entry.grid(row=row_index, column=col_index, padx=5, pady=5, sticky='nsew')
                entry.insert(0, '0')
                entries[label].append(entry)

    for row_index, label in enumerate(['Note', 'X', 'Y', 'Z'], start=2):
        ctk.CTkLabel(master=parent_frame, text=label, font=('Bahnschrift SemiBold', 12)).grid(row=row_index + 6,
                                                                                              column=0, padx=5, pady=5,
                                                                                              sticky='nsew')
        for col_index in range(11, 21):
            if label in ['X', 'Y', 'Z']:
                entry = ctk.CTkLabel(master=parent_frame, text="0", font=('Bahnschrift SemiBold', 12))
                entry.grid(row=row_index + 6, column=col_index - 10, padx=5, pady=5, sticky='nsew')
                entries[label].append(entry)
            else:
                entry = ctk.CTkEntry(master=parent_frame, width=50, height=5)
                entry.configure(state="normal")
                entry.bind("<Key>", restrict_space_key)
                entry.bind("<Key>", restrict_input)
                entry.grid(row=row_index + 6, column=col_index - 10, padx=5, pady=5, sticky='nsew')
                entry.insert(0, '0')
                entries[label].append(entry)

# Title Frame ---------------------------------------------------------------------------------------------

f_title = ctk.CTkFrame(master=frame, fg_color='transparent')
f_title.grid(row=0, column=0, columnspan=2)

header = ctk.CTkLabel(master=f_title, text="SymphoSolids: Configuration", font=('Bahnschrift SemiBold', 42))
header.grid(row=0, column=0, columnspan=2)

# Device Manager Frame-------------------------------------------------------------------------------------
f_device_manager = ctk.CTkFrame(master=frame, fg_color="#e5e5ea")
f_device_manager.grid(row=1, column=0, padx=10, pady=10, sticky='nw')

label = ctk.CTkLabel(master=f_device_manager, text="Device Manager", font=('Bahnschrift SemiBold', 16))
label.grid(row=0, column=0, padx=25, pady=5)

button_scan = ctk.CTkButton(f_device_manager, height=25, width=270, text="Scan for Devices",
                            command=lambda: asyncio.run_coroutine_threadsafe(scan_devices(), loop),
                            fg_color='#6ac4dc', hover_color='#008299', text_color="#302c2c")
button_scan.grid(row=1, column=0, padx=25, pady=5)

options = ["no devices available"]
device_menu = ctk.CTkOptionMenu(f_device_manager, height=25, width=270, variable=selected_address, values=options,
                                fg_color='#c7c7cc', text_color="#302c2c")
device_menu.grid(row=2, column=0, padx=25, pady=5)

button_connect = ctk.CTkButton(f_device_manager, text="Connect", height=25, width=270, command=confirm_selection,
                               fg_color='#6ac4dc', hover_color='#24cc44', text_color="#302c2c")
button_connect.grid(row=3, column=0, padx=25, pady=5)

button_disconnect = ctk.CTkButton(f_device_manager, text="Disconnect", height=25, width=270, command=disconnect,
                                  fg_color='#6ac4dc', hover_color='#ff375f', text_color="#302c2c")
button_disconnect.grid(row=4, column=0, padx=25, pady=5)

for widget in f_device_manager.winfo_children():
    widget.grid_configure(padx=20, pady=5)

# Name Frame -------------------------------------------------------------------------------------
f_name = ctk.CTkFrame(master=frame, fg_color="#e5e5ea")
f_name.grid(row=2, column=0, padx=10, pady=5, sticky='nw')

label_2 = ctk.CTkLabel(master=f_name, text='Name Device', anchor='center', font=('Bahnschrift SemiBold', 16),
                       text_color="#302c2c")
label_2.grid(row=0, column=0, padx=25, pady=5)

name_entry = ctk.CTkEntry(master=f_name, textvariable=device_name, placeholder_text='enter name', height=25, width=270)
name_entry.grid(row=1, column=0, padx=25, pady=5)
name_entry.bind("<Key>", restrict_space_key)


for widget in f_name.winfo_children():
    widget.grid_configure(padx=20, pady=5)


# Controls Frame (Functions and Widgets) -------------------------------------------------------------------------------------
frame.grid_rowconfigure(3, weight=1)
frame.grid_columnconfigure(0, weight=1)

f_controls = ctk.CTkFrame(master=frame, fg_color="#e5e5ea")
f_controls.grid(row=3, column=0, sticky='ew', padx=10, pady=10)

label_2 = ctk.CTkLabel(master=f_controls, text='Controls', font=('Bahnschrift SemiBold', 16), text_color="#302c2c")
label_2.grid(row=0, column=0, columnspan=3, padx=10, pady=5)

button_up = ctk.CTkButton(
    f_controls, text="▲", height=12, width=12,
    command=lambda: [
        number_of_controls.set(min(25, number_of_controls.get() + 1)),  # Ensure the value doesn't go above 20
        confirm_sides(number_of_controls.get()),
        indicate_limit(sides_entry) if number_of_controls.get() == 20 else None
    ],
    fg_color='#6ac4dc', hover_color='#008299', font=('Bahnschrift SemiBold', 12)
)
button_up.grid(row=1, column=0, ipadx=5, ipady=5)

sides_entry = ctk.CTkLabel(f_controls, textvariable=number_of_controls, font=('Bahnschrift SemiBold', 27),
                           text_color="#302c2c")
sides_entry.grid(row=1, column=1, padx=10, pady=5)

button_down = ctk.CTkButton(
    f_controls, text="▼", height=12, width=12,
    command=lambda: [
        number_of_controls.set(max(4, number_of_controls.get() - 1)),  # Ensure the value doesn't go below 4
        confirm_sides(number_of_controls.get()),
        indicate_limit(sides_entry) if number_of_controls.get() == 4 else None
    ],
    fg_color='#6ac4dc', hover_color='#008299', font=('Bahnschrift SemiBold', 12)
)
button_down.grid(row=1, column=2, ipadx=5, ipady=5)

check_var = ctk.StringVar(value="off")  #set checkbox as off


def hide_dp():
    # Loop over the three modes
    for entries in [entries_mode1, entries_mode2, entries_mode3]:
        # First set of 10 columns
        for col_index in range(1, 11):
            entries['Dot Product'][col_index - 1].grid_forget()

        # Second set of 10 columns
        for col_index in range(11, 21):
            entries['Dot Product'][col_index - 1].grid_forget()

    print("DP Hidden")
    print_to_console("DP Hidden")


def show_dp():
    # Loop over the three modes
    for entries in [entries_mode1, entries_mode2, entries_mode3]:
        # First set of 10 columns
        for col_index in range(1, 11):
            entries['Dot Product'][col_index - 1].grid(row=6, column=col_index, padx=5, pady=5, sticky='nsew')

        # Second set of 10 columns
        for col_index in range(11, 21):
            entries['Dot Product'][col_index - 1].grid(row=12, column=col_index - 10, padx=5, pady=5, sticky='nsew')

    print("DP Visible")
    print_to_console("DP Visible")


def checkbox_event():
    print("checkbox toggled, current value:", check_var.get())
    if check_var.get() == "on":
        show_dp()
    else:
        hide_dp()


checkbox = ctk.CTkCheckBox(master=f_controls, text="Show Dot Product", command=checkbox_event,
                           variable=check_var, onvalue="on", offvalue="off", font=('Bahnschrift SemiBold', 10) )
checkbox.grid(row=2, column=0, columnspan=1, sticky='nw')

test_toggle = ctk.CTkSwitch(f_controls, text="Highlight closest", font=('Bahnschrift SemiBold', 10), height=25, width=60,
                            fg_color='#6ac4dc', text_color="#302c2c")
test_toggle.grid(row=2, column=2, columnspan=1, padx=5, pady=5, sticky='ne')


async def toggle_dp_sensor():
    if test_toggle.get() == 1:
        print("Toggle On. Active Tracking On")
        print_to_console("Toggle On. Active Tracking On")

        await send_data(client, "Active Tracking")
    else:
        print("Toggle Off switch. Active Tracking Off.")
        await asyncio.sleep(1)  # Check the toggle state every 1 second

def run_toggle_dp_sensor():
    asyncio.run(toggle_dp_sensor())
    print("pass to async")



test_toggle.configure(command=run_toggle_dp_sensor)

for widget in f_controls.winfo_children():
    widget.grid_configure(padx=5, pady=5)

# File Management -------------------------------------------------------------------------------------
f_file = ctk.CTkFrame(master=frame, fg_color="#e5e5ea")
f_file.grid(row=4, column=0, padx=10, pady=5, sticky='nsw')

button_save = ctk.CTkButton(master=f_file, height=25, width=280, text="Save to File", fg_color='#6ac4dc',
                            hover_color='#008299', text_color="#302c2c", command=save_file)
button_save.grid(row=0, column=0, padx=10, pady=5)

button_import = ctk.CTkButton(master=f_file, height=25, width=280, text="Import File", fg_color='#6ac4dc',
                              hover_color='#008299', text_color="#302c2c", command=import_file)
button_import.grid(row=1, column=0, padx=10, pady=5)





# Face Values Frame -------------------------------------------------------------------------------------
f_face = ctk.CTkFrame(master=frame, fg_color='transparent')
f_face.grid(row=1, column=1, rowspan=4, sticky='nsew', padx=10, pady=10)

entries = {label: [] for label in ['Note', 'X', 'Y', 'Z']}
create_face_layout(f_face, entries)

row_labels = ['Note', 'X', 'Y', 'Z']
last_selected_face = None

tabview = CTkTabview(frame)
tabview.grid(row=1, column=1, rowspan=4, sticky='nsew', padx=10, pady=10)

# Create three tabs
tab_faces1 = tabview.add("Mode 1")
tab_faces2 = tabview.add("Mode 2")
tab_faces3 = tabview.add("Mode 3")

tabs = [tab_faces1, tab_faces2, tab_faces3]

# Add the layout to each tab
create_face_layout(tab_faces1, entries)
create_face_layout(tab_faces2, entries)
create_face_layout(tab_faces3, entries)

entries_A = {label: [] for label in ['Note', 'X', 'Y', 'Z', 'Dot Product']}
entries_B = {label: [] for label in ['Note', 'X', 'Y', 'Z', 'Dot Product']}


# Overall Organization-------------------------------------------------------
for widget in frame.winfo_children():
    widget.grid_configure(padx=10, pady=5, ipady=10)

def update_face_buttons_and_entries(sides, tabs):
    # Iterate over each tab
    for tab in tabs:
        # Update buttons and entries for faces
        for col_index in range(20):
            try:
                # Determine the row and column for the face button
                row, col = (0, col_index + 1) if col_index < 10 else (7, col_index - 9)

                # Update the face button
                face_button = tab.grid_slaves(row=row, column=col)[0]
                face_button.configure(state="normal" if col_index < sides else "disabled")

                # Update the entries
                for row_index, label in enumerate(['Note', 'X', 'Y', 'Z']):
                    entry_list = entries_A[label] if col_index < 10 else entries_B[label]
                    entry_col_index = col_index if col_index < 10 else col_index - 10

                    if entry_col_index < len(entry_list):
                        entry_list[entry_col_index].configure(state="normal" if col_index < sides else "disabled")
            except IndexError:
                continue

# Main function----------------------------------------------------------------------------------------------------
def update_interface_on_connection(status):
    # Define the list of widgets to disable/enable
    widgets_to_control = {
        'tab_faces1': tab_faces1.winfo_children(),
        'tab_faces2': tab_faces2.winfo_children(),
        'tab_faces3': tab_faces3.winfo_children(),
        'f_name': f_name.winfo_children(),
        'f_controls': f_controls.winfo_children()
    }

    # Disable/enable widgets based on connection status
    state = "normal" if status else "disabled"
    for widget_list in widgets_to_control.values():
        for widget in widget_list:
            widget.configure(state=state)


async def main():
    await scan_devices()


async def connect_to_device(address):
    popup = create_popup("Connecting")
    global client
    try:
        print(f"Attempting to connect to {address}")
        print_to_console(f"Attempting to connect to {address}")
        client = BleakClient(address)
        await client.connect()
        print(f"Connected to {address}")

        # Enable the interface on successful connection
        update_interface_on_connection(True)

        # Update the button to show connected status
        button_connect.configure(text="Connected", fg_color='#24cc44', command=connect_to_device)

        confirm_sides(number_of_controls.get())
        popup.destroy()

        services = await client.get_services()

        for service in services:
            print(f"Service: {service.uuid}")
            print_to_console(f"Service: {service.uuid}")

            for characteristic in service.characteristics:
                print(f"  Characteristic: {characteristic.uuid}")
                print_to_console(f"  Characteristic: {characteristic.uuid}")

        await client.start_notify(NOTIFICATION_CHARACTERISTIC_UUID, notification_handler)

        print("Press 'Esc' to exit.")
        print_to_console("Press 'Esc' to exit.")

        while True:
            if keyboard.is_pressed('esc'):
                print("Exiting...")
                print_to_console("Exiting...")
                break
            await asyncio.sleep(0.1)

        await client.stop_notify(NOTIFICATION_CHARACTERISTIC_UUID)
        await client.disconnect()
        print("Disconnected")
        print_to_console("Disconnected")

        # Reset the button back to original state
        button_connect.configure(text="Connect", command=confirm_selection, fg_color='#302c2c', hover_color='#24cc44')

        # Disable the interface after disconnection
        update_interface_on_connection(False)


    except BleakDeviceNotFoundError:
        print(f"Device with address {address} was not found. Ensure the device is on and in range.")
        print_to_console(f"Device with address {address} was not found. Ensure the device is on and in range.")
    except BleakError as e:
        print(f"Bleak error: {e}")
    except Exception as e:
        print(f"Failed to connect to {address}: {e}")
        print_to_console(f"Failed to connect to {address}: {e}")


entries_mode1 = {label: [] for label in ['Note', 'X', 'Y', 'Z', 'Dot Product']}
entries_mode2 = {label: [] for label in ['Note', 'X', 'Y', 'Z', 'Dot Product']}
entries_mode3 = {label: [] for label in ['Note', 'X', 'Y', 'Z', 'Dot Product']}

create_face_layout(tab_faces1, entries_mode1)
create_face_layout(tab_faces2, entries_mode2)
create_face_layout(tab_faces3, entries_mode3)




# Disable the interface initially
update_interface_on_connection(False)


def run_asyncio():
    loop.run_until_complete(main())
    root.after(100, process_asyncio_events)
    root.mainloop()


def process_asyncio_events():
    try:
        loop.stop()
        loop.run_forever()
    except Exception as e:
        print(f"Error in process_asyncio_events: {e}")
    root.after(100, process_asyncio_events)


if __name__ == "__main__":
    run_asyncio()
