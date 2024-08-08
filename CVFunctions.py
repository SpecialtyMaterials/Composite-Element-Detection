import cv2
import numpy as np
import os
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

clicks = []
revised = False

# loads vision parameters from parameters.txt
def load_parameters(file_path):
    params = {}
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip() and not line.startswith('//'):
                key, value = line.split('=')
                params[key.strip()] = float(value.strip())
    return params

#uses Kmeans clustering to identify two thresholding values that optimally divide the 
# three most common values (boron, carbon, polymer)
def find_thresholds(image, n_clusters=3):
    pixel_values = image.flatten().reshape(-1, 1)
    kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(pixel_values)
    cluster_centers = np.sort(kmeans.cluster_centers_.flatten())
    thresholds = [(cluster_centers[i] + cluster_centers[i+1]) / 2 for i in range(n_clusters - 1)]
    return thresholds

#identifies the optimal thresholding value for tungsten segmentation (blue channel)
#by identifying the histogram peak
#black pixels are excluded so only tungsten pixels are analyzed
def find_optimal_blue_threshold(image):
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    blue_channel = image_rgb[:, :, 2]

    mask = np.logical_and(image_rgb[:, :, 0] != 0, 
            np.logical_and(image_rgb[:, :, 1] != 0, 
                            image_rgb[:, :, 2] != 0))
    
    blue_channel_non_black = blue_channel[mask]
    hist = cv2.calcHist([blue_channel_non_black], [0], None, [256], [0, 256])

    optimal_threshold = np.argmax(hist)
    return optimal_threshold

#main loop for boron carbon polymer detection
def bcp(image_file, image, boron_sensitivity=10, boron_detection_threshold = 20, radius_inflation = 1):

    #parameter adjustments based on image zoom as boron radii and distance change
    #critical for exclusion of false positives
    if '10x' in image_file:
        min_radius = 65
        max_radius = 80
        min_distance = 110
    elif '20x' in image_file:
        min_radius = 138
        max_radius = 153
        min_distance = 280
    else:
        max_radius = 80
        min_radius = 65
    
    # remove the bottom x% percent which includes scale bar and other elements
    height, width = image.shape[:2]
    cropped_image = image[:int(height * 0.92), :] 
    
    #carbon and boron thresholding, using find_thresholds
    gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    carbonThreshold, boronThreshold = find_thresholds(gray, 3)
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)

    #grossly sensitive criclce detection to identify boron or tungsten
    #false positives are cleaned later 
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.0,
        minDist=min_distance,
        param1=40,
        param2=boron_sensitivity,
        minRadius=min_radius,
        maxRadius=max_radius
    )

    filtered_circles = []

    #iterate through all detected circles and check the average brightness of the area 
    #they enclose on the original image; if the average brightness is high enough (boron or tungsten detected)
    #the circle is ruled out as a false positive 
    if circles is not None:
        circles = np.uint16(np.around(circles))
        
        for i in circles[0, :]:
            x, y, r = i[0], i[1], i[2]

            mask = np.zeros_like(gray)
            cv2.circle(mask, (x, y), r, 255, thickness=-1)
            masked_image = cv2.bitwise_and(cropped_image, cropped_image, mask=mask)
            masked_gray = cv2.cvtColor(masked_image, cv2.COLOR_BGR2GRAY)
            
            avg_brightness = np.mean(masked_gray[masked_gray > 0])
            if avg_brightness > boronThreshold - boron_detection_threshold:
                filtered_circles.append((x, y, r))

    red_filled_image = cropped_image.copy()

    # draw detected circles in red
    for (x, y, r) in filtered_circles:
        inflated_radius = int(r * radius_inflation)
        cv2.circle(red_filled_image, (x, y), inflated_radius, (0, 0, 255), thickness=-1)

    gray_red_filled = cv2.cvtColor(red_filled_image, cv2.COLOR_BGR2GRAY)
    mask = cv2.inRange(gray_red_filled, boronThreshold, 255)

    # fill remaining, non circle-enclosed light areas -- small boron fragments or partial cricles on image edges 
    result_image = red_filled_image.copy()
    result_image[mask == 255] = (0, 0, 255)

    duplicate_image = cropped_image.copy()

    # generates masks for the carbon, boron, and polymer thresholds identified earlier
    carbonMask = cv2.inRange(gray, 0, carbonThreshold)
    polymerMask = cv2.inRange(gray, carbonThreshold, 200)
    red_mask = cv2.inRange(result_image, (0, 0, 255), (0, 0, 255))

    # fill masks with green, red and blue for vizualization purposes
    duplicate_image[carbonMask == 255] = (0, 255, 0)
    duplicate_image[polymerMask == 255] = (255, 0, 0)
    duplicate_image[red_mask == 255] = (0, 0, 255)

    # overlay images at low opacity for vizualization
    overlay_image = cv2.addWeighted(cropped_image, 0.8, duplicate_image, 0.2, 0)

    # # write image and percentages
    # processed_image_path = os.path.join(processed_images_folder, f'processed_{image_file}')
    # cv2.imwrite(processed_image_path, overlay_image)

    # calculation of percentages of red, green, and blue 
    total_pixels = duplicate_image.size // 3 

    red_pixels = np.sum(np.all(duplicate_image == (0, 0, 255), axis=-1))
    green_pixels = np.sum(np.all(duplicate_image == (0, 255, 0), axis=-1))
    blue_pixels = np.sum(np.all(duplicate_image == (255, 0, 0), axis=-1))

    red_percentage = (red_pixels / total_pixels) * 100
    green_percentage = (green_pixels / total_pixels) * 100
    blue_percentage = (blue_pixels / total_pixels) * 100

    percentages = []
    percentages.append(red_percentage)
    percentages.append(green_percentage)
    percentages.append(blue_percentage)
    return overlay_image, percentages

