import pandas as pd

def sec_corr(preliminary_data_i,ref_name_list):
    # print(preliminary_data_i.columns,'1111111111')
    adv_data=preliminary_data_i.copy()
    # print(adv_data)
    # return 
    # print(preliminary_data_i.iloc[0]['mag_err_(cat-phot)_r6'],'222222222222')
    # return
    # return adv_data
    mag,mag_err=call_mag(preliminary_data_i,
                         ref_name_list,
                         preliminary_data_i.iloc[0]['instrument_mag_target'],
                         preliminary_data_i.iloc[0]['instrument_mag_e_target'])
    # print(mag)

    adv_data.loc[:,'tar_advanced_mag']=mag
    adv_data.loc[:,'tar_advanced_mag_err']=mag_err
    adv_data.loc[:,'ref_list']=str(ref_name_list)
    # print(adv_data.loc[:,'tar_advanced_mag'])
    # return adv_data

    # 将某颗参考星当作未知星等，计算其 星表值 与 测光值 的 差
    for i_ref in range(len(ref_name_list)):
        ref_name_list_for_differ=[]
        boollist=[True]*len(ref_name_list)
        boollist[i_ref]=False   # 
        # print(boollist)
        for i_bool in range(len(boollist)):
            if boollist[i_bool]:
                ref_name_list_for_differ.append(ref_name_list[i_bool])
        # print(ref_name_list_for_differ)

        ref_phot,ref_phot_err=call_mag(preliminary_data_i,ref_name_list_for_differ,
                                     preliminary_data_i.iloc[0]['instrument_mag_%s'%(ref_name_list[i_ref])],
                                     preliminary_data_i.iloc[0]['instrument_mag_err_%s'%(ref_name_list[i_ref])])
        # print(ref_phot,ref_phot_err)
        adv_data.loc[:,'ref_advanced_mag_(cat-phot)_%s'%(ref_name_list[i_ref])]=preliminary_data_i.iloc[0]['Catalog_%s'%(ref_name_list[i_ref])] - ref_phot
        adv_data.loc[:,'ref_advanced_mag_err_(cat-phot)_%s'%(ref_name_list[i_ref])]= ref_phot_err

    # print(adv_data)

    return adv_data.loc[:,:].copy()


def call_mag(data,ref_name_list_for_differ,tar_instru_mag,tar_instru_mag_e):
    # Band=data.iloc[0]['Band']
    # print('********')
    # print(data.loc[0,['Catalog_%s_err_%s'%(Band,ref) for ref in  ref_name_list]])
    # print(ref_name_list,tar_instru_mag,tar_instru_mag_e,Band)
    call_pd=pd.DataFrame(data=None,columns=['ref_text','Catalog_mag','Catalog_mag_e',
                                            'instrument_mag','instrument_mag_e',  'cat-instru',                                          
                                            'tar_instru+(cat-instru)','err*err',
                                            ],index=ref_name_list_for_differ)
    call_pd.loc[:,'ref_text']=ref_name_list_for_differ

    for ref_i in ref_name_list_for_differ:
        call_pd.loc[ref_i,'instrument_mag']=data.iloc[0]['instrument_mag_%s'%(ref_i)]
        call_pd.loc[ref_i,'instrument_mag_e']=data.iloc[0]['instrument_mag_err_%s'%(ref_i)]
        call_pd.loc[ref_i,'Catalog_mag']=data.iloc[0]['Catalog_%s'%(ref_i)]
        call_pd.loc[ref_i,'Catalog_mag_e']=data.iloc[0]['Catalog_err_%s'%(ref_i)]

    call_pd.loc[:,'cat-instru']=call_pd.loc[:,'Catalog_mag']-call_pd.loc[:,'instrument_mag']
    call_pd.loc[:,'tar_instru+(cat-instru)']=tar_instru_mag+call_pd.loc[:,'cat-instru']
    call_pd.loc[:,'err*err']=call_pd.loc[:,'Catalog_mag_e']**2 + call_pd.loc[:,'instrument_mag_e']**2

    mag=call_pd.loc[:,'tar_instru+(cat-instru)'].mean()
    mag_err= ( call_pd.loc[:,'err*err'].mean()+tar_instru_mag_e**2+call_pd['tar_instru+(cat-instru)'].values.var()  )**0.5


    # print(call_pd)
    # print(mag,mag_err)

    return mag,mag_err


if __name__=='__main__':
   
   preliminary_data_file_name='/home/clj/cljphot_data/mrk501/cljphot_reslut_13.tsv'
   preliminary_data=pd.read_csv(preliminary_data_file_name,sep='\t')
   ref_name_list=['r7', 'r5', 'r2', 'r3', 'r1', 'r4', 'r8', 'r6']
   
   advance_datd_pd=pd.DataFrame(data=None,columns=None)

   for i in range(preliminary_data.shape[0]):
        # print(preliminary_data.iloc[[i],:])
        # sec_corr(preliminary_data.iloc[[i],:],ref_name_list)
        adv_data=sec_corr(preliminary_data.iloc[[i],:],ref_name_list)
        advance_datd_pd=pd.concat([advance_datd_pd,adv_data],axis=0)

        # print(adv_data)
        # print(preliminary_data.iloc[[i],:].copy())
   advance_datd_pd.to_csv('ss.tsv',index=0 ,sep="\t")
#    print(advance_datd_pd.loc[advance_datd_pd.loc[:,'Band']=='B' ,'file'])

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