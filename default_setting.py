default_font_size='30'  # 界面字体大小
language='Chinese'  # 本来想弄个双语的，不弄了

banddict={'B':'b' ,'V':'g','R':'r' ,'I':'orange'} # 测光波段画图对应颜色

# 图像头文件关键词 
# LCO
FILTERkey='FILTER'
StartOfExposurekey='MJD-OBS'
StartOfExposureformat='mjd'
EXPTIMEkey='EXPTIME'

# # xinglong 
# FILTERkey='FILTER'
# StartOfExposurekey='JD'
# StartOfExposureformat='jd'
# EXPTIMEkey='EXPTIME'

#######################################
if language=='Chinese':
    display_text={'Button_show_image':'DS9打开图像',
                  'nofilechoiced':'没有选择文件',
                  'Button_read_region_from_file':'从region读取测光位置',
                  'Button_load_region_to':'载入 region 文件到 DS9',
                  'Button_assign_ds9_region_for_phot':'确定DS9当前的region为测光位置',
                  'star_psfmeasure':'开始计算半高全宽',
                  'start_imexa_sky':'开始计算天光sigma'
                  }
else:
    display_text={'ss':'sss'}