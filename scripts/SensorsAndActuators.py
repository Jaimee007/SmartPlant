#!/usr/bin/env python2.7


## @file SensorsAndActuators.py
#  @brief Python node: Poner pequeña descripcion del script
#
#  @section Node_workflow
#
# Quitar lo que no se desee y cambiar lo que se quiera:
#
# This node does nothing but creates a list of motor objects with specific parameters, ones
# from the parameter service of ROS and others from the configuration file generated by and for
# the Pololu Micro Maestro board.
#
# If desired, one can add new motors by filling the gaps in that configuration file. If no named is given, it wont
# treat that channel as a new motor:
#  @code
#   .
#   .
#   .
#  <!--Channel 0-->
#  <Channel name="head" mode="Servo" min="2432" max="8832" homemode="Goto" home="5600" speed="11" acceleration="0" neutral="6000" range="1905" />
#  <!--Channel 1-->
#  <Channel name="NEW_NAME" mode="Servo" min="NEW_MIN" max="NEW_MAX" homemode="Goto" home="NEW_HOME" speed="NEW_HOME_SPEED" acceleration="NEW_ACCELERATION_SPEED" neutral="NEW_NEUTRAL" range="NEW_RANGE" />
#   .
#   .
#   .
#  @endcode
#  Dont forget to load the modified file into the board by executing the UscCmd programm provided by Pololu [here](https://www.pololu.com/file/0J315/maestro-linux-150116.tar.gz).
#  Example:
#  @code
#  cd /home/user/Descargas/mini_maestro
#  ./UscCmd   --configure /home/user/catkin_ws/src/mini_lowcost/maestro_settings.txt
#  @endcode
#
#  Cambiar todo el código del archivo
#
#  @author Jaime Gomez Jimenez.
#  @date  November,2019




import threading
import rospy
from mini_lowcost import maestro
import time
import sys
import rospkg
import string
import math
import numpy as np
from xml.dom import minidom
from motor_msgs.msg import cmd_motor
from std_msgs.msg import Empty
from std_msgs.msg import Bool
from std_msgs.msg import Float32
from std_msgs.msg import Int8
from motor_msgs.srv import *
from dynamixel_msgs.msg import JointState


mutex = threading.Lock()

