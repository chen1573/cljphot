import sys,os
import pandas as pd
from catalog_screen import cata_scr
from match_ref_catalog import match_star
from astropy import units as u
from astropy.time import Time
import os
import numpy as np
from astropy.io import fits
import pyds9
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
from default_setting import *
from subprocess import Popen,run,PIPE
from FWHM_SKYsigma_phot import FWHM_skysigma_phot
from Preliminary_corr_mag import corr
from Second_corr_mag import sec_corr
from pyqtgraph.Qt import QtGui, QtWidgets, mkQApp
## Switch to using white background and black foreground
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

class window(QMainWindow):

    def __init__(self, parent=None):
        super(window,self).__init__(parent)

        self.initUI()

    def initUI(self):

        self.setWindowTitle('cljphot')   
        self.setObjectName("MainWindow")
        self.setWindowIcon(QIcon('%s/icon.jpeg'%(sys.path[0])))
        
        # 设置窗口大小，居中
        desktop = QApplication.desktop()
        screenRect =desktop.screenGeometry()
        self.main_window_width=int(screenRect.width()*2/3)
        self.main_window_height=int(screenRect.height()*2/3)
        self.init_window_x=int((screenRect.width() - self.main_window_width) / 2)
        self.init_window_y=int((screenRect.height() - self.main_window_height) / 2)

        self.setGeometry(self.init_window_x,self.init_window_y,self.main_window_width,self.main_window_height)
        layout = QHBoxLayout()

        self.open_filename=None # DS9打开的图像
        self.catalog_file_name=None
        self.result_file_name=None
        self.dir=os.getcwd()
        self.stop_phot=False
        self.from_continue=False
        self.ref_checkbox_dict={}
        self.plot_window2=None
        self.plot_window3=None
        self.ref_cat=pd.DataFrame(data=None,columns=None)

        self.catalog_delta_mag=0.1 
        self.apertur=1.5  # Phot aperture, R1, times of FWHM
        self.annulus=5.0  # Iner radius of sky, R2, times of FWHM
        self.dannulus=2.0 # Width of aky, Width, times of FWHM 

        # ~~~~~~~~~~~ 主窗口 ~~~~~~~~~~~~~
        main_frame = QWidget() 
        main_frame.setStyleSheet('QWidget{background-color:white;}'
            'QPushButton{font-weight: bold; background: white; border-radius: 14px;'
            'width: 64px; height: 28px; font-size: %spx; text-align: center;}'
            'QPushButton:hover{background: rgb(50, 150, 255);}'
            'QLabel{font-weight: bold; color: orange}'
            'QPushButton{border:2px solid rgb(0, 0, 0)}'
            'QLineEdit{width: 100px; font: 微软雅黑}'%(default_font_size))

        self.setCentralWidget(main_frame)  
        self.statusBar()

        # ~~~~~~~~~~~~ 菜单栏  ~~~~~~~~~~~~
        exitAct = QAction('退出', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('退出应用')
        exitAct.triggered.connect(self.close)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('文件')
        fileMenu.addAction(exitAct)


        # # ~~~~~~~~~~~~ 工具栏  ~~~~~~~~~~~~
        # toolbar = self.addToolBar('toolbar')
        # toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        # toobarAct =QAction('小工具1', self)
        # toobarAct.setStatusTip('点击使用小工具1')
        # toolbar.addAction(toobarAct)


        # ~~~~~~~~~~~~~~~~~~~~~ 分三栏: 参考星 测光 结果 ~~~~~~~~~~~~~~~~~~~~~~
        # 参考星 ~~~~~~~~~~~~~
        ref_star_frame=QFrame(self)
        ref_star_frame.setFrameShape(QFrame.StyledPanel)
        self.ref_star_box1 = QVBoxLayout()
        self._ref_star_frame()
        ref_star_frame.setLayout(self.ref_star_box1)
        
        # 测光 分上中下三框 参数 执行测光 暂停继续从头开始按钮 ~~~~~~~~~~~~~~~
        # 参数
        phot_pars_frame=QFrame(self)
        phot_pars_frame.setFrameShape(QFrame.StyledPanel)
        self.phot_box_pars =QGridLayout()
        self._phot_pars_frame()
        phot_pars_frame.setLayout(self.phot_box_pars)

        # 执行测光
        phot_exc_frame=QFrame(self)
        phot_exc_frame.setFrameShape(QFrame.StyledPanel)
        self.phot_box_exc = QVBoxLayout()
        self._phot_exc_frame()
        phot_exc_frame.setLayout(self.phot_box_exc)

        # # 暂停继续从头开始框
        # phot_stop_frame=QFrame(self)
        # phot_stop_frame.setFrameShape(QFrame.StyledPanel)
        # self.phot_box_stop = QGridLayout()
        # self._phot_stop_frame()
        # phot_stop_frame.setLayout(self.phot_box_stop)

        # 结果栏  ~~~~~~~~~~~~~~~
        reslut_frame=QFrame(self)
        reslut_frame.setFrameShape(QFrame.StyledPanel)
        self.reslut_box1 = QVBoxLayout()
        # reslut_label = QLabel('reslut_label')
        # reslut_box1.addWidget(reslut_label)

        self._reslut_frame()

        reslut_frame.setLayout(self.reslut_box1)

        # ~~~~~~~~~~~~~~~ 
        splitter_c1=QSplitter(Qt.Vertical)

        splitter_r1=QSplitter(Qt.Horizontal)

        splitter_r1c1=QSplitter(Qt.Vertical)
        splitter_r1c1.addWidget(ref_star_frame)

        splitter_r1c2=QSplitter(Qt.Horizontal)
        splitter_r1c2r1=QSplitter(Qt.Vertical)

        splitter_r1c2r1.addWidget(phot_pars_frame)
        splitter_r1c2r1.addWidget(phot_exc_frame)
        # splitter_r1c2r1.addWidget(phot_stop_frame)        
        splitter_r1c2.addWidget(splitter_r1c2r1)

        splitter_r1c3=QSplitter(Qt.Vertical)
        splitter_r1c3.addWidget(reslut_frame)

        splitter_r1.addWidget(splitter_r1c1)
        splitter_r1.addWidget(splitter_r1c2)
        splitter_r1.addWidget(splitter_r1c3)

        splitter_c1.addWidget(splitter_r1)

        # show_infoes_frame=QFrame(self)  # 将信息输出到GUI底部框，以后再写，目前暂时输出到终端
        # show_infoes_frame.setFrameShape(QFrame.StyledPanel)
        # splitter_c1.addWidget(show_infoes_frame)


        layout.addWidget(splitter_c1)
        main_frame.setLayout(layout)

    # 左栏： 参考星栏
    def _ref_star_frame(self):
        self.region_phot_fk5_filename=None
        # 按钮 打开图像
        self.Button_show_image = QPushButton('%s'%display_text['Button_show_image'])
        self.Button_show_image.setCheckable(True)
        self.Button_show_image.clicked.connect(lambda:self.click_Button_show_image(self.Button_show_image))
        self.ref_star_box1.addWidget(self.Button_show_image)

        # 按钮 载入 region 文件到DS9        
        self.Button_load_region_to_DS9 = QPushButton('%s'%display_text['Button_load_region_to'])
        self.Button_load_region_to_DS9.setCheckable(True)
        self.Button_load_region_to_DS9.clicked.connect(lambda:self.click_Button_load_region_to_DS9(self.Button_load_region_to_DS9))
        self.ref_star_box1.addWidget(self.Button_load_region_to_DS9)

        # 按钮 确定 DS9 当前的 region 为测光位置， assign the current region in DS9 as the photmetry position
        self.Button_assign_ds9_region_for_phot = QPushButton('%s'%display_text['Button_assign_ds9_region_for_phot'])
        self.Button_assign_ds9_region_for_phot.setCheckable(True)
        self.Button_assign_ds9_region_for_phot.clicked.connect(lambda:self.click_Button_assign_ds9_region_for_phot(self.Button_assign_ds9_region_for_phot))
        self.ref_star_box1.addWidget(self.Button_assign_ds9_region_for_phot)

        # 按钮 catalog类型
        self.catalog_type_box=QGridLayout()
        self.ref_star_box1.addLayout(self.catalog_type_box)

        label_apertur_name=QLabel("catalog type:")
        self.catalog_type_box.addWidget(label_apertur_name,0,0)


        self.catalog_type_cb=QComboBox()
        self.catalog_type_cb.addItem('SDSS')
        self.catalog_type_cb.addItem('USNO-B1.0')
        # self.catalog_type_cb.addItem('USNO-UCAC4')
        # self.catalog_type_cb.addItem('NOMAD')
        self.catalog_type_cb.addItem('other')

        self.catalog_type_cb.setStyleSheet("QComboBox{background:blue}")
        self.catalog_type_cb.currentIndexChanged[str].connect(self.catalogtypechange)
        self.catalog_type_box.addWidget(self.catalog_type_cb,0,1)



        # 按钮 筛选catalog条目
        self.screen_catalog_box=QGridLayout()
        self.ref_star_box1.addLayout(self.screen_catalog_box)
        self.Button_screen_catalog_item = QPushButton('筛选catalog条目')
        self.Button_screen_catalog_item.setCheckable(True)
        self.Button_screen_catalog_item.clicked.connect(lambda:self.click_Button_screen_catalog_item(self.Button_screen_catalog_item))
        self.screen_catalog_box.addWidget(self.Button_screen_catalog_item,0,0,1,3)

        screen_catalog_modify=QPushButton("...")
        screen_catalog_modify.clicked.connect(self.click_screen_catalog_modify)
        self.screen_catalog_box.addWidget(screen_catalog_modify,0,3)


        # 按钮 选择catalog文件
        self.Button_choice_catalog_file = QPushButton('选择catalog文件')
        self.Button_choice_catalog_file.setCheckable(True)
        self.Button_choice_catalog_file.clicked.connect(lambda:self.click_Button_choice_catalog_file(self.Button_choice_catalog_file))
        self.ref_star_box1.addWidget(self.Button_choice_catalog_file)

       # 按钮 匹配catalog条目与参考星位置
        self.Button_match_catalog_ref = QPushButton('匹配catalog条目与参考星位置')
        self.Button_match_catalog_ref.setCheckable(True)
        self.Button_match_catalog_ref.clicked.connect(lambda:self.click_Button_match_catalog_ref(self.Button_match_catalog_ref))
        self.ref_star_box1.addWidget(self.Button_match_catalog_ref)


    def catalogtypechange(self,catalogtype):
        print('catalog type: ',catalogtype)


    # 筛选catalog 时用的 delta mag
    def click_screen_catalog_modify(self):
        value,ok = QInputDialog.getDouble(self,"delta mag","input delta mag:", self.catalog_delta_mag,0.01, 1, 2)
        if (value !=0):
            self.catalog_delta_mag=value
            print('set delta mag = %s'%(self.catalog_delta_mag))



    # 点击 匹配catalog条目与参考星位置
    def click_Button_match_catalog_ref(self,b):
        if self.region_phot_fk5_filename==None:
            print('未确定测光位置')
            return
        if self.catalog_file_name==None:
            print('未确定catalog')
            return

        ref_cat_file_name=match_star(self.region_phot_fk5_filename,self.catalog_file_name,self.catalog_type_cb.currentText())
        if ref_cat_file_name=='no':
            print('请重新选择参考星！！！')
            return

        self.ref_cat=pd.read_csv(ref_cat_file_name, index_col='ref_text',sep='\t')
        print('保存并指定参考星星等文件为%s'%(ref_cat_file_name))

    # 测光参数框
    def _phot_pars_frame(self):
        # apertur
        label_apertur_name=QLabel("apertur:")
        self.phot_box_pars.addWidget(label_apertur_name,0,0)

        self.label_apertur_value = QLabel("%s"%(self.apertur))
        self.label_apertur_value.setFrameStyle(QFrame.Panel|QFrame.Sunken)
        self.phot_box_pars.addWidget(self.label_apertur_value,0,1)

        label_apertur_modify=QPushButton("modify")
        label_apertur_modify.clicked.connect(self.modify_apertur)
        self.phot_box_pars.addWidget(label_apertur_modify,0,2)

        label_apertur_descri=QLabel("Phot aperture, R1, times of FWHM")
        label_apertur_descri.setFont(QFont('Times', int((float(default_font_size) )/6.0) ) )
        self.phot_box_pars.addWidget(label_apertur_descri,0,3)

        # annulus
        label_annulus_name=QLabel("annulus:")
        self.phot_box_pars.addWidget(label_annulus_name,1,0)

        self.label_annulus_value = QLabel("%s"%(self.annulus))
        self.label_annulus_value.setFrameStyle(QFrame.Panel|QFrame.Sunken)
        self.phot_box_pars.addWidget(self.label_annulus_value,1,1)

        label_annulus_modify=QPushButton("modify")
        label_annulus_modify.clicked.connect(self.modify_annulus)
        self.phot_box_pars.addWidget(label_annulus_modify,1,2)

        label_annulus_descri=QLabel("Iner radius of sky, R2, times of FWHM")
        label_annulus_descri.setFont(QFont('Times', int((float(default_font_size) )/6.0) ) )
        self.phot_box_pars.addWidget(label_annulus_descri,1,3)

        # dannulus
        label_dannulus_name=QLabel("dannulus:")
        self.phot_box_pars.addWidget(label_dannulus_name,2,0)

        self.label_dannulus_value = QLabel("%s"%(self.dannulus))
        self.label_dannulus_value.setFrameStyle(QFrame.Panel|QFrame.Sunken)
        self.phot_box_pars.addWidget(self.label_dannulus_value,2,1)

        label_dannulus_modify=QPushButton("modify")
        label_dannulus_modify.clicked.connect(self.modify_dannulus)
        self.phot_box_pars.addWidget(label_dannulus_modify,2,2)

        label_dannulus_descri=QLabel("Width of aky, Width, times of FWHM")
        label_dannulus_descri.setFont(QFont('Times', int((float(default_font_size) )/6.0) ) )
        self.phot_box_pars.addWidget(label_dannulus_descri,2,3)


        # 是否计算目标源FWHM
        # self.does_mears_tar_fwhm_name=QLabel("是否计算目标源FWHM:")
        # self.phot_box_pars.addWidget(self.does_mears_tar_fwhm_name,3,0,1,2)

        # self.does_mears_tar_fwhm_yes = QRadioButton('Yes')
        # self.does_mears_tar_fwhm_yes.setChecked(True)  # 设置默认选中状态
        # self.meas_tar_fwhm=True
        # self.does_mears_tar_fwhm_yes.toggled.connect(self.click_does_mears_tar)  # 设置按钮的槽函数
        # self.phot_box_pars.addWidget(self.does_mears_tar_fwhm_yes,3,2)

        # self.does_mears_tar_fwhm_no = QRadioButton('No')
        # # self.does_mears_tar_fwhm_no.toggled.connect(self.click_does_mears_tar)   # 设置按钮的槽函数
        # self.phot_box_pars.addWidget(self.does_mears_tar_fwhm_no,3,3)

    # def click_does_mears_tar(self):
    #     if self.does_mears_tar_fwhm_yes.isChecked():  # 按钮是否被选中
    #         self.meas_tar_fwhm=True
    #     else:
    #         self.meas_tar_fwhm=False
    #     print('self.meas_tar_fwhm',self.meas_tar_fwhm)


    def modify_dannulus(self):
        value,ok = QInputDialog.getDouble(self,"dannulus","input dannulus:", self.dannulus,0, 100)
        if (value !=0):
            self.dannulus=value
            print('set dannulus=%s times of FWHM'%(self.dannulus))
            self.label_dannulus_value.setText(str(value))

    def modify_annulus(self):
        value,ok = QInputDialog.getDouble(self,"annulus","input annulus:", self.annulus,self.apertur, 100)
        if (value !=0):
            self.annulus=value
            print('set annulus=%s times of FWHM'%(self.annulus))
            self.label_annulus_value.setText(str(value))

    def modify_apertur(self):
        value,ok = QInputDialog.getDouble(self,"apertur","input apertur:", self.apertur,0.1, 10)
        if (value !=0):
            self.apertur=value
            print('set apertur=%s times of FWHM'%(self.apertur))
            self.label_apertur_value.setText(str(value))


    # 执行测光框
    def _phot_exc_frame(self):
        

        # 按钮 单幅测光
        self.phot_one = QPushButton('孔径测光单幅图像')
        self.phot_one.setCheckable(True)
        self.phot_one.clicked.connect(lambda:self.click_Button_phot_one(self.phot_one))
        self.phot_box_exc.addWidget(self.phot_one)

        # 按钮 多幅测光
        self.phot_list = QPushButton('孔径测光多幅图像')
        self.phot_list.setCheckable(True)
        self.phot_list.clicked.connect(lambda:self.click_Button_phot_list(self.phot_list))
        self.phot_box_exc.addWidget(self.phot_list)


    # 点击 打开图像按钮
    def click_Button_show_image(self,b):
        _open_filename= QFileDialog.getOpenFileName(self,'选择一个图像文件',self.dir, "Fits Flies(*.fit *.fits) ;;All Files(*);;Text Files(*.txt)")
        self.open_filename=_open_filename[0]
        if self.open_filename=='':
            print('%s'%display_text['nofilechoiced'])
            return
        print(self.open_filename)
        self.dir=os.path.dirname(self.open_filename)
        ds9=pyds9.DS9()
        ds9.set('file %s'%self.open_filename)
        os.system('xpaset -p ds9 scale mode zscale')


    def click_Button_load_region_to_DS9(self,b):
        _filename=QFileDialog.getOpenFileName(self,'选择一个文件',self.dir, "reg File(*.reg) ;;All Files(*);;Text Files(*.txt)")
        if _filename[0]=='':
            print('%s'%display_text['nofilechoiced'])
            return
        _filename=_filename[0]
        print(_filename)
        os.system('cat %s | xpaset ds9 region -format ds9'%_filename)

    def click_Button_assign_ds9_region_for_phot(self,b):
        # 读取ds9里的wcs region 做为测光位置
        ds9region=run('xpaget ds9 region -format ds9 -system wcs -sky fk5 -skyformat degrees',shell=True,stdout=PIPE,stderr=PIPE,encoding="gbk")
        self.region_phot_fk5=ds9region.stdout # 多行文本，可以 .splitlines(True) 变成 list
        print(self.region_phot_fk5)
        print('ssssssssssssssssssssssssssssssssss')
        if len(self.region_phot_fk5.splitlines())<3:
            print('!!!!!!!!!!!!!!!!!!\nno wcs region found')
            return
        print(self.region_phot_fk5)
        # 保存测光位置文件 wcs fk5
        if self.open_filename==None: 
            self.dir=os.getcwd()
        else:
            self.dir=os.path.dirname(self.open_filename)
        print(self.dir)
        self.region_phot_fk5_filename='%s/cljpht_wcs_fk5.reg'%(self.dir)
        file=open(self.region_phot_fk5_filename,'w')
        file.write(self.region_phot_fk5)
        file.close()
        print('region file save to %s'%(self.region_phot_fk5_filename))


    # 点击 筛选 catalog条目
    def click_Button_screen_catalog_item(self,b):
        catlog_file_name=QFileDialog.getOpenFileName(self,'选择tsv格式catalog文件',self.dir, "Catalog File(*.tsv *.TSV) ;;All Files(*);;Text Files(*.txt)")
        if catlog_file_name[0]==[]:  # 未选择图像
            print('%s'%display_text['nofilechoiced'])
            return  
        if self.catalog_type_cb.currentText()=='USNO-UCAC4' or \
                self.catalog_type_cb.currentText()=='NOMAD' or \
                self.catalog_type_cb.currentText()=='other':
            print('没写这种的筛选方法')
            return
        self.catalog_file_name=cata_scr(catlog_file_name[0],self.catalog_delta_mag,self.catalog_type_cb.currentText())
        print('保存并指定测光用的catalog文件为%s'%(self.catalog_file_name))
        if self.open_filename==None:
            return
        os.system('xpaset -p ds9 catalog import tsv %s'%self.catalog_file_name)
        
    # 点击 选择catalog
    def click_Button_choice_catalog_file(self,b):
        if self.open_filename==None:
            self.dir=os.getcwd()
        else:
            self.dir=os.path.dirname(self.open_filename)
        choice_filename=QFileDialog.getOpenFileName(self,'选择tsv格式catalog文件',self.dir, "catalog(*.tsv *.TSV) ;;All Files(*);;Text Files(*.txt)")
        print(choice_filename)

        if choice_filename[0]=='':
            print('%s'%display_text['nofilechoiced'])
            return
        self.catalog_file_name=choice_filename[0]
        os.system('xpaset -p ds9 catalog import tsv %s'%self.catalog_file_name)


    # 点击 单幅测光按钮   
    def click_Button_phot_one(self,b):
        # 未确定测光位置
        if self.region_phot_fk5_filename==None:
            print('未确定测光位置')
            return
        
        # 未确定catalog
        if self.catalog_file_name==None:
            print('未确定catalog')
            return
        
        if self.ref_cat.shape[0]==0:
            print('未匹配参考星')
            return

        # 选择图像
        self.fits_file=QFileDialog.getOpenFileName(self,'选择图像',self.dir, "Fits Flies(*.fit *.fits) ;;All Files(*);;Text Files(*.txt)")
        # print(self.fits_fil)
        # return
        if self.fits_file[0]=='':  # 未选择图像
            print('%s'%display_text['nofilechoiced'])
            return  
        self.fits_file=self.fits_file[0]

        # 测光
        print(self.fits_file)
        phot_mag_file,FWHM_str,check=FWHM_skysigma_phot(self.fits_file,self.region_phot_fk5_filename,self.apertur,self.annulus,self.dannulus)
        if  check=='1':
            print('错误！检测到的（参考星+目标源）个数少于输入个数')
            return
        if check=='2':
            print('源或参考星不在视场内')
            return
        # 读取测光文件计算星等
        reslut_pd_i,ref_name_list=corr(self.fits_file,phot_mag_file,self.ref_cat)
 
        print('\n**************************************')
        print( 'Tmid=',reslut_pd_i.loc[0,'Tmid(mjd)'],' mjd\n',
              'Terr= ',reslut_pd_i.loc[0,'Terr(day)'],' day\n', 
              'mag= ', reslut_pd_i.loc[0,'preliminary_mag'] ,
              '\nmag err=',reslut_pd_i.loc[0,'preliminary_mag_err'],'\n',
               reslut_pd_i.loc[0,'Band'])
        # print( 'Tmid=',type(float(Tmid_mjd)),' mjd\n','Terr= ',type(Terr_day.value),' day\n', 'mag= ', type(phot_mag_result) , '\nmag err=',type(phot_mag_err_result),'\n', type(Band))
        print('Finsh photometry %s'%self.fits_file)
        print('**************************************\n')


    # 点击 多幅测光按钮   
    def click_Button_phot_list(self,b):
        # if not self.from_continue: # 是否暂停后点继续的
            # 未确定测光位置
        if self.region_phot_fk5_filename==None:
            print('未确定测光位置')
            return

        # 未确定catalog
        if self.catalog_file_name==None:
            print('未确定catalog')
            return
        
        # 未匹配参考星
        if self.ref_cat.shape[0]==0:
            print('未匹配参考星')
            return
        
        # 选择图像
        
        self.filenamelist=QFileDialog.getOpenFileNames(self,'选择多个图像文件',self.dir, "fits Files(*.fit *.fits) ;;All Files(*);;Text Files(*.txt)",None,QFileDialog.DontUseNativeDialog)
        print(self.filenamelist)
        if self.filenamelist[0]==[]:  # 未选择图像
            print('%s'%display_text['nofilechoiced'])
            return  
        
        # self.i_file=0



        if self.open_filename==None: 
            self.dir=os.getcwd()
        else:
            self.dir=os.path.dirname(self.open_filename)
        print(self.dir)

        i=1  
        self.result_file_name='%s/cljphot_Preliminary_reslut_%d.tsv'%(self.dir,i)
        result_err_file_name ='%s/cljphot_Preliminary_reslut_err_%d.tsv'%(self.dir,i)
        while os.path.isfile(self.result_file_name):
            i=i+1
            self.result_file_name='%s/cljphot_Preliminary_reslut_%d.tsv'%(self.dir,i)
            result_err_file_name ='%s/cljphot_Preliminary_reslut_err_%d.tsv'%(self.dir,i)
        
        result_err_file=open(result_err_file_name,'a+')

        

        
        # 循环测光
        print('**************选择了以下图像**************')
        print(self.filenamelist)

        # self.from_continue=False
        self.plot_window = plotwindow()
        self.plot_window.show()

        QApplication.processEvents()
        Bandlist=[]
        ref_in_lable_dict_list={}
        ref_delta_plot={}
        infline0={}
        infline1={}
        infline_1={}
        print('**************开始测光**************')
        # time.sleep(1)
        reslut_pd=pd.DataFrame(data=None,columns=None)

        self.errNUM=0
        self.warNUM=0
        for i in range(len(self.filenamelist[0])):
            # if self.stop_phot:
            #     self.i_file=i
            #     return
            print('sssssssssssssssssssssss',self.filenamelist[0][i])
            try:
                phot_mag_file,FWHM,check=FWHM_skysigma_phot(self.filenamelist[0][i],self.region_phot_fk5_filename,self.apertur,self.annulus,self.dannulus)
                if check=='0':
                    # 读取测光文件计算星等
                    # Tmid_mjd,Terr_day, phot_mag_result,phot_mag_err_result,Band=corr(self.filenamelist[0][i],phot_mag_file,self.region_phot_fk5_filename,self.catalog_file_name)
                    reslut_pd_i,ref_name_list=corr(self.filenamelist[0][i],phot_mag_file,self.ref_cat)
                    if FWHM>10:
                        warningtext='FWHM 较大，手动检查图像是否错'
                        self.warNUM=self.warNUM+1
                    elif FWHM<2:
                        self.warNUM=self.warNUM+1
                        warningtext='FWHM 较小，手动检查图像是否错'
                    else:
                        warningtext=''
                    reslut_pd_i.loc[0,'warningtext']=warningtext

                    Tmid_mjd=reslut_pd_i.loc[0,'Tmid(mjd)']
                    Terr_day=reslut_pd_i.loc[0,'Terr(day)']
                    phot_mag_result=reslut_pd_i.loc[0,'preliminary_mag'] 
                    phot_mag_err_result=reslut_pd_i.loc[0,'preliminary_mag_err']
                    Band= reslut_pd_i.loc[0,'Band']

                    # result_err_file.writelines('\t'.join([str(Tmid_mjd),str(Terr_day),str(phot_mag_result),str(phot_mag_err_result),Band,self.filenamelist[0][i],str(FWHM),warningtext])+'\n')
                    print('\n**************************************')
                    print( 'Tmid=',Tmid_mjd,' mjd',Terr_day,' day', phot_mag_result ,'mag' , phot_mag_err_result, Band)
                    print('Finsh photometry %s'%self.filenamelist[0][i])
                    print('Total %s/%s'%(i+1,len(self.filenamelist[0])))

                    #  画光变
                    err = pg.ErrorBarItem(x=np.array([float(Tmid_mjd)]) , y=np.array([float(phot_mag_result)]),
                                        left=np.array([float(Terr_day)]),right=np.array([float(Terr_day)]), 
                                        top=np.array([float(phot_mag_err_result)]), bottom=np.array([float(phot_mag_err_result)]),
                                        pen={'color':banddict[Band], 'width': 0},
                                            symbolPen={'width':-1}, )
                    self.plot_window.p1.addItem(err)

                    if Band in Bandlist:
                        Target_label=None
                    else:
                        Target_label=Band
                        Bandlist.append(Band)
                        # 添加画 参考星  星表值减测光值 的画框
                        ref_delta_plot[Band]=self.plot_window.win.addPlot(name="%s cat-phot"%Band, title="%s cat - phot"%Band, row=len(Bandlist), col=0)
                        ref_delta_plot[Band].setXLink(self.plot_window.p1)
                        # ref_delta_plot[Band].setMouseEnabled(x=True, y=False)
                        # ref_delta_plot[Band].enableAutoRange(x=False, y=True)
                        # ref_delta_plot[Band].setAutoVisible(x=False, y=True)
                        ref_delta_plot[Band].setLabel('left', "delta mag")
                        ref_delta_plot[Band].addLegend()

                        infline0[Band] = pg.InfiniteLine(movable=False, angle=0, pen=(0, 0, 200), bounds = None, hoverPen=(0,200,0), label=None )
                        ref_delta_plot[Band].addItem(infline0[Band])

                        infline1[Band] = pg.InfiniteLine(pos=0.1, movable=False, angle=0, pen=(0, 255, 0), bounds = None, hoverPen=(0,200,0), label=None )
                        ref_delta_plot[Band].addItem(infline1[Band])

                        infline_1[Band] = pg.InfiniteLine(pos=-0.1,movable=False, angle=0, pen=(0, 255, 0), bounds = None, hoverPen=(0,200,0), label=None )
                        ref_delta_plot[Band].addItem(infline_1[Band])


                        ref_delta_plot[Band].vb.setMouseMode(ref_delta_plot[Band].vb.PanMode)
                        ref_in_lable_dict_list[Band]=[]

                    self.plot_window.p1.plot(np.array([float(Tmid_mjd)]), np.array([float(phot_mag_result)]),
                            symbol='o', pen={'color':banddict[Band], 'width': 2},symbolBrush=banddict[Band],name=Target_label)
                    # else:
                    #     self.plot_window.p1.plot(np.array([float(Tmid_mjd)]), np.array([float(phot_mag_result)]),
                    #           symbol='o', pen={'color':banddict[Band], 'width': 2},symbolBrush=banddict[Band])
                        # self.plot_window.p2.plot(np.array([float(Tmid_mjd)]), np.array([float(phot_mag_result)]),
                        #       symbol='o', pen={'color':banddict[Band], 'width': 2},symbolBrush=banddict[Band])

                    # 画 参考星 星表值减测光值
                    for i_ref in range(len(ref_name_list)):
                        if ref_name_list[i_ref] in ref_in_lable_dict_list[Band]:
                            ref_label=None
                        else:
                            ref_label= ref_name_list[i_ref]
                            ref_in_lable_dict_list[Band].append(ref_name_list[i_ref])
                        # print(reslut_pd_i.loc[ 0, 'mag_(cat-phot)_%s'%(ref_name_list[i_ref])]  )
                        # print(reslut_pd_i.loc[ 0, 'mag_err_(cat-phot)_%s'%(ref_name_list[i_ref])]  )

                        errref = pg.ErrorBarItem(x=np.array([float(Tmid_mjd)]) , 
                                                y=np.array([reslut_pd_i.loc[ 0, 'mag_(cat-phot)_%s'%(ref_name_list[i_ref])] ]),
                                                left=np.array([float(Terr_day)]),
                                                right=np.array([float(Terr_day)]), 
                                                top=np.array([reslut_pd_i.loc[ 0, 'mag_err_(cat-phot)_%s'%(ref_name_list[i_ref])]]), 
                                                bottom=np.array([reslut_pd_i.loc[ 0, 'mag_err_(cat-phot)_%s'%(ref_name_list[i_ref])]]),
                                                pen={'color':pg.intColor(i_ref,hues=len(ref_name_list),values=1, maxValue=255, minValue=100, maxHue=300, minHue=10, sat=255, alpha=255),
                                                    'width':2})
                        # self.plot_window.p2.addItem(errref)
                        # self.plot_window.p2.plot(np.array([float(Tmid_mjd)]), 
                        #                          np.array([reslut_pd_i.loc[ 0, 'mag_(cat-phot)_%s'%(ref_name_list[i_ref])] ]),
                        #                          symbol='o', 
                        #                          symbolPen={'color':pg.intColor(i_ref,hues=5,values=1, maxValue=169, minValue=80, maxHue=300, minHue=10, sat=255, alpha=255),'width':2},
                        #                          symbolBrush=pg.intColor(i_ref,hues=6,values=1, maxValue=255, minValue=0, maxHue=200, minHue=10, sat=255, alpha=255),
                        #                          name=ref_label)

                        ref_delta_plot[Band].addItem(errref)
                        ref_delta_plot[Band].plot(np.array([float(Tmid_mjd)]), 
                                                np.array([reslut_pd_i.loc[ 0, 'mag_(cat-phot)_%s'%(ref_name_list[i_ref])] ]),
                                                symbol='o', 
                                                symbolPen={'color':pg.intColor(i_ref,hues=5,values=1, maxValue=169, minValue=80, maxHue=300, minHue=10, sat=255, alpha=255),'width':2},
                                                symbolBrush=pg.intColor(i_ref,hues=6,values=1, maxValue=255, minValue=0, maxHue=200, minHue=10, sat=255, alpha=255),
                                                name=ref_label)

                    QApplication.processEvents()

                    print('**************************************\n')
                    reslut_pd=pd.concat([reslut_pd,reslut_pd_i],axis=0)
                else: 
                    if check=='1':
                        self.errNUM=self.errNUM+1
                        errtext='错误！检测到的（参考星+目标源）个数少于输入个数'
                    elif check=='2':
                        self.errNUM=self.errNUM+1
                        errtext='源或参考星不在视场内'
                    fitsio=fits.open(self.filenamelist[0][i])
                    Band=fitsio[0].header[FILTERkey]
                    Tstar=Time(fitsio[0].header[StartOfExposurekey],  format=StartOfExposureformat) 
                    Terr= float(fitsio[0].header[EXPTIMEkey])*u.s /2.0

                    Tmid_mjd=Tstar+Terr
                    result_err_file.writelines('\t'.join([str(Tmid_mjd.mjd),str( (Terr.to(u.day)).value),'','',Band,self.filenamelist[0][i],errtext])+'\n')
            except:
                    self.errNUM=self.errNUM+1
                    fitsio=fits.open(self.filenamelist[0][i])
                    Band=fitsio[0].header[FILTERkey]
                    Tstar=Time(fitsio[0].header[StartOfExposurekey],  format=StartOfExposureformat) 
                    Terr= float(fitsio[0].header[EXPTIMEkey])*u.s /2.0

                    Tmid_mjd=Tstar+Terr
                    errtext='未知错误！！未能测光'
                    result_err_file.writelines('\t'.join([str(Tmid_mjd.mjd),str( (Terr.to(u.day)).value),'','',Band,self.filenamelist[0][i],errtext])+'\n')
            else:
                pass
        reslut_pd.to_csv(self.result_file_name,index=0 ,sep="\t")
        result_err_file.close()
        print('result file svae to %s'%(self.result_file_name))
        print(self.warNUM,' file need to cheak !!!!')
        print('result err file svae to %s'%(result_err_file_name))
        print(self.errNUM,' file can not photmetry !!!!!')
        print('\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print('Finsh photometry list !')

    # def _phot_stop_frame(self):
    #     # 按钮 暂停
    #     self.Button_stop = QPushButton('暂停')
    #     self.Button_stop.setCheckable(True)
    #     self.Button_stop.clicked.connect(lambda:self.click_Button_Button_stop(self.Button_stop))
    #     self.phot_box_stop.addWidget(self.Button_stop,0,0)

    #     # 按钮 继续
    #     self.Button_continue = QPushButton('继续')
    #     self.Button_continue.setCheckable(True)
    #     self.Button_continue.clicked.connect(lambda:self.click_Button_Button_continue(self.Button_continue))
    #     self.phot_box_stop.addWidget(self.Button_continue,0,1)

    #     # 按钮 从头开始
    #     self.Button_startover = QPushButton('从头开始')
    #     self.Button_startover.setCheckable(True)
    #     self.Button_startover.clicked.connect(lambda:self.click_Button_Button_startover(self.Button_startover))
    #     self.phot_box_stop.addWidget(self.Button_startover,0,3)
    
    # # 点击 暂停按钮
    # def click_Button_Button_stop(self,b):
    #     self.stop_phot=True

    # # 点击 继续按钮
    # def click_Button_Button_continue(self,b):
    #     self.from_continue=True

    # # 点击 从头开始按钮
    # def click_Button_Button_startover(self,b):
    #     pass

    # #重写关闭Mmainwindow窗口
    # def closeEvent(self, event):
    #     replp=QMessageBox.question(self,u'',u'确认退出?',QMessageBox.Yes|QMessageBox.No)
    #     if replp==QMessageBox.Yes:
    #         event.accept()
    #     else:
    #         event.ignore()


    def _reslut_frame(self):
        # 按钮 选择批量测光结果文件
        self.Button_select_phot_reslut = QPushButton('选择批量测光结果文件')
        self.Button_select_phot_reslut.setCheckable(True)
        self.Button_select_phot_reslut.clicked.connect(lambda:self.click_Button_select_phot_reslut(self.Button_select_phot_reslut))
        self.reslut_box1.addWidget(self.Button_select_phot_reslut)
        # 按钮 读取批量测光结果文件
        self.Button_read_phot_reslut = QPushButton('读取批量测光结果文件')
        self.Button_read_phot_reslut.setCheckable(True)
        self.Button_read_phot_reslut.clicked.connect(lambda:self.click_Button_read_phot_reslut(self.Button_read_phot_reslut))
        self.reslut_box1.addWidget(self.Button_read_phot_reslut)

        # 是否使用 waring 的数据
        self.if_use_waring_data_box = QGridLayout()
        self.reslut_box1.addLayout(self.if_use_waring_data_box)

        self.if_use_waring_data_name=QLabel("是否使用waring的数据:")
        self.if_use_waring_data_box.addWidget(self.if_use_waring_data_name,3,0)

        self.if_use_waring_data_yes = QRadioButton('Yes')
        self.if_use_waring_data_yes.setChecked(True)  # 设置默认选中状态
        self.use_waring_data=True
        self.if_use_waring_data_yes.toggled.connect(self.click_if_use_waring_data)  # 设置按钮的槽函数
        self.if_use_waring_data_box.addWidget(self.if_use_waring_data_yes,3,1)

        self.if_use_waring_data_no = QRadioButton('No')
        # self.does_mears_tar_fwhm_no.toggled.connect(self.click_does_mears_tar)   # 设置按钮的槽函数
        self.if_use_waring_data_box.addWidget(self.if_use_waring_data_no,3,2)


        # 按钮 计算星等
        self.Button_call_mag = QPushButton('计算星等')
        self.Button_call_mag.setCheckable(True)
        self.Button_call_mag.clicked.connect(lambda:self.click_Button_call_mag(self.Button_call_mag))
        self.reslut_box1.addWidget(self.Button_call_mag)

        # 按钮 保存最终星等文件
        self.Button_save_final_mag = QPushButton('保存星等最终文件')
        self.Button_save_final_mag.setCheckable(True)
        self.Button_save_final_mag.clicked.connect(lambda:self.click_Button_save_final_mag(self.Button_save_final_mag))
        self.reslut_box1.addWidget(self.Button_save_final_mag)
    # 
    def click_if_use_waring_data(self,b):
        if self.if_use_waring_data_yes.isChecked():  # 按钮是否被选中
            self.use_waring_data=True
        else:
            self.use_waring_data=False
        print('use_waring_data',self.use_waring_data)


    
    # 点击按钮 选择批量测光结果文件
    def click_Button_select_phot_reslut(self,b):
            self.result_file_name=QFileDialog.getOpenFileName(self,'选择批量测光结果文件',self.dir, "TSV Files(*.TSV *.tsv) ;;All Files(*);;Text Files(*.txt)")
            if self.result_file_name[0]=='':
                print('没有选择文件')
                self.result_file_name=None
                return
            self.result_file_name=self.result_file_name[0]
    
    # 点击按钮 读取批量测光结果文件
    def click_Button_read_phot_reslut(self,b):
        print('click_Button_read_phot_reslut')
        if self.result_file_name==None:
            # self.result_file_name=['/home/clj/cljphot_data/mrk501/cljphot_reslut_13.tsv','ss']
            self.result_file_name=QFileDialog.getOpenFileName(self,'选择批量测光结果文件',self.dir, "TSV Files(*.TSV *.tsv) ;;All Files(*);;Text Files(*.txt)")
            self.result_file_name=self.result_file_name[0]
        
        #  如果是第二次执行，清空按钮
        if self.ref_checkbox_dict !={}:
            for i in range(self.ref_checkbox_layout.count()):
                self.ref_checkbox_layout.itemAt(i).widget().deleteLater()
            self.ref_checkbox_dict ={}
        else: # 
            self.ref_checkbox_group = QGroupBox("勾选参考星")
            self.ref_checkbox_group.setFlat(False)
            self.ref_checkbox_layout = QVBoxLayout()

        self.preliminary_data=pd.read_csv(self.result_file_name, sep='\t')
        ref_name_list_temp= self.preliminary_data.columns[ self.preliminary_data.columns.str.startswith('mag_(cat-phot)_')]
        self.ref_name_list=[]
        for i in range(len(ref_name_list_temp)):
            self.ref_name_list.append(ref_name_list_temp[i][15:])
        print(self.ref_name_list)


        self.ref_checkbox_all=QCheckBox('全选')
        self.ref_checkbox_all.setChecked(True)
        self.ref_use_to_phot=self.ref_name_list
        print('use all ref star to photmetry',self.ref_use_to_phot)
        self.ref_checkbox_all.stateChanged.connect(lambda: self.change_ref_checkbox_all(self.ref_checkbox_all))
        self.ref_checkbox_layout.addWidget(self.ref_checkbox_all)
        
        # 创建参考星复选框
        for ref_i in self.ref_name_list:
            self.ref_checkbox_dict[ref_i] = QCheckBox(ref_i)	# 实例化一个QCheckBox，把文字传进去
            self.ref_checkbox_dict[ref_i].setChecked(True)
            self.ref_checkbox_dict[ref_i].clicked.connect(lambda: self.click_ref_checkbox(self.ref_checkbox_dict[ref_i]))
            self.ref_checkbox_layout.addWidget(self.ref_checkbox_dict[ref_i])

        self.ref_checkbox_group.setLayout(self.ref_checkbox_layout)
        self.reslut_box1.addWidget(self.ref_checkbox_group)
        print('data: ',self.preliminary_data.shape[0])
        print('warning data: ',self.preliminary_data['warningtext'].notnull().sum())
    
    # 点击按钮 计算星等
    def click_Button_call_mag(self,b):
        if self.ref_checkbox_dict=={}:
            print('请选择并读取测光结果文件')
            return
        print('use follow ref star to photmetry',self.ref_use_to_phot)

        # 进一步计算星等 保存的文件名
        i=1
        self.advanced_result_file_name='%s/cljphot_advanced_reslut_%d.tsv'%(self.dir,i)
        while os.path.isfile(self.advanced_result_file_name):
            i=i+1
            self.advanced_result_file_name='%s/cljphot_advanced_reslut_%d.tsv'%(self.dir,i)

        # 选择不同的参考星，进一步计算星等
        self.advance_datd_pd=pd.DataFrame(data=None,columns=None)
        for i in range(self.preliminary_data.shape[0]):
            if not self.use_waring_data: # 如果不使用带waring提示的数据
                if not pd.isna(self.preliminary_data.iloc[i]['warningtext']):
                    continue

            advance_datd_i= sec_corr(self.preliminary_data.iloc[[i],:],self.ref_use_to_phot)

            self.advance_datd_pd=pd.concat([self.advance_datd_pd,advance_datd_i],axis=0)
            
        self.advance_datd_pd.sort_values(by=['Tmid(mjd)'],ascending=True,inplace=True, na_position='first')
        self.advance_datd_pd.to_csv(self.advanced_result_file_name,index=0 ,sep="\t")
        print('save result file as %s'%(self.advanced_result_file_name))

        # 画图 源光变和参考星 
        if self.plot_window2==None:
            self.plot_window2 = plotwindow()
            self.plot_window2.show()
        else:
            self.plot_window2.deleteLater()
            self.plot_window2 = plotwindow()
            self.plot_window2.show()
        # 画图 源光变
        if self.plot_window3==None:
            self.plot_window3 = plotwindow()
            self.plot_window3.show()
        else:
            self.plot_window3.deleteLater()
            self.plot_window3 = plotwindow()
            self.plot_window3.show()
        

        QApplication.processEvents()
        Bandlist=list(self.advance_datd_pd.loc[:,'Band'].unique())
        
        ref_in_lable_dict_list={}
        ref_delta_plot={}
        infline0={}
        infline1={}
        infline_1={}
        for i_band in range(len(Bandlist)):

            if True:
                Band= Bandlist[i_band]
                Target_label=Band
                # print(Band,'BBBBBBBBBBB')
                Tmid_mjd=self.advance_datd_pd.loc[self.advance_datd_pd.loc[:,'Band']==Band ,'Tmid(mjd)'].values
                Terr_day=self.advance_datd_pd.loc[self.advance_datd_pd.loc[:,'Band']==Band ,'Terr(day)'].values
                phot_mag_result=self.advance_datd_pd.loc[self.advance_datd_pd.loc[:,'Band']==Band ,'tar_advanced_mag'].values
                phot_mag_err_result=self.advance_datd_pd.loc[self.advance_datd_pd.loc[:,'Band']==Band ,'tar_advanced_mag_err'].values

                #  画光变
                err1 = pg.ErrorBarItem(x=Tmid_mjd , y=phot_mag_result,
                                      left=Terr_day,right=Terr_day, 
                                      top=phot_mag_err_result, bottom=phot_mag_err_result,
                                      pen={'color':banddict[Band], 'width': 0},
                                        symbolPen={'width':-1}, )
                self.plot_window2.p1.addItem(err1)

                self.plot_window2.p1.plot(Tmid_mjd, phot_mag_result,
                          symbol='o', pen=None,symbolBrush=banddict[Band],name=Target_label)
                
                err2 = pg.ErrorBarItem(x=Tmid_mjd , y=phot_mag_result,
                                      left=Terr_day,right=Terr_day, 
                                      top=phot_mag_err_result, bottom=phot_mag_err_result,
                                      pen={'color':banddict[Band], 'width': 0},
                                        symbolPen={'width':-1}, )
                self.plot_window3.p1.addItem(err2)
                self.plot_window3.p1.plot(Tmid_mjd, phot_mag_result,
                          symbol='o', pen=None,symbolBrush=banddict[Band],name=Target_label)
                          
                if True:
                    # 添加画 参考星  星表值减测光值 的画框
                    ref_delta_plot[Band]=self.plot_window2.win.addPlot(name="%s cat-phot"%Band, title="%s cat - phot"%Band, row=i_band+1, col=0)
                    ref_delta_plot[Band].setXLink(self.plot_window2.p1)
                    ref_delta_plot[Band].setLabel('left', "delta mag")
                    ref_delta_plot[Band].addLegend(offset=(0.1,0.9),colCount=len(self.ref_use_to_phot))

                    infline0[Band] = pg.InfiniteLine(movable=False, angle=0, pen=(0, 0, 200), bounds = None, hoverPen=(0,200,0), label=None )
                    ref_delta_plot[Band].addItem(infline0[Band])

                    infline1[Band] = pg.InfiniteLine(pos=0.1, movable=False, angle=0, pen=(0, 255, 0), bounds = None, hoverPen=(0,200,0), label=None )
                    ref_delta_plot[Band].addItem(infline1[Band])

                    infline_1[Band] = pg.InfiniteLine(pos=-0.1,movable=False, angle=0, pen=(0, 255, 0), bounds = None, hoverPen=(0,200,0), label=None )
                    ref_delta_plot[Band].addItem(infline_1[Band])

                    ref_delta_plot[Band].vb.setMouseMode(ref_delta_plot[Band].vb.PanMode)
                    ref_in_lable_dict_list[Band]=[]
                    
                    # 画 参考星 星表值减测光值
                    for i_ref in range(len(self.ref_use_to_phot)):
                        ref_cat_phot_mag_result=self.advance_datd_pd.loc[self.advance_datd_pd.loc[:,'Band']==Band ,'ref_advanced_mag_(cat-phot)_%s'%self.ref_use_to_phot[i_ref]].values
                        ref_cat_phot_mag_err_result=self.advance_datd_pd.loc[self.advance_datd_pd.loc[:,'Band']==Band ,'ref_advanced_mag_err_(cat-phot)_%s'%self.ref_use_to_phot[i_ref]].values
 
                        err = pg.ErrorBarItem(x=Tmid_mjd , y=ref_cat_phot_mag_result,
                                      left=Terr_day,right=Terr_day, 
                                      top=ref_cat_phot_mag_err_result, bottom=ref_cat_phot_mag_err_result,
                                      pen={'color':pg.intColor(i_ref,hues=len(self.ref_use_to_phot[i_ref]),values=1, maxValue=255, minValue=100, maxHue=300, minHue=10, sat=255, alpha=255),
                                                  'width':2} )
                        ref_delta_plot[Band].addItem(err)
                        ref_delta_plot[Band].plot(Tmid_mjd, ref_cat_phot_mag_result,
                                                  symbol='o', 
                                                  pen={'color':pg.intColor(i_ref,hues=5,values=1, maxValue=169, minValue=80, maxHue=300, minHue=10, sat=255, alpha=255),'width':2},
                                             symbolPen={'color':pg.intColor(i_ref,hues=5,values=1, maxValue=169, minValue=80, maxHue=300, minHue=10, sat=255, alpha=255),'width':2},
                                             symbolBrush=pg.intColor(i_ref,hues=6,values=1, maxValue=255, minValue=0, maxHue=200, minHue=10, sat=255, alpha=255),
                                             name=self.ref_use_to_phot[i_ref])

                QApplication.processEvents()

    # 点击按钮 保存最终星等文件
    def click_Button_save_final_mag(self,b):
        i=1
        self.final_result_file_name='%s/cljphot_final_reslut_%d.tsv'%(self.dir,i)
        while os.path.isfile(self.final_result_file_name):
            i=i+1
            self.final_result_file_name='%s/cljphot_final_reslut_%d.tsv'%(self.dir,i)

        self.advance_datd_pd.to_csv(self.final_result_file_name,index=0, columns=['Tmid(mjd)','Terr(day)','tar_advanced_mag','tar_advanced_mag_err','Band','file','warningtext','ref_list'] ,sep="\t")
        print('保存最终结果文件 %s'%self.final_result_file_name)

    # 点击 全选按钮        
    def change_ref_checkbox_all(self,b):
        if b.checkState() == Qt.Checked:
            for ref_i in self.ref_name_list:
                self.ref_checkbox_dict[ref_i].setChecked(True)
            self.ref_use_to_phot=self.ref_name_list
            print('use all ref star to photmetry',self.ref_use_to_phot)
        if b.checkState() == Qt.Unchecked:
            for ref_i in self.ref_name_list:
                self.ref_checkbox_dict[ref_i].setChecked(False)
            self.ref_use_to_phot=[]
            print('Select at least two ref star')

    # 点击 参考星复选框
    def click_ref_checkbox(self,b):
        booltemplist=[]
        for ref_i in self.ref_name_list:
            booltemplist.append(self.ref_checkbox_dict[ref_i].isChecked())
        if booltemplist== [True]*len(self.ref_checkbox_dict):
            self.ref_checkbox_all.setCheckState(Qt.Checked)
        elif booltemplist == [False]*len(self.ref_checkbox_dict):
            self.ref_checkbox_all.setCheckState(Qt.Unchecked)
        else:
            self.ref_checkbox_all.setCheckState(Qt.PartiallyChecked)
        self.ref_use_to_phot=[]
        for i_bool in range(len(booltemplist)):
            if booltemplist[i_bool]:
                self.ref_use_to_phot.append(self.ref_name_list[i_bool])
        if len(self.ref_use_to_phot)<2:
            print('Select at least two ref star',self.ref_use_to_phot)
        else:
            print('use follow ref star to photmetry',self.ref_use_to_phot)
            


class plotwindow(QWidget):
    def __init__(self):
        super().__init__()
        # self.setWindowTitle("我是子窗口啊")
        self.initUI()
    def initUI(self):
        hbox = QHBoxLayout()  # 外层大盒子
        self.win = pg.GraphicsLayoutWidget(show=True, title="LC")
        self.win.resize(800,600)

        self.p1 = self.win.addPlot(name="plot1", title="LC", row=0, col=0)
        self.p1.setLabel('left','Mag')
        self.p1.getViewBox().invertY(True)
        self.p1.addLegend()
        # self.p1.setMouseEnabled(x=True, y=False)
        # self.p1.enableAutoRange(x=False, y=True)
        # self.p1.setAutoVisible(x=False, y=True)
        self.p1.vb.setMouseMode(self.p1.vb.PanMode)
        hbox.addWidget(self.win)
        self.setLayout(hbox)  # 窗口装入外层大盒子hbox


def main():
   app = QApplication(sys.argv)
   ex = window()
   ex.show()
   sys.exit(app.exec_())

if __name__ == '__main__':
   main()


