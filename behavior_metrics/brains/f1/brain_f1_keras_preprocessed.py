"""
    Robot: F1
    Framework: keras
    Number of networks: 1
    Network type: None
    Predicionts:
        linear speed(v)
        angular speed(w)

"""

import tensorflow as tf
import numpy as np
import cv2
import time
import os

from utils.constants import PRETRAINED_MODELS_DIR, ROOT_PATH
from os import path

PRETRAINED_MODELS = ROOT_PATH + '/' + PRETRAINED_MODELS_DIR + 'dir1/'

class Brain:
    """Specific brain for the f1 robot. See header."""

    def __init__(self, sensors, actuators, model=None, handler=None):
        """Constructor of the class.

        Arguments:
            sensors {robot.sensors.Sensors} -- Sensors instance of the robot
            actuators {robot.actuators.Actuators} -- Actuators instance of the robot

        Keyword Arguments:
            handler {brains.brain_handler.Brains} -- Handler of the current brain. Communication with the controller
            (default: {None})
        """
        self.motors = actuators.get_motor('motors_0')
        self.camera = sensors.get_camera('camera_0')
        self.handler = handler
        self.cont = 0
        self.inference_times = []
        self.gpu_inferencing = True if tf.test.gpu_device_name() else False
        
        if model:
            if not path.exists(PRETRAINED_MODELS + model):
                print("File " + model + " cannot be found in " + PRETRAINED_MODELS)

            self.net = tf.keras.models.load_model(PRETRAINED_MODELS + model)
        else: 
            print("Brain not loaded")

    def update_frame(self, frame_id, data):
        """Update the information to be shown in one of the GUI's frames.

        Arguments:
            frame_id {str} -- Id of the frame that will represent the data
            data {*} -- Data to be shown in the frame. Depending on the type of frame (rgbimage, laser, pose3d, etc)
        """
        self.handler.update_frame(frame_id, data)

    def execute(self):
        """Main loop of the brain. This will be called iteratively each TIME_CYCLE (see pilot.py)"""
         
        self.cont += 1
        
        image = self.camera.getImage().data
        image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

        
        if self.cont == 1:
            self.first_image = image

        try:
            image = image[240:480, 0:640]
            img = cv2.resize(image, (int(image.shape[1] / 4), int(image.shape[0] / 4)))
            # img = np.expand_dims(img, axis=0)
            
            #red_low   = (40,0,0)
            #red_low = (155,25,0)
            #red_up   = (255,0,0)
            #red_up = (179,255,255)
            #mask = cv2.inRange(img, red_low, red_up)
            
            #img_points = [img[0][79], img[14][79], img[29][79], img[44][79], img[59][79]]

            lower = np.array([0,150,170])
            upper = np.array([0, 255, 255])
            mask = cv2.inRange(img, lower, upper)
            
            img_points = [mask[0], mask[19], mask[39], mask[59]]
            # img_points = [mask[0], mask[14], mask[29], mask[44], mask[59]]
            # img_points = [mask[0], mask[4], mask[9], mask[14], mask[19], mask[24], mask[29], mask[34], mask[39], mask[44], mask[49], mask[54], mask[59]]
            
            new_img_points = []
            # Get center point from line where the mask 
            for img_point in img_points:
                mask_points = []
                for x, point in enumerate(img_point):
                    if point == 255:
                        mask_points.append(x)
                if len(mask_points) > 0:
                    new_img_points.append(mask_points[len(mask_points)//2])
                else:
                    #new_img_points.append(-1)
                    new_img_points.append(0)
                    
            img_points = new_img_points
            
            new_img = []
            for x in img_points:
                x = (x - 0) / 160 * 1 + 0
                new_img.append(x)
                
            img_points = new_img
            
            # print(img_points)
            
            #print(img[14])
            #print(mask[14])
            
            img_points = np.expand_dims(img_points, axis=0)
            start_time = time.time()
            prediction = self.net.predict(img_points)
            print('prediciton time ' + str(time.time() - start_time))
            self.inference_times.append(time.time() - start_time)
            prediction_v = prediction[0][0]*.5
            #prediction_v = prediction[0][0]
            prediction_w = prediction[0][1]*3
            #prediction_w = prediction[0][1]
            #print(str(prediction_v) + " - " + str(prediction_w))
            if prediction_w != '' and prediction_w != '':
                self.motors.sendV(prediction_v)
                self.motors.sendW(prediction_w)
                #self.motors.sendV(0)
                #self.motors.sendW(0)

        except Exception as err:
            print(err)
        
        self.update_frame('frame_0', img)
        # self.update_frame('frame_0', mask)