#!/usr/bin/env python

# import ROS libraries
import rospy
import mavros
from mavros.utils import *
from mavros import setpoint as SP
import mavros.setpoint
import mavros.command
import mavros_msgs.msg
import mavros_msgs.srv
import geometry_msgs
import time
import serial
from datetime import datetime

# import mraa
import sys
import subprocess
import os
import sys
import platform
sys.path.append('/usr/local/lib/i386-linux-gnu/python2.7/site-packages/')



class vector3(object):
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0


class update_setpoint(object):
    def __init__(self,rospy):
        self.update_flag='LOCAL'
        self.frame_id='UPDATE_SETPOINT'
        self.timestamp=rospy.Time.now()

        #setup local position 
        self.local_pub = mavros.setpoint.get_pub_position_local(queue_size=10)
        self.local_sub = rospy.Subscriber(mavros.get_topic('setpoint_position', 'local'),
        geometry_msgs.msg.PoseStamped, self._local_cb)
        self.local_last_pos=vector3()
        self.local_msg=mavros.setpoint.PoseStamped(
            header=mavros.setpoint.Header(
                frame_id=self.frame_id,
                stamp=rospy.Time.now()),
            )

        #setup GPS position
        # self.GPS_pub =  rospy.Publisher(mavros.get_topic('setpoint_raw', 'global'),
        #  mavros_msgs.msg.GlobalPositionTarget, queue_size=10)
        # self.GPS_last_pos=0
        # self.GPS_sub = rospy.Subscriber(mavros.get_topic('setpoint_raw', 'target_global'),
        # mavros_msgs.msg.GlobalPositionTarget, self._GPS_cb)
        # self.GPS_msg=0

    def _local_cb(self, topic):
        if (topic.header.frame_id == self.frame_id):
            # ignore the msgs sent by myselfs
            return

        self.update_flag='LOCAL'
        self.timestamp=rospy.Time.now()
        # rospy.loginfo("setpoint_raw target_local get: x=%s, y=%s, z=%s,", 
            # topic.pose.position.x, topic.pose.position.y, topic.pose.position.z)
        self.local_last_pos.x=topic.pose.position.x;
        self.local_last_pos.y=topic.pose.position.y;
        self.local_last_pos.z=topic.pose.position.z;

    # def _GPS_cb(self, topic):
    #     self.update_flag='GPS'
    #     self.GPS_last_pos = topic

    def _set_pose(self, pose, pos):
        pose.pose.position.x = pos.x
        pose.pose.position.y = pos.y
        pose.pose.position.z = pos.z
        pose.header=mavros.setpoint.Header(
                    frame_id=self.frame_id,
                    stamp=rospy.Time.now())

    def update(self):
        if(rospy.Time.now()-self.timestamp < (rospy.Duration(0.05))):
            # if setpoint was publishing on time, dont bother to send again
            return
        # rospy.loginfo("Setpoint_keeper sending the setpoint!")
        if (self.update_flag=='LOCAL'):
            self._set_pose(self.local_msg, self.local_last_pos)
            self.local_pub.publish(self.local_msg)
        # if (update_flag=='GPS'):
        #     self._set_pose(self.GPS_msg, self.GPS_last_pos)
        #     self.GPS_pub.publish(self.GPS_msg)
        pass

class Task_manager(object):
    def __init__(self, fname):
        self.tasklog = open(fname, 'r')
        self.tasklist=[]
        self.task_amount=0
        self.task_index=0
        self.task_finish=True
        self.task_env = os.environ.copy()
        self.timestamp=rospy.Time.now()

        for eachline in self.tasklog:
            line = eachline.strip('\n').split(' ')
            # python TASK.py [args] [timeout in second]
            self.tasklist.append(['python', str(line[0])+'.py', ' '.join(line[1:-1])])
            self.task_amount+=1
        self.tasklog.close()



    def alldone(self):
        if (self.task_index>=self.task_amount):
            return True
        else:
            return False

    def nexttask(self):
        if (self.alldone()):
            pass
        rospy.loginfo("New task will execute: {}".format(self.tasklist[self.task_index]))
        subprocess.call(self.tasklist[self.task_index], env=self.task_env)
        self.task_index+=1
        self.task_finish = False
        self.timestamp=rospy.Time.now()


    def task_finished(self):
        if (self.task_finish):
            return True
        else:
            return False

    def task_left(self):
        return (self.task_amount-self.task_index)

    def task_elapse(self):
        return rospy.Duration(rospy.Time.now()-self.timestamp)