#     percentage_file.write(f'{image_file} - Boron: {red_percentage:.2f}%, Polymer: {green_percentage:.2f}%, Carbon: {blue_percentage:.2f}%\n')
#     print('Image Complete')

# percentage_file.close()

#records mouse position when clicked and viualizes clicks with a red cricle
#used for cleaning data in btp (boron tungsten polymer) mode 

def mouse_callback(event, x, y, flags, param):
    global overlay_image
    global revised
    global clicks

    if event == cv2.EVENT_LBUTTONDOWN:
        x = 2*x
        y = (2*y)-40
        clicks.append((x, y))
        cv2.circle(overlay_image, (x, y), 5, (0, 0, 255), -1) 
        revised = True

#main function for boron tungsten polymer mode 
#revised runs if corrections have been made 
def btp(clicks_array, image_file, image, boron_sensitivity=10, boron_detection_threshold = 20, radius_inflation = 1):
    finished = False
    global overlay_image, revised, clicks

    if '10x' in image_file:
        min_radius = 65
        max_radius = 80
        min_distance = 110
    elif '20x' in image_file:
        min_radius = 138
        max_radius = 153
        min_distance = 280
    else:
        max_radius = 80
        min_radius = 65

    # remove the bottom x% percent which includes scale bar and other elements
    height, width = image.shape[:2]
    cropped_image = image[:int(height * 0.92), :] 
    
    #carbon and boron thresholding, using find_thresholds
    gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    carbonThreshold, boronThreshold = find_thresholds(gray, 3)
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)
    
    gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    _, boronThreshold = find_thresholds(gray, 3)
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.0,
        minDist=min_distance,
        param1=40,
        param2=boron_sensitivity,
        minRadius=min_radius,
        maxRadius=max_radius
    )

    filtered_circles = []
    filtered_circles2 = []

    if circles is not None:
        circles = np.uint16(np.around(circles))

        mask_total = np.zeros_like(gray)
        
        for i in circles[0, :]:
            x, y, r = i[0], i[1], i[2]
            cv2.circle(mask_total, (x, y), r, 255, thickness=-1)
            masked_image = cv2.bitwise_and(cropped_image, cropped_image, mask=mask_total)


        #optimal blue threshold to distinguish between tungsten and boron is
        # deterined with find_optimal_blue_threshold
        blue_thresh = find_optimal_blue_threshold(masked_image)
        print(blue_thresh)

        for i in circles[0, :]:
            x, y, r = i[0], i[1], i[2]

            mask = np.zeros_like(gray)
            cv2.circle(mask, (x, y), r, 255, thickness=-1)
            masked_image = cv2.bitwise_and(cropped_image, cropped_image, mask=mask)
            masked_gray = cv2.cvtColor(masked_image, cv2.COLOR_BGR2GRAY)

            avg_brightness = np.mean(masked_gray[masked_gray > 0])

            avg_blue_brightness = np.mean(masked_image[:,:,0][masked_image[:,:,0] > 0])

            #if false negative corrections have been made by the user, circles that contain the 
            #correction coordinates will diverted to the correct array (filtered_circles2)
            if revised:
                in_circle = any((px - x)**2 + (py - y)**2 <= r**2 for px, py in clicks_array)
            else: in_circle = False

            if in_circle:
                filtered_circles2.append((x, y, r))
            else:

                # circles with sufficient average brightness but low blue hue (boron) and circles with
                #sufficient average brightness and high blue hue (tungsten) are categorized from all circles
                #because manual corrections will be made later, this process tungsten detection is conservative
                if avg_brightness > boronThreshold - boron_detection_threshold:
                    if avg_blue_brightness > blue_thresh:
                        filtered_circles2.append((x, y, r))
                    else:
                        filtered_circles.append((x, y, r))

    red_filled_image = cropped_image.copy()

    for (x, y, r) in filtered_circles:
        inflated_radius = int(r * radius_inflation)
        cv2.circle(red_filled_image, (x, y), inflated_radius, (0, 0, 255), thickness=-1)

    for (x, y, r) in filtered_circles2:
        inflated_radius = int(r * radius_inflation)
        cv2.circle(red_filled_image, (x, y), inflated_radius, (0, 255, 0), thickness=-1)

    green_mask = (red_filled_image[:, :, 0] == 0) & (red_filled_image[:, :, 1] == 255) & (red_filled_image[:, :, 2] == 0)

    red_filled_copy = red_filled_image.copy()
    red_filled_copy[green_mask] = [0, 0, 0]

    gray_red_filled = cv2.cvtColor(red_filled_copy, cv2.COLOR_BGR2GRAY)
    mask = cv2.inRange(gray_red_filled, boronThreshold-20, 255)

    if revised:
        revised = False
        finished = True
        clicks = []

        #if the image has been corrected, islands are iterated through to determine if they should be ejected
        #every pixel is checked to see if it corresponds with one in the clicks_array (the user has selected it as anomalous)
        #all pixels connected ot the fault are removed
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
        green_mask = np.zeros_like(mask, dtype=np.uint8)
        clicks_set = set(tuple(coord) for coord in clicks_array)

        for label in range(1, num_labels):

            island_coords = np.argwhere(labels == label)
            
            for coord in island_coords:
                coord_tuple = tuple(coord)
                coord_tuple = coord_tuple[::-1]

                if coord_tuple in clicks_set:
                    green_mask[labels == label] = 255
                    mask[labels == label] = 0

    #paint boron in red
    result_image = red_filled_image.copy()
    result_image[mask == 255] = (0, 0, 255)

    #revised tungsten in green
    duplicate_image = cropped_image.copy()
    if revised: duplicate_image[green_mask==255] = (0,255,0)

    #new, composite tungsten mask (everywhere where the previous vizualization was green)
    polymerMask = cv2.inRange(gray, 0, 200)
    tungstenMask = (red_filled_image[:, :, 0] == 0) & (red_filled_image[:, :, 1] == 255) & (red_filled_image[:, :, 2] == 0)
    tungstenMask = tungstenMask.astype(np.uint8) * 255

    #paint polymer and tungsten in blue and green on new image
    duplicate_image[polymerMask == 255] = (255, 0, 0)
    duplicate_image[tungstenMask == 255] = (0, 255, 0)

    #paint boron on new image
    red_mask = cv2.inRange(result_image, (0, 0, 255), (0, 0, 255))
    duplicate_image[red_mask == 255] = (0, 0, 255)

    overlay_image = cv2.addWeighted(cropped_image, 0.8, duplicate_image, 0.2, 0)

    total_pixels = duplicate_image.size // 3 

    red_pixels = np.sum(np.all(duplicate_image == (0, 0, 255), axis=-1))
    green_pixels = np.sum(np.all(duplicate_image == (0, 255, 0), axis=-1))
    blue_pixels = np.sum(np.all(duplicate_image == (255, 0, 0), axis=-1))

    red_percentage = (red_pixels / total_pixels) * 100
    green_percentage = (green_pixels / total_pixels) * 100
    blue_percentage = (blue_pixels / total_pixels) * 100

    percentages = []
    percentages.append(red_percentage)
    percentages.append(green_percentage)
    percentages.append(blue_percentage)


    #after this function runs once, the user has the opportunity to make manual corrections to the tungsten detection
    #creates a window where the final result is vizualized; the user clicks on tungsten that has been mis-identified as boron, presses 'd'
    #and the code re-runs 
    #mouse clicks are saved to the global variable clicks_array 

    if finished == False: 
        finished = True
        
        cv2.namedWindow('Image')
        cv2.setMouseCallback('Image', mouse_callback)

        print("Click on the image to record points. Press 'd' when done.")

        while True:
            heightOI, widthOI = overlay_image.shape[:2]
            half_size_OI = cv2.resize(overlay_image, (widthOI // 2, heightOI // 2))

            # Create a white strip of 20 pixels in height and the same width as the resized image
            white_strip = np.ones((20, widthOI // 2, 3), dtype=np.uint8) * 255

            # Add text to the white strip
            text = "Click to correct misidentified tungsten. Press 'd' when done."
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            color = (0, 0, 0)  # Black text
            thickness = 1
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            text_x = (white_strip.shape[1] - text_size[0]) // 2
            text_y = (white_strip.shape[0] + text_size[1]) // 2
            cv2.putText(white_strip, text, (text_x, text_y), font, font_scale, color, thickness)

            # Stack the white strip on top of the resized image
            image_with_text = np.vstack((white_strip, half_size_OI))

            # Display the final image
            cv2.imshow('Image', image_with_text)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('d'):
                break

        cv2.destroyAllWindows()

        clicks_array = np.array(clicks)

    return revised, clicks_array, overlay_image, percentages


# #parameter declaration post loading from paramteres.txt
# params = load_parameters('Parameters.txt')
# mode = params.get('mode', 1)
# radius_inflation = params.get('radius_inflation', 1.0)
# boron_sensitivity = int(params.get('boron_sensitivity', 10))
# boron_detection_threshold = int(params.get('boron_detection_threshold', 20))

# print(mode) #mode selector for bcp or btp 

# #output dir
# processed_images_folder = 'Processed Images'
# if not os.path.exists(processed_images_folder):
#     os.makedirs(processed_images_folder)

# #input dir
# images_folder = 'Images'
# image_files = [f for f in os.listdir(images_folder) if os.path.isfile(os.path.join(images_folder, f))]

# #result dir
# percentage_file = open('percentages.txt', 'w')

# #global var declaration
# clicks = []
# overlay_image = None
# revised = False


# #main runner
# if mode == 1: bcp()
# elif mode == 2: 
#     clicks_array = btp()
#     print(clicks_array)
#     if revised: btp(clicks_array)

# percentage_file.close()


