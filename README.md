# Composite Substance Quantifier
Computer vision algorithm for detection of boron, carbon fiber, tungsten, and polymer percentages in a microscope image.  

![Sample Image](images/20x_BCP_Example.jpg)

## Usage 

Input images are placed in the 'Images' folder and each must have '10x' or '20x' somewhere in the file name for processing to work accurately. 'Parameters.txt' contains the following parameters. 

- Mode: Boron Carbon Polymer (BCP) or Boron Tungsten Polymer (BTP), depending on the type of composite being characterized. 
- Radius inflation: percent that each boron detection circle is inflated
- Boron sensitivity: sensitivity with which circles are fitted to boron fiber candidates
- Boron detection threshold: threshold with which fitted boron candidates are validated

The proram will output two folders: 'Percentages.txt,' which contains the percentages of each constituent (BCP or BTP as per mode) and 'Processed Images,' which contains each input image with overlayed characterization criteria. 
