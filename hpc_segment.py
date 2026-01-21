
import yaml
import skimage
import os
from cellpose import models
from aicsimageio import AICSImage
import numpy as np


CONFIG_NAME = 'config.yaml'

with open(CONFIG_NAME, "r") as f:
	config = yaml.safe_load(f)

raw_folder = config['input_folder']
output_folder = config['output_folder']
dapi_channel = config['dapi_channel']
dapi_channel = dapi_channel - 1
diameter = config['diameter']

# os.makedirs(os.path.join(output_folder, 'segmentationSAM'), exist_ok=True)
# os.makedirs(os.path.join(output_folder, 'raw_projected'), exist_ok=True)

files = os.listdir(raw_folder)
file = files[0]
for file in files:
    os.makedirs(os.path.join(output_folder, file), exist_ok=True)
    print('segmenting ' + file)	
    img = AICSImage(os.path.join(raw_folder, file))  # selects the first scene found
    DAPI_im = np.mean(img.get_image_data("CZYX", S=0, C=dapi_channel), axis=1)
    model = models.CellposeModel()
    masks, flows, styles = model.eval(DAPI_im)
    
    os.makedirs(os.path.join(output_folder, file, 'seg'), exist_ok=True)
    skimage.io.imsave(os.path.join(output_folder, file, 'seg', file[:-4] + '.tif'), masks)
    os.makedirs(os.path.join(output_folder, file, 'dapi'), exist_ok=True)
    skimage.io.imsave(os.path.join(output_folder, file, 'dapi', file[:-4] + '.tif'), DAPI_im)

    for i in range(0, img.shape[1]):
        if i != dapi_channel:
            ch_im = np.mean(img.get_image_data("CZYX", S=0, C=i), axis=1)
            os.makedirs(os.path.join(output_folder, file, 'ch' + str(i+1)), exist_ok=True)
            skimage.io.imsave(os.path.join(output_folder, file, 'ch' + str(i+1) ,file[:-4] + '.tif'), ch_im)
    
