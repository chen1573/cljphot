from astropy.time import Time
import os
from astropy.io import fits
import pandas as pd
import re
from astropy import units as u
from astropy.coordinates import SkyCoord
from default_setting import *

def corr(fits_file,mag_file_name,ref_catalog):
    re_pattern = "^(?P<regionshape>[\w]+)\((?P<x>[0-9]+.[0-9]+)\,(?P<y>\-?\d+(\.\d*)?)\,(?P<r>\d+(\.\d*)?.*)\).*text\=\{(?P<text>\w*)?\}"
    region_physical_file=open('%s_region_physical.reg'%(fits_file),'r')
    reftext=region_physical_file.readlines()
    ref_physical_list=[]
    ref_name_list=[]
    target_physical_list=[]
    sky_physical_list=[]

    # 读取 xxx-region_physical.reg,
    for i in range(len(reftext)):
        x = re.search(re_pattern,reftext[i][:-1])
        # print(i)
        if x==None: continue
        if x['text']=='p':
            # print(x['text'][0],'target')
            target_physical_list.append([x.groupdict(),reftext[i][:-1]])
        if x['text'][0]=='r':
            # print(x['text'],'ref_star')
            ref_physical_list.append([x.groupdict(),reftext[i][:-1]])
            ref_name_list.append(x['text'])
        if x['text']=='s':
            # print(x['text'],'sky')
            sky_physical_list.append([x.groupdict(),reftext[i][:-1]])
    ref_tar_phy_list=ref_physical_list+target_physical_list

    # for i in range(len(ref_physical_list)):
    #     print(ref_physical_list[i])
    print(ref_name_list)

    # 读取仪器星等
    mag_file=open('%s'%(mag_file_name),'r')
    mag_file=mag_file.readlines()
    instrument_mag=[]
    instrument_e_mag=[]
    INDEF_list=[]
    # print('reading ',mag_file_name)
    for i in range( len(ref_physical_list) + len(target_physical_list)):
        # print(i)
        # text1=mag_file[75+i*5].split()
        # print(text1)
        text2=mag_file[75+i*5+4].split()
        # print(text2[4],text2[5]) # 仪器星等 误差
        # if i < len(ref_physical_list): print('xxxxxyyyy',ref_physical_list[i][0]['x'],ref_physical_list[i][0]['y'])
        if text2[4]=='INDEF':
            INDEF_list.append('%s: ;%s'%(ref_tar_phy_list[i][0]['text'],text2[4]))
            continue
        instrument_mag.append(float(text2[4]))
        instrument_e_mag.append(float(text2[5]))
        # print('*************\n\n')
    
    print(instrument_mag)
    print(instrument_e_mag)
    print(INDEF_list)

    # print(ref_catalog.loc[ref_name_list,'cat_R'])

    fitsio=fits.open(fits_file)
    Band=fitsio[0].header[FILTERkey]
    Tstar=Time(fitsio[0].header[StartOfExposurekey],  format=StartOfExposureformat) 
    Terr= float(fitsio[0].header[EXPTIMEkey])*u.s /2.0
    Tmid=Tstar+Terr

    final_data= pd.DataFrame(data=None,columns=['file', 'Tmid(mjd)','Terr(day)','Band']
                                +['Catalog_%s'%(ref_i) for ref_i in ref_name_list]
                                +['Catalog_err_%s'%(ref_i) for ref_i in ref_name_list]
                                +['instrument_mag_%s'%(ref_i) for ref_i in ref_name_list]
                                +['instrument_mag_err_%s'%(ref_i) for ref_i in ref_name_list]
                                +['instrument_mag_target','instrument_mag_e_target'])
    final_data.loc[0,'file']=os.path.basename(fits_file)
    final_data.loc[0,'Tmid(mjd)']=Tmid.mjd
    final_data.loc[0,'Terr(day)']=(Terr.to(u.day)).value
    final_data.loc[0,'Band']=Band
    for i_ref in range(len(ref_name_list)):
        final_data.loc[0,'Catalog_%s'%(ref_name_list[i_ref])]=ref_catalog.loc[ref_name_list[i_ref],'%smag'%Band]
        final_data.loc[0,'Catalog_err_%s'%(ref_name_list[i_ref])]=ref_catalog.loc[ref_name_list[i_ref],'e_%smag'%Band]
        final_data.loc[0,'instrument_mag_%s'%(ref_name_list[i_ref])]=instrument_mag[i_ref]
        final_data.loc[0,'instrument_mag_err_%s'%(ref_name_list[i_ref])]=instrument_e_mag[i_ref]
    final_data.loc[0,'instrument_mag_target']=instrument_mag[-1]
    final_data.loc[0,'instrument_mag_e_target']=instrument_e_mag[-1]


    mag,mag_err=call_mag(final_data,ref_name_list,instrument_mag[len(ref_name_list)],instrument_e_mag[len(ref_name_list)])

    final_data.loc[0,'preliminary_mag']=mag
    final_data.loc[0,'preliminary_mag_err']=mag_err

    # 将某颗参考星当作未知星等，计算其 星表值 与 测光值 的 差
    for i_ref in range(len(ref_name_list)):
        ref_name_list_for_differ=[]
        boollist=[True]*len(ref_name_list)
        boollist[i_ref]=False   # 
        print(boollist)
        for i_bool in range(len(boollist)):
            if boollist[i_bool]:
                ref_name_list_for_differ.append(ref_name_list[i_bool])
        # print(ref_name_list_for_differ)

        ref_phot,ref_phot_err=call_mag(final_data,ref_name_list_for_differ,
                                     final_data.loc[0,'instrument_mag_%s'%(ref_name_list[i_ref])],
                                     final_data.loc[0,'instrument_mag_err_%s'%(ref_name_list[i_ref])])
        print(ref_phot,ref_phot_err)
        final_data.loc[0,'mag_(cat-phot)_%s'%(ref_name_list[i_ref])]=final_data.loc[0,'Catalog_%s'%(ref_name_list[i_ref])] - ref_phot
        final_data.loc[0,'mag_err_(cat-phot)_%s'%(ref_name_list[i_ref])]= ref_phot_err

    # print(final_data)

    return final_data , ref_name_list


