import napari
from qtpy.QtWidgets import QPushButton, QSlider, QVBoxLayout, QWidget, QLineEdit, QLabel, QComboBox
from qtpy.QtCore import Qt
import easygui
import skimage
import os
import yaml
import pandas as pd
import numpy as np
from tqdm import tqdm
global last_path
global global_multiplier
global seg_method
global current_file
#last_path = os.getcwd()
last_path = '/facility/imganfac/neurogenomics/Testa/Lisa/test_output/11-19'

seg_method = 'otsu'


CONFIG_NAME = 'config.yaml'

with open(CONFIG_NAME, "r") as f:
	config = yaml.safe_load(f)

# raw_folder = config['raw_folder']
# output_folder = config['output_folder']


dapi_channel = config['dapi_channel']
num_channels = config['num_channels']
quant_channels = []

for chan in range(1, num_channels+1):
    if chan != dapi_channel:
        quant_channels.append(chan)

print('total channels = ' + str(num_channels))
print('channels to quantifty = ' + str(quant_channels))
print('dapi channel = ' + str(dapi_channel))

viewer = napari.Viewer() 



def on_dropdown_change(index):
    print(f"Selected channel: {dropdown.itemText(index)}")
    global seg_method
    layer_map = {0: 'otsu', 1: 'triangle', 2: 'isodata', 3: 'li', 4: 'mean', 5: 'minimum', 6: 'yen'}
    seg_method = layer_map[index]

def on_load_button_click():
    global last_path
    global current_file
    print("Load Button was clicked!")
    viewer.layers.clear()
    file_path = easygui.diropenbox(title="Select Processed Image Folder", default=last_path)
    print(file_path)
    if file_path is not None:
        head, tail = os.path.split(file_path)
        label_filename.setText(tail)
        base_filename = tail[:-4]
        last_path = head        
        print(file_path)
        seg = skimage.io.imread(os.path.join(file_path, 'seg', base_filename + '.tif'))
        viewer.add_labels(seg, name='segmentation', blending='additive', visible=False)
        dapi = skimage.io.imread(os.path.join(file_path, 'dapi', base_filename + '.tif'))
        image = skimage.io.imread(os.path.join(file_path, 'ch' + str(quant_channels[0]), base_filename + '.tif'))
        viewer.add_image(image, name='image', blending='additive', visible=True)
        viewer.add_image(dapi, name='dapi', blending='additive', visible=False)
        current_file = base_filename + '.tif'
       
def on_file_dropdown_change(index):
    global last_path
    file_path = last_path
    current_channel_name = str(dropdown_filename.itemText(index))
    base_filename = label_filename.text()[:-4]
    
    chan_im = skimage.io.imread(os.path.join(file_path, label_filename.text(), current_channel_name, base_filename + '.tif'))


    layer = next((layer for layer in viewer.layers if 'image' in layer.name), None)
    if layer:
       viewer.layers.remove(layer)

    viewer.add_image(chan_im, name='image', blending='additive', visible=True)

def calculate_threshold(intensity_im, seg_method):  

    if seg_method == 'otsu':
        thresh = skimage.filters.threshold_otsu(intensity_im, nbins=256)
    elif seg_method == 'triangle':
        thresh = skimage.filters.threshold_triangle(intensity_im, nbins=256)
    elif seg_method == 'isodata':
        thresh = skimage.filters.threshold_isodata(intensity_im)
    elif seg_method == 'li':
        thresh = skimage.filters.threshold_li(intensity_im)
    elif seg_method == 'mean':
        thresh = skimage.filters.threshold_mean(intensity_im)
    elif seg_method == 'minimum':
        thresh = skimage.filters.threshold_minimum(intensity_im)
    elif seg_method == 'yen':
        thresh = skimage.filters.threshold_yen(intensity_im)
    else:
        print('No method found')

    return thresh

def on_threshold_method_button_click():
    global seg_method
    layer = next((layer for layer in viewer.layers if 'thresholded' in layer.name), None)
    if layer:
       viewer.layers.remove(layer)
    #selected_layer = viewer.layers.selection.active
    
    # if selected_layer is None:
    #     print("No layer selected")
    #     return

    intensity_layer = next((layer for layer in viewer.layers if layer.name == 'image'), None).data
    if intensity_layer is None:
        print("No image layer found")
        return
    thresholded = np.zeros(intensity_layer.shape, dtype=np.uint8)
    viewer.add_labels(thresholded, name='thresholded', blending='additive', visible=True)
    seg_method = dropdown.currentText()
    multiplier = float(text_box_multuplier.text())
    print('Thresholding with ' + seg_method + ' and multiplier ' + str(multiplier))
    thresh = calculate_threshold(intensity_layer, seg_method)
    print('using raw threshold: ' + str(thresh) + ' and multiplier: ' + str(multiplier) + ' (final = ' + str(thresh*multiplier) + ')')
    viewer.layers['thresholded'].data = np.where(intensity_layer > thresh*multiplier, 1, 0)

