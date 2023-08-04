import pandas as pd
import os
from astropy import units as u
from astropy.coordinates import SkyCoord

def cata_scr(catalog_file,delta_mag,catalog_type):
    # 读取参考星的星表值
    print('cccccccccccccccccccccccccccccccc')
    catalog0=pd.read_csv(catalog_file, sep='\t')

    print(catalog_type)
    print(delta_mag)
    if catalog_type=='USNO-B1.0':
        # 筛除无星等值
        not_NAN_list=[]
        for i in range(len(catalog0)):
            if (pd.isnull(catalog0.loc[i,'B1mag']))  or \
                (pd.isnull(catalog0.loc[i,'R1mag'])) or \
                (pd.isnull(catalog0.loc[i,'B2mag'])) or \
                (pd.isnull(catalog0.loc[i,'R2mag']))  or \
                (pd.isnull(catalog0.loc[i,'Imag'])) :
                not_NAN_list.append(False)
            else:
                not_NAN_list.append(True)

        catalog=catalog0[not_NAN_list].copy()
        catalog_coord=SkyCoord(catalog['_RAJ2000'],catalog['_DEJ2000'],unit=(u.deg, u.deg),frame='icrs')

        screenlist=[False]*len(catalog)
        srceen_catalog=catalog[ [False]*len(catalog) ]

        for i in range(len(catalog)):
            sep=(catalog_coord[i].separation(catalog_coord))
            bool_list=sep<0.5*u.arcsec # 相差小于 0.5*u.arcsec 当作同一颗星
            obj = catalog[bool_list]

            # 两次观测相差大于 delta_mag
            if  (abs(obj['B1mag'].max() - obj['B2mag'].min()) < delta_mag ) and \
                (abs(obj['R1mag'].max() - obj['R2mag'].min()) < delta_mag )\
                :
                screenlist[i]=True
            # else:
            #     print(i,'F')

        # pandas 取行另存
        srceen_catalog=catalog[screenlist]


    if catalog_type=='SDSS':
        # 筛除无星等值
        not_NAN_list=[]
        for i in range(len(catalog0)):
            if (pd.isnull(catalog0.loc[i,'umag']))  or \
                (pd.isnull(catalog0.loc[i,'gmag'])) or \
                (pd.isnull(catalog0.loc[i,'rmag'])) or \
                (pd.isnull(catalog0.loc[i,'imag']))  or \
                (pd.isnull(catalog0.loc[i,'zmag'])) :
                not_NAN_list.append(False)
            else:
                not_NAN_list.append(True)

        catalog=catalog0[not_NAN_list].copy()
        catalog_coord=SkyCoord(catalog['_RAJ2000'],catalog['_DEJ2000'],unit=(u.deg, u.deg),frame='icrs')

        screenlist=[False]*len(catalog)
        srceen_catalog=catalog[ [False]*len(catalog) ]

        for i in range(len(catalog)):
            sep=(catalog_coord[i].separation(catalog_coord))
            bool_list=sep<0.5*u.arcsec # 相差小于 0.5*u.arcsec 当作同一颗星
            obj = catalog[bool_list]
            #  只有一次观测
            if obj.shape[0]<2 : 
                continue

            # 多次观测相差大于 delta_mag
            if  abs(obj['umag'].max() - obj['umag'].min()) < delta_mag and \
                abs(obj['gmag'].max() - obj['gmag'].min()) < delta_mag and \
                abs(obj['rmag'].max() - obj['rmag'].min()) < delta_mag and \
                abs(obj['imag'].max() - obj['imag'].min()) < delta_mag and \
                abs(obj['zmag'].max() - obj['zmag'].min()) < delta_mag   \
                :
                screenlist[i]=True

        # pandas 取行另存
        srceen_catalog=catalog[screenlist]

    scr_cat_name='%s/srceen_catalog_%s.tsv'%(os.path.dirname(catalog_file),catalog_type)
    i=1  
    scr_cat_name='%s/srceen_catalog_%s_%d.tsv'%(os.path.dirname(catalog_file),catalog_type,i)
    while os.path.isfile(scr_cat_name):
        i=i+1
        scr_cat_name='%s/srceen_catalog_%s_%d.tsv'%(os.path.dirname(catalog_file),catalog_type,i)

    srceen_catalog.to_csv(scr_cat_name,index=0 ,sep="\t")
    
    return scr_cat_name


if __name__=="__main__":
    catalog_file='/home/clj/我的坚果云/code/cljphot/USNOB1.tsv'
    ss=cata_scr(catalog_file,0.1,'USNO-B1.0')
    print(ss)