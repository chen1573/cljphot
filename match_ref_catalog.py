from astropy.time import Time
import os
from astropy.io import fits
import pandas as pd
import re
from astropy import units as u
from astropy.coordinates import SkyCoord
def match_star(region_file,catalog_file,catalog_type):
    # 
    region_wcs_file=open(region_file,'r')
    reftext=region_wcs_file.readlines()
    region_wcs_file.close()
    re_pattern = "^(?P<regionshape>[\w]+)\((?P<x>[0-9]+.[0-9]+)\,(?P<y>\-?\d+(\.\d*)?)\,(?P<r>\d+(\.\d*)?.*)\).*text\=\{(?P<text>\w*)?\}"
    ref_wcs_list=[]
    target_wcs_list=[]
    sky_wcs_list=[]
    ref_ra=[]
    ref_dec=[]
    ref_textlist=[]
    # 读取测光位置文件（wcs坐标的），ra, dec , text
    for i in range(len(reftext)):
        x = re.search(re_pattern,reftext[i][:-1])
        # print(i)
        if x==None: continue
        if x['text'][0]=='p':
            # print(x['text'],'target')
            target_wcs_list.append([x.groupdict(),reftext[i][:-1]])
        if x['text'][0]=='r':
            # print(x['text'],'ref_star')
            ref_ra.append(x['x'])
            ref_dec.append(x['y'])
            ref_wcs_list.append([x.groupdict(),reftext[i][:-1]])
            ref_textlist.append(x['text'])
        if x['text']=='s':
            # print(x['text'],'sky')
            sky_wcs_list.append([x.groupdict(),reftext[i][:-1]])
    
    if len(target_wcs_list)>1:
        print('仅支持一个目标源')
        return
    if len(target_wcs_list)<1:
        print('未指定目标源')
        return
    # ref_tarwcs_list=ref_wcs_list+target_wcs_list
    # print(ref_ra)
    # print(ref_dec)
    # print(ref_textlist)
    ref_coord=SkyCoord(ref_ra,ref_dec,  unit=(u.deg, u.deg),frame='icrs')
    # for i in range(len(ref_coord)):
        # print(ref_wcs_list[i][0]['text'],ref_ra[i],ref_dec[i],ref_coord[i])

    
    catalog=pd.read_csv(catalog_file, sep='\t')
    catalog_coord=SkyCoord(catalog['_RAJ2000'],catalog['_DEJ2000'],unit=(u.deg, u.deg),frame='icrs')

    # 匹配最近的星
    idx_in_catalog, sep2d_catalog, _ =ref_coord.match_to_catalog_sky(catalog_coord)
    print(idx_in_catalog,sep2d_catalog)


    for i_ref in range(len(ref_textlist)):
        if sep2d_catalog[i_ref] > 2.0*u.arcsec:
            print(ref_textlist[i_ref],' do not match any item')

    for i_ref in range(len(ref_textlist)):
        if sep2d_catalog[i_ref] > 2.0*u.arcsec:
            return 'no'


    ref_catalog=catalog.iloc[idx_in_catalog]

    # 如果是用以前匹配过的
    if set(['ref_text']).issubset(ref_catalog.columns):
        ref_catalog.drop(columns='ref_text', inplace=True)
    ref_catalog.insert(0,'ref_text', ref_textlist)

    if catalog_type=='USNO-UCAC4' or catalog_type=='NOMAD' or catalog_type=='other':
        pass

    if catalog_type=='USNO-B1.0':
        ref_catalog['Bmag']= ref_catalog['B2mag']
        ref_catalog['e_Bmag']=0.0

        ref_catalog['Rmag']=ref_catalog['R2mag']
        ref_catalog['e_Rmag']=0.0

        ref_catalog['e_Imag']=0.0

    if catalog_type=='SDSS':
        # ugriz to BVRI https://classic.sdss.org/dr7/algorithms/sdssUBVRITransform.php#Rodgers2005
        ref_catalog['Bmag']= ref_catalog['umag'] - 0.8116 * (ref_catalog['umag'] - ref_catalog['gmag'] ) + 0.1313
        ref_catalog['e_Bmag']=ref_catalog['e_umag']+ 0.8116*(ref_catalog['e_umag'] + ref_catalog['e_gmag']) +0.0095

        ref_catalog['Vmag']=ref_catalog['gmag'] - 0.5784*(ref_catalog['gmag'] - ref_catalog['rmag']) - 0.0038
        ref_catalog['e_Vmag']=ref_catalog['e_gmag'] + 0.5784*(ref_catalog['e_gmag'] + ref_catalog['e_rmag']) + 0.0054

        ref_catalog['Rmag']=ref_catalog['rmag'] - 0.2936*(ref_catalog['rmag'] - ref_catalog['imag']) - 0.1439
        ref_catalog['e_Rmag']=ref_catalog['e_rmag'] + 0.2936*(ref_catalog['e_rmag'] + ref_catalog['e_imag']) + 0.0072

        ref_catalog['Imag']=ref_catalog['imag'] - 0.3780*(ref_catalog['imag'] - ref_catalog['zmag']) -0.3974
        ref_catalog['e_Imag']=ref_catalog['e_imag'] + 0.3780*(ref_catalog['e_imag'] + ref_catalog['e_zmag']) + 0.0063


    i=1  
    refcatfile='%s/ref_catalog_%d.tsv'%(os.path.dirname(catalog_file),i)
    while os.path.isfile(refcatfile):
        i=i+1
        refcatfile='%s/ref_catalog_%d.tsv'%(os.path.dirname(catalog_file),i)
    ref_catalog.to_csv(refcatfile,index=0 ,sep="\t")
    
    print(ref_catalog)

    return refcatfile


if __name__=='__main__':
   region_file='/home/clj/我的坚果云/code/cljphot/cljpht_wcs_fk5.reg'
   catalog_file='/home/clj/我的坚果云/code/cljphot/srceen_catalog.tsv'
   ref_item = match_star(region_file,catalog_file)
   print(ref_item)

#    final_data= pd.DataFrame(data=None,columns=['file', 'Tmid(mjd)','Terr(day)','Band']
#                             +['Catalog_%s_%s'%(Band,ref_i) for ref_i in textlist ]
#                             +['Catalog_%s_err_%s'%(Band,ref_i) for ref_i in textlist]
#                             +['instrument_mag_%s_err_%s'%(Band,ref_i) for ref_i in textlist])
#    final_data.iloc[0,'file']=fits_file

#    print(final_data)