---
title: "我的第一台海外 VPS：从服务器测速到个人博客部署"
date: 2026-06-05
draft: false
tags: ["VPS", "DigitalOcean", "Cloudflare", "Hugo", "Linux", "Docker"]
cover:
  image: "/images/vps-setup/cover.png"
  alt: "VPS 配置记录"
  caption: "DigitalOcean + Cloudflare + Hugo"
---

这篇文章记录我第一次从零配置海外 VPS 的完整过程。

最开始，我只是想买一台云服务器，用来学习 Linux、SSH、Docker、Nginx 和域名解析。后来这个 VPS 逐渐变成了一个小型个人基础设施：它承担了服务器实验、个人博客、工具页面和 AI Agent 服务等功能。

这篇不是“炫技教程”，而是一份普通用户也可以参考的实践记录。

---

## 一、为什么要搭一台 VPS

相比直接使用各种现成平台，自己配置 VPS 有几个明显好处：

- 可以系统学习 Linux、SSH、Nginx、Docker 等基础技能
- 可以部署自己的博客、API、工具页和轻量数据库
- 可以更直观地理解域名、DNS、HTTPS 和 Cloudflare
- 后续可以作为 AI Agent、小程序、自动化任务的运行环境
- 出问题时能真正理解服务是怎么跑起来的

我选择的是 DigitalOcean，系统使用 Ubuntu 24.04 LTS。对个人博客、轻量服务和学习用途来说，入门配置不需要太高，`1 vCPU / 2GB RAM` 已经足够。

---

## 二、创建服务器

创建 VPS 时，我主要关注这几个选项：

| 配置项 | 推荐选择 |
|---|---|
| Region | 选择自己实际访问更稳定的区域 |
| Image | Ubuntu 24.04 LTS |
| Size | 1 vCPU / 2GB RAM 起步 |
| Authentication | 优先使用 SSH Key |
| Monitoring | 建议开启 |

我分别测试了纽约和旧金山两个节点。理论上美国西海岸离亚洲更近，但跨境线路并不只取决于地理距离，还取决于运营商路由、IP 段、晚高峰拥堵等因素。

因此，最终选择哪个区域，最好以自己的实测为准。

---

## 三、连接服务器

创建好服务器后，可以用 SSH 登录。

```bash
ssh root@你的服务器公网IP
```

初次登录后，我不建议长期使用 root 用户。root 权限太高，误操作风险比较大。更稳妥的做法是创建普通用户，并给它 sudo 权限。

```bash
adduser leo
usermod -aG sudo leo
```

之后日常登录使用：

```bash
ssh leo@你的服务器公网IP
```

---

## 四、基础安全配置

服务器上线后，我做了几项基础安全加固。

### 1. 更新系统

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. 开启 UFW 防火墙

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

当前主要开放端口：

```text
22/tcp   SSH
80/tcp   HTTP
443/tcp  HTTPS
```

如果后续部署其他服务，也应该按需开放端口，而不是一次性开放所有端口。

### 3. 禁用 root 登录和密码登录

编辑 SSH 配置：

```bash
sudo nano /etc/ssh/sshd_config
```

确认以下配置：

```text
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
```

检查配置语法：

```bash
sudo sshd -t
```

重启 SSH：

```bash
sudo systemctl restart ssh
```

这样服务器会更安全：不能直接用 root 登录，也不能用密码暴力尝试登录，只能通过 SSH Key 访问。

---

## 五、VPS 性能与网络测试

为了了解服务器的性能和网络情况，我使用了 `bench.sh` 做基础测试：

```bash
curl -Lso- bench.sh | bash
```

主要关注几个指标：

- CPU 核心数
- 内存大小
- 磁盘 I/O
- 上传 / 下载速度
- 延迟和丢包

本地也可以用 PowerShell 测试：

```powershell
ping 你的VPS公网IP -n 50
tracert 你的VPS公网IP
```

我最终对比了 NYC3 和 SFO3 两个区域：

| 节点 | 平均延迟 | 丢包 |
|---|---:|---:|
| NYC3 | 约 238ms | 0% |
| SFO3 | 约 249ms | 0% |

虽然旧金山从地理位置上看更近，但实际测试中纽约节点更稳定，因此最终保留了 NYC3。

这个过程也让我意识到：**VPS 选区不能只看地图距离，实际延迟、丢包和路由才更重要。**

---

## 六、安装 Docker

为了避免把所有软件都直接装在系统里，我选择用 Docker 管理后续服务。

安装完成后，用下面命令验证 Docker 是否可用：

```bash
docker run hello-world
```

