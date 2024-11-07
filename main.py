#importing all the libraries essential in micropython

import sensor, image, time, math

#------------------

def map_angle_to_speed(angle): #This function maps the angle with the speed of the car
    min_angle = -30
    max_angle = 210
    min_speed = 0
    max_speed = 240

    if angle < min_angle:
        angle = min_angle
    elif angle > max_angle:
        angle = max_angle

    speed = ((angle - min_angle) / (max_angle - min_angle)) * (max_speed - min_speed) + min_speed
    return speed

def map_angle_to_rpm(angle): #This function maps the angle with the RPM of the car
    min_angle = -30
    max_angle = 210
    min_rpm = 0
    max_rpm = 6

    if angle < min_angle:
        angle = min_angle
    elif angle > max_angle:
        angle = max_angle

    rpm = ((angle - min_angle) / (max_angle - min_angle)) * (max_rpm - min_rpm) + min_rpm
    return rpm

def posToAngle(x_center,y_center,x_end,y_end):
    if x_end == x_center:
        return 90
    elif x_end>x_center:
        if y_end>y_center:
              return 180 + math.degrees(math.atan((y_end-y_center)/(x_end-x_center)))
        else :
              return 180 - math.degrees(math.atan((y_center-y_end)/(x_end-x_center)))
    else :
        if y_end>y_center:
              return -math.degrees(math.atan((y_end-y_center)/(x_center-x_end)))
        else :
              return math.degrees(math.atan((y_center-y_end)/(x_center-x_end)))

# Initialize the camera sensor
sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)  # or RGB565 if needed
sensor.set_framesize(sensor.QVGA)       # Set resolution
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)             # Turn off auto gain for color tracking

dials = []
dials_center = []

