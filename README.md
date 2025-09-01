# bilibili-download-web

哔哩哔哩视频在线解析下载网站源码，支持通过本地运行或 Docker 部署的方式启动服务，实现 B 站视频的在线解析与下载功能。

## 一、运行方式

### 方式 1：本地运行



1.  进入后端目录



```
cd backend
```



1.  安装依赖包



```
pip install -r requirements.txt
```



1.  启动服务（默认端口 8000）



```
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 方式 2：Docker 部署



1.  进入后端目录



```
cd backend
```



1.  构建 Docker 镜像



```
docker build -t bili-downloader .
```



1.  启动 Docker 容器（端口映射：主机 8000 端口 -> 容器 8000 端口）



```
docker run -d -p 8000:8000 bili-downloader
```

## 二、前端访问

服务启动后，直接打开项目中的前端文件即可使用：



```
frontend/index.html
```

## 三、效果展示



![demo](https://github.com/SUWJTech/bilibili-download-web/blob/main/demo.png)

