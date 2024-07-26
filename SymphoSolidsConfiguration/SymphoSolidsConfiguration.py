import asyncio
import customtkinter as ctk
import keyboard
import struct
import time
from customtkinter import *
from customtkinter import filedialog
import math
import itertools
import threading
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError, BleakDeviceNotFoundError

# BLE Definitions ------------------------------------------------------------------------------------------------
WRITE_CHARACTERISTIC_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
NOTIFICATION_CHARACTERISTIC_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

# GUI Root -----------------------------------------------------------------------------------------------------------
root = ctk.CTk()
root.geometry("1020x770")
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
f_console.grid(row=5, column=0, padx=20, pady=20, columnspan=2, sticky='nsew')

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
dot_product_visible = ctk.BooleanVar(value=False)

global current_dot_prod
current_dot_prod = None


faces = [f"Face {i}" for i in range(1, 21)]
number_of_sides = ctk.IntVar(value=4)  # Default value
device_name = ctk.StringVar(value='')  # Default value
dot_product_vars = [ctk.StringVar() for i in faces]

unit_vector = [0, 0, 1]

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


def confirm_sides():
    global debounce_timer
    sides = number_of_sides.get()
    if debounce_timer is not None:
        root.after_cancel(debounce_timer)
    debounce_timer = root.after(3000, lambda: [update_face_buttons_and_entries(sides, tabs)])


def parse_accelerometer_data(data):
    try:
        accelX, accelY, accelZ = struct.unpack('fff', data)
        accelX = round(accelX, 2)
        accelY = round(accelY, 2)
        accelZ = round(accelZ, 2)
        return {'X': accelX, 'Y': accelY, 'Z': accelZ}
    except struct.error as e:
        print(f"Failed to parse data: {e}")
        print_to_console(f"Failed to parse data: {e}")
        return {}


def dot_product(face, data, unit_vector):
    x = data.get('X', 0)
    y = data.get('Y', 0)
    z = data.get('Z', 0)

    # Calculate magnitude of XYZ vector
    magnitude = math.sqrt(x * x + y * y + z * z)

    if magnitude == 0:
        return  # Avoid division by zero if magnitude is zero

    # Normalize XYZ vector to unit vector
    normalized_x = x / magnitude
    normalized_y = y / magnitude
    normalized_z = z / magnitude

    # Calculate dot product with unit vector
    dot_product_value = normalized_x * unit_vector[0] + \
                        normalized_y * unit_vector[1] + \
                        normalized_z * unit_vector[2]

    return round(dot_product_value, 3)


async def notification_handler(sender, data):
    global record_message_sent, current_dot_prod
    try:
        print(f"Received data: {data}")
        print_to_console(f"Received data: {data}")

        if len(data) == 12:
            parsed_data = parse_accelerometer_data(data)

            if parsed_data:
                print(f"Parsed data: X={parsed_data['X']}, Y={parsed_data['Y']}, Z={parsed_data['Z']}")
                print_to_console(f"Parsed data: X={parsed_data['X']}, Y={parsed_data['Y']}, Z={parsed_data['Z']}")
                update_entries(last_selected_face, parsed_data)

                dp_value = dot_product(last_selected_face, parsed_data, unit_vector)

                if dp_value is not None:
                    update_dot_product_entry(last_selected_face, dp_value)
        elif len(data) == 4:
            current_dot_prod = round(struct.unpack('f', data)[0],3)
            print(f"Received 4-byte dot product: {current_dot_prod}")
            print_to_console(f"Received 4-byte dot product: {current_dot_prod}")
            highlight_closest(current_dot_prod)

    except Exception as e:
        print(f"Error in notification handler: {e}")
        print_to_console(f"Error in notification handler: {e}")

    record_message_sent = False


def highlight_closest(refrence_dot):
    if current_dot_prod is None:
        print("current_dot_prod is None, cannot compute closest value.")
        return
    # Convert the values, setting invalid or empty values to 0
    dot_product_values = []
    for var in dot_product_vars:
        try:
            value = float(var.get())
        except ValueError:
            value = 0.0  # Set invalid or empty values to 0
            print(f"Invalid value '{var.get()}', setting to 0")
        dot_product_values.append(value)

    if dot_product_values:
        closest_value = min(dot_product_values, key=lambda x: abs(x - current_dot_prod))
        print(f"The closest dot product value to {current_dot_prod} is {closest_value}")
        # Highlight the corresponding label in the GUI
        for label, value in zip(entries_mode1['Dot Product'], dot_product_values):
            if value == closest_value:
                label.configure(fg_color="yellow")  # Change the foreground color to highlight
            else:
                label.configure(fg_color="#e5e5ea")  # Reset the color for other labels
    else:
        print("No valid dot product values to compare.")

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
def update_dot_product_entry(face, dot_product_value):
    col_index = faces.index(face)
    dot_product_vars[col_index].set(dot_product_value)


