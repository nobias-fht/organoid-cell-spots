### Installation
1. clone the repo by opening a terminal and typing `git clone https://github.com/nobias-fht/organoid-cell-spots`
2. Enter the folder that is made by typing `cd organoid-cell-spots`
3. Make a conda environment from the enviroment file by typing `conda create -f env.yaml`

### Step 1: Cell Segmentation
1. Activate the conda enviroment by typing `conda activate nobias`
2. Update the `config.yaml` file, changing the number of channels, the position of the DAPI channel (these are 1-indexed, ie the first channel is channel 1, NOT channel 0), and the paths of the input and output folders
3. run the segmetation pipeline by typing `python hpc_segment.py`. NOTE that this will run it locally. On a machine without a GPU, it is highly recommended that you submit a job to the HPC using slurm

### Step 2: Quantification
1. If not already activated, activate the conda environment by typing `conda activate nobias`
2. Launch the interatcive viewer by typing `python viewer.py`
3. Open an image by clicking the `Open Single Image` button and selecting the output folder of a single image from the previous step
4. Select a channel from the dropdown
5. Test various thresholding mechanisms and multipliers by changing the dropdown and the `Threshold Scaling Factor` setting and then pressing `Threshold Image Using Method`
6. Once you have tested and are happy with a method and threshold on several representative test images, press `Threshold Folder (Batch)` and select the output folder from step 1.
7. This will apply the selected segmentation method and scaling factor to each image in the output folder, and generate the output images and csv files. 
8. Repeat for other channels if needed