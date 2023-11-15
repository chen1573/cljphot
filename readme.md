# 基于 pyraf 的测光程序

可用于单幅、批量测光

程序还不完善，不定期更新

github:<https://github.com/chen1573/cljphot>

## 要求：

1.  电脑装有`iraf`
2.  图像需要有正确的 wcs 坐标
3.  使用 J2000的坐标
4.  图像已经过 本底、平场 矫正

## 安装：

这是python3程序，直接用python3运行`cljphot.py`就行，建议用`venv`或`conda`创建一个虚拟环境，然后在自己的`.bashrc`文件加入一个命令。

1.  如用`venv`，将整个程序文件夹放到一个合适的地方，在程序文件夹下打开终端，运行

        python3 -m venv cljphotenv
        source cljphotenv/bin/activate
        pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
        which python3

    `which python3` 命令给出了一个python3的路径，在自己的`.bashrc`文件加入`alias cljphot='/那个python3的路径/python3  /到/程/序/的/路/经/cljphot.py'`

2.  如用`conda`，将整个程序文件夹放到一个合适的地方，在程序文件夹下打开终端，运行

        conda create -n cljphotenv python=python3
        conda activate cljphotenv
        pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
        which python3

    `which python3` 命令给出了一个python3的路径，在自己的`.bashrc`文件加入`alias cljphot='/那个python3的路径/python3  /到/程/序/的/路/经/cljphot.py'`

## 设置

1.  `default_setting.py` 里fits文件的keyword根据自己图像修改, imtsize数字应与自己要测的图像大小一致，否则保存图像时画测光孔径位置有大幅度偏差。
2.  环境变量 `iraf`需指向自己计算机的iraf安装目录，例如我的，`export iraf="/home/clj/applications/iraf-2.17/"`，使用apt-get 安装iraf的一般已经自动定义好。


## 使用方法：

1.  打开终端运行 `cljphot`

2.  点击打开图像按钮，选择一张图像，会用 DS9 打开图像

3.  用 ds9 下载catalog，导出为tsv格式的文件。

4.  选择catalog类型，点击`筛选catalog条目`，选择刚才导出的catalog文件，程序选出用多次测光且多次测光间差值小于`delta_mag`的条目，`delta_mag`可以点击旁边的`…`按钮指定，默认是0.1。筛选结束会保存到`srceen_catalog.tsv`, 同时在ds9展示catalog，并指定测光用的catalog为该文件，不需要再点击`选择catalog文件`

5.  如已有无需筛选的可用的catalog文件，可点击`选择catalog文件`选择该文件。

6.  catalog文件可以手动编辑，tsv格式，需包含

        _RAJ2000 _DEJ2000 Xmag e_Xmag Xmag e_Xmag ....

    X为测光波段，

7.  使用 ds9 的 region 功能标记如下内容

    1.  参考星，圆形，记为 r1, r2, r3, … 4到6个，不能重复,  r,  for references
    2.  测半高宽的位置，圆形，都记为 a,  4到6个
    3.  天光位置，圆形，都记为 s，4到6个,  s for sigma of sky
    4.  目标源的位置，圆形，只能有一个，记为 p ， p for photometry

8.  点击`确定DS9当前的region为测光位置`,程序确定本次测光的位置，并保存文件，下次可点击`载入 region 文件到 DS9`选择该文件。

9.  点击`匹配catalog条目与参考星位置`，程序会在catalog文件内寻找参考星对应的条目，并将`ugriz`转换为`BVRI`[Lupton (2005)](https://classic.sdss.org/dr7/algorithms/sdssUBVRITransform.php#Rodgers2005)。

10. 测光孔径、背景环可点击`modify`按钮修改，

11. 点击`孔径测光单幅图像`，结果显示在终端，并在ds9 绘制以下内容：

    1.  半高全宽 蓝圈
    2.  测光孔径 红圈
    3.  背景环 黄圈
    4.  测天光位置 青方框

12. 点击`孔径测光多幅图像`，程序根据wcs坐标对每幅图像测光，并实时画出光变以及每次测光的参考星的星表值与测光值的差值，如差值过大说明该星可能为变星，不宜做参考星。测光结束保存`cljphot_Preliminary_reslut_%d.tsv` 和 `cljphot_Preliminary_reslut_err_%d.tsv` 文件以及png格式的图像，可通过图像检查测光位置是否正确。

13. `cljphot_Preliminary_reslut_%d.tsv`记录了测光结果，其中带有`warningtext` 的应人工确认图像是否出错。

14. `cljphot_Preliminary_reslut_err_%d.tsv`记录了不能测光的图像，应人工检查图像。

15. 批量测光结束自动指定批量测光结果文件，也可点击按钮`选择批量测光结果文件`指定

16. 点击`读取批量测光结果文件`，点击`计算星等`，画出 光变 以及  参考星的星表值与测光值的差值，可选择不同的查考星进行计算，最后点击`保存星等最终文件`,结果保存到`cljphot_final_reslut_%d.tsv`。

## 其他：

1.  使用sdss的星表较差测光，根据 [Lupton (2005)](https://classic.sdss.org/dr7/algorithms/sdssUBVRITransform.php#Rodgers2005) 换算星等 （具体哪篇文章以后再找）

           B = u - 0.8116*(u - g) + 0.1313;  sigma = 0.0095
           B = g + 0.3130*(g - r) + 0.2271;  sigma = 0.0107
           V = g - 0.2906*(u - g) + 0.0885;  sigma = 0.0129
           V = g - 0.5784*(g - r) - 0.0038;  sigma = 0.0054
           R = r - 0.1837*(g - r) - 0.0971;  sigma = 0.0106
           R = r - 0.2936*(r - i) - 0.1439;  sigma = 0.0072
           I = r - 1.2444*(r - i) - 0.3820;  sigma = 0.0078
           I = i - 0.3780*(i - z)  -0.3974;  sigma = 0.0063

