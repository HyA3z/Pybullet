from table_environment import *
import random

class Motion_primitives():
    def __init__(self, env_api, obj_list, drop_type=None, drop_prob=None, dt=None):
        """
        - drop_type (str): Specifies the type of operation where drops may occur. 
            Possible values:
            - 'pick': Drops may occur during the pick operation.
            - 'place': Drops may occur during the place operation.
            - 'pick+place': Drops may occur during both pick and place operations.
        - drop_prob (float): The probability of a drop. You can set specific probabilities for:
            - 'pick': Probability of dropping during the pick operation.
            - 'place': Probability of dropping during the place operation.
        - dt (float): Every `dt` seconds, the system checks if a drop occurs based on the defined probability.
        """
        self.env_API = env_api
        self.obj_list = obj_list
        self.motion_names = [
            'locate', 'pick', 'place'
        ]
        self.drop_type = drop_type 
        self.drop_prob = drop_prob
        self.dt = dt
        self.ratio = 0.2
        
    def check_vaild(self, motion):
        if motion not in self.motion_names:
            print("Illegal directives input!\n")
            return False
        return True

    def get_new_pos(self, place_xyz, ee_xyz):
        step = (place_xyz - ee_xyz) * self.ratio
        new_pos = ee_xyz + step
        return new_pos

    def move_to(self, target_pos):
        ee_xyz = self.env_API.get_ee_pos()
        while np.linalg.norm(target_pos - ee_xyz) > 0.01:
            new_pos = self.get_new_pos(target_pos, ee_xyz)
            self.env_API.movep(new_pos)
            self.env_API.step_sim_and_render()
            ee_xyz = self.env_API.get_ee_pos()

    def detect(self, pic, prompt):
        pass

    
    def locate(self, name):
        if name not in self.obj_list:
            print("Items that do not exist in the scene!\n")
            return
        else:
            return self.env_API.get_obj_pos(name)
    
    def pick(self, pick_pos):
        hover_xyz = np.float32([pick_pos[0], pick_pos[1], 0.2])
        if pick_pos.shape[-1] == 2:
            pick_xyz = np.append(pick_pos, 0.025)
        else:
            pick_xyz = pick_pos
            pick_xyz[2] = 0.025

        # Move to object.
        self.move_to(hover_xyz)
        self.move_to(pick_xyz)

        # Pick up object.
        if self.drop_type in ['pick', 'pick+place'] and random.random() < self.drop_prob[0]:
            self.env_API.gripper.release()  
        else:
            self.env_API.gripper.activate()

        for _ in range(240):
            self.env_API.step_sim_and_render()
        
        self.move_to(hover_xyz)

        for _ in range(50):
            self.env_API.step_sim_and_render()
        
        observation = self.env_API.get_observation()
        reward = self.env_API.get_reward()
        done = False
        info = {}
        return observation, reward, done, info

    def place(self, place_pos):
        if place_pos.shape[-1] == 2:
            place_xyz = np.append(place_pos, 0.15)
        else:
            place_xyz = place_pos
            place_xyz[2] = 0.15
        
        #Initilize start time and drop
        start_time = time.time()
        drop = False

        # Move to place location.
        ee_xyz = self.env_API.get_ee_pos()
        while np.linalg.norm(place_xyz - ee_xyz) > 0.01:
            new_pos = self.get_new_pos(place_xyz, ee_xyz)
            if self.drop_type in ['place', 'pick+place'] and time.time() - start_time >= 0.2 and drop != True and random.random() < self.drop_prob[1]:
                self.env_API.gripper.release()
                for _ in range(240):
                    self.env_API.step_sim_and_render()
                drop = True
                start_time = time.time()
            self.env_API.movep(new_pos)
            self.env_API.step_sim_and_render()
            ee_xyz = self.env_API.get_ee_pos()
        # Place down object.
        while (not self.env_API.gripper.detect_contact()) and (place_xyz[2] > 0.03):
            place_xyz[2] -= 0.001  # Modify????
            self.env_API.movep(place_xyz)
            for _ in range(3):
                self.env_API.step_sim_and_render()
        
        self.env_API.gripper.release()
        for _ in range(240):
            self.env_API.step_sim_and_render()

        place_xyz[2] = 0.2
        self.move_to(place_xyz)
        
        # Back to setting position
        self.move_to(np.float32([0, -0.5, 0.2]))

        observation = self.env_API.get_observation()
        reward = self.env_API.get_reward()
        done = False
        info = {}
        return observation, reward, done, info