#------------------------------------------------------------#
## @brief Main and unique class.
#  Class created in order to have the possibility of publish inside subscribers among other capabilities.
#
#
class servo_control(threading.Thread):


    #------------------------------------------------------------#
    ## @brief Constructor of the class
    #  @param self:
    #  @param id:                  Name of the joint.
    #  @param channel:             Physical channel where the motor is connected.
    #  @param home:                Home position for the motor.
    #  @param min_possible_us:     Min value in microseconds corresponding with the low position limit of the servo
    #  @param max_possible_us:     Max value in microseconds corresponding with the high position limit of the servo
    #  @param user_min:            Minimum angle in radians set by the user, must be negative
    #  @param user_max:            Maximum angle in radians set by the user, must be positive
    #  @param motor_amplitude:     Motor movement rang in degrees
    #  @param default_vel:         Default velocity for the scenario where no velocity values are sent
    #  @param default_acc:         Default acceleration for the scenario where no acceleration values are sent
    #  @param port:                Udev rule SYMLINK for the Pololu Maestro board.
    #  @param num_device:          Pololu Maestro board number, in hexadecimal the default is 0x0C
    def __init__(self,id,channel,home,min_possible_us,max_possible_us,user_min,user_max,motor_amplitude,default_vel,default_acc,pololu_vel_min,pololu_vel_max,port='/dev/ttyACM0',num_device=0x0c):
        threading.Thread.__init__(self)
        ## @var command_pololu_sub
        #  @brief Subscriber object of command topic
        self.command_pololu_sub =rospy.Subscriber(id+'/command'           ,cmd_motor      ,self.command_pololu_callback)
        ## @var default_pololu_sub
        #  @brief Subscriber object of default_position topic
        self.default_pololu_sub =rospy.Subscriber(id+'/default_position'  ,Empty          ,self.default_pololu_callback)
        ## @var arrived_motor_pub
        #  @brief Publisher object of arrived success topic
        self.arrived_motor_pub  =rospy.Publisher (id+'/command_completed'  ,Bool           ,queue_size=10)
        ## @var motor_state_pub
        #  @brief Publisher object of current motor state
        self.state_motor_pub    =rospy.Publisher (id+'/state_lowfreq'              ,JointState ,queue_size=10)
        ## @var calibrate_service
        #  @brief Service object of calibrate service
        self.calibrate_service  =rospy.Service  (id+'/calibrate'           ,TestStatus  ,self.calibrate_callback)
        ## @var ping_service
        #  @brief Service object of ping service
        self.ping_service       =rospy.Service  (id+'/ping'                ,TestStatus  ,self.ping_callback)
        ## @var enable_service
        #  @brief Service object of enable service
        self.enable_service     =rospy.Service  (id+'/enable'              ,TestStatus  ,self.enable_callback)
        ## @var disable_service
        #  @brief Service object of disable service
        self.disable_service    =rospy.Service  (id+'/disable'             ,TestStatus  ,self.disable_callback)
        ## @var get_status_service
        #  @brief Service object of get_status service
        self.get_status_service =rospy.Service  (id+'/get_status'          ,GetState    ,self.get_status_callback)

        self.pub_plot_goal =rospy.Publisher (id+'/plot_goal'  , Float32           ,queue_size=10)
        self.pub_plot_current_pos  =rospy.Publisher (id+'/plot_current_pos'  ,Float32           ,queue_size=10)
        self.pub_plot_is_moving  =rospy.Publisher (id+'/plot_is_moving'  ,Int8           ,queue_size=10)

        ## @var _id
        #  @brief parser variable for id param
        self._id                =id
        ## @var _channel
        #  @brief  parser variable for channel param
        self._channel           =channel
        ## @var _port
        #  @brief  parser variable for port param
        self._port              =port
        ## @var _home
        #  @brief  parser variable for port param
        self._home              =home
        ## @var _num_device
        #  @brief  parser variable for home param
        self._num_device        =num_device
        ## @var _min_possible_us
        #  @brief  parser variable for num_device param
        self._min_possible_us   =min_possible_us
        ## @var _max_possible_us
        #  @brief  parser variable for max_possible_us param
        self._max_possible_us   =max_possible_us
        ## @var _default_vel
        #  @brief  parser variable for default_vel param
        self._default_vel=default_vel
        ## @var _default_acc
        #  @brief  parser variable for default_acc param
        self._default_acc=default_acc
        ## @var _pololu_vel_min
        #  @brief  parser variable for pololu_vel_min param
        self._pololu_vel_min=pololu_vel_min
        ## @var _pololu_vel_max
        #  @brief  parser variable for pololu_vel_max param
        self._pololu_vel_max=pololu_vel_max
        ## @var servo_arrived
        #  @brief  Boolean used to indicate if the arrived was successfull or interrupted
        self.servo_arrived      =True
        ## @var newcommand_flag
        #  @brief  Flag used to check multiple commands
        self.newcommand_flag    =True
        ## @var togglechecker
        #  @brief  Flag used to check if new command arrived
        self.togglechecker      =True
        ## @var micro_maestro
        #  @brief Main object of third parties library to send serial commands
        self.micro_maestro      =maestro.Controller(self._port,self._num_device)
        ## @var checkinterval
        #  @brief Time between checking movement to detect wether it's arrived or not
        self.checkinterval      =0.1
        ## @var enabled
        #  @brief Flag which determines if a servomotor can receive orders or not
        self.enabled            =True
        ## @var _motor_amplitude
        #  @brief Difference between max and min reachable angles by the motor, in degrees
        self._motor_amplitude   =motor_amplitude
        ## @var halfrangeinradians
        #  @brief Half of that range converted into radians
        self.halfrangeinradians =((self._motor_amplitude*2*math.pi)/360)/2
        self._user_min_us = 0
        self._user_max_us = 0
        self.initialize_callback(-1*user_min,user_max)
        self.position_converted=0
        self.lastvel = 0
        self.last_goal_in_radians=0
        self.current_pos_in_radians=0
    #------------------------------------------------------------#
    ## @brief Initialize the servo range based in the user min and max writen in the file "motors_limit.txt".
    #  @param user_min: view description in the constructor method
    #  @param user_max: view description in the constructor method
    def initialize_callback(self,user_min,user_max):
        self._user_min_us =int(np.interp (    user_min,   (-self.halfrangeinradians,0)    ,(self._min_possible_us,self._home) )   )
        self._user_max_us =int(np.interp (    user_max,   (0,self.halfrangeinradians)     ,(self._home,self._max_possible_us) )   )
        self.micro_maestro.setRange(self._channel,self._user_min_us,self._user_max_us)
        rospy.logdebug("##############################################")
        rospy.logdebug("##############       %s       ##############",self._id )
        rospy.logdebug("##############################################")
        rospy.logdebug("amplitude (degrees) : %s"    ,str(self._motor_amplitude))
        rospy.logdebug("amplitude (radians) : %s"    ,str(self.halfrangeinradians*2))
        rospy.logdebug("min limit (radians) : %s"    ,str(-1*self.halfrangeinradians))
        rospy.logdebug("max limit (radians) : %s"    ,str(self.halfrangeinradians))
        rospy.logdebug("user min  (radians) : %s"    ,str(user_min))
        rospy.logdebug("user max  (radians) : %s"    ,str(user_max))
        rospy.logdebug("min limit (quarter-useconds): %s"    ,str(self._min_possible_us))
        rospy.logdebug("max limit (quarter-useconds): %s"    ,str(self._max_possible_us))
        rospy.logdebug("user min  (quarter-useconds): %s"    ,str(self._user_min_us))
        rospy.logdebug("user max  (quarter-useconds): %s"    ,str(self._user_max_us))
        rospy.logdebug("default velocity (0-100): %s"    ,str(self._default_vel))
        rospy.logdebug("default acceleration: %s"    ,str(self._default_acc))
        rospy.logdebug("##############################################")

    #------------------------------------------------------------#
    ## @brief Calibrate service callback.
    #  @return  response:
    #  - bool success
    #  - string message
    def calibrate_callback(self,req):
    	mutex.acquire()
        self.micro_maestro.setAccel(self._channel,10)
        self.micro_maestro.setSpeed(self._channel,self.normalize_vel(30))
        self.lastvel=self.normalize_vel(30)
        self.micro_maestro.setTarget(self._channel,self._user_min_us)
        while self.micro_maestro.isMoving(self._channel):
            time.sleep(self.checkinterval)
        self.micro_maestro.setTarget(self._channel,self._user_max_us)
        while self.micro_maestro.isMoving(self._channel):
            time.sleep(self.checkinterval)
        self.micro_maestro.setTarget(self._channel,self._home)
        while self.micro_maestro.isMoving(self._channel):
            time.sleep(self.checkinterval)
        self.newcommand_flag = not self.newcommand_flag
        mutex.release()
        self.last_goal_in_radians=self.usec2radians(self._home)
        resp         =TestStatusResponse()
        resp.success =True
        resp.message ="Checked user limits"
        rospy.logdebug("Servicio calibrado para "+str(self._id)+"con velocidad 70 y aceleracion 10")
        return resp


    #------------------------------------------------------------#
    ## @brief Ping service callback.
    #  @param req: None
    #  @return response:
    #  - bool success
    #  - string reason.
    def ping_callback(self,req):
        resp         =TestStatusResponse()
        resp.success =False
        resp.message ="Feature not set yet"
        rospy.logdebug("Servicio ping para "+str(self._id))
        return resp

    #------------------------------------------------------------#
    ## @brief Enable service callback.
    #  @param req
    #  - string name
    #  - bool data.
    #  @return response: None
    def enable_callback(self,req):
        self.enabled=True
        mutex.acquire()
        self.micro_maestro.setAccel(self._channel,0)
        self.micro_maestro.setSpeed(self._channel,self.normalize_vel(0))
        self.lastvel=self.normalize_vel(30)
        self.micro_maestro.setTarget(self._channel,self._home)
        mutex.release()
        self.last_goal_in_radians=self.usec2radians(self._home)
        resp         =TestStatusResponse()
        resp.success =True
        resp.message ="Motor enabled and send to "+str(self._home)
        rospy.logdebug("Servicio enable para "+str(self._id))
        return resp
    #------------------------------------------------------------#
    ## @brief Disable service callback.
    #  @param req:
    #  - string name
    #  - bool data.
    #  @return response: None
    def disable_callback(self,req):
    	mutex.acquire()
        self.micro_maestro.setTarget(self._channel,0)
        mutex.release()
        self.enabled=False
        resp         =TestStatusResponse()
        resp.success =True
        resp.message ="Motor disabled"
        rospy.logdebug("Servicio disable para "+str(self._id))
        return resp


    #------------------------------------------------------------#
    ## @brief Get status service callback.
    #  @param req : None
    #  @return response:
    #  - string id
    #  - float64 position
    #  - float64 velocity
    #  - float64 acceleration
    #  - float64 torque
    #  - float64 goal
    #  - float64 voltage
    #  - int32 temperature
    #  - bool is_moving
    #  - float64 error
    def get_status_callback(self,req):
        resp             =GetStateResponse()
        resp.id          =0
        mutex.acquire()
        resp.position    =self.micro_maestro.getPosition(self._channel)
        resp.velocity    =0
        resp.torque      =0
        resp.goal        =0
        resp.voltage     =0
        resp.temperature =0
        resp.is_moving   =self.micro_maestro.isMoving(self._channel)
        mutex.release()
        resp.error       =0
        rospy.logdebug("Servicio get status para "+str(self._id))
        return resp

    #------------------------------------------------------------#
    ## @brief Command service callback.
    #  @param self The object pointer.
    #  @param command_msg Paso de argumento a la funcion callback
    #  @see default_pololu_callback()
    #  @return None
    def command_pololu_callback(self, command_msg):
        rospy.logdebug ('id: '+str(self._id)+ ', channel: '+str(self._channel)+', position: ' + str(command_msg.position)+' ,velocity: '+str(command_msg.velocity) +', acceleration: '+ str(command_msg.acceleration))
        if self.enabled:
            mutex.acquire()
            self.micro_maestro.setAccel(self._channel,int(command_msg.acceleration))
            if command_msg.velocity == 0:
                self.micro_maestro.setSpeed(self._channel,self.normalize_vel(self._default_vel))
                self.lastvel=self.normalize_vel(30)
            else:
                self.micro_maestro.setSpeed(self._channel,self.normalize_vel(command_msg.velocity))
                self.lastvel=self.normalize_vel(command_msg.velocity)
            if command_msg.position >0:
                self.position_converted = np.interp(command_msg.position,(0,self.halfrangeinradians),(self._home,self._max_possible_us))
            else:
                self.position_converted = np.interp(command_msg.position,(-self.halfrangeinradians,0),(self._min_possible_us,self._home))
            if self.micro_maestro.setTarget(self._channel,int(self.position_converted)):
                rospy.logdebug("Inside the set range")
            else :
                rospy.logwarn("Angle outside the user set range, going to user limit")
            mutex.release()
            self.last_goal_in_radians=self.usec2radians(self.position_converted)
            self.newcommand_flag = not self.newcommand_flag
            time.sleep(self.checkinterval*2)
            self.checkservo()
        else:
            rospy.logwarn("Not enabled")

    #------------------------------------------------------------#
    ## @brief Default position callback.
    #  @param self The object pointer.
    #  @param default_msg: Paso de argumento a la funcion callback
    #  @see command_pololu_callback()
    #  @return None
    def default_pololu_callback(self, command_msg):
        rospy.logdebug('Mandando '+str(self._id)+' a home')
        mutex.acquire()
        self.micro_maestro.setAccel(self._channel,0)
        self.micro_maestro.setSpeed(self._channel,self.normalize_vel(0))
        self.lastvel=self.normalize_vel(0)
        self.micro_maestro.setTarget(self._channel,self._home)
        mutex.release()
        self.last_goal_in_radians=self.usec2radians(self._home)
        self.newcommand_flag = not self.newcommand_flag
        time.sleep(self.checkinterval*2)
        self.checkservo()
        #1self.micro_maestro.goHome()#self._channel,command_msg.position)
        #1print(self.micro_maestro.getError())



    #------------------------------------------------------------#
    ## @brief Check servo function
    #  @param self The object pointer.
    #  @see command_pololu_callback()
    #  @return None
    def checkservo(self):
        self.togglechecker = self.newcommand_flag
        mutex.acquire()
        se_mueve=self.micro_maestro.isMoving(self._channel)
        mutex.release()
        while se_mueve:
            time.sleep(self.checkinterval)
            if self.togglechecker!=self.newcommand_flag:
                message=False
                self.arrived_motor_pub.publish(message)
                rospy.logwarn("New command received and didnt finish previus movement")
                break
            mutex.acquire()
            se_mueve=self.micro_maestro.isMoving(self._channel)
            mutex.release()
        if self.togglechecker==self.newcommand_flag:
            message=True
            self.arrived_motor_pub.publish(message)

    #------------------------------------------------------------#
    ## @brief Normalize velocity from 0-100 to a set range
    #  @param vel_percentage Velocity taken from the message
    #  @return Interpolated velocity based in _pololu_vel_min and _pololu_vel_max
    def normalize_vel(self,vel_percentage):
        return int(np.interp(vel_percentage,(0,100),(self._pololu_vel_min,self._pololu_vel_max)))

    def usec2radians(self,usec):
    	if usec>=self._home:
    		radians=np.interp(usec,(self._home,self._max_possible_us),(0,self.halfrangeinradians))
    	else:
    		radians=np.interp(usec,(self._min_possible_us,self._home),(-self.halfrangeinradians,0))
    	return radians
    #------------------------------------------------------------#
    ## @brief Publish motor status
    #  @param vel_percentage Velocity taken from the message
    #  @return Interpolated velocity based in _pololu_vel_min and _pololu_vel_max
    def publish_state(self):
        sent_state=JointState()
        sent_state.name=str(self._id)
        sent_state.goal_pos=self.last_goal_in_radians
        sent_state.velocity=int(np.interp(self.lastvel,(self._pololu_vel_min,self._pololu_vel_max),(0,100)))
        mutex.acquire()
        pos=float(self.micro_maestro.getPosition(self._channel))
        sent_state.is_moving=self.micro_maestro.isMoving(self._channel)
        mutex.release()
        sent_state.current_pos=self.usec2radians(pos)
        self.state_motor_pub.publish(sent_state)
        self.pub_plot_goal.publish(self.last_goal_in_radians)
        self.pub_plot_current_pos.publish(sent_state.current_pos)
        self.pub_plot_is_moving.publish(int(sent_state.is_moving))



