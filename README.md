# Composite Substance Quantifier
Computer vision algorithm for detection of boron, carbon fiber, tungsten, and polymer percentages in a microscope image.  

![Sample Image](images/20x_BCP_Example.jpg)

## Logic 

Composite Element Detection operates in two modes: BCP, for boron carbon polymer composites, and BTP, for boron tungsten polymer composites. 



### BCP Logic

BCP operation has three primary stages: circle fitting, to identify whole boron fibers; circle validation, to remove invalid boron detection; and thresholding, to identify boron fragments, carbon, and polymer regions. Circle fitting is used in addition to thresholding to include boron voids, which would otherwise be incorrectly identified as polymer. 

Circle fitting is excessive to ensure all boron is identified; as a result, many extraneous circles are also identified. Circle sensitivity is controlled with Parameter 3. Circle candidates are validated by analyzing the average brightness of the original image in the area contained by each circle; a low average brightness is likely polymer, and high, boron. Brightness detection threshold is controlled with Parameter 4. The remaining circles are assumed to be correctly identified boron fibers and the associated regions are removed from the subsequent thresholding steps. 

The image is then thresholded for three brightnesses: high, which identifies boron fragments that circle detection did not identify, middle, which identifies carbon fiber, and low, which identifies polymer. 

### BTP Logic

BTP operation is similar to BCP. Boron and tungsten are grouped identified and validated with the same circle and thresholding logic. To separate boron from tungsten, a subtle hue difference is used. The remaining polymer is thresholded, and the image is returned to the user for optional correction. Using a mouse, tungsten fibers or fragments that have been mischaracterized as boron are identified. The algorithm runs a second time with these data, and the final detection is produced. 


## Usage 

Input images are placed in the 'Images' folder; each must have '10x' or '20x' somewhere in the file name for processing to work accurately. 'Parameters.txt' contains the following parameters. 

- Mode: Boron Carbon Polymer (BCP) or Boron Tungsten Polymer (BTP), depending on the type of composite being characterized. 
- Radius inflation: percent that each boron detection circle is inflated
- Boron sensitivity: sensitivity with which circles are fitted to boron fiber candidates
- Boron detection threshold: threshold with which fitted boron candidates are validated

The program will output two folders: 'Percentages.txt,' which contains the percentages of each constituent (BCP or BTP as per mode), and 'Processed Images,' which contains each input image with overlayed characterization criteria. 

# BCP Operation

Place images in the 'Images' folder, select the correct operation mode (1) and run the script. The percentages of each detected item will be output in 'Percentages.txt.' Detection quality should be confirmed by inspecting the 'Processed Images' folder; if needed, adjust the final two parameters in 'Parameters.txt.' 

# BTP Operation

Place a single image in the 'Images' folder, select the operation mode (2) and run the script. When the image is presented to the user, the mouse may be used to click on additional tungsten fibers or fragments that have been mischaracterized as boron. After corrections have been made, or if none were needed, press 'd'. After reprocessing, the percentages of each detected item will be output in 'Percentages.txt.' Detection quality should be confirmed by inspecting the 'Processed Images' folder; if needed, adjust the final two parameters in 'Parameters.txt.' 


