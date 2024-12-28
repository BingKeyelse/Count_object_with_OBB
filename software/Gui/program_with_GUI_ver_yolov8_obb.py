import sys
import cv2
import os
import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QEvent , QDateTime, QTimer , QMutex
from PyQt5.QtGui import QImage, QPixmap, QTransform, QPainter, QPainterPath, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel
#pyuic5 -x gui_main.ui -o gui_main.py
#pyuic5 -x gui_main_adjust.ui -o gui_main.py
# pyrcc5 -o resource_rc.py resource.qrc

#1280 960


from gui_main import Ui_MainWindow
from pypylon import pylon
from multiprocessing import Process, Value
import time
import threading
import pyscreenshot as ImageGrab
import serial
from datetime import datetime
import imutils
import shutil
import natsort
import resource_rc
from ultralytics import YOLO

time_start_ok=0

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        ### Define read weight model
        self.model= YOLO("/home/pronics-super/Desktop/hunghung back data/software Y Hook/Gui/best.pt")
        ### Run before to do not initie
        img = cv2.imread('/home/pronics-super/Desktop/hunghung back data/software Y Hook/Gui/data/image_to_handle.png')

        results=self.model.predict(img)
        ##### Set timer
        self.timer = QTimer(self)
        self.timer_log_out = QTimer(self)
        self.login_wrong=QTimer(self)
        self.adjust_parameter_program=QTimer(self)

        ##### check dữ liệu xem như nào trước khi đọc để gán
        self.check_read_data_back()
        ###### khoi tao gia tri cho toan bo adjust
        self.read_again_value_adjust()
        ###### khoi tao gia tri cho toan bo adjust camera
        self.read_again_value_camera_adjust()
        ##### bat cu khi nao co gia tri nao thay doi thi cap nhap vao


        data_backup_read= open("data/data_backup.txt","r")
        data_backup=data_backup_read.readlines()
        data_backup_read.close()

        self.load_value_adjust()
        self.load_point_backup()


        self.banana=0
        self.banana_ate=0
        self.area_count=0
        self.count_times=0
        self.count_sum=int(data_backup[0])
        self.mode_rotate=False
        self.mode_have_sponge=False
        self.frame_old=[]
        self.temp_image=[]
        self.mode_NG=False
        self.count_screw=0
        self.count_ok=int(data_backup[1])
        self.count_ng=int(data_backup[2])
        self.mode_running_gui=False
        # self.over_point=130 #### phần này viết thêm sau nhé
        # self.break_point=440 #### phần này viết thêm sau nhé
        self.mode_out_control=False
        self.mode_auto_scan= False
        self.mode_start_auto_scan=False
        self.mode_reset=False
        self.mode_but_show=False
        self.time_start_log_out=time.time()
        self.time_login_wrong=time.time()
        self.year_backup=[]
        self.month_backup=[]
        self.path_folder_today=0
        self.path_backup='data_backup_everyday'
        self.time_auto_scan_start=0
        

        self.ui.count_sum.setText(' Sum of products: {}'.format(self.count_sum))
        self.ui.count_ok.setText(' Sum of OK products: '+str(self.count_ok))
        self.ui.count_ng.setText(' Sum of NG products: '+str(self.count_ng))

        self.display_right_img_on_gui()
        self.ui.value_over.setValue(self.over_point)
        self.ui.value_break.setValue(self.break_point)

        self.ui.display_value_over.setText(str(self.over_point))
        self.ui.display_value_break.setText(str(self.break_point))
        self.ui.login.hide()


        ######## Phần này dùng để chiều chỉnh được ánh sáng và độ chập mở
        self.ui.adjust_basler.hide()
        self.ui.but_config_camera.clicked.connect(self.open_adjust_camera)
        self.ui.but_exit_camera.clicked.connect(self.close_adjust_camera)

        self.ui.display_running.hide()

        # Neu co su thay doi thi cap nhap
        self.ui.value_gain_raw.valueChanged.connect(self.upgrade_parameter_camera)
        self.ui.value_black_level.valueChanged.connect(self.upgrade_parameter_camera)

        self.ui.value_gramma_enable.valueChanged.connect(self.upgrade_parameter_camera)
        self.ui.value_gramma_selector.valueChanged.connect(self.upgrade_parameter_camera)
        

        self.ui.but_OK_gramma.clicked.connect(self.upgrade_parameter_camera)
        self.ui.value_digital_shift.valueChanged.connect(self.upgrade_parameter_camera)
        self.ui.value_expose.valueChanged.connect(self.upgrade_parameter_camera)
        self.ui.value_thread_camera.valueChanged.connect(self.upgrade_parameter_camera)

        # self.ui.adjust_expose.setEnabled(False)
        # self.ui.adjust_light.setEnabled(False)
        #############################

        # self.ui.adjust_light.valueChanged.connect(self.change_light)
        # self.ui.adjust_expose.valueChanged.connect(self.change_expose)

        # Nút start
        self.ui.but_start.clicked.connect(self.start)

        # Nút stop
        self.ui.but_pause.clicked.connect(self.pause)

        # Nút reset
        self.ui.but_reset.clicked.connect(self.reset)

        # Nút Save_daily_data
        self.ui.but_end_and_save.clicked.connect(self.save_daily_data)

        # Nút Scan Product
        self.ui.but_scan.clicked.connect(self.scan)

        # nut test ok
        self.ui.but_test_ok.hide()
        self.ui.but_test_ok.clicked.connect(self.output_ok)

        # nut test ng
        self.ui.but_test_ng.hide()
        self.ui.but_test_ng.clicked.connect(self.output_ng)

        ### Phần giao diện loggin
        self.ui.button_cancer.clicked.connect(self.cancer)
        self.ui.button_login.clicked.connect(self.loggin)
        self.ui.but_reset.setStyleSheet("""
            background-color: rgb(0, 0, 0);
            color: rgb(255, 255, 255);
            border-radius: 15px;
        """)
        self.ui.button_show.clicked.connect(self.show_pass)
        self.ui.label_wrong.hide()

        # Phần giao dien history
        self.ui.history_NG.hide()
        self.ui.but_history_NG.clicked.connect(self.history_NG)
        self.ui.but_exit.clicked.connect(self.exit_history_NG)
        self.ui.listWidget_NG.clicked.connect(self.show_img_NG)
        self.ui.but_up.clicked.connect(self.up_currentRow)
        self.ui.but_down.clicked.connect(self.down_currentRow)
        self.ui.but_clear.clicked.connect(self.clear_listwidget)


        self.stage=Value("i",0)
        self.mode_output_basler=Value("i",0)
        self.camera_process = Process(
    target=cam_Basler,
    args=(
        self.stage,
        self.mode_output_basler,
        self.value_gain_raw,
        self.value_black_level,
        self.value_gramma_enable,
        self.value_gramma_selector,
        self.value_gramma,
        self.value_digital_shift,
        self.value_expose,
        self.value_thread_camera,
        self.mode_adjust_camera,
    ),
    daemon=True
)
        # self.camera_process = Process(target = cam_Basler, daemon=True)
        self.camera_process.start()

        self.frame_count=0
        self.start_time=time.time()

        self.timer.timeout.connect(self.display_on_gui)
        self.timer.start(1)

        self.timer_log_out.timeout.connect(self.log_out)
        self.timer_log_out.start(1)

        self.login_wrong.timeout.connect(self.log_wrong)
        self.login_wrong.start(1)


        #### add more adjust #################################
        self.ui.widget_2.hide()
        ##### setup phần hiển thị khởi tạo lúc đầu
        self.ui.adjust_balance.show()
        self.ui.adjust_screw.hide()
        self.ui.adjust_pin.hide()
        self.ui.adjust_aid.hide()
        self.ui.label_OK.hide()

        #####
        self.value_thresh=0
        self.value_k=0
        self.value_area_thresh=0
        self.value_area_filter=0

        self.value_thresh_screw=0
        self.value_k_screw=0
        self.value_area_thresh_screw_max=0
        self.value_area_thresh_screw_min=0
        self.value_k_approval_screw=0

        self.value_thresh_pin=0
        self.value_k_pin=0
        self.value_area_thresh_pin_max=0
        self.value_area_thresh_pin_min=0
        self.value_k_approval_pin=0
        self.value_double_pin=0

        self.value_thresh_aid=0
        self.value_k_aid=0
        self.value_area_thresh_aid_limit=0
        self.value_area_thresh_aid_max=0
        self.value_area_thresh_aid_min=0
        self.value_area_thresh_aid_tiny=0
        self.value_area_thresh_aid_noise=0
        #####
        self.link_image_adjust=None
        self.path_folder_adjust='data_before_rorate'
        self.mode_adjust=False
        self.ui.adjust.hide()

        self.ui.but_balance_large.clicked.connect(self.show_adjust_balance)
        self.ui.but_balance_mini.clicked.connect(self.show_adjust_balance)
        self.ui.but_screw_large.clicked.connect(self.show_adjust_screw)
        self.ui.but_screw_mini.clicked.connect(self.show_adjust_screw)
        self.ui.but_pin_large.clicked.connect(self.show_adjust_pin)
        self.ui.but_pin_mini.clicked.connect(self.show_adjust_pin)
        self.ui.but_aid_large.clicked.connect(self.show_adjust_aid)
        self.ui.but_aid_mini.clicked.connect(self.show_adjust_aid)

        self.ui.but_config.clicked.connect(self.config_parameter)
        self.ui.but_config.clicked.connect(self.show_adjust_balance)

        self.ui.pushButton_30.clicked.connect(self.off_adjust_program)
        self.ui.pushButton_9.clicked.connect(self.off_adjust_program)
        self.ui.listWidget_image_original.clicked.connect(self.show_img_adjust)
        self.ui.but_up_adjust.clicked.connect(self.up_currentRow_adjust)
        self.ui.but_down_adjust.clicked.connect(self.down_currentRow_adjust)

        ########### Nhấn nhấn để lưu lại dữ liệu của value_adjust
        self.ui.pushButton_29.clicked.connect(self.save_value_adjust)
        self.ui.pushButton_10.clicked.connect(self.save_value_adjust)

        #### Phần này là timer cho phần điều chỉnh
        self.adjust_parameter_program.timeout.connect(self.adjust_program)
        self.adjust_parameter_program.start(1)

    ## Code 
    ####################################### camera adjust###################################
    def read_again_value_camera_adjust(self):
        # doc fil du lieu adjust a
        self.mode_adjust_camera=Value("b",0)
        self.value_gain_raw= Value("i",0)
        self.value_black_level= Value("i",0)
        self.value_gramma_enable= Value("b",0)
        self.value_gramma_selector= Value("b",0)
        self.value_gramma= Value("d",0)
        self.value_digital_shift= Value("i",0)
        self.value_expose= Value("d",0)
        self.value_thread_camera= Value("i",0)

        file_read_value_adjust= open("data/data_value_adjust_camera.txt","r")
        file_read_value_adjust=file_read_value_adjust.readlines()

        self.value_gain_raw.value= (int(file_read_value_adjust[0]))      #0
        self.value_black_level.value= (int(file_read_value_adjust[1]))           #1
        self.value_gramma_enable.value= (int(file_read_value_adjust[2])) #2
        self.value_gramma_selector.value = (int(file_read_value_adjust[3])) #3
        self.value_gramma.value= (float(file_read_value_adjust[4]))         #4
        self.value_digital_shift.value = (int(file_read_value_adjust[5]))              #5
        self.value_expose.value= (float(file_read_value_adjust[6]))#6
        self.value_thread_camera.value= (int(file_read_value_adjust[7]))#6

        #########

        self.ui.value_gain_raw.setValue(self.value_gain_raw.value)
        self.ui.value_black_level.setValue(self.value_black_level.value)

        self.ui.value_gramma_enable.setValue(self.value_gramma_enable.value)
        self.ui.value_gramma_selector.setValue(self.value_gramma_selector.value)

        self.ui.value_gramma.setText(str(self.value_gramma.value))
        self.ui.value_digital_shift.setValue(self.value_digital_shift.value)
        self.ui.value_expose.setValue(int(self.value_expose.value))
        self.ui.value_thread_camera.setValue(int(self.value_thread_camera.value))

        ###########

        self.ui.value_gain_raw_display.setText(str(self.value_gain_raw.value))
        self.ui.value_black_level_display.setText(str(self.value_black_level.value))

        self.ui.value_digital_shift_display.setText(str(self.value_digital_shift.value))
        self.ui.value_expose_display.setText(str(self.value_expose.value))
        self.ui.value_thread_camera_display.setText(str(self.value_thread_camera.value))
    
    def upgrade_parameter_camera(self):

        self.value_gain_raw.value=int(self.ui.value_gain_raw.value())
        self.value_black_level.value=int(self.ui.value_black_level.value())
        self.value_gramma_enable.value= int(self.ui.value_gramma_enable.value())
        self.value_gramma_selector.value= int(self.ui.value_gramma_selector.value())
        self.value_gramma.value= float(self.ui.value_gramma.text())
        self.value_digital_shift.value= int(self.ui.value_digital_shift.value())
        self.value_expose.value= float(self.ui.value_expose.value())
        self.value_thread_camera.value= int(self.ui.value_thread_camera.value())

        self.ui.value_gain_raw_display.setText(str(self.value_gain_raw.value))
        self.ui.value_black_level_display.setText(str(self.value_black_level.value))

        self.ui.value_digital_shift_display.setText(str(self.value_digital_shift.value))
        self.ui.value_expose_display.setText(str(self.value_expose.value))
        self.ui.value_thread_camera_display.setText(str(self.value_thread_camera.value))


        data_backup_write=open("data/data_value_adjust_camera.txt","w")
        data_all_write = [str(self.value_gain_raw.value)+"\n"+str(self.value_black_level.value)+"\n"+str(self.value_gramma_enable.value)+"\n"+\
                            str(self.value_gramma_selector.value)+"\n"+str(self.value_gramma.value)+"\n"+str(self.value_digital_shift.value)+"\n"+\
                            str(self.value_expose.value) +"\n"+ str(self.value_thread_camera.value)]
        
        data_backup_write.writelines(data_all_write)
        data_backup_write.close()


    
    def open_adjust_camera(self):
        self.ui.adjust_basler.show()
        self.mode_adjust_camera.value=1

    def close_adjust_camera(self):
        self.ui.adjust_basler.hide()
        self.mode_adjust_camera.value=0



