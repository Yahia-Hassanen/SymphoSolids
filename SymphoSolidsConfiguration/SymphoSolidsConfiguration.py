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


# Colot Lib

green = '#aaf255'
L_grey = '#f2f2f7' #root bg
D_gray = '#e5e5ea' #frame_bg
blue = '#4a26fd'
L_teal = '#6ac4dc'
D_teal = '#008299'

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

frame = ctk.CTkFrame(root, fg_color=L_grey)
frame.grid(row=0, column=0, sticky='nsew')
frame.grid_rowconfigure(0, weight=1)
frame.grid_rowconfigure(1, weight=100)
frame.grid_rowconfigure(2, weight=100)
frame.grid_rowconfigure(3, weight=20)
frame.grid_rowconfigure(4, weight=1)

frame.grid_columnconfigure(0, weight=1)
frame.grid_columnconfigure(1, weight=1000)

# Console Frame-----------------------------------------------------------------------------------------------------------
f_console = ctk.CTkFrame(master=frame, fg_color=L_grey)
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

class Face:
    def __init__(self, accel_X, accel_Y, accel_Z):
        self.accel_X = accel_X
        self.accel_Y = accel_Y
        self.accel_Z = accel_Z

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
    button_connect.configure(text="Connect", command=confirm_selection, fg_color=L_teal, hover_color='#24cc44')


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
    global angles
    angles = []  # Reset the list for new calculations
    print("Calculating angle...")
    current_xyz_array = numpy.array([current_xyz['X'], current_xyz['Y'], current_xyz['Z']])

    for face in faces:
        face_index = faces.index(face)
        face_array = numpy.array([float(accel_X[face_index]), float(accel_Y[face_index]), float(accel_Z[face_index])])

        try:
            angle = math.acos(
                numpy.dot(face_array, current_xyz_array) /
                (numpy.linalg.norm(face_array) * numpy.linalg.norm(current_xyz_array))
            )
            angles.append(angle)  # Store the calculated angle
            print(f"Angle between current orientation and Face {face_index + 1} is:", round(angle, 3))
            print_to_console(f"Angle between current orientation and Face {face_index + 1} is: {round(angle, 3)}")
        except ValueError as e:
            print(f"Failed to calculate angle for Face {face_index + 1}: {e}")
            print_to_console(f"Failed to calculate angle for Face {face_index + 1}: {e}")

    # Highlight the closest angle
    highlight_closest()





async def notification_handler(sender, data):
    global record_message_sent, current_xyz
    try:
        print(f"Received data: {data}")
        print_to_console(f"Received data: {data}")

        if len(data) == 12:
            await parse_accelerometer_data(data)
            print("Data sent to parse")
            print_to_console("Data send to parse")

    except Exception as e:
        print(f"Error in notification handler: {e}")
        print_to_console(f"Error in notification handler: {e}")

    record_message_sent = False

