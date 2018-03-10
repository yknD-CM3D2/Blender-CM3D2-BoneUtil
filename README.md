# Blender-CM3D2-BoneUtil
---
　本アドオンは、**主に** 「[カスタムメイド3D2](http://kisskiss.tv/cm3d2/)」向けモデルデータのボーンに関連した補助機能を提供します。  
（ボーン以外の機能が追加される可能性もあります）  
　また、モデルデータの扱いは、[CM3D2 Converter][]の使用を前提としています。

　本アドオンは、**不具合が残っている可能性** があるため、データのバックアップを推奨します。

## ■ インストール (Installation)
#### ◇事前準備
　Blender2.76以上(動作確認は[2.79a][blender279])がインストールされていることが前提です。

#### ◇ダウンロード・展開
　[Releases][]のリンク先にある該当バージョンか、
画面右の[Download ZIP][master_zip]からファイルをダウンロード・解凍し、  

```
 %APPDATA%\Blender Foundation\Blender\{Version}\scripts\addons\  
 ```
に配置してください。  
例) Windows7/10、Blender-2.78、ユーザ名「UserA」の場合  
```
C:\Users\UserA\AppData\Roaming\Blender Foundation\Blender\2.78\scripts\addons\CM3D2 BoneUtil\*.py
```
   に配置する形になります。  
   もし、フォルダが存在しない場合は作成してください。

#### ◇設定
　Blenderを起動し、ユーザー設定のアドオンタブで「cm3d2」等で検索し、  
　「Tools: CM3D2 BoneUtil」をオンにすれば(一時的に)有効になります。  
　次回起動時からも有効にしたい場合は「ユーザー設定の保存」をクリックして下さい。  

![UserSave](https://raw.githubusercontent.com/wiki/trzr/Blender-CM3D2-BoneUtil/images/repos_config.png)

## ■ 提供機能

使い方の詳細は、[wiki][] を参照してください。  
一部は以下のリンクから参照できます。  

|機能| 概要|
|:---|:----|
| **[BoneData取り込み機能][BoneImport]** | Blender上のボーンからBoneDataを取込む機能|
| **[揺れボーンタイプ 一括変更機能][BoneTypeRename]** （オプション） | 揺れボーンの型を一括で変更する機能|
| **[シェイプキー 一括操作機能][BlendsetEdit]** | blendsetを元に、シェイプキーの値を一括で変更する機能|


## ■ 免責
  本アドオンの使用または使用不能から生じるいかなる損害について、作者は一切の責任を負えません。  
  各自の責任において使用してください。

## ■ 謝辞
  ボーン計算式のベースは、[夜勤D][]さんの作成されたスクリプトを参考にさせていただいております。  
  Blenderアドオン作成についても [CM3D2 Converter][]を参考にさせていただきました。  
  また、twitterでも多くの方に刺激や助言をいただいております。感謝！   


[CM3D2 Converter]:https://github.com/CM3Duser/Blender-CM3D2-Converter
[blender279]:http://download.blender.org/release/Blender2.79/
[master_zip]:https://github.com/trzr/Blender-CM3D2-BoneUtil/archive/master.zip
[Releases]:https://github.com/trzr/Blender-CM3D2-BoneUtil/releases
[wiki]:https://github.com/trzr/Blender-CM3D2-BoneUtil/wiki
[BoneImport]:https://github.com/trzr/Blender-CM3D2-BoneUtil/wiki/BoneDataImport
[BoneTypeRename]:https://github.com/trzr/Blender-CM3D2-BoneUtil/wiki/BoneTypeRename
[BlendsetEdit]:https://github.com/trzr/Blender-CM3D2-BoneUtil/wiki/BlendsetEdit
[夜勤D]:https://github.com/yknD-CM3D2