def call_mag(data,ref_name_list,tar_instru_mag,tar_instru_mag_e):
    Band=data.loc[0,'Band']
    print('********')
    # print(data.loc[0,['Catalog_%s_err_%s'%(Band,ref) for ref in  ref_name_list]])
    # print(ref_name_list,tar_instru_mag,tar_instru_mag_e,Band)
    call_pd=pd.DataFrame(data=None,columns=['ref_text','Catalog_mag','Catalog_mag_e',
                                            'instrument_mag','instrument_mag_e',  'cat-instru',                                          
                                            'tar_instru+(cat-instru)','err*err',
                                            ],index=ref_name_list)
    call_pd.loc[:,'ref_text']=ref_name_list

    for ref_i in ref_name_list:
        call_pd.loc[ref_i,'instrument_mag']=data.loc[0, 'instrument_mag_%s'%(ref_i)]
        call_pd.loc[ref_i,'instrument_mag_e']=data.loc[0, 'instrument_mag_err_%s'%(ref_i)]
        call_pd.loc[ref_i,'Catalog_mag']=data.loc[0, 'Catalog_%s'%(ref_i)]
        call_pd.loc[ref_i,'Catalog_mag_e']=data.loc[0, 'Catalog_err_%s'%(ref_i)]

    call_pd.loc[:,'cat-instru']=call_pd.loc[:,'Catalog_mag']-call_pd.loc[:,'instrument_mag']
    call_pd.loc[:,'tar_instru+(cat-instru)']=tar_instru_mag+call_pd.loc[:,'cat-instru']
    call_pd.loc[:,'err*err']=call_pd.loc[:,'Catalog_mag_e']**2 + call_pd.loc[:,'instrument_mag_e']**2

    mag=call_pd.loc[:,'tar_instru+(cat-instru)'].mean()
    mag_err= ( call_pd.loc[:,'err*err'].mean()+tar_instru_mag_e**2+call_pd['tar_instru+(cat-instru)'].values.var()  )**0.5


    # print(call_pd)
    # print(mag,mag_err)

    return mag,mag_err


if __name__=='__main__':
   fits_file='/home/clj/cljphot_data/mrk501/ss/elp1m006-fa07-20221101-0050-e91.fits'
   mag_file_name='/home/clj/cljphot_data/mrk501/ss/elp1m006-fa07-20221101-0050-e91.fits.cljphot.mag.1'
   ref_catalog_file_name='/home/clj/cljphot_data/mrk501/ss/ref_catalog.tsv'
   ref_catalog=pd.read_csv(ref_catalog_file_name, index_col='ref_text',sep='\t')
   final_data,ref_name_list=corr(fits_file,mag_file_name,ref_catalog)

#    ss=pd.DataFrame(data=None,columns=None)
# #    ss.iloc[0,:]=final_data.iloc[0,:]

#    ss=pd.concat([ss,final_data],axis=0)
#    ss=pd.concat([ss,final_data],axis=0)
#    print('ssssssssssssss')
#    print(ss.iloc[0])
#    TTTTTTTTTTTTTTTTTTTTTTTTTT
#    Tmid_mjd,Terr_day, phot_mag_result,phot_mag_err_result,Band,textlist,instrument_mag,instrument_e_mag,result_pd = corr(fits_file,mag_file_name,ref_catalog_file_name)
#    print(Tmid_mjd,Terr_day, phot_mag_result,phot_mag_err_result,Band,textlist,instrument_mag,instrument_e_mag,result_pd )
#    print(Tmid_mjd,Terr_day, phot_mag_result,phot_mag_err_result,Band,)#textlist,instrument_mag,instrument_e_mag,result_pd )

#    final_data= pd.DataFrame(data=None,columns=['file', 'Tmid(mjd)','Terr(day)','Band']
#                             +['Catalog_%s_%s'%(Band,ref_i) for ref_i in textlist ]
#                             +['Catalog_%s_err_%s'%(Band,ref_i) for ref_i in textlist]
#                             +['instrument_mag_%s_err_%s'%(Band,ref_i) for ref_i in textlist])
#    final_data.iloc[0,'file']=fits_file

#    print(final_data)