while True:
    img = sensor.snapshot()
    
    # Detect circles
    circles = img.find_circles(threshold=2000, x_margin=10, y_margin=10, r_margin=10,
                               r_min=120, r_max=250, r_step=2)
    x_center, y_center = 150, 150
    max_line_length = 150
    
    # Process each detected circle
    for i, c in enumerate(circles):
        x, y, r = c.x(), c.y(), c.r()

        # Create a mask for the circle
        mask = image.Image(img.width(), img.height(), sensor.GRAYSCALE)  # Create an empty grayscale mask
        mask.draw_circle(x, y, r, color=(255, 255, 255), fill=True)      # Draw filled circle as mask

        # Apply mask to the image
        masked_img = img.copy()                                          # Make a copy of the image
        masked_img.mask(mask, invert=False)                              # Apply the mask to the copy

        # Crop the masked image to the circle's bounding box
        x1, y1, x2, y2 = max(0, x - r), max(0, y - r), min(img.width(), x + r), min(img.height(), y + r)
        circle_crop = masked_img.crop(x1, y1, x2 - x1, y2 - y1)

        # Append the cropped dial and its center to lists
        dials.append(circle_crop)
        dials_center.append((x, y))

        # Optionally, display the dial (if you have an LCD attached)
        # lcd.display(circle_crop)
        time.sleep_ms(500)  # Small delay for viewing each dial if needed

    # Further process a subset of dials if needed
    final_dials = []
    final_dials_center = []
    for i in range(min(2, len(dials))):   # Select first two dials or fewer if less detected
        final_dials.append(dials[i])
        final_dials_center.append(dials_center[i])

        # Display the final dials if LCD is available
        # lcd.display(final_dials[i])
        time.sleep_ms(500)
        
        
    dial = final_dials[1]  # Assuming final_dials[1] is set up as in previous steps

    # Apply edge detection
    edges = dial.find_edges(image.EDGE_CANNY, threshold=(50, 150))

    # Find line segments using Hough Transform
    lines = edges.find_line_segments(threshold=100, theta_margin=25, rho_margin=20, 
                                     segment_threshold=20)

    # Check if lines were found
    if lines:
        for line in lines:
            x1, y1, x2, y2 = line.line()

            # Calculate line length
            line_length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

            # Find the endpoint closest to the center
            if ((x1 - x_center) ** 2 + (y1 - y_center) ** 2 > (x2 - x_center) ** 2 + (y2 - y_center) ** 2):
                x_end, y_end = x1, y1
            else:
                x_end, y_end = x2, y2

            # Check if the line length is within max_line_length
            if line_length <= max_line_length:
                # Draw line on the image for visualization
                img.draw_line(line.line(), color=(0, 255, 0))

                # Calculate angle in degrees relative to the center
                dx = x_end - x_center
                dy = y_end - y_center
                angle_degrees = posToAngle(x_center, y_center, x_end, y_end)  # Custom function for angle calculation

                # Print results
                print(f"Line: ({x1}, {y1}) -> ({x2}, {y2}), Length: {line_length:.2f}, Angle: {angle_degrees:.2f} degrees")
                print("Current RPM:", map_angle_to_rpm(angle_degrees) * 1000)
    else:
        print("No lines were detected.")
        
    
    max_line_length = 210
    dial = final_dials[0]
    
    # Apply edge detection
    edges = dial.find_edges(image.EDGE_CANNY, threshold=(50, 150))

    # Detect line segments in the edge-detected image
    lines = edges.find_line_segments(threshold=135, theta_margin=25, rho_margin=10, segment_threshold=10)

    # Check if any lines were detected
    if lines:
        for line in lines:
            x1, y1, x2, y2 = line.line()

            # Calculate the length of the line
            line_length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

            # Filter out lines longer than the max length
            if line_length <= max_line_length:
                # Draw the line on the image for visualization
                img.draw_line(line.line(), color=(0, 255, 0), thickness=2)

                # Calculate angle in degrees
                dx = x2 - x1
                dy = y2 - y1
                angle_radians = math.atan2(dy, dx)
                angle_degrees = math.degrees(angle_radians)

                # Print the line details and calculated angle
                print(f"Line: ({x1}, {y1}) -> ({x2}, {y2}), Length: {line_length:.2f}, Angle: {angle_degrees:.2f} degrees")
                print("Current Speed:", map_angle_to_speed(angle_degrees))
    else:
        print("No lines were detected.")

    # Display the image on an LCD if available
    # lcd.display(img)

    time.sleep_ms(500)    
    

    # Detect rectangles or squares
    rectangles = img.find_rects(threshold=10000)

    for r in rectangles:
        # Filter rectangles based on size and aspect ratio
        w = r.w()
        h = r.h()
        aspect_ratio = w / float(h)
        
        if 0.8 <= aspect_ratio <= 1.25 and 100 < w < 300 and 100 < h < 300:
            # Draw the bounding box around the detected square/rectangle
            img.draw_rectangle(r.rect(), color=(0, 255, 0))

    # Optionally, you can display the processed image on an LCD if available
    # lcd.display(img)

    # Add delay for viewing the frames
    time.sleep_ms(100)
    
    RED_THRESHOLD = (60, 255, -128, 127, -128, 127)
    blobs = img.find_blobs([RED_THRESHOLD], pixels_threshold=50, area_threshold=50, merge=True)

    for blob in blobs:
        x, y, w, h = blob.rect()
        
        # Assuming indicators are smaller
        if w < 50 and h < 50:
            indicator_region = img.crop((x, y, w, h))

            # Count the number of red pixels in the indicator region
            red_pixels = 0
            for i in range(w):
                for j in range(h):
                    r, g, b = indicator_region.get_pixel(i, j)
                    if r > 100 and g < 80 and b < 80:  # Approximation for red
                        red_pixels += 1
            
            red_percentage = (red_pixels / (w * h)) * 100

            # If red is dominant
            if red_percentage > 30:
                # Mark the detected red indicator on the image
                img.draw_rectangle(x, y, w, h, color=(255, 0, 0))
                lcd.display(img)
                print("Red Indicator Detected")

