import sys
import cv2
import os
import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QEvent , QDateTime, QTimer , QMutex
from PyQt5.QtGui import QImage, QPixmap, QTransform, QPainter, QPainterPath, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel
#pyuic5 -x gui_main.ui -o gui_main.py

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
time_start_ok=0

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.timer = QTimer(self)
        self.timer_log_out = QTimer(self)
        self.login_wrong=QTimer(self)

        self.check_read_data_back()

        data_backup_read= open("data/data_backup.txt","r")
        data_backup=data_backup_read.readlines()
        data_backup_read.close()

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
        self.over_point=128
        self.break_point=300
        self.mode_out_control=False
        self.mode_auto_scan= False
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

        self.light= Value("i",self.ui.adjust_light.value())
        self.ui.value_light.setText(str(self.light.value))
        self.expose= Value("d",self.ui.adjust_expose.value())
        self.ui.value_expose.setText(str(self.expose.value))

        self.ui.display_running.hide()
        self.ui.adjust_expose.setEnabled(False)
        self.ui.adjust_light.setEnabled(False)

        self.ui.adjust_light.valueChanged.connect(self.change_light)
        self.ui.adjust_expose.valueChanged.connect(self.change_expose)
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
        self.ui.but_test_ok.clicked.connect(self.output_ok)
        # nut test ng
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


        self.stage=Value("i",0)
        self.mode_output_basler=Value("i",0)
        self.camera_process = Process(target = cam_Basler,args=(self.stage,self.expose,self.light,self.mode_output_basler), daemon=True)
        # self.camera_process = Process(target = cam_Basler, daemon=True)
        self.camera_process.start()

        self.timer.timeout.connect(self.display_on_gui)
        self.timer.start(1)

        self.timer_log_out.timeout.connect(self.log_out)
        self.timer_log_out.start(1)

        self.login_wrong.timeout.connect(self.log_wrong)
        self.login_wrong.start(1)

    def history_NG(self):
        self.ui.history_NG.show()

    def exit_history_NG(self):
        self.ui.history_NG.hide()
    
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
        self.mode_output_basler.value=1
    
    def output_ng(self):
        self.mode_output_basler.value=2


    def display_on_gui(self):
        self.check_link_now_to_save_data()
        self.restore_data()
        if self.stage.value==1 and self.mode_running_gui==True:
            self.start=time.time()
            img=cv2.imread("data/image_to_save.png",0)
            if img is not None:
                # self.start=time.time()

                cv2.line(img, (10, 0), (10,324), (255), 2)

                ### out screen1
                h,w=img.shape
                step= w
                q = QImage(img.data,w,h,step, QImage.Format_Grayscale8)
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
    
    def restore_data(self):
        # Đường dẫn tới file nguồn và file đích
        source_file_path = 'data/data_backup.txt'
        destination_file_path = 'data/data_backup_v1.txt'

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
        folder_path_before='data_before_rorate'
        folder_path_save= 'data_save'
        self.banana+=1
        img_draw=frame_gray.copy()
        self.mode_rotate=False
        ##### Draw on screen test 1
        if self.banana>1 :
            temp_sub = cv2.absdiff(img_draw, self.frame_old)
            ret2, th2 = cv2.threshold(temp_sub,20,255,cv2.THRESH_BINARY) 
            kernel = np.ones((1,1),np.uint8)
            erosion2 = cv2.erode(th2,kernel,iterations = 5)
            kernel = np.ones((5,5),np.uint8)

            dilation2 = cv2.dilate(erosion2,kernel,iterations = 5)

            # h,w=dilation2.shape
            # step= w
            # q = QImage(dilation2.data,w,h,step, QImage.Format_Grayscale8)
            # self.ui.trigger_screen.setPixmap(QPixmap.fromImage(q))

            area_scan=dilation2[:,10:30]
            ####
            h,w=area_scan.shape
            step= w
            q = QImage(bytes(area_scan.data),w,h,step, QImage.Format_Grayscale8)
            self.ui.trigger_screen.setPixmap(QPixmap.fromImage(q))
            ############
            contours, hierarchy = cv2.findContours(area_scan, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
            for i in range(len(contours)):
                if cv2.contourArea(contours[i])>60:
                    self.area_count = cv2.contourArea(contours[i])+ self.area_count
                # self.ui.count_sum.setText(' Sum of products: {}'.format(cv2.contourArea(contours[i])))
            
            if hierarchy is not None:
                self.banana_ate=self.banana
                if self.area_count>2000:
                    self.count_times=self.count_times+1
                    self.ui.count_point.setText(' Count acreage:'+str(self.count_times))
            
            self.mode_out_control=False

            if self.count_times>self.break_point and self.mode_auto_scan==False:
                #  xuất tín hiện dừng băng tải 
                self.count_times=0
                # self.mode_out_control=True
                frame_gray=cv2.cvtColor(frame_gray,cv2.COLOR_GRAY2RGB)
                frame_gray=cv2.resize(frame_gray,(220,220))
                h,w,c=frame_gray.shape
                step= c*w
                q = QImage(frame_gray.data,w,h, step, QImage.Format_RGB888)
                self.ui.screen2.setPixmap(QPixmap.fromImage(q))

        

            if (self.banana-self.banana_ate>5):
                # print(self.count_times)
                # if self.count_times>self.over_point and self.mode_out_control!=True:
                if self.count_times>self.over_point:
                    if self.mode_auto_scan==False:
                        self.count_sum=self.count_sum+1
                        self.mode_rotate=True
                        self.ui.count_sum.setText(' Sum of products: {}'.format(self.count_sum))
                        image_to_rotate=frame_gray.copy()[:-15,25:320]
                        # cv2.imshow("hahahaha", image_to_rotate)
                        # cv2.waitKey(1)
                        
                        # self.rotate_image(image_to_rotate)
                        # cv2.imwrite(r'/home/ponics-tiny/Desktop/software Y Hook/Gui/data/image_to_handle4.png',frame_gray.copy()[:,20:300])
                        new_file_name_before = f"{self.count_sum}.png"
                        new_file_path_before = os.path.join(folder_path_before, new_file_name_before)

                        # # Lưu hình ảnh với tên tệp mới
                        cv2.imwrite(new_file_path_before, image_to_rotate)
                    else: ### mode chạy auto scaning self.mode_auto_scan=True

                        self.ui.but_scan.setText('Auto scan product')
                        self.mode_auto_scan=False
                        self.over_point  =int(self.count_times*0.55)
                        self.break_point = int(self.count_times*1.1)
                        self.ui.value_over.setValue(self.over_point)
                        self.ui.value_break.setValue(self.break_point)

                        self.ui.display_value_over.setText(str(self.over_point))
                        self.ui.display_value_break.setText(str(self.break_point))
                else:
                    self.ui.count_point.setText(' Count acreage:'+str(0))
                self.count_times=0
                self.area_count=0


            # Hàm viết thêm nếu không có sự kiện auto
            if 5<(time.time()-self.time_auto_scan_start) and self.count_times==0 and self.area_count==0 and self.mode_auto_scan==True:
                print(f'Thời gian được tính toán để out :{time.time()-self.time_auto_scan_start}')
                self.mode_auto_scan=False###
                self.ui.but_scan.setText('Auto scan product')

            ###########

            if self.mode_rotate==True:
                self.mode_rotate=False
                # print(image_to_rotate.shape)
                rotate_image= self.rotate_image(image_to_rotate)

                new_file_name_save = f"{self.count_sum}.png"
                new_file_path_save = os.path.join(folder_path_save, new_file_name_save)

                # # Lưu hình ảnh với tên tệp mới
                cv2.imwrite(new_file_path_save, rotate_image)

                if self.mode_NG==True:

                    image_clr=cv2.cvtColor(rotate_image,cv2.COLOR_GRAY2RGB)
                    
                    self.count_ng+=1
                    cv2.putText(image_clr, "NG", (25,50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,0,0), 2)
                    self.ui.count_ng.setText(' Sum of NG products: '+str(self.count_ng))
                    image_clr=cv2.resize(image_clr,(220,220))
                    h,w,c=image_clr.shape
                    step= c*w
                    q = QImage(image_clr.data,w,h, step, QImage.Format_RGB888)
                    self.ui.screen2.setPixmap(QPixmap.fromImage(q))

                    # name_NG='HangNG_so '+ str(self.count_ng) +"_"+ str(datetime.now())[0:16] +'.jpg'
                    name_NG =str(datetime.now())[0:16] + ' HangNG so '+ str(self.count_ng)

                    name_NG_jpg= name_NG +'.jpg'
                    name_NG_txt= name_NG +'.txt'

                    path_name_NG=os.path.join(self.path_folder_today, name_NG)
                    cv2.imwrite(path_name_NG,image_clr)
                else:
                    self.detect_number_of_component(rotate_image)
                    image_target_return=cv2.imread('data/image_target.png',1)
                    # print(image_target.shape)
                    # image_target = cv2.cvtColor(image_target, cv2.COLOR_BGR2RGB)

                    image_target_return=cv2.resize(image_target_return,(220,220))

                    h,w,c=image_target_return.shape
                    step= c*w
                    q = QImage(image_target_return.data,w,h, step, QImage.Format_RGB888)
                    self.ui.screen2.setPixmap(QPixmap.fromImage(q))

                ### Time cycle
                cycle_time=time.time()-self.start
                self.ui.cycle_time.setText(' Cycle Time: {:.4f}'.format(cycle_time))

        self.mode_NG=False

        self.frame_old=img_draw

    def detect_number_of_component(self,img):
        folder_path='data_handle'
        blurred = cv2.GaussianBlur(img, (11, 11), 1)
        _, thresh = cv2.threshold(blurred, 130, 255, cv2.THRESH_BINARY)
        # cv2.imshow("Thresh", img)

        k=3
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
            region1 = img[0:y-1, x:x+w]
            region2 = img[y+1:y+h-1, x:x+w]
            region3 = img[y+h+1:, x:x+w]

        ####check push pin
            region1=self.check_screw(region1)
            region2=self.check_push_pin(region2)
            region3=self.check_push_aid(region3)

            # Ghép lại các vùng ảnh theo chiều dọc
            reconstructed_img = np.vstack((region1, region2, region3))
            if self.mode_NG==True :
                self.count_ng+=1
                cv2.putText(reconstructed_img, "NG", (25,50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,0,0), 2)
                self.ui.count_ng.setText(' Sum of NG products: '+str(self.count_ng))

                # name_NG='HangNG_so '+ str(self.count_ng) +"_"+ str(datetime.now())[0:16] +'.jpg'
                name_NG =str(datetime.now())[0:16] + ' HangNG so '+ str(self.count_ng)+'.jpg'
                path_name_NG=os.path.join(self.path_folder_today, name_NG)
                cv2.imwrite(path_name_NG,reconstructed_img)
            else:
                cv2.putText(reconstructed_img, "OK", (25,50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 2)
                self.count_ok+=1
                self.ui.count_ok.setText(' Sum of OK products: '+str(self.count_ok))

            self.mode_NG=False
            cv2.imwrite('data/image_target.png', reconstructed_img)            
            
    def check_screw(self,image):
        count_area=0
        image_clr=cv2.cvtColor(image,cv2.COLOR_GRAY2RGB)
        _, thresh = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY)

        kernel11 = np.ones((7,7), np.uint8)

        # edges = cv2.erode(thresh, kernel11, iterations=10)
        edges1 = cv2.dilate(thresh, kernel11, iterations=1)
        kernel11 = np.ones((3,3), np.uint8)

        edges1 = cv2.dilate(edges1, kernel11, iterations=1)
        # cv2.imshow("draw",edges1)
        contours, _ = cv2.findContours(edges1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            for i in range(len(contours)):
                count_area=count_area+cv2.contourArea(contours[i])
            if count_area>1748:
                for contour in contours:
                    cv2.drawContours(image_clr, [contour], -1, (0, 0, 255), 2)
            else:
                self.mode_NG=True
                for contour in contours:
                    cv2.drawContours(image_clr, [contour], -1, (255, 0, 0), 2)
        else:
            self.mode_NG=True

        count_area=0
        return image_clr

    def check_push_pin(self,image):
        count_area_push_pin=0
        ## ảnh màu
        image_clr=cv2.cvtColor(image,cv2.COLOR_GRAY2RGB)
        _, thresh = cv2.threshold(image, 200, 255, cv2.THRESH_BINARY)
        # cv2.imshow('Push Pin  thresh', thresh)

        kernel11 = np.ones((5,5), np.uint8)
        # edges = cv2.dilate(thresh, kernel11, iterations=2)


        edges = cv2.erode(thresh, kernel11, iterations=1)
        kernel11 = np.ones((3,3), np.uint8)
        edges = cv2.erode(edges, kernel11, iterations=1)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            for i in range(len(contours)):
                if cv2.contourArea(contours[i])>1.5 and cv2.contourArea(contours[i])<60 :
                    count_area_push_pin+=1
            if count_area_push_pin>=18:
                for countour in contours:
                        if cv2.contourArea(contours[i])>3 and cv2.contourArea(contours[i])<60 :
                            cv2.drawContours(image_clr, [countour], -1, (0,0,255), 2)
            else:
                self.mode_NG=True
                for countour in contours:
                        cv2.drawContours(image_clr, [countour], -1, (255,0,0), 2)
        else:
            self.mode_NG=True
        count_area_push_pin=0
        return image_clr

    def check_push_aid(self,image):
        largest_area=0
        image_clr=cv2.cvtColor(image,cv2.COLOR_GRAY2RGB)
        _, thresh = cv2.threshold(image, 95, 255, cv2.THRESH_BINARY)

        kernel11 = np.ones((3,3), np.uint8)

        edges = cv2.erode(thresh, kernel11, iterations=1)
        edges1 = cv2.dilate(edges, kernel11, iterations=3)

        contours, _ = cv2.findContours(edges1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            largest_area = int(cv2.contourArea(largest_contour))
            if largest_area>1700:
            # Tính hình chữ nhật bao nhỏ nhất quanh contour lớn nhất
                rect = cv2.minAreaRect(largest_contour)
                box = cv2.boxPoints(rect)
                box = np.intp(box)

                cv2.drawContours(image_clr, [box], -1, (0, 0, 255), 2)
            else:
                self.mode_NG=True
        else:
            self.mode_NG=True
        
        return image_clr

    def rotate_image(self,image):
        largest_area=0
        blurred = cv2.GaussianBlur(image.copy(), (11, 11), 1)
        _, thresh = cv2.threshold(blurred, 100, 255, cv2.THRESH_BINARY)

        k=3
        kernel11 = np.ones((3,3), np.uint8)
        edges = cv2.erode(thresh, kernel11, iterations=k)
        edges = cv2.dilate(edges, kernel11, iterations=k)

        # Tìm các contour
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
        # if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            largest_area = int(cv2.contourArea(largest_contour))
            print(largest_area)
            if largest_area>7500 and largest_area<25000:
                rect = cv2.minAreaRect(largest_contour)
                box = cv2.boxPoints(rect)
                box = np.intp(box)

                center, size, angle = rect
                width, height = size

                if width < height:
                    angle = angle + 90
                
                rotated_process = imutils.rotate(image.copy(),angle)
                return self.detect_sponge(rotated_process)
            else:
                self.mode_NG=True ## Dont have Sponge
                return image
        else:
            self.mode_NG=True ## Dont have Sponge instead of Dont have anything
            return image
    
    def detect_sponge(self,image):
        blurred = cv2.GaussianBlur(image, (11, 11), 1)
        _, thresh = cv2.threshold(blurred, 130, 255, cv2.THRESH_BINARY)

        k=3
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
        region1 = image[0:y-3, x:]
        region2 = image[y+h+3:, x:]

        # cv2.imshow("region2", region2)
        ## additionally check push aid
        mode_flip=self.filter_thresh_2area(region1,region2)

        if mode_flip:
            img_standard=cv2.rotate(image, cv2.ROTATE_180)
        else:
            img_standard=image
        return img_standard

    def filter_thresh_2area(self,region1, region2):
        sum_area1=0
        sum_area2=0
        largest_area1=0
        largest_area2=0
        # cv2.imshow("Result", img_standard)
        _, thresh1 = cv2.threshold(region1, 105, 255, cv2.THRESH_BINARY)
        _, thresh2 = cv2.threshold(region2, 105, 255, cv2.THRESH_BINARY)

        k=4
        kernel11 = np.ones((3,3), np.uint8)

        edges = cv2.erode(thresh1, kernel11, iterations=1)
        edges1 = cv2.dilate(edges, kernel11, iterations=k)

        edges = cv2.erode(thresh2, kernel11, iterations=1)
        edges2 = cv2.dilate(edges, kernel11, iterations=k)
        # cv2.imshow('Th1',thresh1)
        # cv2.imshow('Th2',thresh2)

        # cv2.imshow('Th2',thresh2)
        contours1, _ = cv2.findContours(edges1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours2, _ = cv2.findContours(edges2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # print('So luong contour lan luot la {} và {}'.format(len(contours1), len(contours2)))
        if contours1:
            largest_contour = max(contours1, key=cv2.contourArea)
            largest_area1 = int(cv2.contourArea(largest_contour))
            for i in range(len(contours1)):
                sum_area1= cv2.contourArea(contours1[i])+ sum_area1
            # print(largest_area1)

        if contours2:
            largest_contour = max(contours2, key=cv2.contourArea)
            largest_area2 = int(cv2.contourArea(largest_contour))
            for i in range(len(contours2)):
                sum_area2= cv2.contourArea(contours2[i])+ sum_area2
        
        if largest_area1>700 and largest_area2>700:
            if largest_area1>largest_area2:
                mode_flip= True
            else:
                mode_flip= False
        else:
            if largest_area1>700:
                mode_flip= True
            elif largest_area2> 700:
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
            # print('da tao xong folder moi nhat de su dung ')
        # else:
        #     print('co roi chang oi ')

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

    def change_light(self):
        self.light.value= self.ui.adjust_light.value()
        self.ui.value_light.setText(str(self.light.value))

    def change_expose(self):
        self.expose.value= self.ui.adjust_expose.value()
        self.ui.value_expose.setText(str(self.expose.value))
    
    def start(self):
        self.mode_running_gui=True
        self.ui.display_running.show()
        self.ui.adjust_expose.setEnabled(True)
        self.ui.adjust_light.setEnabled(True)
    
    def pause(self):
        self.mode_running_gui=False
        self.ui.display_running.hide()
        self.ui.adjust_expose.setEnabled(False)
        self.ui.adjust_light.setEnabled(False)
        
    def reset(self):
        if self.mode_reset==False:
            self.ui.login.show()
        else:
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
        print(ID)
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
def cam_Basler(mode,expose,light,mode_output):
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
        camera.AcquisitionMode.SetValue('Continuous')
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
        time.sleep(0.001)
        grabResult =  cameras.RetrieveResult(0, pylon.TimeoutHandling_Return)

        try:
        # start=time.time()
        # try:
            if grabResult.GrabSucceeded():
                # start=time.time()
                # print(mode.value)
            
                # for camera in cameras:
                #     camera.ExposureTimeAbs.SetValue(expose.value)
                #     camera.DigitalShift.SetValue(light.value)
                # key=cv2.waitKey(1) & 0xFF
                image_grabed = converter.Convert(grabResult)
                image_grabed = image_grabed.GetArray()
                # image_grabed=image_grabed[10:,:]
                image_grabed_resize = cv2.resize(image_grabed, (320, 240))
                
                # cv2.imwrite('/home/pronics-super/Desktop/new_project/image_save.png',image_grabed)
                # cv2.imshow('Heloo',image_grabed_resize)
                if mode.value==0:
                    cv2.imwrite('data/image_to_save.png',image_grabed_resize)
                    mode.value=1
                # print(int(1/(time.time()-start)))

                # Increment frame count
                frame_count += 1
                elapsed_time = time.time() - start_time
                if elapsed_time > 1.0:
                    fps = frame_count / elapsed_time
                    print(f"FPS: {fps}")
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
    time_start_ng=time.time()
    count_start=0
    count_limit=0
    
    while True:
        # print(mode_output.value)

        if mode_output.value==1:
            time_start_ok=time.time()
            count_start=0
            count_limit=5
        #     print(time_start_ok)
        elif mode_output.value==2:
            count_start=0
            count_limit=1
            time_start_ok=time.time()
        mode_output.value=0

        if (time.time()-time_start_ok)<1 and count_start<count_limit:
            # print('ok')
            # print(time.time()-time_start_ok)
            if (time.time()-time_start_ok)>0.00000000000001*(1+count_start):# mac dinh do phan cung
                print(time.time()-time_start_ok)
                camera.UserOutputValueAll.SetValue(False)
                # print('len')
                count_start+=1
        camera.UserOutputValueAll.SetValue(True)
            

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())