def on_threshold_folder_button_click():
    global seg_method
    multiplier = float(text_box_multuplier.text())    
    folder_path = easygui.diropenbox(title="Select Processed Image Folder", default=last_path)
    folders = os.listdir(folder_path)
    channel_name = dropdown_filename.currentText()
    for folder in folders:
        print('running folder: ' + folder)
        cell_sums = []
        cell_means = []
        cell_labs = []
        cell_total_area = []
        cell_total_intensity = []
        cell_mean_intensity = []
        cell_thresh_area = []
        df = pd.DataFrame()
        im = skimage.io.imread(os.path.join(folder_path, folder, channel_name, folder[:-4] + '.tif'))
        im = np.squeeze(im)
        seg = skimage.io.imread(os.path.join(folder_path, folder, 'seg', folder[:-4] + '.tif'))
        thresh = calculate_threshold(im, seg_method)
        thresh_mask = im > (thresh * multiplier)
        props = skimage.measure.regionprops(seg)
        for prop in tqdm(props):
            cell_labs.append(prop['label'])
            mask = (seg == prop['label']) & thresh_mask
            cell_sums.append(round(im[mask].sum(), 2))
            cell_means.append(round(im[mask].mean(),2))
            cell_total_area.append(prop['area'])
            cell_total_intensity.append(round(im[seg == prop['label']].sum(), 2))
            cell_mean_intensity.append(round(im[seg == prop['label']].mean(), 2))
            cell_thresh_area.append(np.sum(mask))


        df['label'] = cell_labs
        df['total_sum_intensity'] = cell_total_intensity
        df['total_mean_intensity'] = cell_mean_intensity
        df['total_area'] = cell_total_area
        df['thresholded_sum'] = cell_sums
        df['thresholded_mean'] = cell_means
        df['thresholded_area'] = cell_thresh_area
        with open(os.path.join(folder_path, folder, channel_name + '_params.txt'), 'w') as f:
            f.write(f'Threshold: {thresh}\n')
            f.write(f'Multiplier: {multiplier}\n')
            f.write(f'Segmentation Method: {seg_method}\n')
        df.to_csv(os.path.join(folder_path, folder, channel_name + '_quant.csv'), index=False)
        thresh_folder = os.path.join(folder_path, folder, 'thresholded')
        
        os.makedirs(thresh_folder, exist_ok=True)
        # temp = np.zeros(im.shape, dtype=np.uint8)
        # temp[im > (thresh * multiplier)] = 1
        skimage.io.imsave(os.path.join(thresh_folder, channel_name + '_thresholded.tif'), thresh_mask, check_contrast=False)

widget = QWidget()
layout = QVBoxLayout()
button = QPushButton("Load an Image")
button.clicked.connect(on_load_button_click)
layout.addWidget(button)

label_filename = QLabel("Filename")
layout.addWidget(label_filename)  # Add the label to the layout


dropdown_filename = QComboBox()
dropdown_filename.currentIndexChanged.connect(on_file_dropdown_change)
layout.addWidget(dropdown_filename)

#dropdown_filename.clear()
for i in quant_channels:
    dropdown_filename.addItem('ch' + str(i))

dropdown = QComboBox()
dropdown.addItem("otsu")
dropdown.addItem("triangle")
dropdown.addItem("isodata")
dropdown.addItem("li")
dropdown.addItem("mean")
dropdown.addItem("minimum")
dropdown.addItem("yen")
dropdown.currentIndexChanged.connect(on_dropdown_change)
layout.addWidget(dropdown)


label_multiplier = QLabel("Threshold scaling factor")
layout.addWidget(label_multiplier)  # Add the label to the layout
text_box_multuplier = QLineEdit()
text_box_multuplier.setReadOnly(False)  # Make the text box read-only
text_box_multuplier.setText('1')
layout.addWidget(text_box_multuplier)

button = QPushButton("Threshold Image Using Method")
button.clicked.connect(on_threshold_method_button_click)
layout.addWidget(button)

button_all = QPushButton("Threshold Folder (Batch)")
button_all.clicked.connect(on_threshold_folder_button_click)
layout.addWidget(button_all)


# Set the layout on the widget and add it to the viewer
widget.setLayout(layout)
viewer.window.add_dock_widget(widget)


napari.run()








