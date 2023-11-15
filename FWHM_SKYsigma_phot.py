import pyds9,re,os
from subprocess import Popen,run,PIPE
# import easygui
from pyraf import iraf
from pyraf.iraf import noao, images
from default_setting import display_text,imtsize
from pathlib import Path
images.tv()
iraf.set(stdgraph="stdplot")
iraf.set(stdimage	= "imt%s"%(imtsize))


def FWHM_skysigma_phot(fits_file,region_phot_fk5_filename,apertur,annulus,dannulus):
    print(fits_file)
    # 打开图像
    ds9=pyds9.DS9()
    ds9.set('file %s'%fits_file)

    # 
    run('xpaset -p ds9 region delete', shell=True)
    run('xpaset -p ds9 region load %s'%region_phot_fk5_filename, shell=True)
    run('xpaset -p ds9 scale mode zscale',shell=True)

    size_ds9=run(['xpaget', 'ds9', 'fits', 'size'],stdout=PIPE,stderr=PIPE,encoding="gbk")
    fits_width=float(size_ds9.stdout.split()[0])
    fits_hight=float(size_ds9.stdout.split()[1])
    proc_ds9=run(['xpaget', 'ds9', 'region', '-format', 'ds9', '-system', 'physical'],stdout=PIPE,stderr=PIPE,encoding="gbk")

    # 保存 xxx-region_physical.reg
    region_file=proc_ds9.stdout
    region_physical_file=open('%s_region_physical.reg'%(fits_file),'w')
    region_physical_file.write(region_file)
    region_physical_file.close()
    reftext=region_file.splitlines(True)
    ref_physical_list=[]
    apertur_physical_list=[]
    target_physical_list=[]
    sky_physical_list=[]

    # 读取 xxx-region_physical.reg,
    re_pattern = "^(?P<regionshape>[\w]+)\((?P<x>[0-9]+.[0-9]+)\,(?P<y>\-?\d+(\.\d*)?)\,(?P<r>\d+(\.\d*)?.*)\).*text\=\{(?P<text>\w*)?\}"
    for i in range(len(reftext)):
        x = re.search(re_pattern,reftext[i][:-1])
        # print(i)
        if x==None: continue
        if x['text']=='p':
            # print(x['text'][0],'target')
            os.system('xpaset -p ds9 pan to %s %s physical'%(x['x'],x['y']))
            if not (0 < float(x['x']) < fits_width and 0 < float(x['y']) < fits_hight):
                check='2'
                return 'no','FWHM',check
            target_physical_list.append([x.groupdict().copy(),reftext[i][:-1]])

        if x['text'][0]=='r':
            # print(x['text'],'ref_star')
            if not (0 < float(x['x']) < fits_width and 0 < float(x['y']) < fits_hight):
                check='2'
                return 'no','FWHM',check
            ref_physical_list.append([x.groupdict().copy(),reftext[i][:-1]])
        
        if x['text'][0]=='a':
            # print(x['text'],'ref_star')
            if not (0 < float(x['x']) < fits_width and 0 < float(x['y']) < fits_hight):
                check='2'
                return 'no','FWHM',check
            apertur_physical_list.append([x.groupdict().copy(),reftext[i][:-1]])

        if x['text']=='s':
            # print(x['text'],'sky')
            sky_physical_list.append([x.groupdict().copy(),reftext[i][:-1]])

    if len(apertur_physical_list)==0:
        print('!!!! 未输入 测半高宽位置')
        ting
    if len(ref_physical_list)==0:
        print('!!!! 未输入参考星位置')
        ting
    if len(target_physical_list)==0:
        print('!!!! 未输入目标源位置')
        ting

    #  保存计算半高宽位置文件 先参考星，后目标源
    imagecurlist=open('%s.imagecurlist'%fits_file,'w')  # 计算半高宽位置文件 
    for i_ap in range(len(apertur_physical_list)):
        imagecurlist.writelines('%s %s m\n'%(apertur_physical_list[i_ap][0]['x'], apertur_physical_list[i_ap][0]['y']))
    # if measure_tar_FWHM:
    #     for i_tar in range(len(target_physical_list)):
    #         imagecurlist.writelines('%s %s m\n'%(target_physical_list[i_tar][0]['x'], target_physical_list[i_tar][0]['y']))
    imagecurlist.writelines('q')
    imagecurlist.close()

    #  保存 测光位置文件，先参考星，后目标源
    phot_icommands_file='%s_photxy'%fits_file  # 测光位置文件
    photxy=open(phot_icommands_file,'w')
    for i_ref in range(len(ref_physical_list)):
        photxy.writelines('%s %s\n'%(ref_physical_list[i_ref][0]['x'], ref_physical_list[i_ref][0]['y']))
        print(ref_physical_list[i_ref][0]['x'],ref_physical_list[i_ref][1])
        
    for i_tar in range(len(target_physical_list)):
        photxy.writelines('%s %s\n'%(target_physical_list[i_tar][0]['x'], target_physical_list[i_tar][0]['y']))
        print(target_physical_list[i_tar][0]['x'],target_physical_list[i_tar][1])
    photxy.close()
    if not os.path.exists('q'): os.system("echo 'q' > q")

    iraf.display(image=fits_file,
                 frame=1,
                 bpmask = "BPM",
                 bpdisplay = "none",
                 bpcolors = "red",
                 overlay = "",
                 erase = 'yes',
                 border_erase = 'yes',
                select_frame = 'yes',
                repeat = 'no',
                fill = 'no',
                zscale = 'yes',
                contrast = 0.25,
                zrange = 'yes',
                zmask = "",
                nsample = 1000,
                xcenter = 0.5, ycenter = 0.5,
                xsize = 1, ysize = 1,
                xmag = 1.0, ymag = 1.0,
                order = 0,
                ztrans = "linear",
                lutfile = ""
                 )
    run('xpaset -p ds9 region load %s_region_physical.reg'%(fits_file), shell=True)
    
    # psfmeasure 计算半高全宽
    # print(display_text['star_psfmeasure'])
    noao.obsutil()
    psfmeasure_out=noao.obsutil.psfmeasure(
        images=fits_file,
        coords='markall',
        wcs = "physical",
        display = 'yes', frame = 1,
        level = 0.5,
        size = "MFWHM",
        beta = 'INDEF',
        scale = 1.0,
        radius = 10, iterations = 10,
        sbuffer = 5, swidth = 5.0,
        saturation='INDEF', ignore_sat='no',
        xcenter = 'INDEF', ycenter = 'INDEF',
        logfile = "%s.psfmeasure.log"%fits_file,
        imagecur = '%s.imagecurlist'%fits_file,
        graphcur ='q',
        Stdout=True
    )

    FWHM_str=psfmeasure_out[-1].split()[-1] # Average full width at half maximum (MFWHM)
    FWHM=float(FWHM_str)

    # 如未在指定位置测出半高宽
    if (len(psfmeasure_out[5:-2]) <  len(apertur_physical_list) ) :
        print('!!!!!!!!!! 错误！未在指定位置测出半高宽')
        check='1'
        return 'no',FWHM,check
    else:
        check='0'

    # 画 半高宽
    text=psfmeasure_out[5].split()
    os.system("echo 'physical; circle %s %s %s # color=Blue' | xpaset ds9 region"%(text[1],text[2],text[4]))
    for i in range(len(psfmeasure_out[6:-2])):
        text=psfmeasure_out[6+i].split()
        # print(text)
        os.system("echo 'physical; circle %s %s %s # color=Blue' | xpaset ds9 region"%(text[0],text[1],text[3]))
    print('end psfmeasure_out\n\n************************************')
    # #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


    # 保存测天光sigma位置文件  
    # print(display_text['start_imexa_sky'])
    imagecurlist_sky=open('%s.imagecurlist_sky'%fits_file,'w')
    for i_ref in range(len(sky_physical_list)):
        imagecurlist_sky.writelines('%s %s m\n'%(sky_physical_list[i_ref][0]['x'], sky_physical_list[i_ref][0]['y']))
        # print(sky_physical_list[i_ref][0]['x'],sky_physical_list[i_ref][1])
    imagecurlist_sky.writelines('q')
    imagecurlist_sky.close()

    # 测天光sifgma
    imexamine_a_out=images.tv.imexamine(input=fits_file,
        output = "",
        ncoutput = 101, nloutput = 101,
        frame = 1,
        logfile = "%s.imexa_m.log"%(fits_file),
        keeplog = 'yes',
        defkey = "m",
        autoredraw = 'yes',
        allframes = 'yes',
        nframes = 0,
        ncstat = 10, nlstat = 10,
        graphcur = "",
        imagecur = '%s.imagecurlist_sky'%fits_file,
        wcs = "physical",
        xformat = "", yformat = "",
        graphics = "stdgraph",
        display = "display(image='$1',frame=$2)",
        use_display = 'no',
        Stdout=True
    )

    STDDEV=[]
    for i in imexamine_a_out[2:]:
        isplit=i.split()
        print(isplit)
        xy=re.split(':|,',isplit[0][1:-1])
        xy=[float(i_xy) for i_xy in xy]
        os.system("echo 'box %s %s %s %s 0  # color=cyan' | xpaset ds9 region"%((xy[0]+xy[1])/2, (xy[2]+xy[3])/2,(xy[1]-xy[0]),(xy[3]-xy[2]))) # 标记测天光sigma的位置
        STDDEV.append(float(isplit[4]))
    sky_sigma=sum(STDDEV) / len(STDDEV)

    

    #### 设置测光参数
    
    sky_inner=annulus*FWHM
    sky_width=dannulus*FWHM
    phot_apertures=apertur*FWHM
    print('FWHM= ',FWHM)
    print('sky_inner= ',sky_inner)
    print('sky_width= ',sky_width)
    print('phot_apertures= ',phot_apertures)
    noao.digiphot()
    noao.digiphot.apphot()
    noao.digiphot.apphot.datapars.scale=1.0
    noao.digiphot.apphot.datapars.fwhmpsf =FWHM  ################
    noao.digiphot.apphot.datapars.emission = 'yes'
    noao.digiphot.apphot.datapars.sigma = sky_sigma #################
    noao.digiphot.apphot.datapars.datamin = 'INDEF'
    noao.digiphot.apphot.datapars.noise = "poisson"
    noao.digiphot.apphot.datapars.ccdread = ""
    noao.digiphot.apphot.datapars.gain = ""
    noao.digiphot.apphot.datapars.readnoise = 0.0
    noao.digiphot.apphot.datapars.epadu = 1.0
    noao.digiphot.apphot.datapars.exposure = ""
    noao.digiphot.apphot.datapars.airmass = ""
    noao.digiphot.apphot.datapars.filter = ""
    noao.digiphot.apphot.datapars.obstime = ""
    noao.digiphot.apphot.datapars.itime = 1.0
    noao.digiphot.apphot.datapars.xairmass = 'INDEF'
    noao.digiphot.apphot.datapars.ifilter = "INDEF"
    noao.digiphot.apphot.datapars.otime = "INDEF"
    noao.digiphot.apphot.datapars.mode='ql'


    noao.digiphot.apphot.centerpars.calgorithm = "centroid"
    noao.digiphot.apphot.centerpars.cbox = 2.0*FWHM #########
    noao.digiphot.apphot.centerpars.cthreshold = 0.0 
    noao.digiphot.apphot.centerpars.minsnratio = 1.0
    noao.digiphot.apphot.centerpars.cmaxiter = 10
    noao.digiphot.apphot.centerpars.maxshift = 1.0
    noao.digiphot.apphot.centerpars.clean = 'no'
    noao.digiphot.apphot.centerpars.rclean = 1.0
    noao.digiphot.apphot.centerpars.rclip = 2.0 
    noao.digiphot.apphot.centerpars.kclean = 3.0
    noao.digiphot.apphot.centerpars.mkcenter = 'no'
    noao.digiphot.apphot.centerpars.mode='ql'
    
    noao.digiphot.apphot.fitskypars.salgorithm = "mode"
    noao.digiphot.apphot.fitskypars.annulus = sky_inner ######
    noao.digiphot.apphot.fitskypars.dannulus = sky_width ######
    noao.digiphot.apphot.fitskypars.skyvalue = 0.0
    noao.digiphot.apphot.fitskypars.smaxiter = 10
    noao.digiphot.apphot.fitskypars.sloclip = 0.0
    noao.digiphot.apphot.fitskypars.shiclip = 0.0
    noao.digiphot.apphot.fitskypars.snreject = 50
    noao.digiphot.apphot.fitskypars.sloreject = 3.0
    noao.digiphot.apphot.fitskypars.shireject = 3.0
    noao.digiphot.apphot.fitskypars.khist = 3.0
    noao.digiphot.apphot.fitskypars.binsize = 0.10
    noao.digiphot.apphot.fitskypars.smooth = 'no'
    noao.digiphot.apphot.fitskypars.rgrow = 0.0
    noao.digiphot.apphot.fitskypars.mksky = 'no'
    noao.digiphot.apphot.fitskypars.mode='ql'
    
    noao.digiphot.apphot.photpars.weighting = "constant"
    noao.digiphot.apphot.photpars.apertures = str(phot_apertures)
    noao.digiphot.apphot.photpars.zmag = 25.00
    noao.digiphot.apphot.photpars.mkapert = 'no'
    noao.digiphot.apphot.photpars.mode='ql'
    

    # 测光并保存mag文件，先参考星后目标源


    i=1  
    phot_mag_file='%s.cljphot.mag.%d'%(fits_file,i)
    while os.path.isfile(phot_mag_file):
        i=i+1
        phot_mag_file='%s.cljphot.mag.%d'%(fits_file,i)

    # print('mag file is ',phot_mag_file)
    noao.digiphot.apphot.phot(
        image=fits_file,
        coords=phot_icommands_file,
        output= phot_mag_file,
        skyfile = "",
        plotfile = "",
        datapars = "",
        centerpars = "",
        fitskypars = "",
        photpars = "",
        interactive = 'no',
        radplots = 'no',
        icommands = '',
        gcommands = "",
        wcsin = "physical", wcsout = "physical",
        verify = 'no',
        mode='ql',
    )

    # 画测光孔径和背景环
    mag_file=open(phot_mag_file, 'r')
    mag_file=mag_file.readlines()
    for i in range(75,len(mag_file),5):
        text=mag_file[i+1].split()
        os.system("echo 'physical; circle %s %s %s # color=red' | xpaset ds9 region"%(text[0],text[1],phot_apertures))
        os.system("echo 'physical; circle %s %s %s # color=Yellow' | xpaset ds9 region"%(text[0],text[1],sky_inner))
        os.system("echo 'physical; circle %s %s %s # color=Yellow' | xpaset ds9 region"%(text[0],text[1],sky_inner+sky_width))
    for i in imexamine_a_out[2:]:
        isplit=i.split()
        xy=re.split(':|,',isplit[0][1:-1])
        xy=[float(i_xy) for i_xy in xy]
        os.system("echo 'box %s %s %s %s 0  # color=cyan' | xpaset ds9 region"%((xy[0]+xy[1])/2, (xy[2]+xy[3])/2,(xy[1]-xy[0]),(xy[3]-xy[2]))) # 标记测天光sigma的位置


    # 保存孔径和背景环region
    proc_ds9=run(['xpaget', 'ds9', 'region', '-format', 'ds9', '-system', 'physical'],stdout=PIPE,stderr=PIPE,encoding="gbk")
    region_file=proc_ds9.stdout
    region_physical_file=open('%s_phot_result_region_physical.reg'%(fits_file),'w')
    region_physical_file.write(region_file)
    region_physical_file.close()
    # # 兴隆的图像画环有偏差，重新画
    # run('xpaset -p ds9 region delete', shell=True)
    # run('xpaset -p ds9 region load %s_phot_result_region_physical.reg'%(fits_file), shell=True)

    os.system('xpaset -p ds9 saveimage %s.png 100'%fits_file)

    return  phot_mag_file,FWHM,check

if __name__=='__main__':
    fits_file='/media/clj/T7/LCODATA/MRK-501/allfits/elp1m008-fa05-20210828-0043-e91.fits'
    region_phot_fk5_filename='/media/clj/T7/LCODATA/MRK-501/allfits/1.cljpht_wcs_fk5.reg'
    apertur=1.5
    annulus=5.0
    dannulus=2.0
    measure_tar_FWHM=True
    ss=FWHM_skysigma_phot(fits_file,region_phot_fk5_filename,apertur,annulus,dannulus,measure_tar_FWHM)
    print(ss)