if __name__ == '__main__':
    ## @var verbosity_level
    #  @brief Minimum level that will be shown in the command window
    verbosity_level=rospy.DEBUG
    ## @var log_level
    #  @brief Variable which stores the verbosity of the messages, default=INFO
    rospy.init_node('motores_clases',log_level=verbosity_level)
    ## @var rospack
    #  @brief Instance of ros package object
    rospack          =rospkg.RosPack()
    ## @var pkg_name
    #  @brief Variable which stores the name of the package
    pkg_name         ="mini_lowcost"
    ## @var PATH_CONFIG_FILE
    #  @brief Complete path to the configuration file of Pololu Maestro settings
    PATH_CONFIG_FILE =rospack.get_path(pkg_name) + str('/scripts/maestro_settings.txt')
    ## @var PATH_USER_FILE
    #  @brief Complete path to the user settings file of Pololu Maestro
    PATH_USER_FILE   =rospack.get_path(pkg_name) + str('/scripts/motors_limits.txt')
    ## @var xmldoc
    #  @brief Result of parsing the configuration file in order to get some values
    xmldoc           =minidom.parse(PATH_CONFIG_FILE)
    ## @var xmldoc2
    #  @brief Result of parsing the user settings file in order to get some values
    xmldoc2          =minidom.parse(PATH_USER_FILE)
    ## @var port_address
    #  @brief getting Ros parameter which stores the port name of Pololu, from alz_Devices launcher
    port_address     =rospy.get_param("~port")
    ## @var device_id
    #  @brief getting Ros parameter which stores the device number of the Maestro board,default is 0x0C (12), from alz_Devices launcher
    device_id        =rospy.get_param("~device_number")
    ## @var itemlist
    #  @brief Getting all items inside "channel" tag from the config file
    itemlist         = xmldoc.getElementsByTagName('Channel')
    ## @var itemlist2
    #  @brief Getting all items inside "channel" tag from the user settings file
    itemlist2        = xmldoc2.getElementsByTagName('Channel')
    ## @var objects_list
    #  @brief List where each instance of each motor will be stored.
    #  @see servo_control.__init__
    objects_list     =[]
    ## @var rate
    #  @brief Variable which stores the frequency sleep rate
    rate             =rospy.Rate(20)
    for x in range(0,len(itemlist)) :
        if(itemlist[x].attributes['name'].value)!='':
            objects_list.append(servo_control(id=str(itemlist[x].attributes['name'].value),channel=x,home=int(itemlist[x].attributes['home'].value),min_possible_us = int(itemlist[x].attributes['min'].value) ,max_possible_us = int(itemlist[x].attributes['max'].value),user_min=float(itemlist2[x].attributes['user_min_radians'].value),user_max=float(itemlist2[x].attributes['user_max_radians'].value), motor_amplitude = float(itemlist2[x].attributes['range_degrees'].value),default_vel=int(itemlist2[x].attributes['default_speed'].value),default_acc=int(itemlist2[x].attributes['default_acceleration'].value),pololu_vel_min=int(itemlist2[x].attributes['pololu_vel_min'].value),pololu_vel_max=int(itemlist2[x].attributes['pololu_vel_max'].value),port=str(port_address),num_device=int(device_id,16)))
            rospy.logdebug("-----------------------------------------------------------")
    while not rospy.is_shutdown():
        for Numero_motor in range(0,len(objects_list)):
            objects_list[Numero_motor].publish_state()
            rate.sleep()
            #rate.sleep()