常用命令：

```bash
docker ps
docker ps -a
docker logs 容器名 --tail=100
docker compose ps
docker compose restart 服务名
```

Docker 的好处是：每个服务都相对独立，后续迁移、删除、重启和排错都更清晰。

---

## 七、域名与 Cloudflare

后来我购买了域名，并将 DNS 托管到 Cloudflare。

我的域名结构如下：

```text
blog.estevancyber.net   → 个人博客
tools.estevancyber.net  → 工具页
```

Cloudflare 主要负责：

- DNS 管理
- HTTPS 证书
- 基础缓存
- 隐藏源站 IP
- 基础安全防护

接入 Cloudflare 的核心步骤是：

1. 在 Cloudflare 添加域名
2. 获取 Cloudflare 分配的两个 Nameserver
3. 到域名注册商处替换原 Nameserver
4. 等待 Cloudflare 显示 Active
5. 在 Cloudflare DNS 中添加 A / CNAME 记录

我的 DNS 记录大致如下：

```text
blog   A      VPS公网IP
tools  A      VPS公网IP
www    CNAME  estevancyber.net
@      A      VPS公网IP
```

一开始建议先用灰云 `DNS only`，等网站部署和 HTTPS 都确认正常后，再切换为橙云 `Proxied`。

---

## 八、Nginx 多站点配置

我的 VPS 上使用 Nginx 根据不同子域名分发到不同目录：

```text
blog.estevancyber.net   → /var/www/blog
tools.estevancyber.net  → /var/www/tools
```

Nginx 配置示例：

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name blog.estevancyber.net;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name blog.estevancyber.net;

    ssl_certificate /etc/nginx/ssl/estevancyber/origin.pem;
    ssl_certificate_key /etc/nginx/ssl/estevancyber/origin.key;

    root /var/www/blog;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}

server {
    listen 80;
    listen [::]:80;
    server_name tools.estevancyber.net;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name tools.estevancyber.net;

    ssl_certificate /etc/nginx/ssl/estevancyber/origin.pem;
    ssl_certificate_key /etc/nginx/ssl/estevancyber/origin.key;

    root /var/www/tools;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

检查配置：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 九、Cloudflare HTTPS 配置

最开始我直接打开橙云后遇到了 `Error 525 SSL handshake failed`。原因是 Cloudflare 到源站服务器的 HTTPS 握手失败。

临时可以使用 Flexible 模式恢复访问，但这不是长期推荐方案。

最终我选择使用 Cloudflare Origin CA 证书：

1. Cloudflare → SSL/TLS → Origin Server
2. 创建 Origin Certificate
3. Hostnames 设置为：

```text
*.estevancyber.net
estevancyber.net
```

4. 将证书保存到服务器：

```text
/etc/nginx/ssl/estevancyber/origin.pem
/etc/nginx/ssl/estevancyber/origin.key
```

5. 设置权限：

```bash
sudo chmod 600 /etc/nginx/ssl/estevancyber/origin.key
sudo chmod 644 /etc/nginx/ssl/estevancyber/origin.pem
```

6. Cloudflare SSL/TLS 模式改为：

```text
Full (strict)
```

这样最终链路就是：

```text
浏览器 → Cloudflare：HTTPS
Cloudflare → VPS Nginx：HTTPS
Nginx → 静态网站目录
```

---

## 十、部署 Hugo + PaperMod 博客

博客使用 Hugo + PaperMod 构建。

创建站点：

```bash
hugo new site estevancyber-blog
cd estevancyber-blog
```

安装 PaperMod：

```bash
git init
git submodule add --depth=1 https://github.com/adityatelange/hugo-PaperMod.git themes/PaperMod
```

注意：新版 PaperMod 对 Hugo 版本有要求。如果系统自带的 Hugo 版本太低，可以下载新版 Hugo Extended。

检查版本：

```bash
hugo version
```

构建博客：

```bash
hugo
```

发布到 Nginx 目录：

```bash
sudo rm -rf /var/www/blog/*
sudo cp -r public/* /var/www/blog/
```

---


## 总结

这次配置让我真正理解了 VPS、SSH、DNS、Nginx、Cloudflare、Docker 和博客之间的关系。

对普通用户来说，最重要的不是一开始就追求复杂架构，而是先做到：

- 能安全登录服务器
- 能更新和维护系统
- 能正确配置防火墙
- 能用域名访问网站
- 能通过 Docker 管理服务
- 能逐步形成自己的技术基础设施

这台 VPS 也会成为我后续学习 AI Agent 和部署个人项目的主要实验环境。