def indicate_limit(label):
   def update_color():
       sides = number_of_sides.get()
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


def save_to_file():
    file_path = filedialog.asksaveasfilename(
        initialdir="C://Users//1yahi//Desktop",
        defaultextension=".h",
        filetypes=[("Header files", "*.h"), ("All files", "*.*")]
    )

    if not file_path:
        print("Save operation cancelled")
        return

    device_name = name_entry.get()

    try:
        with open(file_path, 'w') as file:
            file.write('#ifndef CONFIG_H\n#define CONFIG_H\n\n')
            file.write(f'#define DEVICE_NAME "{device_name}"\n\n')

            # Face data configuration
            file.write("// Face data configuration\n")

            def write_entries(entries, mode):
                for face, face_entries in entries.items():
                    for i, entry in enumerate(face_entries):
                        if face in ['X', 'Y', 'Z']:
                            value = entry.cget("text")  # Get text from label
                        else:
                            value = entry.get()  # Get text from entry
                        face_label = faces[i]
                        file.write(f"#define {mode}_{face_label}_{face.upper()} {value}\n")

            # Write entries for each mode
            write_entries(entries_mode1, 'MODE1')
            write_entries(entries_mode2, 'MODE2')
            write_entries(entries_mode3, 'MODE3')

            file.write("\n#endif // CONFIG_H\n")

        print("Configuration saved to", file_path)
        print_to_console(f"Configuration saved to {file_path}")
    except Exception as e:
        print(f"Failed to save to file: {e}")
        print_to_console(f"Failed to save to file: {e}")


def parse_h_file(file_path):
    data = {'MODE1': {}, 'MODE2': {}, 'MODE3': {}}
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if '#define' in line:
                parts = line.split()
                if len(parts) == 3:
                    key = parts[1]
                    value = parts[2]
                    mode = None

                    # Extract mode
                    if 'MODE1' in key:
                        mode = 'MODE1'
                    elif 'MODE2' in key:
                        mode = 'MODE2'
                    elif 'MODE3' in key:
                        mode = 'MODE3'

                    if mode:
                        face_key, param = extract_face_and_param(key, mode)
                        if face_key and param:
                            if face_key not in data[mode]:
                                data[mode][face_key] = {}
                            data[mode][face_key][param] = value
                        else:
                            print(f"Skipping malformed key: {key}")
                    else:
                        print(f"Skipping key without mode: {key}")
    return data


def extract_face_and_param(key, mode):
    face_param_part = key.split(f"{mode}_Face")
    if len(face_param_part) > 1:
        face_param = face_param_part[1].strip()
        face_parts = face_param.split('_')
        if len(face_parts) == 2:
            face_number = face_parts[0]
            param = face_parts[1]
            face_key = f"Face {face_number}"
            return face_key, param
    return None, None


def import_file():
    file_path = filedialog.askopenfilename(filetypes=[("Header files", "*.h")])
    if file_path:
        data = parse_h_file(file_path)


