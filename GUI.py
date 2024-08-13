import flet as ft
import cv2
import numpy as np
import base64
import tkinter as tk
from tkinter import filedialog
from CVFunctions import find_thresholds, bcp, btp

globalImage = None
globalFilePath = ""
percentages_text = ""
boron_sensitivity = 10
boron_detection_threshold = 20

def to_base64(image):
    base64_image = cv2.imencode('.png', image)[1]
    base64_image = base64.b64encode(base64_image).decode('utf-8') 
    return base64_image

def save_image_action(e):
    
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
    )
    if file_path:
        cv2.imwrite(file_path, globalImage)
        print(f"Image saved as {file_path}")

def main(page):
    global boron_sensitivity, boron_detection_threshold

    # Create a blank image for the initial display,
    # image element does not support None for src_base64
    init_image = np.zeros((480, 640, 3), dtype=np.uint8) + 128
    init_base64_image = to_base64(init_image)

    image_src = ft.Image(src_base64=init_base64_image, width=640, height=480)
    image_dst = ft.Image(src_base64=init_base64_image, width=640, height=480)

    image_row = ft.Row([image_src, image_dst])

    image = None
    percentages_field = ft.TextField(value="", width=1000, read_only=True, border_color='blue')

    # Slider components
    slider_boron_sensitivity = ft.Slider(
        value=boron_sensitivity, min=1, max=30, divisions=29, 
        label="Boron Sensitivity: {value}", on_change=lambda e: update_global_variables()
    )
    slider_boron_detection_threshold = ft.Slider(
        value=boron_detection_threshold, min=1, max=50, divisions=49, 
        label="Boron Detection Threshold: {value}", on_change=lambda e: update_global_variables()
    )

    def update_global_variables():
        global boron_sensitivity, boron_detection_threshold
        boron_sensitivity = slider_boron_sensitivity.value
        boron_detection_threshold = slider_boron_detection_threshold.value
        print(f"Global variables updated: Boron Sensitivity = {boron_sensitivity}, Boron Detection Threshold = {boron_detection_threshold}")

    def BTPMain(e):
        nonlocal image
        global globalImage, boron_sensitivity, boron_detection_threshold
        revised = False
        clicks_array = None

        if image is None:
            return
        
        revised, clicks_array, processed, percentages = btp(clicks_array, globalFilePath, image, boron_sensitivity, boron_detection_threshold)
        if revised: _, _, processed, percentages = btp(clicks_array, globalFilePath, image, boron_sensitivity, boron_detection_threshold)

        percentages_text = f"Boron: {percentages[0]}%, Tungsten: {percentages[1]}%, Polymer: {percentages[2]}%"

        globalImage = processed
        base64_image = to_base64(globalImage)
        image_dst.src_base64 = base64_image
        image_dst.update()
        percentages_field.value = percentages_text
        percentages_field.update()

    def BCPMain(e):
        global globalImage, boron_sensitivity, boron_detection_threshold
        nonlocal image
        if image is None:
            return

        # Pass slider values to bcp function if needed
        processed, percentages = bcp(globalFilePath, image, boron_sensitivity, boron_detection_threshold)
        percentages_text = f"Boron: {percentages[0]}%, Polymer: {percentages[1]}%, Carbon: {percentages[2]}%"

        globalImage = processed
        base64_image = to_base64(processed)
        image_dst.src_base64 = base64_image
        image_dst.update()
        percentages_field.value = percentages_text
        percentages_field.update()

    def on_file_selected(e):
        global globalFilePath
        nonlocal image

        file_path = e.files[0].path
        globalFilePath = file_path
        print("file selected :", file_path)
        image = cv2.imread(file_path)
        base64_image = to_base64(image)
        image_src.src_base64 = base64_image
        image_src.update()

    file_picker = ft.FilePicker(on_result=on_file_selected)
    page.overlay.append(file_picker)

    def on_click(e):
        file_picker.pick_files(allow_multiple=False, 
                               file_type=ft.FilePickerFileType.IMAGE)
        

    button = ft.ElevatedButton("Select Image File", on_click=on_click)
    button_BTPMain = ft.ElevatedButton("BTP", on_click=BTPMain)
    button_BCPMain = ft.ElevatedButton("BCP", on_click=BCPMain)
    button_save_image = ft.ElevatedButton("Save Image", on_click=lambda e: save_image_action(e))
    
    page.add(button)
    page.add(image_row)
    page.add(button_BTPMain)
    page.add(button_BCPMain)
    page.add(button_save_image)
    page.add(percentages_field)
    page.add(ft.Text("Boron Detection Threshold (1-50):"))
    page.add(slider_boron_detection_threshold)
    page.add(ft.Text("Boron Sensitivity (1-30):"))
    page.add(slider_boron_sensitivity)


ft.app(target=main)