####################################### widget adjust###################################

    def show_adjust_balance(self):
        self.ui.adjust_balance.show()
        self.ui.adjust_screw.hide()
        self.ui.adjust_pin.hide()
        self.ui.adjust_aid.hide()
    
    def show_adjust_screw(self):
        self.ui.adjust_balance.hide()
        self.ui.adjust_screw.show()
        self.ui.adjust_pin.hide()
        self.ui.adjust_aid.hide()

    def show_adjust_pin(self):
        self.ui.adjust_balance.hide()
        self.ui.adjust_screw.hide()
        self.ui.adjust_pin.show()
        self.ui.adjust_aid.hide()
    
    def show_adjust_aid(self):
        self.ui.adjust_balance.hide()
        self.ui.adjust_screw.hide()
        self.ui.adjust_pin.hide()
        self.ui.adjust_aid.show()

    def up_currentRow_adjust(self):
        self.ui.space_picture_apply.clear()
        current_row=self.ui.listWidget_image_original.currentRow()
        if current_row>=1:
            current_row-=1
            self.ui.listWidget_image_original.setCurrentRow(current_row)
            self.show_img_adjust()

    def down_currentRow_adjust(self):
        self.ui.space_picture_apply.clear()

        #### Xem so luong file trong path
        count_limit= self.ui.listWidget_image_original.count()

        current_row=self.ui.listWidget_image_original.currentRow()
        # print(current_row)
        if current_row<=(count_limit-2):
            current_row+=1
            self.ui.listWidget_image_original.setCurrentRow(current_row)
            self.show_img_adjust()

    def show_img_adjust(self):
        self.ui.space_picture_apply.clear()
        item_img_ng = self.ui.listWidget_image_original.currentItem()
        if item_img_ng is not None:
            name_image = item_img_ng.text()
            # print(item_img_ng)
            # link_NG_picture = item_img_ng.replace('.txt', '.png')
            # print(link_NG_picture)
            #print(item_show_ng_text)
            self.link_image_adjust=os.path.join(self.path_folder_adjust, name_image)
        
    def history_adjust(self):
        # self.ui.history_NG.show()
        # Khi mở là sắp xếp luôn nhé ở phần listwidget
        self.ui.listWidget_image_original.clear()

        path_txt_NG='data_before_rorate_txt/'
        path_list_ptxt_NG= ((os.listdir(os.path.expanduser(path_txt_NG))))
        number_path_list = natsort.natsorted(path_list_ptxt_NG,reverse = 0)
        # print(number_path_list)

        #### đổi đuôi luôn
        # Đổi phần mở rộng từ .txt sang .png
        new_file_names = []
        for file_name in number_path_list:
            if file_name.endswith('.txt'):
                new_file_name = file_name.replace('.txt', '.png')
                new_file_names.append(new_file_name)
            else:
                new_file_names.append(file_name)
        ####
        
        if len(number_path_list)<100:
            for i in range(0,len(new_file_names)):
                self.ui.listWidget_image_original.insertItem(i+1,str(new_file_names[i])) 
        else:
            for i in range(len(number_path_list)-100,len(number_path_list)):
                self.ui.listWidget_image_original.insertItem(i+1,str(new_file_names[i])) 

        self.ui.listWidget_image_original.scrollToBottom()

    def load_value_adjust(self):
        ################# read value balance
        self.value_thresh=self.ui.value_thresh.value()            #0
        self.value_k=self.ui.value_k.value()                      #1
        self.value_area_thresh=self.ui.value_area_thresh.value()  #2
        self.value_area_filter=self.ui.value_area_filter.value()  #3

        self.ui.thresh.setText('Thresh: '+str(self.value_thresh))
        self.ui.k.setText('K: '+str(self.value_k))
        self.ui.area_thresh.setText('Area thresh: '+str(self.value_area_thresh))
        self.ui.area_filter.setText('Area filter:'+str(self.value_area_filter))

        ################# read value screw
        self.value_thresh_screw=self.ui.value_thresh_screw.value()                   #4
        self.value_k_screw=self.ui.value_k_screw.value()                             #5
        self.value_area_thresh_screw_max=self.ui.value_area_thresh_screw_max.value() #6
        self.value_area_thresh_screw_min=self.ui.value_area_thresh_screw_min.value() #7
        self.value_k_approval_screw=self.ui.value_k_accept_screw.value()             #8

        self.ui.thresh_screw.setText('Thresh: '+str(self.value_thresh_screw))
        self.ui.k_screw.setText('K: '+str(self.value_k_screw))
        self.ui.area_thresh_screw_max.setText('Area thresh max: '+str(self.value_area_thresh_screw_max))
        self.ui.area_thresh_screw_min.setText('Area thresh min: '+str(self.value_area_thresh_screw_min))
        self.ui.k_approval_screw.setText('K approval: '+str(self.value_k_approval_screw))

        ########## read value pin
        self.value_thresh_pin=self.ui.value_thresh_pin.value()                  #9
        self.value_k_pin=self.ui.value_k_pin.value()                            #10
        self.value_area_thresh_pin_max=self.ui.value_area_thresh_pin_max.value()#11
        self.value_area_thresh_pin_min=self.ui.value_area_thresh_pin_min.value()#12
        self.value_k_approval_pin=self.ui.value_k_accept_pin.value()            #13
        self.value_double_pin= self.ui.value_area_double_pin.value()            #14

        self.ui.thresh_pin.setText('Thresh: '+str(self.value_thresh_pin))
        self.ui.k_pin.setText('K: '+str(self.value_k_pin))
        self.ui.area_thresh_pin_max.setText('Area thresh max: '+str(self.value_area_thresh_pin_max))
        self.ui.area_thresh_pin_min.setText('Area thresh min: '+str(self.value_area_thresh_pin_min))
        self.ui.k_approval_pin.setText('K approval: '+str(self.value_k_approval_pin))
        self.ui.area_double_pin.setText('Area double pin: '+str(self.value_double_pin))

        ########## read value aid
        self.value_thresh_aid=self.ui.value_thresh_aid.value()                      #15
        self.value_k_aid=self.ui.value_k_aid.value()                                #16
        self.value_area_thresh_aid_limit=self.ui.value_area_thresh_aid_limit.value()#17
        self.value_area_thresh_aid_max=self.ui.value_area_thresh_aid_max.value()    #18
        self.value_area_thresh_aid_min=self.ui.value_area_thresh_aid_min.value()    #19
        self.value_area_thresh_aid_tiny=self.ui.value_area_thresh_aid_tiny.value()    #20
        self.value_area_thresh_aid_noise=self.ui.value_area_thresh_aid_noise.value()    #21

        self.ui.thresh_aid.setText('Thresh: '+str(self.value_thresh_aid))
        self.ui.k_aid.setText('K: '+str(self.value_k_aid))
        self.ui.area_thresh_aid_limit.setText('Limit break: '+str(self.value_area_thresh_aid_limit))

        self.ui.area_thresh_aid_max.setText('Area thresh max: '+str(self.value_area_thresh_aid_max))
        self.ui.area_thresh_aid_min.setText('Area thresh min: '+str(self.value_area_thresh_aid_min))
        self.ui.area_thresh_aid_tiny.setText('Tiny break: '+str(self.value_area_thresh_aid_tiny))
        self.ui.area_thresh_aid_noise.setText('Noise break: '+str(self.value_area_thresh_aid_noise))

    def save_value_adjust(self):
        self.load_value_adjust()

        data_backup_write=open("data/data_value_adjust.txt","w")
        data_all_write = [str(self.value_thresh)+"\n"+str(self.value_k)+"\n"+str(self.value_area_thresh)+"\n"+\
                            str(self.value_area_filter)+"\n"+str(self.value_thresh_screw)+"\n"+str(self.value_k_screw)+"\n"+\
                            str(self.value_area_thresh_screw_max)+"\n"+str(self.value_area_thresh_screw_min)+"\n"+str(self.value_k_approval_screw)+"\n"+\
                            str(self.value_thresh_pin)+"\n"+str(self.value_k_pin)+"\n"+str(self.value_area_thresh_pin_max)+"\n"+\
                            str(self.value_area_thresh_pin_min)+"\n"+str(self.value_k_approval_pin)+"\n"+str(self.value_double_pin)+"\n"+\
                            str(self.value_thresh_aid)+"\n"+str(self.value_k_aid)+"\n"+str(self.value_area_thresh_aid_limit)+"\n"+\
                            str(self.value_area_thresh_aid_max)+ "\n"+ str(self.value_area_thresh_aid_min)+"\n"+ str(self.value_area_thresh_aid_tiny) +"\n"+\
                            str(self.value_area_thresh_aid_noise)]
        data_backup_write.writelines(data_all_write)
        data_backup_write.close()
    
    def read_again_value_adjust(self):
        # doc fil du lieu adjust a
        file_read_value_adjust= open("data/data_value_adjust.txt","r")
        file_read_value_adjust=file_read_value_adjust.readlines()
        # file_read_value_adjust.close()

        self.ui.value_thresh.setValue(int(file_read_value_adjust[0]))      #0
        self.ui.value_k.setValue(int(file_read_value_adjust[1]))           #1
        self.ui.value_area_thresh.setValue(int(file_read_value_adjust[2])) #2
        self.ui.value_area_filter.setValue(int(file_read_value_adjust[3])) #3

        ################# read value screw
        self.ui.value_thresh_screw.setValue(int(file_read_value_adjust[4]))         #4
        self.ui.value_k_screw.setValue(int(file_read_value_adjust[5]))              #5
        self.ui.value_area_thresh_screw_max.setValue(int(file_read_value_adjust[6]))#6
        self.ui.value_area_thresh_screw_min.setValue(int(file_read_value_adjust[7]))#7
        self.ui.value_k_accept_screw.setValue(int(file_read_value_adjust[8]))       #8

        ########## read value pin
        self.ui.value_thresh_pin.setValue(int(file_read_value_adjust[9]))           #9
        self.ui.value_k_pin.setValue(int(file_read_value_adjust[10]))               #10
        self.ui.value_area_thresh_pin_max.setValue(int(file_read_value_adjust[11])) #11
        self.ui.value_area_thresh_pin_min.setValue(int(file_read_value_adjust[12])) #12
        self.ui.value_k_accept_pin.setValue(int(file_read_value_adjust[13]))        #13
        self.ui.value_area_double_pin.setValue(int(file_read_value_adjust[14]))     #14

        ########## read value aid
        self.ui.value_thresh_aid.setValue(int(file_read_value_adjust[15]))            #15
        self.ui.value_k_aid.setValue(int(file_read_value_adjust[16]))                 #16
        self.ui.value_area_thresh_aid_limit.setValue(int(file_read_value_adjust[17])) #17
        self.ui.value_area_thresh_aid_max.setValue(int(file_read_value_adjust[18]))   #18
        self.ui.value_area_thresh_aid_min.setValue(int(file_read_value_adjust[19]))   #19
        self.ui.value_area_thresh_aid_tiny.setValue(int(file_read_value_adjust[20]))   #20
        self.ui.value_area_thresh_aid_noise.setValue(int(file_read_value_adjust[21]))   #20
    

    def adjust_program(self):
        self.load_value_adjust()
        if self.mode_adjust==True:
            self.ui.label_screw_ok.hide()
            self.ui.label_pin_ok.hide()
            self.ui.label_aid_ok.hide()
            

            # phần đầu của việc xử lý các thông số hình ảnh 
            largest_area=0
            image=cv2.imread(self.link_image_adjust,0)

            ### đầu tiền để xoay cần xác định được hình ảnh của thằng sponge 
            if image is not None:
                image=cv2.imread(self.link_image_adjust,0)
                image=cv2.resize(image,(320,250))
                blurred = cv2.GaussianBlur(image.copy(), (11, 11), 1)
                _, thresh = cv2.threshold(blurred, self.value_thresh, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)# tham số ngưỡng phán định

                k=self.value_k 
                kernel11 = np.ones((3,3), np.uint8) ### lựa chọn hệ số kernel phù hợp
                edges = cv2.erode(thresh, kernel11, iterations=k)  ## hệ số mở rộng
                edges = cv2.dilate(edges, kernel11, iterations=k)  ## hệ số thu nhỏ

                # Tìm các contour
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    largest_contour = max(contours, key=cv2.contourArea)
                    largest_area = int(cv2.contourArea(largest_contour))
                    self.ui.value_result_area.setText(str(largest_area))

                if largest_area>self.value_area_thresh and largest_area<25000:
                    rect = cv2.minAreaRect(largest_contour)
                    box = cv2.boxPoints(rect)
                    box = np.intp(box)

                    center, size, angle = rect
                    width, height = size

                    if width < height:
                        angle = angle + 90
                    
                    rotated_process = imutils.rotate(image.copy(),angle)
                    ### Đã xoay thành công giờ là phần detect lại để xoay đúng chiều như mong muốn

                    ###detect_sponge

                    blurred1 = cv2.GaussianBlur(rotated_process.copy(), (11, 11), 1)

                    _, thresh1 = cv2.threshold(blurred1, self.value_thresh, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    k=self.value_k 
                    kernel11 = np.ones((3,3), np.uint8) ### lựa chọn hệ số kernel phù hợp
                    edges1 = cv2.erode(thresh1, kernel11, iterations=k)  ## hệ số mở rộng
                    edges1 = cv2.dilate(edges1, kernel11, iterations=k)  ## hệ số thu nhỏ

                    # hình ảnh đang điều chỉnh
                    edges_show=cv2.resize(edges1,(300,230))
                    h,w=edges_show.shape
                    step= w
                    q = QImage(bytes(edges_show.data),w,h,step, QImage.Format_Grayscale8)
                    self.ui.space_image_balance.setPixmap(QPixmap.fromImage(q))


                    # Tìm các contour
                    contours, _ = cv2.findContours(edges1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if contours:
                        largest_contour = max(contours, key=cv2.contourArea)
                        # Tính hình chữ nhật bao quanh contour lớn nhất
                        x, y, w, h = cv2.boundingRect(largest_contour)

                    # print('gia tri mang:{} and {}'.format(x,y))

                    region1 = rotated_process[0:y, :]
                    region2 = rotated_process[y+h:, :]
                    mode_flip=self.filter_thresh_2area_adjust(region1,region2)

                    if mode_flip:
                        img_standard=cv2.rotate(rotated_process, cv2.ROTATE_180)
                    else:
                        img_standard=rotated_process

                    # detect_number_of_component
                    _, thresh_component = cv2.threshold(img_standard, self.value_thresh, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    
                    k=self.value_k 
                    kernel11 = np.ones((3,3), np.uint8) ### lựa chọn hệ số kernel phù hợp
                    edges_component = cv2.erode(thresh_component, kernel11, iterations=k)  ## hệ số mở rộng
                    edges_component = cv2.dilate(edges_component, kernel11, iterations=k)  ## hệ số thu nhỏ

                    # Tìm các contour
                    contours_component, _ = cv2.findContours(edges_component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if contours_component:
                        largest_contour = max(contours_component, key=cv2.contourArea)
                        # largest_area = cv2.contourArea(largest_contour)

                        # Tính hình chữ nhật bao quanh contour lớn nhất
                        x, y, w, h = cv2.boundingRect(largest_contour)

                    # Chia ảnh thành 3 vùng dọc
                        # region1 = img_standard[0:y+20, :]
                        region1 = img_standard[0:y, x-5:x+w+5]
                        region2 = img_standard[y:y+h, x-5:x+w+5]
                        region3 = img_standard[y+h+2:, x-5:x+w+5]
                    # Check thong so nao
                        bit1, region1=self.check_screw_adjust(region1)
                        bit2, region2=self.check_push_pin_adjust(region2)
                        bit3, region3=self.check_push_aid_adjust(region3)
                        # print('gia tri bit nhan duoc: {} {} {}'.format(bit1,bit2,bit3))

                        if bit1==True and bit2==True and bit3==True:
                            reconstructed_img = np.vstack((region1, region2, region3))
                            reconstructed_img=cv2.resize(reconstructed_img,(300,230))
                            h,w,c=reconstructed_img.shape
                            step= c*w
                            q = QImage(reconstructed_img.data,w,h, step, QImage.Format_RGB888)
                            self.ui.space_picture_apply.setPixmap(QPixmap.fromImage(q))
                            self.ui.label_OK.show()
                        else:
                            img_standard=cv2.resize(img_standard,(300,230))
                            h,w=img_standard.shape
                            step= w
                            q = QImage(bytes(img_standard.data),w,h,step, QImage.Format_Grayscale8)
                            self.ui.space_picture_apply.setPixmap(QPixmap.fromImage(q))
                            self.ui.label_OK.hide()
                    else:
                        self.ui.space_picture_apply.clear()
                        self.ui.label_OK.hide()



                else:
                    thresh=cv2.resize(thresh,(300,230))
                    h,w=thresh.shape
                    step= w
                    q = QImage(thresh.data,w,h,step, QImage.Format_Grayscale8)
                    self.ui.space_image_balance.setPixmap(QPixmap.fromImage(q))
            else:
                self.ui.space_picture_apply.clear()


    def off_adjust_program(self):
        self.mode_adjust=False
        self.load_value_adjust()

    def config_parameter(self):
        self.ui.adjust.show()
        self.history_adjust()
        self.mode_adjust=True

#########################################################################################
    def load_point_backup(self):
        file_to_read= open("data/data_point_backup.txt","r")
        file_to_read=file_to_read.readlines()
        # print(file_to_read)
        self.over_point=int(file_to_read[0])
        self.break_point=int(file_to_read[1])
        # return None
        self.ui.value_over.setValue(self.over_point)
        self.ui.value_break.setValue(self.break_point)
    def clear_listwidget(self):
        self.ui.space_to_display_history_NG.clear()
        self.ui.listWidget_NG.clear()

        path_txt_NG='data/data_backup_everyday_txt/'
        path_list_ptxt_NG= ((os.listdir(os.path.expanduser(path_txt_NG))))

        for file in path_list_ptxt_NG:
            file_path = os.path.join(path_txt_NG, file)
            os.remove(file_path)
 
    def up_currentRow(self):
        # count= self.ui.listWidget_NG.count()
        current_row=self.ui.listWidget_NG.currentRow()
        # print(current_row)
        if current_row>=1:
            current_row-=1
            self.ui.listWidget_NG.setCurrentRow(current_row)
            self.show_img_NG()

    def down_currentRow(self):
        #### Xem so luong file trong path
        count_limit= self.ui.listWidget_NG.count()

        current_row=self.ui.listWidget_NG.currentRow()
        # print(current_row)
        if current_row<=(count_limit-2):
            current_row+=1
            self.ui.listWidget_NG.setCurrentRow(current_row)
            self.show_img_NG()
    
    def show_img_NG(self):
        # count= self.ui.listWidget_NG.count()
        item_img_ng = self.ui.listWidget_NG.currentItem()
        if item_img_ng is not None:
            item_img_ng = item_img_ng.text()
            link_NG_picture = item_img_ng.replace('.txt', '.jpg')
            # print(link_NG_picture)
            #print(item_show_ng_text)
            link=os.path.join(self.path_folder_today, link_NG_picture)
            img=cv2.imread(link)
            img=cv2.cvtColor(img,cv2.COLOR_RGB2BGR)  
            # self.ui.space_to_display_history_NG.setPixmap(QtGui.QPixmap(img))

            h,w,c=img.shape
            step= c*w
            q = QImage(img.data,w,h, step, QImage.Format_BGR888)
            self.ui.space_to_display_history_NG.setPixmap(QPixmap.fromImage(q))

    def history_NG(self):
        self.ui.history_NG.show()
        # Khi mở là sắp xếp luôn nhé ở phần listwidget
        self.ui.listWidget_NG.clear()

        path_txt_NG='data/data_backup_everyday_txt/'
        path_list_ptxt_NG= ((os.listdir(os.path.expanduser(path_txt_NG))))
        number_path_list = natsort.natsorted(path_list_ptxt_NG,reverse = 0)

        #### Đổi đuôi luôn
        # Đổi phần mở rộng từ .txt sang .jpg
        new_file_names = []
        for file_name in number_path_list:
            if file_name.endswith('.txt'):
                new_file_name = file_name.replace('.txt', '.jpg')
                new_file_names.append(new_file_name)
            else:
                new_file_names.append(file_name)
        ####
        
        if len(number_path_list)<100:
            for i in range(0,len(new_file_names)):
                self.ui.listWidget_NG.insertItem(i+1,str(new_file_names[i])) 
        else:
            for i in range(0,100):
                self.ui.listWidget_NG.insertItem(i+1,str(new_file_names[i])) 

        self.ui.listWidget_NG.scrollToBottom()
    
    def update_listwidget(self):
        # self.ui.history_NG.show()
        # Khi mở là sắp xếp luôn nhé ở phần listwidget
        self.ui.listWidget_NG.clear()

        path_txt_NG='data/data_backup_everyday_txt/'
        path_list_ptxt_NG= ((os.listdir(os.path.expanduser(path_txt_NG))))
        number_path_list = natsort.natsorted(path_list_ptxt_NG,reverse = 0)

        #### Đổi đuôi luôn
        # Đổi phần mở rộng từ .txt sang .jpg
        new_file_names = []
        for file_name in number_path_list:
            if file_name.endswith('.txt'):
                new_file_name = file_name.replace('.txt', '.jpg')
                new_file_names.append(new_file_name)
            else:
                new_file_names.append(file_name)
        ####
        
        if len(number_path_list)<100:
            for i in range(0,len(new_file_names)):
                self.ui.listWidget_NG.insertItem(i+1,str(new_file_names[i])) 
        else:
            for i in range(0,100):
                self.ui.listWidget_NG.insertItem(i+1,str(new_file_names[i])) 

        self.ui.listWidget_NG.scrollToBottom()

    def exit_history_NG(self):
        self.ui.history_NG.hide()
    
    # Nếu chương trình có lỗi gì đó xảy ra thì luôn có một file backup sẵn sàng được sử dụng
    def check_read_data_back(self):
        data_backup_read= open("data/data_backup.txt","r")
        data_backup=data_backup_read.readlines()
        if len(data_backup)==3:
            for i in range(3):
                if self.Check_convert_str_to_int(data_backup[i])==False:
                    self.swap_file_data_bakcup()
        else:
            self.swap_file_data_bakcup()

    def output_ok(self):
        self.mode_output_basler.value=1 # OK
    
    def output_ng(self):
        self.mode_output_basler.value=2 # NG

    def display_on_gui(self):

        ##### Lệnh để check fps của chương trình
        self.frame_count += 1
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 1.0:
            fps = self.frame_count / elapsed_time
            # print(f"FPS: {fps}")
            self.frame_count = 0
            self.start_time = time.time()
        #####

        self.check_link_now_to_save_data()
        self.restore_data()
        if self.stage.value==1 and self.mode_running_gui==True:
            self.start=time.time()
            img=cv2.imread("data/image_to_save.png",0)
            # print(img.shape)
            # cv2.line(img, (100, 430), (100,470), (255), 2)
            img_sz = cv2.resize(img, (140, 240))

            if img is not None:
                # self.start=time.time()

                # cv2.line(img, (0, 230), (141,230), (0), 2)
                # cv2.line(img, (0, 225), (141,225), (0), 2)
                cv2.line(img_sz, (0, 225), (141,225), (0), 2)


                ### out screen1
                h,w=img_sz.shape
                step= w
                q = QImage(img_sz.data,w,h,step, QImage.Format_Grayscale8)
                self.ui.screen1.setPixmap(QPixmap.fromImage(q))

                self.conveyor_running_count(img)
                self.stage.value=0
                # print(int(1/(time.time()-self.start)))

                data_backup_write=open("data/data_backup.txt","w")
                data_all_write = [str(self.count_sum)+"\n"+str(self.count_ok)+"\n"+str(self.count_ng)]
                data_backup_write.writelines(data_all_write)
                data_backup_write.close()
                self.restore_data()


            else:
                self.stage.value=0
    
    def restore_data(self): # dùng để chuyển dữ liệu từ file này sang 1 file backup dự phòng
        # Đường dẫn tới file nguồn và file đích
        source_file_path = 'data/data_backup.txt'
        destination_file_path = 'data/data_backup_v1.txt'

        ### Phai check data truoc tie
        self.check_read_data_back()
        # Mở file nguồn để đọc dữ liệu
        with open(source_file_path, 'r', encoding='utf-8') as source_file:
            # Đọc toàn bộ nội dung từ file nguồn
            data = source_file.read()

        # Mở file đích để ghi dữ liệu
        with open(destination_file_path, 'w', encoding='utf-8') as destination_file:
            # Ghi dữ liệu vào file đích
            destination_file.write(data)

        # print("Dữ liệu đã được sao chép thành công từ", source_file_path, "sang", destination_file_path)

    def swap_file_data_bakcup(self):
        # Đường dẫn tới file nguồn và file đích
        destination_file_path = 'data/data_backup.txt'
        source_file_path = 'data/data_backup_v1.txt'

        # Mở file nguồn để đọc dữ liệu
        with open(source_file_path, 'r', encoding='utf-8') as source_file:
            # Đọc toàn bộ nội dung từ file nguồn
            data = source_file.read()

        # Mở file đích để ghi dữ liệu
        with open(destination_file_path, 'w', encoding='utf-8') as destination_file:
            # Ghi dữ liệu vào file đích
            destination_file.write(data)
    
    def Check_convert_str_to_int(self,number_check):
        try:
            int(number_check)
            return True
        except ValueError:
            return False
            
    def conveyor_running_count(self,frame_gray):
        folder_path_before='data_before_rorate'### luu giu lieu truoc khi anh duoc xoay
        folder_path_after='data_after_rorate'### luu giu lieu truoc khi anh duoc xoay
        self.folder_path_save= 'data_save'  ### luu giu lieu sau khi anh duoc xoay
        self.banana+=1
        img_draw=frame_gray.copy()
        # print(img_draw.shape)

        self.mode_rotate=False
        ##### Draw on screen test 1
        if self.banana>1 :
            temp_sub = cv2.absdiff(img_draw, self.frame_old)
            ret2, th2 = cv2.threshold(temp_sub,30,255,cv2.THRESH_BINARY) 
            kernel = np.ones((1,1),np.uint8)
            erosion2 = cv2.erode(th2,kernel,iterations = 5)
            kernel = np.ones((5,5),np.uint8)

            dilation2 = cv2.dilate(erosion2,kernel,iterations = 5)

            # area_scan=dilation2[:,10:30]## Y,X
            area_scan=dilation2[430:470,:] 

            ####
            area_scan_display=cv2.resize(area_scan,(140,20))
            h,w=area_scan_display.shape
            step= w
            q = QImage(bytes(area_scan_display.data),w,h,step, QImage.Format_Grayscale8)
            self.ui.trigger_screen.setPixmap(QPixmap.fromImage(q))
            ############
            contours, hierarchy = cv2.findContours(area_scan, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
            for i in range(len(contours)):
                if cv2.contourArea(contours[i])>200:
                    self.area_count = cv2.contourArea(contours[i])+ self.area_count
                    if self.mode_auto_scan==True:
                        self.time_auto_scan_start=time.time()
                        self.mode_start_auto_scan=True
           
            if hierarchy is not None: # xem có sự đúng là có sự kiện xảy ra khi băng tải có sự thay đổi về chuyển động
                self.banana_ate=self.banana
                if self.area_count>2000:
                    self.count_times=self.count_times+1
                    self.ui.count_point.setText(' Count acreage:'+str(self.count_times))
            
            self.mode_out_control=False

            if self.count_times>self.break_point and self.mode_auto_scan==False: ### chương trình này xử lý phần tín hiệu khi có 2 con hàng liền kề 
                #  xuất tín hiện dừng băng tải 
                self.count_times=0
                # self.mode_out_control=True
                frame_gray=cv2.cvtColor(frame_gray,cv2.COLOR_GRAY2RGB)
                # frame_gray=cv2.resize(frame_gray,(220,220))
                h,w,c=frame_gray.shape
                step= c*w
                q = QImage(frame_gray.data,w,h, step, QImage.Format_RGB888)
                # self.ui.screen2.setPixmap(QPixmap.fromImage(q)) này sau này muốn viết thêm ở đây thì nên chút ý về phần muốn xuất tín hiệu ra ngoài

        

            if (self.banana-self.banana_ate>20): ## nếu quá 5 khung hình mà không nhận được rằng có sự chuyển động thì xử lý 
                # print(self.count_times)
                # if self.count_times>self.over_point and self.mode_out_control!=True:
                if self.count_times>self.over_point: # khi vượt qua điểm giới hạn thì kích hoạt việc xoay hình 
                    if self.mode_auto_scan==False:
                        self.count_sum=self.count_sum+1
                        self.mode_rotate=True
                        self.ui.count_sum.setText(' Sum of products: {}'.format(self.count_sum))
                        image_to_rotate=frame_gray.copy()[:425,:]
                        new_file_name_before = f"{self.count_sum}.png"
                        # new_file_name_before = str(datetime.now())[0:16] +".png"
                        new_file_path_before = os.path.join(folder_path_before, new_file_name_before)

                        path_txt_img_before= open("data_before_rorate_txt/" + str(self.count_sum)+'.txt',"w",errors = "ignore")  # lưu file text
                        path_txt_img_before.close()


                        _, thresh = cv2.threshold(image_to_rotate, self.value_thresh, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU) #


                        # # Lưu hình ảnh với tên tệp mới
                        cv2.imwrite(new_file_path_before, image_to_rotate)
                        image_to_rotate_display=cv2.resize(image_to_rotate,(140,190))
                        h,w=image_to_rotate_display.shape
                        step= w
                        q = QImage(image_to_rotate_display.data,w,h, step, QImage.Format_Grayscale8)
                        self.ui.screen2.setPixmap(QPixmap.fromImage(q))

                else:
                    self.ui.count_point.setText(' Count acreage:'+str(0))

                if  self.mode_auto_scan==True and self.mode_start_auto_scan==True:
                    self.ui.but_scan.setText('Auto scan product')
                    self.mode_auto_scan=False
                    self.mode_start_auto_scan=False
                    self.over_point  =int(self.count_times*0.55)
                    self.break_point = int(self.count_times*1.8)
                    self.ui.value_over.setValue(self.over_point)
                    self.ui.value_break.setValue(self.break_point)
                    

                    self.ui.display_value_over.setText(str(self.over_point))
                    self.ui.display_value_break.setText(str(self.break_point))

                    data_backup_write=open("data/data_point_backup.txt","w")
                    data_all_write = [str(self.over_point)+"\n"+str(self.break_point)]
                    data_backup_write.writelines(data_all_write)
                    data_backup_write.close()

                self.count_times=0
                self.area_count=0


            # Hàm viết thêm nếu không có sự kiện auto
            if 10<(time.time()-self.time_auto_scan_start) and self.count_times==0 and self.area_count==0 and self.mode_auto_scan==True:
                # print(f'Thời gian được tính toán để out :{time.time()-self.time_auto_scan_start}')
                self.mode_auto_scan=False###
                self.ui.but_scan.setText('Auto scan product')

            ###########

            if self.mode_rotate==True and self.mode_adjust==False:
                self.mode_NG=False
                self.mode_rotate=False
                rotate_image= self.rotate_image(image_to_rotate) ### chính ở phần này mới đẩy tín hiệu ra 
            #     # print(1)
                # new_file_name_save = f"{self.count_sum}.png"
                new_file_name_after = str(datetime.now())[0:19] +".png"
                new_file_path_save = os.path.join(folder_path_after, new_file_name_after)

                # # Lưu hình ảnh với tên tệp mới
                cv2.imwrite(new_file_path_save, rotate_image)
                cv2.imwrite('/home/pronics-super/Desktop/hunghung back data/software Y Hook/Gui/data/image_to_handle.png', rotate_image)

                img = cv2.imread('/home/pronics-super/Desktop/hunghung back data/software Y Hook/Gui/data/image_to_handle.png')

                results=self.model.predict(img)
                number=len(results[0].obb.cls)

                count_screw=0
                count_pin=0
                count_aid=0
                count_ng=0

                for i in range(number):
                    if results[0].obb[i].conf>0.75:
                        id= results[0].obb[i].cls[0]
                        # print(id)
                        if results[0].names[id.item()]=='pin':
                            count_pin+=1
                        elif results[0].names[id.item()]=='aid':
                            count_aid+=1
                        elif results[0].names[id.item()]=='screw':
                            count_screw+=1
                        elif results[0].names[id.item()]=='ng':
                            count_ng+=1
                for i in range(number):
                    if results[0].obb[i].conf>0.75:
                        id= results[0].obb[i].cls
                        
                        datas=results[0].obb[i].xyxyxyxy
                        datas=datas.cpu().numpy()

                        for data in datas:
                            points = np.array(data, dtype=np.int32).reshape((-1, 1, 2))
                            if results[0].names[id.item()]=='pin':

                                if count_pin==18:
                                # Vẽ OBB lên ảnh (màu xanh lá cây và đường viền dày 2 pixel)
                                    cv2.polylines(img, [points], isClosed=True, color=(0, 0, 255), thickness=2)
                                else:
                                    cv2.polylines(img, [points], isClosed=True, color=(255, 0, 0), thickness=2)
                            
                            elif results[0].names[id.item()]=='aid':

                                if count_aid==1:
                                # Vẽ OBB lên ảnh (màu xanh lá cây và đường viền dày 2 pixel)
                                    cv2.polylines(img, [points], isClosed=True, color=(0, 0, 255), thickness=2)
                                else:
                                    cv2.polylines(img, [points], isClosed=True, color=(255, 0, 0), thickness=2)
                                
                            elif results[0].names[id.item()]=='screw':

                                if count_screw==4:
                                # Vẽ OBB lên ảnh (màu xanh lá cây và đường viền dày 2 pixel)
                                    cv2.polylines(img, [points], isClosed=True, color=(0, 0, 255), thickness=2)
                                else:
                                    cv2.polylines(img, [points], isClosed=True, color=(255, 0, 0), thickness=2)
                            elif results[0].names[id.item()]=='ng':

                                cv2.polylines(img, [points], isClosed=True, color=(255, 0, 0), thickness=2)
                
                if count_ng==0:
                    if count_pin==18 and count_screw ==4 and count_aid==1:
                        cv2.putText(img, "OK", (25,50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 2)
                        

                        image_target=cv2.resize(img,(200,200))

                        h,w,c=image_target.shape
                        step= c*w
                        q = QImage(image_target.data,w,h, step, QImage.Format_RGB888)
                        self.ui.screen_process.setPixmap(QPixmap.fromImage(q))
                        self.mode_NG=False
                    else:
                        self.mode_NG=True
                else:
                    self.mode_NG=True

                if self.mode_NG==True:
                    self.mode_output_basler.value=2
                    self.count_ng+=1
                    cv2.putText(img, "NG", (25,50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,0,0), 2)

                    image_target=cv2.resize(img,(200,200))
                    self.ui.count_ng.setText(' Sum of NG products: '+str(self.count_ng))
                    h,w,c=image_target.shape
                    step= c*w
                    q = QImage(image_target.data,w,h, step, QImage.Format_RGB888)
                    self.ui.screen_process.setPixmap(QPixmap.fromImage(q))

                    # name_NG='HangNG_so '+ str(self.count_ng) +"_"+ str(datetime.now())[0:16] +'.jpg'
                    name_NG =str(datetime.now())[0:16] + ' HangNG so '+ str(self.count_ng)

                    name_NG_jpg= name_NG +'.jpg'
                    name_NG_txt= name_NG +'.txt'

                    path_name_NG=os.path.join(self.path_folder_today, name_NG_jpg)#lưu ảnh NG
                    cv2.imwrite(path_name_NG,image_target)

                    path_txt_NG = open("data/data_backup_everyday_txt/" + name_NG_txt,"w",errors = "ignore")  # lưu file text
                    path_txt_NG.close()
                    self.update_listwidget()


                        


                # if self.mode_NG==True:
                #     self.mode_output_basler.value=2

                #     image_clr=cv2.cvtColor(rotate_image,cv2.COLOR_GRAY2RGB)
                    
                #     self.count_ng+=1
                #     cv2.putText(image_clr, "NG", (25,50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,0,0), 2)
                #     self.ui.count_ng.setText(' Sum of NG products: '+str(self.count_ng))
                #     image_clr=cv2.resize(image_clr,(200,200))
                #     h,w,c=image_clr.shape
                #     step= c*w
                #     q = QImage(image_clr.data,w,h, step, QImage.Format_RGB888)
                #     self.ui.screen_process.setPixmap(QPixmap.fromImage(q))

                #     # name_NG='HangNG_so '+ str(self.count_ng) +"_"+ str(datetime.now())[0:16] +'.jpg'
                #     name_NG =str(datetime.now())[0:16] + ' HangNG so '+ str(self.count_ng)

                #     name_NG_jpg= name_NG +'.jpg'
                #     name_NG_txt= name_NG +'.txt'

                #     path_name_NG=os.path.join(self.path_folder_today, name_NG_jpg)#lưu ảnh NG
                #     cv2.imwrite(path_name_NG,image_clr)

                #     path_txt_NG = open("data/data_backup_everyday_txt/" + name_NG_txt,"w",errors = "ignore")  # lưu file text
                #     path_txt_NG.close()
                #     self.update_listwidget()
                # else:
                #     self.detect_number_of_component(rotate_image)
                #     image_target_return=cv2.imread('data/image_target.png',1)

                #     image_target_return=cv2.resize(image_target_return,(200,200))

                #     h,w,c=image_target_return.shape
                #     step= c*w
                #     q = QImage(image_target_return.data,w,h, step, QImage.Format_RGB888)
                #     self.ui.screen_process.setPixmap(QPixmap.fromImage(q))

                ### Time cycle
                cycle_time=time.time()-self.start
                self.ui.cycle_time.setText(' Cycle Time: {:.4f}'.format(cycle_time))
            

        self.mode_NG=False

        self.frame_old=img_draw

    def detect_number_of_component(self,img):
        # folder_path='data_handle'
        blurred = cv2.GaussianBlur(img, (11, 11), 1)
        _, thresh = cv2.threshold(blurred, self.value_thresh, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU) #
        # cv2.imshow("Thresh", img)

        k=self.value_k 
        kernel11 = np.ones((3,3), np.uint8)
        edges = cv2.erode(thresh, kernel11, iterations=k)
        edges = cv2.dilate(edges, kernel11, iterations=k)
        

        # Tìm các contour
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            # largest_area = cv2.contourArea(largest_contour)

            # Tính hình chữ nhật bao quanh contour lớn nhất
            x, y, w, h = cv2.boundingRect(largest_contour)

        # Chia ảnh thành 3 vùng dọc
            region1 = img[0:y, x-5:x+w+5]
            region2 = img[y:y+h, x-5:x+w+5]
            region3 = img[y+h+2:, x-5:x+w+5]

            # new_file_name_save = f"{self.count_sum}.png"
            # new_file_path_save = os.path.join(self.folder_path_save, new_file_name_save)

            # # # Lưu hình ảnh với tên tệp mới
            # cv2.imwrite(new_file_path_save, region1)

        ####check push pin
            region1=self.check_screw(region1)
            region2=self.check_push_pin(region2)
            region3=self.check_push_aid(region3)

            # Ghép lại các vùng ảnh theo chiều dọc
            reconstructed_img = np.vstack((region1, region2, region3))
            if self.mode_NG==True :
                self.mode_output_basler.value=2
                self.count_ng+=1
                cv2.putText(reconstructed_img, "NG", (25,50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,0,0), 2)
                self.ui.count_ng.setText(' Sum of NG products: '+str(self.count_ng))

                # name_NG='HangNG_so '+ str(self.count_ng) +"_"+ str(datetime.now())[0:16] +'.jpg'
                name_NG =str(datetime.now())[0:16] + ' HangNG so '+ str(self.count_ng)
                name_NG_jpg= name_NG +'.jpg'
                name_NG_txt= name_NG +'.txt'

                path_name_NG=os.path.join(self.path_folder_today, name_NG_jpg)#lưu ảnh NG
                cv2.imwrite(path_name_NG,reconstructed_img)

                path_txt_NG = open("data/data_backup_everyday_txt/" + name_NG_txt,"w",errors = "ignore")
                path_txt_NG.close()
                self.update_listwidget()

            else:
                self.mode_output_basler.value=1
                cv2.putText(reconstructed_img, "OK", (25,50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 2)
                self.count_ok+=1
                self.ui.count_ok.setText(' Sum of OK products: '+str(self.count_ok))

            self.mode_NG=False
            cv2.imwrite('data/image_target.png', reconstructed_img)            
        else:#########phần viết thêm xem sao nhé
            self.mode_output_basler.value=2
            self.count_ng+=1
            cv2.putText(reconstructed_img, "NG", (25,50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,0,0), 2)
            self.ui.count_ng.setText(' Sum of NG products: '+str(self.count_ng))

            # name_NG='HangNG_so '+ str(self.count_ng) +"_"+ str(datetime.now())[0:16] +'.jpg'
            name_NG =str(datetime.now())[0:16] + ' HangNG so '+ str(self.count_ng)
            name_NG_jpg= name_NG +'.jpg'
            name_NG_txt= name_NG +'.txt'

            path_name_NG=os.path.join(self.path_folder_today, name_NG_jpg)#lưu ảnh NG
            cv2.imwrite(path_name_NG,reconstructed_img)

            path_txt_NG = open("data/data_backup_everyday_txt/" + name_NG_txt,"w",errors = "ignore")
            path_txt_NG.close()
            self.update_listwidget()
            self.mode_NG=False
            cv2.imwrite('data/image_target.png', reconstructed_img)  

    def check_screw(self,image):
        count_area=0
        count_number=0  
        k=self.value_k_screw

        image = cv2.GaussianBlur(image, (21,21), 1)
        image_clr=cv2.cvtColor(image,cv2.COLOR_GRAY2RGB)
        # image_clr=image_clr[:-18,:]
        # Tạo một ảnh trống để vẽ các contour
        contour_mask = np.zeros_like(image)

        image_clr=cv2.cvtColor(image,cv2.COLOR_GRAY2RGB)
        image_hsv=cv2.cvtColor(image_clr,cv2.COLOR_RGB2HSV)

        lower_hsv=np.array([0,0,0])
        upper_hsv=np.array([179, 255, self.value_thresh_screw])

        mask= cv2.inRange(image_hsv,lower_hsv,upper_hsv)
        mask= cv2.bitwise_not(mask)

        kernel11 = np.ones((3,3), np.uint8)

        mask = cv2.dilate(mask, kernel11, iterations=k)

        # cv2.imshow("draw",edges1)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            for contour in contours:
                # count_area=count_area+cv2.contourArea(contours[i])
                if cv2.contourArea(contour)>self.value_area_thresh_screw_min and cv2.contourArea(contour)<self.value_area_thresh_screw_max:# self.value_area_thresh_screw_min   self.value_area_thresh_screw_max
                # for contour in contours:
                    # count_area=count_area+cv2.contourArea(contour)
                    count_number+=1
                    cv2.drawContours(contour_mask, [contour], -1, 255, thickness=cv2.FILLED)

            contours_mask, _ = cv2.findContours(contour_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours_mask:

                if count_number==self.value_k_approval_screw:
                    for contour in contours_mask:
                        cv2.drawContours(image_clr, [contour], -1, (0, 0, 255), 2)
                else:
                    for contour in contours_mask:
                        cv2.drawContours(image_clr, [contour], -1, (255, 0, 0), 2)
                    self.mode_NG=True
            else:
                self.mode_NG=True
        else:
            self.mode_NG=True

        return image_clr

    def check_push_pin(self,image):
        count=0
        k=self.value_k_pin
        ## ảnh màu
        image = cv2.GaussianBlur(image.copy(), (7,7), 1)
        # Tạo một ảnh trống để vẽ các contour
        contour_mask = np.zeros_like(image)

        image_clr=cv2.cvtColor(image,cv2.COLOR_GRAY2RGB)
        _, thresh = cv2.threshold(image, self.value_thresh_pin, 255, cv2.THRESH_BINARY)
        # cv2.imshow('Push Pin  thresh', thresh)


        kernel11 = np.ones((3,3), np.uint8)
        edges = cv2.erode(thresh, kernel11, iterations=k)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            for countour in contours:
                if cv2.contourArea(countour) > self.value_area_thresh_pin_min and cv2.contourArea(countour) < self.value_area_thresh_pin_max:
                    if cv2.contourArea(countour)> self.value_double_pin:
                        count+=2
                    else:
                        count+=1
                    cv2.drawContours(contour_mask, [countour], -1, 255, thickness=cv2.FILLED)

            contours_mask, _ = cv2.findContours(contour_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours_mask:

                if count==self.value_k_approval_pin:
                    for countour in contours_mask:
                        cv2.drawContours(image_clr, [countour], -1, (0,0,255), 2)
                else:
                    self.mode_NG=True
                    for countour in contours_mask:
                            cv2.drawContours(image_clr, [countour], -1, (255,0,0), 2)
            else:
                self.mode_NG=True
        else:
            self.mode_NG=True
        return image_clr

    def check_push_aid(self,image):
        count_aid=0
        bit_set=False
        k=self.value_k_aid
        contour_mask = np.zeros_like(image)

        image_clr=cv2.cvtColor(image,cv2.COLOR_GRAY2RGB)
        _, thresh = cv2.threshold(image, self.value_thresh_aid, 255, cv2.THRESH_BINARY)

        kernel11 = np.ones((3,3), np.uint8)

        edges = cv2.erode(thresh, kernel11, iterations=1)
        edges1 = cv2.dilate(edges, kernel11, iterations=k)

        contours, _ = cv2.findContours(edges1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = min(contours, key=cv2.contourArea)
            largest_area1 = int(cv2.contourArea(largest_contour))

            if largest_area1< self.value_area_thresh_aid_limit:
                for contour in contours:
                    # if (cv2.contourArea(contour) > self.value_area_thresh_aid_min and cv2.contourArea(contour)< self.value_area_thresh_aid_max) :
                    #     bit_set=True ### NG cái chắc
                    if cv2.contourArea(contour) > self.value_area_thresh_aid_min and cv2.contourArea(contour)< self.value_area_thresh_aid_noise or  cv2.contourArea(contour) > self.value_area_thresh_aid_max and cv2.contourArea(contour)< self.value_area_thresh_aid_limit:
                        cv2.drawContours(contour_mask, [contour], -1, 255, thickness=cv2.FILLED)
                    if cv2.contourArea(contour) > self.value_area_thresh_aid_min and cv2.contourArea(contour)< self.value_area_thresh_aid_noise or  cv2.contourArea(contour) > self.value_area_thresh_aid_max and cv2.contourArea(contour)< self.value_area_thresh_aid_limit:
                        count_aid+=1
                contours_mask, _ = cv2.findContours(contour_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                if contours_mask:
                    if bit_set==False and count_aid==1:
                        for contour in contours_mask:
                            cv2.drawContours(image_clr, [contour], -1, (0, 0, 255), 2) #### draw ok
                    else:
                        self.mode_NG=True
                        for contour in contours_mask:
                            cv2.drawContours(image_clr, [contour], -1, (255, 0, 0), 2) #### draw ng
                else:
                    self.mode_NG=True
            else:
                self.mode_NG=True
        else:
            self.mode_NG=True
        return image_clr

    def rotate_image(self,image): ### để xoay dựa vào sponge
        largest_area=0
        # image=cv2.resize(image,(320,250))
        blurred = cv2.GaussianBlur(image.copy(), (11, 11), 1)
        _, thresh = cv2.threshold(blurred, 140, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)# tham số ngưỡng phán định #self.value_thresh

        # k=self.value_k  
        kernel11 = np.ones((3,3), np.uint8) ### lựa chọn hệ số kernel phù hợp
        # edges = cv2.erode(thresh, kernel11, iterations=k)  ## hệ số mở rộng
        edges = cv2.dilate(thresh, kernel11, iterations=2)  ## hệ số thu nhỏ

        # Tìm các contour
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # print(len(contours))
        # print('gia tri can biet lan: {}'.format(len(contours)))
        if contours:
        # if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            largest_area = int(cv2.contourArea(largest_contour))
            # print('gia tri can biet lan: {}'.format(largest_area))
            # print(largest_area)   ##### thể hiện diện tích bao nhiêu
            if largest_area>5000 and largest_area<25000:## self.value_area_thresh
                rect = cv2.minAreaRect(largest_contour)
                box = cv2.boxPoints(rect)
                box = np.intp(box)

                center, size, angle = rect
                width, height = size

                if width < height:
                    angle = angle + 90
                
                rotated_process = imutils.rotate(image.copy(),angle)
                # return self.detect_sponge(rotated_process)
                return rotated_process
            else:
                self.mode_NG=True ## Dont have Sponge
                return image
        else:
            self.mode_NG=True ## Dont have Sponge instead of Dont have anything
            return image
    
    def detect_sponge(self,image):
        blurred = cv2.GaussianBlur(image.copy(), (11, 11), 1)
        _, thresh = cv2.threshold(blurred, self.value_thresh, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU) ## self.value_thresh

        k=self.value_k 
        kernel11 = np.ones((3,3), np.uint8)
        edges = cv2.erode(thresh, kernel11, iterations=k)
        edges = cv2.dilate(edges, kernel11, iterations=k)

        # Tìm các contour
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            # largest_area = cv2.contourArea(largest_contour)

            # Tính hình chữ nhật bao quanh contour lớn nhất
            x, y, w, h = cv2.boundingRect(largest_contour)
            # Chia ảnh thành 2 vùng dọc
            region1 = image[0:y, :]
            region2 = image[y+h:, :]

            # cv2.imshow("region2", region2)
            ## additionally check push aid
            mode_flip=self.filter_thresh_2area(region1,region2)

            if mode_flip:
                img_standard=cv2.rotate(image, cv2.ROTATE_180)
            else:
                img_standard=image

            
            return img_standard
        else:
            self.mode_NG=True ## Dont have Sponge instead of Dont have anything
            return image

    def filter_thresh_2area(self,region1, region2):
  
        largest_area1=0
        largest_area2=0

        # cv2.imshow("Result", img_standard)
        _, thresh1 = cv2.threshold(region1, self.value_thresh, 255, cv2.THRESH_BINARY)# 
        _, thresh2 = cv2.threshold(region2, self.value_thresh, 255, cv2.THRESH_BINARY)# 

        k=self.value_k
        kernel11 = np.ones((3,3), np.uint8)

        edges = cv2.erode(thresh1, kernel11, iterations=1)
        edges1 = cv2.dilate(edges, kernel11, iterations=k)

        edges = cv2.erode(thresh2, kernel11, iterations=1)
        edges2 = cv2.dilate(edges, kernel11, iterations=k)

        # cv2.imshow('Th2',thresh2)
        contours1, _ = cv2.findContours(edges1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours2, _ = cv2.findContours(edges2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # print('So luong contour lan luot la {} và {}'.format(len(contours1), len(contours2)))
        if contours1:
            largest_contour1 = max(contours1, key=cv2.contourArea)
            largest_area1 = int(cv2.contourArea(largest_contour1))

        if contours2:
            largest_contour2 = max(contours2, key=cv2.contourArea)
            largest_area2 = int(cv2.contourArea(largest_contour2))
        
        if largest_area1>self.value_area_filter and largest_area2>self.value_area_filter:
            if largest_area1>largest_area2:
                mode_flip= True
            else:
                mode_flip= False
        else:
            if largest_area1>self.value_area_filter:
                mode_flip= True
            elif largest_area2> self.value_area_filter:
                mode_flip= False
            else:
                if largest_area1 > largest_area2:
                    mode_flip= False
                else:
                    mode_flip= True
        return mode_flip
        
    def check_link_now_to_save_data(self):
        self.year_backup=[]
        self.month_backup=[]
        self.path_folder_today=0
        today=datetime.today()
        # Lay gia tri hien tai
        month_now=today.month
        year_now=today.year

        # Tao folder hien tai de su dung cho muc dich luu tru
        path_folder_year_now   = os.path.join(self.path_backup,str(year_now))
        self.path_folder_today = os.path.join(path_folder_year_now,str(month_now))
        if not os.path.exists(self.path_folder_today):
            os.makedirs(self.path_folder_today)

        ### check lai folder voi muc dich chi co the chua duoc nhieu nhat 6 thang
        for year in os.listdir(self.path_backup):
            self.year_backup.append(year)
        self.year_backup=sorted(self.year_backup)
        path_year_now=os.path.join(self.path_backup, self.year_backup[-1])
        # print(path_year_now)

        for month in os.listdir(path_year_now):
            self.month_backup.append(month)
        self.month_backup=sorted(self.month_backup)

        if int(self.month_backup[-1])>=6:
            if len(self.month_backup)>6:
                for month in self.month_backup[0:-6]:
                    path_month_clear=os.path.join(path_year_now,month)

                    if os.path.exists(path_month_clear):
                        shutil.rmtree(path_month_clear)

            for year in self.year_backup[:-1]:
                path_year_to_clear=os.path.join(self.path_backup, year)

                if os.path.exists(path_year_to_clear):
                    shutil.rmtree(path_year_to_clear)
        else:
            # số tháng còn có thể chứa lại bên kia là 
            month_cap=6-int(self.month_backup[-1])
            path_year_old=os.path.join(self.path_backup, self.year_backup[-2])
            for month in os.listdir(path_year_old):
                # month=month
                if int(month)<=(12-month_cap):
                    path_month_old_clear=os.path.join(path_year_old,month)
                    if os.path.exists(path_month_old_clear):
                        shutil.rmtree(path_month_old_clear)

    def display_right_img_on_gui(self):
        # out screen3
        right_img=cv2.imread("data/Right_picture.jpg",1)
        right_img=cv2.resize(right_img,(140,140))
        h,w,c=right_img.shape
        step= c*w
        q = QImage(right_img.data,w,h,step, QImage.Format_RGB888)
        self.ui.screen3.setPixmap(QPixmap.fromImage(q))
    
    def start(self):
        self.mode_running_gui=True
        self.ui.display_running.show()
        
    
    def pause(self):
        self.mode_running_gui=False
        self.ui.display_running.hide()
       
    def reset(self):
        if self.mode_reset==False:
            self.ui.login.show()
        else:
            # self.clear_listwidget() ### muon thi mo cai nay ra
            self.count_sum=0
            self.count_ok=0
            self.count_ng=0

            self.ui.count_sum.setText(' Sum of products: {}'.format(self.count_sum))
            self.ui.count_ok.setText(' Sum of OK products: '+str(self.count_ok))
            self.ui.count_ng.setText(' Sum of NG products: '+str(self.count_ng))

            data_backup_write=open("data/data_backup.txt","w")
            data_all_write = [str(self.count_sum)+"\n"+str(self.count_ok)+"\n"+str(self.count_ng)]
            data_backup_write.writelines(data_all_write)
            data_backup_write.close()

            paths=["data_before_rorate","data_before_rorate_txt"]
            
            for path in paths:
                for file in os.listdir(path):
                    link_file=os.path.join(path,file)
                    # print(link_file)
                    try:
                        if os.path.isfile(link_file):
                            os.remove(link_file)
                    except:
                        return None


         
    def scan(self):
        if self.mode_running_gui==True:
            self.time_auto_scan_start=time.time() ##### lệnh này viết thêm khi không có sự kiện gì hết trơn
            self.mode_auto_scan=True
            self.ui.but_scan.setText('Scanning')
        
    def cancer(self):
        self.ui.login.hide()
        self.ui.lineEdit_2.clear()

    def loggin(self):
        ID = self.ui.lineEdit.text()
        # print(ID)
        password = self.ui.lineEdit_2.text()
        if ID=="Pronics Long An" and password=='1':
            self.ui.lineEdit_2.clear()
            self.time_start_log_out=time.time()
            self.mode_reset=True
            self.ui.but_reset.setStyleSheet("""
            background-color: rgb(0, 255, 255);
            color: rgb(0, 0, 0);
            border-radius: 15px;
        """)
            self.ui.login.hide()
        else:
            self.ui.lineEdit_2.clear()
            self.time_login_wrong=time.time()
            self.mode_reset=False
        
    def log_wrong(self):
        time_out=time.time()
        if time_out-self.time_login_wrong<0.5:
            self.ui.label_wrong.show()
        else:
            self.ui.label_wrong.hide()

    def log_out(self):
        time_out=time.time()
        if self.mode_reset==True and time_out-self.time_start_log_out>10:
            self.mode_reset=False
            self.ui.but_reset.setStyleSheet("""
            background-color: rgb(0, 0, 0);
            color: rgb(255, 255, 255);
            border-radius: 15px;
        """)
    
    def show_pass(self):
        if self.mode_but_show==False:
            self.mode_but_show=True
            self.ui.lineEdit_2.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.mode_but_show=False
            self.ui.lineEdit_2.setEchoMode(QtWidgets.QLineEdit.Password)

    def save_daily_data(self):
        img_of_the_end_day = ImageGrab.grab()
        cv2.imwrite("Data_end_of_day/Tongket_ngay_" + str(datetime.now())[0:16] + ".jpg",np.float32(img_of_the_end_day))
        main_win.close()

# Setup camera Basler
def cam_Basler(mode,mode_output , gain_raw ,black_level,gramma_enable,gramma_selector, gramma, digital_shift, expose,thread,mode_adjust_camera):
    maxCamerasToUse = 10
    tlFactory = pylon.TlFactory.GetInstance()
    devices = tlFactory.EnumerateDevices()
    if len(devices) == 0:
        raise pylon.RuntimeException("No camera present.")
    cameras = pylon.InstantCameraArray(min(len(devices), maxCamerasToUse))
    l = cameras.GetSize()
    
    for i, camera in enumerate(cameras):
        if(i == 0):
            camera11 = camera
            id_camera1_setup_delay_trigger = camera
        else:
            camera22 = camera
            id_camera2_setup_delay_trigger = camera
        camera.Attach(tlFactory.CreateDevice(devices[i]))
        while True:
            try:
                camera.Open()
                break  # Exit the loop if camera is successfully opened and configured
            except pylon.RuntimeException as e:
                print(f"Error: {e}. Retrying in 5 seconds...")
                time.sleep(5)  # Wait for 5 seconds before retrying
        print("DeviceClass: ", camera.GetDeviceInfo().GetDeviceClass())
        print("DeviceFactory: ", camera.GetDeviceInfo().GetDeviceFactory())
        print("ModelName: ", camera.GetDeviceInfo().GetModelName())
        camera.MaxNumBuffer = 100
        # Select the Frame Start trigger 
        camera.TriggerSelector.SetValue('FrameStart') #  Continuous
        # Acquisition mode
        # camera.AcquisitionMode.SetValue('Continuous')
        camera.GammaEnable.SetValue(False)####
        # camera.GammaSelector.SetValue('User')
        # camera.Gamma.SetValue(0.85)
        # camera.ExposureTimeAbs.SetValue(9000)###
        # Enable triggered image acquisition for the Frame Start trigger 
        camera.TriggerMode.SetValue('Off') 
        # Set the trigger source to Line 1 
        camera.TriggerSource.SetValue('Line1')
        # Set the trigger activation mode to rising edge 
        camera.TriggerActivation.SetValue('RisingEdge')  #Falling Edge   RisingEdge  99995  309540
        camera.UserOutputSelector.SetValue('UserOutput1')
        camera.UserOutputValueAll.SetValue(False)
        camera.Width.SetValue(1280)
        camera.Height.SetValue(960)
        if(i == 0):
            camera.TriggerDelayAbs.SetValue(0)
        else:
            camera.TriggerDelayAbs.SetValue(0)
        camera.PixelFormat.SetValue('Mono8')

        output= threading.Thread(target=process_mode_output, args=(mode_output,camera))
        # output = Process(target = process_mode_output,args=(mode_output,camera), daemon=True)
        output.start()
    cameras.StartGrabbing()
    converter = pylon.ImageFormatConverter()
    # convertion openCV BGR format 
    converter.OutputPixelFormat = pylon.PixelType_BGR8packed 
    converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
    # Variables for FPS calculation
    fps = 0
    frame_count = 0
    start_time = time.time()

    while True:
        time.sleep(0.00001)
        grabResult =  cameras.RetrieveResult(0, pylon.TimeoutHandling_Return)

        try:
            start=time.time()
        # try:
            if grabResult.GrabSucceeded():
                # start=time.time()
            
                for camera in cameras:
                    camera.GainRaw.SetValue(gain_raw.value)
                    camera.BlackLevelRaw.SetValue(black_level.value)


                    if gramma_enable.value==0:
                        camera.GammaEnable.SetValue(False)
                    else:
                        camera.GammaEnable.SetValue(True)
                    
                    
                    if gramma_selector.value==0:
                        camera.GammaSelector.SetValue('User')
                        camera.Gamma.SetValue(float(gramma.value))
                    else:
                        camera.GammaSelector.SetValue('sRGB')
                

                    camera.DigitalShift.SetValue(digital_shift.value)
                    camera.ExposureTimeAbs.SetValue(expose.value)
                # key=cv2.waitKey(1) & 0xFF
                image_grabed = converter.Convert(grabResult)
                image_grabed = image_grabed.GetArray()
                # image_grabed=image_grabed[10:,:]
                # image_grabed_resize = cv2.resize(image_grabed, (320, 240))
                image_grabed_resize = cv2.resize(image_grabed,None,fx=0.5,fy=0.5)
                image_grabed_resize=image_grabed_resize[:,220:560]
                # image_grabed_resize=image_grabed_resize[:,90:260]
                
                # cv2.imwrite('/home/pronics-super/Desktop/new_project/image_save.png',image_grabed)
                # cv2.imshow('Heloo',image_grabed_resize)
                # if mode_adjust_camera.value==1:
                #     image_x = cv2.resize(image_grabed, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_LINEAR)
                #     image_x=cv2.cvtColor(image_x,cv2.COLOR_BGR2GRAY)
                #     _, thresh = cv2.threshold(image_x, thread.value, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU) #
                #     # _, thresh = cv2.threshold(image_x, thread.value, 255, cv2.THRESH_BINARY) #
                #     cv2.imshow('image',image_x)
                #     cv2.imshow('Thred',thresh)
                #     cv2.waitKey(1)

                # else:
                #     cv2.destroyAllWindows()

                if mode.value==0:
                    cv2.imwrite('data/image_to_save.png',image_grabed_resize)
                    mode.value=1
                # print(int(1/(time.time()-start)))
                # cv2.imshow('hasjdfh',image_grabed_resize)

                # Increment frame count
                frame_count += 1
                elapsed_time = time.time() - start_time
                if elapsed_time > 1.0:
                    fps = frame_count / elapsed_time
                    # print(f"FPS: {fps}")
                    # print(image_grabed_resize.shape)
                    frame_count = 0
                    start_time = time.time()
                grabResult.Release()
            grabResult.Release()
            
        except Exception as e:
            with open('error_log.txt', 'w') as log_file:
                log_file.write(f'Error in processing_for_picture loop 0: {e}')
        grabResult.Release()

def process_mode_output(mode_output,camera):
    time_start_ok=time.time()
    count_start=0
    count_limit=0
    
    while True:
        time.sleep(0.00001)

        try:
            # print(mode_output.value)

            if mode_output.value==1: #ok
                print('ok')
                time_start_ok=time.time()
                count_start=0
                count_limit=7
            #     print(time_start_ok)
            elif mode_output.value==2: #ng
                print('ng')
                count_start=0
                count_limit=3
                time_start_ok=time.time()
            mode_output.value=0

            if (time.time()-time_start_ok)<1 and count_start<count_limit:
                # print('ok')
                # print(time.time()-time_start_ok)
                if (time.time()-time_start_ok)>0.001*(1+count_start):# mac dinh do phan cung
                    # print(time.time()-time_start_ok)
                    camera.UserOutputValueAll.SetValue(False)
                    # print('len')
                    count_start+=1
                    camera.UserOutputValueAll.SetValue(True)
                else:
                    pass
            else:
                # camera.UserOutputValueAll.SetValue(True)
                pass
        except Exception as e:
            with open('error_log.txt', 'w') as log_file:
                log_file.write(f'Error in processing_for_picture loop 0: {e}')

        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())