def create_face_layout(parent_frame, entries):
    for col_index, face in enumerate(faces):
        face_button = ctk.CTkButton(
            master=parent_frame,
            text=face,
            command=lambda v=face: asyncio.run_coroutine_threadsafe(record_face(v), loop),
            height=20,
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

    for row_index, label in enumerate(['Note', 'X', 'Y', 'Z', 'Dot Product'], start=2):
        ctk.CTkLabel(master=parent_frame, text=label, font=('Bahnschrift SemiBold', 12)).grid(row=row_index, column=0,
                                                                                              padx=5, pady=5,
                                                                                              sticky='nsew')
        for col_index in range(1, 11):
            if label == 'Dot Product':
                dot_product_label = ctk.CTkLabel(master=parent_frame, textvariable=dot_product_vars[col_index - 1],
                             font=('Bahnschrift SemiBold', 12))
                dot_product_label.grid(row=row_index, column=col_index, padx=5, pady=5, sticky='nsew')
                dot_product_label.grid_remove()  # Initially hidden
                entries[label].append(dot_product_label)
            elif label in ['X', 'Y', 'Z']:
                entry = ctk.CTkLabel(master=parent_frame, text="0", font=('Bahnschrift SemiBold', 12))
                entry.grid(row=row_index, column=col_index, padx=5, pady=5, sticky='nsew')
                entries[label].append(entry)
            else:
                entry = ctk.CTkEntry(master=parent_frame, width=50, height=5)
                entry.configure(state="normal")
                entry.grid(row=row_index, column=col_index, padx=5, pady=5, sticky='nsew')
                entry.insert(0, '0')
                entries[label].append(entry)

    for row_index, label in enumerate(['Note', 'X', 'Y', 'Z', 'Dot Product'], start=2):
        ctk.CTkLabel(master=parent_frame, text=label, font=('Bahnschrift SemiBold', 12)).grid(row=row_index + 6,
                                                                                              column=0, padx=5, pady=5,
                                                                                              sticky='nsew')
        for col_index in range(11, 21):
            if label == 'Dot Product':
                dot_product_label = ctk.CTkLabel(master=parent_frame, textvariable=dot_product_vars[col_index - 1], font=('Bahnschrift SemiBold', 12))
                dot_product_label.grid(row=row_index + 6, column=col_index - 10, padx=5, pady=5, sticky='nsew')
                dot_product_label.grid_remove()  # Initially hidden
                entries[label].append(dot_product_label)
            elif label in ['X', 'Y', 'Z']:
                entry = ctk.CTkLabel(master=parent_frame, text="0", font=('Bahnschrift SemiBold', 12))
                entry.grid(row=row_index + 6, column=col_index - 10, padx=5, pady=5, sticky='nsew')
                entries[label].append(entry)
            else:
                entry = ctk.CTkEntry(master=parent_frame, width=50, height=5)
                entry.configure(state="normal")
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
f_device_manager.grid(row=1, column=0, padx=10, pady=10, sticky='nsw')

label = ctk.CTkLabel(master=f_device_manager, text="Device Manager", font=('Bahnschrift SemiBold', 16))
label.grid(row=0, column=0, padx=20, pady=5)

button_scan = ctk.CTkButton(f_device_manager, height=30, width=270, text="Scan for Devices",
                            command=lambda: asyncio.run_coroutine_threadsafe(scan_devices(), loop),
                            fg_color='#6ac4dc', hover_color='#008299', text_color="#302c2c")
button_scan.grid(row=1, column=0, padx=20, pady=5)

options = ["no devices available"]
device_menu = ctk.CTkOptionMenu(f_device_manager, height=30, width=270, variable=selected_address, values=options,
                                fg_color='#c7c7cc', text_color="#302c2c")
device_menu.grid(row=2, column=0, padx=20, pady=5)

button_connect = ctk.CTkButton(f_device_manager, text="Connect", height=30, width=270, command=confirm_selection,
                               fg_color='#6ac4dc', hover_color='#24cc44', text_color="#302c2c")
button_connect.grid(row=3, column=0, padx=20, pady=5)

button_disconnect = ctk.CTkButton(f_device_manager, text="Disconnect", height=30, width=270, command=disconnect,
                                  fg_color='#6ac4dc', hover_color='#ff375f', text_color="#302c2c")
button_disconnect.grid(row=4, column=0, padx=20, pady=5)

for widget in f_device_manager.winfo_children():
    widget.grid_configure(padx=20, pady=5)

# Name Frame -------------------------------------------------------------------------------------
f_name = ctk.CTkFrame(master=frame, fg_color="#e5e5ea")
f_name.grid(row=2, column=0, padx=10, pady=10, sticky='nsw')

label_2 = ctk.CTkLabel(master=f_name, text='Name Device', anchor='center', font=('Bahnschrift SemiBold', 16),
                       text_color="#302c2c")
label_2.grid(row=0, column=0, padx=20, pady=5)

name_entry = ctk.CTkEntry(master=f_name, textvariable=device_name, placeholder_text='enter name', height=30, width=270)
name_entry.grid(row=1, column=0, padx=20, pady=5)

for widget in f_name.winfo_children():
    widget.grid_configure(padx=20, pady=5)

# Sides Frame -------------------------------------------------------------------------------------
f_sides = ctk.CTkFrame(master=frame, fg_color="#e5e5ea")
f_sides.grid(row=3, column=0, sticky='nswe', padx=10, pady=10)

label_2 = ctk.CTkLabel(master=f_sides, text='# of Sides', font=('Bahnschrift SemiBold', 16), text_color="#302c2c")
label_2.grid(row=0, column=1, padx=10, pady=5)

sides_entry = ctk.CTkLabel(f_sides, textvariable=number_of_sides, font=('Bahnschrift SemiBold', 27),
                           text_color="#302c2c")
sides_entry.grid(row=1, column=1, padx=10, pady=5)

button_down = ctk.CTkButton(
    f_sides, text="▼", height=20, width=20,
    command=lambda: [
        number_of_sides.set(max(4, number_of_sides.get() - 1)),  # Ensure the value doesn't go below 4
        confirm_sides(),
        indicate_limit(sides_entry) if number_of_sides.get() == 4 else None
    ],
    fg_color='#6ac4dc', hover_color='#008299', font=('Bahnschrift SemiBold', 25)
)
button_down.grid(row=1, column=0, ipadx=12, ipady=5)

button_up = ctk.CTkButton(
    f_sides, text="▲", height=20, width=20,
    command=lambda: [
        number_of_sides.set(min(20, number_of_sides.get() + 1)),  # Ensure the value doesn't go above 20
        confirm_sides(),
        indicate_limit(sides_entry) if number_of_sides.get() == 20 else None
    ],
    fg_color='#6ac4dc', hover_color='#008299', font=('Bahnschrift SemiBold', 25)
)
button_up.grid(row=1, column=2, ipadx=12, ipady=5)

for widget in f_sides.winfo_children():
    widget.grid_configure(padx=20, pady=5)

# File Management -------------------------------------------------------------------------------------
f_file = ctk.CTkFrame(master=frame, fg_color="#e5e5ea")
f_file.grid(row=4, column=0, padx=10, pady=5, sticky='nsw')

button_save = ctk.CTkButton(master=f_file, height=30, width=280, text="Save to File", fg_color='#6ac4dc',
                            hover_color='#008299', text_color="#302c2c", command=save_to_file)
button_save.grid(row=0, column=0, padx=10, pady=5)

button_import = ctk.CTkButton(master=f_file, height=30, width=280, text="Import File", fg_color='#6ac4dc',
                              hover_color='#008299', text_color="#302c2c", command=import_file)
button_import.grid(row=1, column=0, padx=10, pady=5)


test_toggle = ctk.CTkSwitch(f_file, text="Test Toggle", font=('Bahnschrift SemiBold', 12), height=30, width=270,
                            fg_color='#6ac4dc', text_color="#302c2c")
test_toggle.grid(row=2, column=0, padx=20, pady=5, sticky='nswe')



# Face Values Frame -------------------------------------------------------------------------------------
f_face = ctk.CTkFrame(master=frame, fg_color='transparent')
f_face.grid(row=1, column=1, rowspan=4, sticky='nsew', padx=10, pady=10)

entries = {label: [] for label in ['Note', 'X', 'Y', 'Z', 'Dot Product']}
create_face_layout(f_face, entries)

row_labels = ['Note', 'X', 'Y', 'Z', 'Dot Product']
last_selected_face = None

tabview = CTkTabview(frame)
tabview.grid(row=1, column=1, rowspan=4, sticky='nsew', padx=10, pady=10)

# Create three tabs
tab_faces1 = tabview.add("Mode 1")
tab_faces2 = tabview.add("Mode 2")
tab_faces3 = tabview.add("Mode 3")
tab_faces4 = tabview.add("Test")

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
                for row_index, label in enumerate(['Note', 'X', 'Y', 'Z', 'Dot Product']):
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
        'f_sides': f_sides.winfo_children()
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

        confirm_sides()
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




async def toggle_dot_product_sensor():
    global current_dot_prod  # Ensure this is treated as a global variable
    if test_toggle.get() == 1:
        visibility = dot_product_visible.get()
        new_state = not visibility
        dot_product_visible.set(new_state)

        for row_index in [6, 12]:  # Adjusted row indices for Dot Product
            for col_index in range(1, 11):
                entries_mode1['Dot Product'][col_index - 1].grid_remove() if not new_state else \
                entries_mode1['Dot Product'][col_index - 1].grid()
            for col_index in range(11, 21):
                entries_mode1['Dot Product'][col_index - 1].grid_remove() if not new_state else \
                entries_mode1['Dot Product'][col_index - 1].grid()


        print("The switch is ON and the function is activated.")
        print_to_console("The switch is ON and the function is activated.")
        time.sleep(2)
        await send_data(client, "Test")

        await asyncio.sleep(5)  # Wait for 5 seconds before repeating

    else:
        for row_index in [6, 12]:  # Adjusted row indices for Dot Product
            for col_index in range(1, 11):
                entries_mode1['Dot Product'][col_index - 1].grid_remove()
            for col_index in range(11, 21):
                entries_mode1['Dot Product'][col_index - 1].grid_remove()

            # Remove highlights
        for label in entries_mode1['Dot Product']:
            label.configure(fg_color="#FFFFFF")

        print("The switch is OFF. The function is deactivated.")

def run_toggle_dot_product_sensor():
    asyncio.run(toggle_dot_product_sensor())
    print("pass to async")

test_toggle.configure(command= run_toggle_dot_product_sensor)
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
