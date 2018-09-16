# 简介

为了方便自动化编译和配置WRF，比如在Docker容器中编译WRF，编写这么一套Python脚本工具。

## 编译WRF

```
$ ./build-wrf.py --codes <WRF程序目录> --compiler-suite gnu [--force]
```

其中`<WRF程序目录>`应该包含WRF、WPS、WRFDA源程序目录。