def highlight_closest():
    print("Highlighting...")
    smallest_angle = min(angles)
    smallest_angle_index = angles.index(smallest_angle)
    print(f"The closest face value to {current_xyz} is {smallest_angle_index}")

    if test_toggle.get() == 1:
        # Reset highlight for all columns
        for mode_entries in [entries_mode1, entries_mode2, entries_mode3]:
            for key in ['X', 'Y', 'Z']:
                # Reset color for all entries in the column
                for i in range(len(mode_entries[key])):
                    mode_entries[key][i].configure(fg_color="#e5e5ea")

        # Highlight the entire column for the closest face
        for mode_entries in [entries_mode1, entries_mode2, entries_mode3]:
            for key in ['X', 'Y', 'Z']:
                label = mode_entries[key][smallest_angle_index]
                label.configure(fg_color="yellow")  # Highlight the label
                print(f"Highlighted {key} at index {smallest_angle_index}")

        time.sleep(2)
        print("Sending data")
        # Schedule the async function to run
        asyncio.create_task(send_data(client, "Record"))
        print("Data sent")

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
            # Write header
            file.write("#ifndef CONFIG_H\n#define CONFIG_H\n\n")
            file.write(f'#define DEVICE_NAME "{name_entry.get()}"\n')
            file.write(f'#define NUM_SIDES "{number_of_controls.get()}"\n\n')

            # Define struct
            file.write("struct FaceConfig {\n")
            file.write("    float x;\n")
            file.write("    float y;\n")
            file.write("    float z;\n")
            file.write("    byte note1;\n")
            file.write("    byte note2;\n")
            file.write("    byte note3;\n")
            file.write("};\n\n")

            # Write face configurations
            file.write("const FaceConfig faceConfigs[] = {\n")
            for i in range(number_of_controls.get()):  # Adjust the range according to the number of faces
                x = accel_X[i]
                y = accel_Y[i]
                z = accel_Z[i]
                note1 = entries_mode1['Note'][i].get()
                note2 = entries_mode2['Note'][i].get()
                note3 = entries_mode3['Note'][i].get()
                file.write(f"    {{{x}, {y}, {z}, {note1}, {note2}, {note3}}}, // Face {i+1}\n")
            file.write("};\n\n")

            # Calculate and write total faces
            file.write("const int totalFaces = sizeof(faceConfigs) / sizeof(faceConfigs[0]);\n\n")
            file.write("#endif // CONFIG_H\n")

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
    modes = {'MODE1': {'X': [0] * 20, 'Y': [0] * 20, 'Z': [0] * 20, 'NOTE': ['0'] * 20},
             'MODE2': {'X': [0] * 20, 'Y': [0] * 20, 'Z': [0] * 20, 'NOTE': ['0'] * 20},
             'MODE3': {'X': [0] * 20, 'Y': [0] * 20, 'Z': [0] * 20, 'NOTE': ['0'] * 20}}

    device_name = None
    num_sides = None
    face_configs = []

    with open(file_path, 'r') as file:
        inside_face_configs = False

        for line in file:
            line = line.strip()
            print("Processing line:", line)  # Debugging statement

            # Parse device name
            if '#define DEVICE_NAME' in line:
                device_name = line.split()[2].strip('"')
                print("Device Name:", device_name)
                # name_entry.delete(0, 'end')  # Clear the current value
                # name_entry.insert(0, device_name)  # Insert the new value

            # Parse number of sides
            elif '#define NUM_SIDES' in line:
                num_sides = int(line.split()[2].strip('"'))  # Convert to int for later use
                print("Number of Sides:", num_sides)
                # confirm_sides(num_sides)
                # number_of_controls.set(num_sides)

            # Detect the start of face configurations
            elif 'const FaceConfig faceConfigs[]' in line:
                print("Enter FaceConfig")
                inside_face_configs = True
                continue

            # Parse face configurations
            elif inside_face_configs and line.startswith('{') and line.endswith('},'):
                print("Parsing face configuration line:", line)  # Debugging statement
                line = line.strip('{};,')
                values = line.split(', ')

                if len(values) == 6:
                    face_config = {
                        'X': float(values[0]),
                        'Y': float(values[1]),
                        'Z': float(values[2]),
                        'NOTE': [int(values[3]), int(values[4]), int(values[5])]  # Store all Note values
                    }
                    face_configs.append(face_config)
                else:
                    print("Unexpected number of values in face configuration line")
            else:
                print("Skipping line:", line)

    print("Finished parsing file")  # Debugging statement

    # Process all faces and modes
    for mode in modes:
        mode_index = int(mode[-1]) - 1  # Convert mode (1, 2, 3) to index (0, 1, 2)
        for face_num, config in enumerate(face_configs, start=1):  # Faces 1 to num_sides
            face = f'Face {face_num}'
            data = {axis: config[axis] for axis in ['X', 'Y', 'Z']}
            data['Note'] = config['NOTE'][mode_index]  # Select the Note value based on the mode

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
            fg_color=L_teal,
            text_color="white",
            hover_color="#008299",
            font=('Bahnschrift SemiBold', 10),
            text_color_disabled='grey'
        )
        if col_index < 10:
            face_button.grid(row=0, column=col_index + 1, padx=5, pady=5, sticky='nsew')
        else:
            face_button.grid(row=7, column=col_index - 9, padx=5, pady=5, sticky='nsew')

    for row_index, label in enumerate(['Note', 'X', 'Y', 'Z'], start=2):
        ctk.CTkLabel(master=parent_frame, text=label, font=('Cascadia Code', 12)).grid(row=row_index, column=0,
                                                                                              padx=5, pady=5,
                                                                                              sticky='nsew')
        for col_index in range(1, 11):
            if label in ['X', 'Y', 'Z']:
                entry = ctk.CTkLabel(master=parent_frame, text="0", font=('Cascadia Code', 12))
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
        ctk.CTkLabel(master=parent_frame, text=label, font=('Cascadia Code', 12)).grid(row=row_index + 6,
                                                                                              column=0, padx=5, pady=5,
                                                                                              sticky='nsew')
        for col_index in range(11, 21):
            if label in ['X', 'Y', 'Z']:
                entry = ctk.CTkLabel(master=parent_frame, text="0", font=('Cascadia Code', 12))
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

header = ctk.CTkLabel(master=f_title, text="SymphoSolids", font=('Bahnschrift SemiBold', 42))
header.grid(row=0, column=0, columnspan=2)

sub_header = ctk.CTkLabel(master=f_title, text="Configuration", font=('Bahnschrift SemiBold', 32))
sub_header.grid(row=1, column=0, columnspan=2)

# Device Manager Frame-------------------------------------------------------------------------------------
f_device_manager = ctk.CTkFrame(master=frame, fg_color="#e5e5ea")
f_device_manager.grid(row=1, column=0, padx=10, pady=10, sticky='nw')

label = ctk.CTkLabel(master=f_device_manager, text="Device Manager", font=('Bahnschrift SemiBold', 16))
label.grid(row=0, column=0, padx=25, pady=5)

button_scan = ctk.CTkButton(f_device_manager, height=25, width=270, text="Scan for Devices",
                            command=lambda: asyncio.run_coroutine_threadsafe(scan_devices(), loop),
                            fg_color=L_teal, hover_color=D_teal, text_color="#302c2c")
