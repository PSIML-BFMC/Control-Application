import cv2
import numpy as np
import matplotlib.pyplot as plt
import math
import time

def detect_lines(image):
    gray=cv2.cvtColor(image,cv2.COLOR_RGB2GRAY)
    blur=cv2.GaussianBlur(gray,(5,5),0) #originalno korisceno 5,5
    canny=cv2.Canny(blur,50,150)
    
    diff_height = 40
    diff_width = 25
    height=canny.shape[0]
    polygons=np.array([
       [(1+diff_width,height-diff_height),(1+diff_width,2*height//3-diff_height),(512-diff_width,2*height//3-diff_height),(512-diff_width,height-diff_height)] #put the coordinates of the triangle that you decide upon
        ])
    mask=np.zeros_like(canny)
    cv2.fillPoly(mask,polygons,255)
    masked_image=cv2.bitwise_and(canny,mask)

    
    lines=cv2.HoughLinesP(masked_image,2,np.pi/180,50,np.array([]),minLineLength=5,maxLineGap=20)
    return lines


def display_lines(image,lines): #display lines on the iage
    line_image=np.zeros_like(image)
    if lines is not None:
        for x1,y1,x2,y2 in lines:
            cv2.line(line_image,(x1,y1),(x2,y2),(255,0,0),10)
    return line_image


######################################## COMPUTING LANE LINES ########################################

def make_coordinates(height,line_parameters):
    slope,intercept=line_parameters
    print("slope", slope)
    y1=height
    y2=int(y1*(3/5))
    x1=int((y1-intercept)/slope)
    x2=int((y2-intercept)/slope)
    return np.array([x1,y1,x2,y2])

def average_slope_intersect(height,lines):
    left_fit=[]
    right_fit=[]
    for line in lines:
        x1,y1,x2,y2=line.reshape(4) #mozda za ove tacke da dodas naknadno, neki uslov da bude sigurno koje su to tacno tacke
        parameters=np.polyfit((x1,x2),(y1,y2),1)
        slope=parameters[0]
        intersect=parameters[1]
        if slope<0:
            left_fit.append((slope,intersect)) #vodi racuna o tome kako su koordinate slike postavljene!!!!!
        else:
            right_fit.append((slope,intersect))
    left_fit_average=np.average(left_fit,axis=0)
    right_fit_average=np.average(right_fit,axis=0)
    left_line=make_coordinates(height,left_fit_average)
    right_line=make_coordinates(height,right_fit_average)
    return np.array([left_line,right_line])


######################################## COMPUTING AND DISPLAYING HEADING LINE ########################################
def get_steering_angle(height,width, lane_lines):

    if len(lane_lines) == 2: # if two lane lines are detected
        left_x1, left_y1, left_x2, left_y2 = lane_lines[0] # extract left x2 from lane_lines array
        right_x1, right_y1, right_x2, right_y2 = lane_lines[1] # extract right x2 from lane_lines array
        mid = int(width / 2)
        x_offset = (left_x1 + right_x1) / 2 - mid
        y_offset = int(height / 2)  

    elif len(lane_lines) == 1: # if only one line is detected
        x1, _, x2, _ = lane_lines[0]
        x_offset = x2 - x1
        y_offset = int(height / 2)

    elif len(lane_lines) == 0: # if no line is detected
        x_offset = 0
        y_offset = int(height / 2)

    angle_to_mid_radian = math.atan(x_offset / y_offset)
    angle_to_mid_deg = float(angle_to_mid_radian * 180.0 / math.pi)  
    print(angle_to_mid_deg)
    steering_angle = angle_to_mid_deg + 90 

    return steering_angle

def display_heading_line(frame, steering_angle, line_color=(0, 0, 255), line_width=5 ):

    heading_image = np.zeros_like(frame)
    height, width, _ = frame.shape

    steering_angle_radian = steering_angle / 180.0 * math.pi
    x1 = int(width / 2)
    y1 = height
    x2 = int(x1 - height / 2 / math.tan(steering_angle_radian))
    y2 = int(height / 2)

    cv2.line(heading_image, (x1, y1), (x2, y2), line_color, line_width)

    heading_image = cv2.addWeighted(frame, 0.8, heading_image, 1, 1)

    return heading_image

if __name__ == "__main__":
    start_time=time.time()
    image=cv2.imread('finding_lanes\\test10.jpg')
    lane_image=np.copy(image)
    height,width,_=lane_image.shape
    lines=detect_lines(lane_image)
    average_lines=average_slope_intersect(height,lines)
    line_image=display_lines(lane_image,average_lines)
    combo_image=cv2.addWeighted(lane_image,0.8,line_image,1,1)
    st_angle=get_steering_angle(height,width,average_lines)
    heading_line_img=display_heading_line(combo_image,st_angle)
    end_time=time.time()
    cv2.imshow("result",heading_line_img)
    cv2.waitKey()
    print(end_time-start_time)