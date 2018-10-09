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
    "forecast_hours": 48,
    "min_lon": [70.0, 120],
    "max_lon": [140.0, 130],
    "min_lat": [10.0, 30],
    "max_lat": [55.0, 40],
    "resolution": 27000.0,
    "time_step": 90.0,
    "parent_id": [1, 1],
    "parent_grid_ratio": [1, 3],
    "max_dom": 2
  },
  "da": {
    "cv_options": "cv3",
    "nmc": {
      "long_forecast_hours": 24,
      "short_forecast_hours": 12,
      "start_time": "2018090100",
      "end_time": "2018100100",
      "start_hours_per_day": [0, 12]
    }
  }
}
```
然后运行`config-wrf.py`
```
$ ./config-wrf.py --codes <WRF程序目录> --geog-root <GEOG静态数据目录> --config-json <JSON配置文件路径> [--force]
[Notice]: Edit namelist.wps.
[Notice]: Succeeded.
```

## 运行WPS

```
$ ./run-wps.py --codes <WRF程序目录> --config-json <JSON配置文件路径> -b <GFS驱动场根目录> [--force]
[Notice]: Run geogrid.exe ...
==> rm -f geo_em.d*.nc
==> ./geogrid.exe &> geogrid.out
[Notice]: Succeeded.
==> ls -l /models/WPS/geo_em.*.nc
-rw-r--r-- 1 root root 1178744 Sep 29 06:43 /models/WPS/geo_em.d01.nc
[Notice]: Run ungrib.exe ...
==> ln -sf ungrib/Variable_Tables/Vtable.GFS Vtable
==> rm -f FILE:*
==> ./link_grib.csh /data/raw/gfs/gfs.2018091600/*
==> ./ungrib.exe &> ungrib.out
[Notice]: Succeeded.
==> ls -l FILE:*
-rw-r--r-- 1 root root 144348292 Sep 29 06:45 FILE:2018-09-16_00
-rw-r--r-- 1 root root 144348292 Sep 29 06:45 FILE:2018-09-16_06
-rw-r--r-- 1 root root 144348292 Sep 29 06:45 FILE:2018-09-16_12
-rw-r--r-- 1 root root 144348292 Sep 29 06:45 FILE:2018-09-16_18
-rw-r--r-- 1 root root 144348292 Sep 29 06:45 FILE:2018-09-17_00
-rw-r--r-- 1 root root 144348292 Sep 29 06:45 FILE:2018-09-17_06
-rw-r--r-- 1 root root 144348292 Sep 29 06:45 FILE:2018-09-17_12
-rw-r--r-- 1 root root 144348292 Sep 29 06:45 FILE:2018-09-17_18
-rw-r--r-- 1 root root 144348292 Sep 29 06:45 FILE:2018-09-18_00
[Notice]: Run metgrid.exe ...
==> rm -f met_em.*
==> ./metgrid.exe &> metgrid.out
[Notice]: Succeeded.
==> ls -l met_em.*
-rw-r--r-- 1 root root 3451444 Sep 29 06:46 met_em.d01.2018-09-16_00:00:00.nc
-rw-r--r-- 1 root root 3420950 Sep 29 06:46 met_em.d01.2018-09-16_06:00:00.nc
-rw-r--r-- 1 root root 3441674 Sep 29 06:46 met_em.d01.2018-09-16_12:00:00.nc
-rw-r--r-- 1 root root 3441057 Sep 29 06:46 met_em.d01.2018-09-16_18:00:00.nc
-rw-r--r-- 1 root root 3445411 Sep 29 06:46 met_em.d01.2018-09-17_00:00:00.nc
-rw-r--r-- 1 root root 3432556 Sep 29 06:46 met_em.d01.2018-09-17_06:00:00.nc
-rw-r--r-- 1 root root 3428337 Sep 29 06:46 met_em.d01.2018-09-17_12:00:00.nc
-rw-r--r-- 1 root root 3426699 Sep 29 06:46 met_em.d01.2018-09-17_18:00:00.nc
-rw-r--r-- 1 root root 3435980 Sep 29 06:46 met_em.d01.2018-09-18_00:00:00.nc
```