button_scan.grid(row=1, column=0, padx=25, pady=5)

options = ["no devices available"]
device_menu = ctk.CTkOptionMenu(f_device_manager, height=25, width=270, variable=selected_address, values=options,
                                fg_color='#c7c7cc', text_color="#302c2c")
device_menu.grid(row=2, column=0, padx=25, pady=5)

button_connect = ctk.CTkButton(f_device_manager, text="Connect", height=25, width=270, command=confirm_selection,
                               fg_color=L_teal, hover_color='#24cc44', text_color="#302c2c")
button_connect.grid(row=3, column=0, padx=25, pady=5)

button_disconnect = ctk.CTkButton(f_device_manager, text="Disconnect", height=25, width=270, command=disconnect,
                                  fg_color=L_teal, hover_color='#ff375f', text_color="#302c2c")
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

f_controls = ctk.CTkFrame(master=frame, fg_color="#e5e5ea")
f_controls.grid(row=3, column=0, sticky='ew', padx=10, pady=10)

# Label
label_2 = ctk.CTkLabel(master=f_controls, text='Controls', font=('Bahnschrift SemiBold', 16), text_color="#302c2c")
label_2.grid(row=0, column=1, sticky='new', pady=5)


# Number display
sides_entry = ctk.CTkLabel(f_controls, textvariable=number_of_controls, font=('Bahnschrift SemiBold', 27),
                           text_color="#302c2c")
sides_entry.grid(row=1, column=1, padx=0, pady=(0, 10), sticky='new')


# Down button
button_down = ctk.CTkButton(
    f_controls, text="▼", height=30, width=45,
    command=lambda: [
        number_of_controls.set(max(4, number_of_controls.get() - 1)),  # Ensure the value doesn't go below 4
        confirm_sides(number_of_controls.get()),
        indicate_limit(sides_entry) if number_of_controls.get() == 4 else None
    ],
    fg_color=L_teal, hover_color=D_teal, font=('Bahnschrift SemiBold', 12)
)
button_down.grid(row=1, column=0, sticky='nsw')

# Up button
button_up = ctk.CTkButton(
    f_controls, text="▲", height=30, width=45,
    command=lambda: [
        number_of_controls.set(min(20, number_of_controls.get() + 1)),  # Ensure the value doesn't go above 20
        confirm_sides(number_of_controls.get()),
        indicate_limit(sides_entry) if number_of_controls.get() == 20 else None
    ],
    fg_color=L_teal, hover_color=D_teal, font=('Bahnschrift SemiBold', 12)
)
button_up.grid(row=1, column=2, sticky='nsw')


# Toggle switch
check_var = ctk.StringVar(value="off")  # Set checkbox as off
test_toggle = ctk.CTkSwitch(f_controls, text="Active Tracking", font=('Bahnschrift SemiBold', 10), height=25, width=60,
                            fg_color=L_teal, text_color="#302c2c", switch_width=100,switch_height=30, progress_color="#6ac4dc")
test_toggle.grid(row=3, column=1, pady=(5, 0))


async def toggle_dp_sensor():
    if test_toggle.get() == 1:
        print("Toggle On. Active Tracking On")
        print_to_console("Toggle On. Active Tracking On")

        await send_data(client, "Record")
    else:
        # Reset highlight for all columns
        for mode_entries in [entries_mode1, entries_mode2, entries_mode3]:
            for key in ['X', 'Y', 'Z']:
                # Reset color for all entries in the column
                for i in range(len(mode_entries[key])):
                    mode_entries[key][i].configure(fg_color="#e5e5ea")


def run_toggle_dp_sensor():
    asyncio.run(toggle_dp_sensor())
    print("pass to async")



test_toggle.configure(command=run_toggle_dp_sensor)

for widget in f_controls.winfo_children():
    widget.grid_configure(padx=5, pady=5)

# File Management -------------------------------------------------------------------------------------
f_file = ctk.CTkFrame(master=frame, fg_color="#e5e5ea")
f_file.grid(row=4, column=0, padx=10, pady=5, sticky='nsw')

button_save = ctk.CTkButton(master=f_file, height=25, width=280, text="Save to File", fg_color=L_teal,
                            hover_color=D_teal, text_color="#302c2c", command=save_file)
button_save.grid(row=0, column=0, padx=10, pady=5)

button_import = ctk.CTkButton(master=f_file, height=25, width=280, text="Import File", fg_color=L_teal,
                              hover_color=D_teal, text_color="#302c2c", command=import_file)
button_import.grid(row=1, column=0, padx=10, pady=5)



# Face Values Frame -------------------------------------------------------------------------------------
f_face = ctk.CTkFrame(master=frame, fg_color='transparent')
f_face.grid(row=1, column=1, rowspan=4, sticky='nsew', padx=10, pady=10)

entries = {label: [] for label in ['Note', 'X', 'Y', 'Z']}
create_face_layout(f_face, entries)

row_labels = ['Note', 'X', 'Y', 'Z']
last_selected_face = None

tabview = CTkTabview(frame, segmented_button_fg_color=blue, segmented_button_unselected_color=blue, fg_color=D_gray)
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
