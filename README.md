# 简介

为了方便自动化编译和配置WRF，比如在Docker容器中编译WRF，编写这么一套Python脚本工具。

## 编译WRF

```
$ ./build-wrf.py --codes <WRF程序目录> --compiler-suite gnu [--force]
```
其中`<WRF程序目录>`应该包含WRF、WPS、WRFDA源程序目录。

## 编译GSI

```
$ ./build-gsi.py --codes <WRF和GSI程序目录> --compiler-suite gnu [--force]
```
其中`<WRF和GSI程序目录>`应该包含WRF、GSI源程序目录。

## 配置WRF

输入设定的JSON配置文件，例如
```json
{
  "tag": "test",
  "common": {
    "start_time": "2018091600",
    "forecast_hour": 48,
    "min_lon": 70.0,
    "max_lon": 140.0,
    "min_lat": 10.0,
    "max_lat": 55.0,
    "resolution": 9000.0,
    "max_dom": 1
  }
}
```
然后运行`config-wrf.py`
```
$ ./config-wrf.py --codes <WRF程序目录> --geog-root <GEOG静态数据目录> --config-json <JSON配置文件路径> [--force]
```

## 运行WPS

```
$ ./run-wps.py --codes <WRF程序目录> --config-json <JSON配置文件路径> -b <GFS驱动场根目录> [--force]
```
这里假设`<WRF程序目录>`包含静态数据集`WPS_GEOG`。
